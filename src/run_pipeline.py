import sys
import os
from pathlib import Path

import pandas as pd

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from utils.logger import logger
from storage.mongo import save_document_to_mongo, save_image_metadata, save_to_mongo, save_transcript_to_mongo
from storage.s3 import upload_file_to_s3
from api.client import fetch_artists
from documents.extractor import process_documents
from image_processing.batch import batch_process_images
from scraping.dynamic_scraper import scrape_dynamic_content
from scraping.scraper import scrape_local_html_samples, save_scraped_json
from ocr.ocr_utils import process_ocr_assets
from parsing.parsers import extract_artist_fields
from media_pipeline import run_media_pipeline
from utils.upload_utils import upload_batch
from analytics.numpy_ops import run_numpy_foundations
from analytics.data_loader import (
    load_available_mongo_collections,
    load_csv_data,
    optimize_dataframe_dtypes,
    process_csv_in_chunks,
    save_dataframe_csv,
)
from analytics.explorer import (
    dataframe_info_text,
    describe_dataframe,
    extract_release_year,
    inspect_structure,
    save_distribution_charts,
    value_counts_report,
)
from analytics.selector import (
    filter_by_between,
    filter_by_isin,
    filter_quality_popularity,
    filter_with_loc,
    sample_with_iloc,
    select_columns,
)
from analytics.regex_ops import (
    count_crime_terms,
    extract_numbers_from_titles,
    extract_year_from_titles,
    filter_titles_by_prefix,
    most_common_genres,
    short_overviews,
    validate_ids,
)
from analytics.quality_report import run_full_quality_audit


ROOT_DIR = Path(__file__).resolve().parents[1]
ANALYTICS_DIR = ROOT_DIR / "data" / "processed" / "analytics"
ANALYTICS_CHARTS_DIR = ANALYTICS_DIR / "charts"


def _first_existing(columns, candidates):
    for candidate in candidates:
        if candidate in columns:
            return candidate
    return None


def _numeric_columns(df: pd.DataFrame):
    return [c for c in df.select_dtypes(include="number").columns]


def run_analytics_stage():
    """Run NumPy+pandas analytics workflow and persist artifacts."""
    logger.info("Analytics stage started")
    ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)
    ANALYTICS_CHARTS_DIR.mkdir(parents=True, exist_ok=True)

    numpy_result = run_numpy_foundations()
    for name, meta in numpy_result["array_metadata"].items():
        logger.info(
            "NumPy %s -> dtype=%s shape=%s ndim=%s size=%s itemsize=%s",
            name,
            meta["dtype"],
            meta["shape"],
            meta["ndim"],
            meta["size"],
            meta["itemsize"],
        )

    combined_df = load_available_mongo_collections()
    if combined_df.empty:
        logger.warning("Analytics stage skipped: no MongoDB collections available with data")
        return

    raw_csv_path = save_dataframe_csv(combined_df, ANALYTICS_DIR / "integrated_raw_export.csv")
    df = load_csv_data(raw_csv_path)

    rating_col = _first_existing(
        df.columns,
        ["vote_average", "rating_imdb", "rating", "score", "wins", "listeners", "playcount"],
    )
    if not rating_col:
        numeric_cols = _numeric_columns(df)
        rating_col = numeric_cols[0] if numeric_cols else None

    language_col = _first_existing(df.columns, ["original_language", "language", "metadata.language"]) or "source_collection"

    if rating_col:
        chunk_stats = process_csv_in_chunks(
            raw_csv_path,
            rating_col=rating_col,
            language_col=language_col,
            chunksize=2000,
        )
        logger.info(
            "Chunk stats rating_col=%s global_mean=%s count=%s",
            rating_col,
            chunk_stats["global_mean"],
            chunk_stats["rating_count"],
        )
        pd.DataFrame(
            [{"language": k, "mean_rating": v} for k, v in chunk_stats["per_language_mean"].items()]
        ).to_csv(ANALYTICS_DIR / "chunk_language_means.csv", index=False)

    optimized_df, memory_stats = optimize_dataframe_dtypes(df)
    logger.info(
        "Dtype optimization memory MB: before=%s after=%s reduction=%s MB (%s%%)",
        memory_stats["before_mb"],
        memory_stats["after_mb"],
        memory_stats["reduction_mb"],
        memory_stats["reduction_pct"],
    )
    save_dataframe_csv(optimized_df, ANALYTICS_DIR / "integrated_optimized.csv")

    structure = inspect_structure(optimized_df)
    with open(ANALYTICS_DIR / "eda_info.txt", "w", encoding="utf-8") as fh:
        fh.write(dataframe_info_text(optimized_df))
    logger.info("EDA structure shape=%s columns=%s", structure["shape"], len(structure["columns"]))

    described = describe_dataframe(optimized_df)
    described["numeric"].to_csv(ANALYTICS_DIR / "describe_numeric.csv", index=True)
    described["categorical"].to_csv(ANALYTICS_DIR / "describe_categorical.csv", index=True)

    categorical_candidates = [
        col
        for col in ["source_collection", "original_language", "language", "status", "adult"]
        if col in optimized_df.columns
    ]
    value_reports = value_counts_report(optimized_df, categorical_candidates, top_n=15)
    for col_name, report in value_reports.items():
        report.rename_axis(col_name).reset_index(name="count").to_csv(
            ANALYTICS_DIR / f"value_counts_{col_name}.csv", index=False
        )

    release_date_col = _first_existing(optimized_df.columns, ["release_date", "metadata.release_date", "date"])
    eda_df = extract_release_year(optimized_df, date_col=release_date_col) if release_date_col else optimized_df.copy()

    dynamic_rating_cols = tuple(
        [c for c in [rating_col, "vote_average", "rating_imdb", "rating"] if c and c in eda_df.columns]
    )

    popularity_col = _first_existing(eda_df.columns, ["popularity", "vote_count", "listeners", "playcount", "wins"])
    if not popularity_col:
        numeric_cols = [c for c in _numeric_columns(eda_df) if c != rating_col]
        popularity_col = numeric_cols[0] if numeric_cols else None

    dynamic_popularity_cols = tuple([popularity_col] if popularity_col else [])

    charts = save_distribution_charts(
        eda_df,
        ANALYTICS_CHARTS_DIR,
        rating_cols=dynamic_rating_cols or ("vote_average",),
        popularity_cols=dynamic_popularity_cols or ("popularity",),
    )
    if charts:
        upload_results = upload_batch(list(charts.values()))
        logger.info("Google Drive chart uploads attempted=%s succeeded=%s", len(charts), len(upload_results))

    selected_cols = [
        col
        for col in ["title", "name", rating_col, "popularity", "original_language", "source_collection"]
        if col and col in eda_df.columns
    ]
    select_columns(eda_df, selected_cols).head(100).to_csv(ANALYTICS_DIR / "selection_columns.csv", index=False)
    sample_with_iloc(eda_df, 0, 20, 2).to_csv(ANALYTICS_DIR / "selection_iloc_sample.csv", index=False)

    if rating_col:
        rating_series = pd.to_numeric(eda_df[rating_col], errors="coerce")
        loc_filtered = filter_with_loc(eda_df, rating_series >= rating_series.median())
        loc_filtered.head(150).to_csv(ANALYTICS_DIR / "selection_loc_filtered.csv", index=False)

    if rating_col and popularity_col:
        filtered = filter_quality_popularity(
            eda_df,
            rating_col=rating_col,
            popularity_col=popularity_col,
            min_rating=6.0,
            min_popularity=10.0,
            language_col=language_col,
            language_value="en" if language_col in eda_df.columns else None,
        )
        filtered.head(200).to_csv(ANALYTICS_DIR / "selection_boolean_filtered.csv", index=False)
        between_filtered = filter_by_between(eda_df, rating_col, low=4.0, high=8.5)
        between_filtered.head(200).to_csv(ANALYTICS_DIR / "selection_between_filtered.csv", index=False)

    if language_col in eda_df.columns:
        top_langs = eda_df[language_col].astype(str).value_counts().head(3).index.tolist()
        filter_by_isin(eda_df, language_col, top_langs).head(200).to_csv(
            ANALYTICS_DIR / "selection_isin_filtered.csv", index=False
        )
        filter_by_isin(eda_df, language_col, top_langs, exclude=True).head(200).to_csv(
            ANALYTICS_DIR / "selection_isin_excluded.csv", index=False
        )

    title_col = _first_existing(eda_df.columns, ["title", "name", "metadata.file_name"])
    overview_col = _first_existing(eda_df.columns, ["overview", "summary", "description", "content"])
    regex_summary = pd.DataFrame(index=eda_df.index)

    if title_col:
        title_series = eda_df[title_col].astype(str)
        regex_summary["title_year"] = extract_year_from_titles(title_series)
        regex_summary["title_numbers"] = extract_numbers_from_titles(title_series).astype(str)
        regex_summary["title_prefix_the"] = title_series.index.isin(
            filter_titles_by_prefix(title_series, "The").index
        )

    if overview_col:
        overview_series = eda_df[overview_col].astype(str)
        regex_summary["crime_term_count"] = count_crime_terms(overview_series)
        regex_summary["short_overview"] = overview_series.index.isin(short_overviews(overview_series, max_words=8).index)

    common_genres = most_common_genres(eda_df, top_n=15)
    common_genres.rename_axis("genre").reset_index(name="count").to_csv(
        ANALYTICS_DIR / "regex_common_genres.csv", index=False
    )

    id_col = _first_existing(eda_df.columns, ["id", "movie_id", "tmdb_id", "imdb_id", "metadata.id"])
    if id_col:
        validate_ids(eda_df, id_col, source="tmdb").to_csv(ANALYTICS_DIR / "regex_id_validation.csv", index=False)

    if not regex_summary.empty:
        regex_summary.to_csv(ANALYTICS_DIR / "regex_summary.csv", index=False)

    quality_output_dir = ANALYTICS_DIR / "quality"
    quality = run_full_quality_audit(
        eda_df,
        output_dir=quality_output_dir,
        id_columns=[c for c in ["id", "movie_id", "tmdb_id", "imdb_id", "metadata.id"] if c in eda_df.columns],
        title_column=title_col or "title",
    )
    logger.info(
        "Quality audit finished: combined_report=%s heatmap=%s",
        quality["combined_path"],
        quality["heatmap_path"],
    )

    logger.info("Analytics stage finished")


def run_pipeline():
    logger.info("Starting pipeline...")

    # 1. Fetch data
    artists = []
    try:
        artists = fetch_artists(3)
        logger.info(f"Fetched {len(artists)} artists from API")
    except Exception as e:
        logger.error(f"API fetch stage failed: {e}")

    # 2. Parse and save API records to MongoDB
    api_saved = 0
    for artist in artists:
        try:
            parsed = extract_artist_fields(artist)
            save_to_mongo(parsed, "lastfm_api")
            api_saved += 1
        except Exception as e:
            logger.error(f"Failed parsing/saving artist record: {e}")
    logger.info(f"Saved {api_saved} parsed API records")

    # 3. Upload one raw page to LocalStack S3
    raw_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/raw/api/artists_page_1.json"))
    try:
        upload_file_to_s3(raw_file, "artists_page_1.json")
    except Exception as e:
        logger.error(f"S3 upload stage failed: {e}")

    # 4. Extract documents (PDF, DOCX, XLSX, TXT) and store in MongoDB
    document_records = []
    try:
        document_records = process_documents()
    except Exception as e:
        logger.error(f"Document extraction stage failed: {e}")

    for record in document_records:
        try:
            save_document_to_mongo(record, "document_extractions")
        except Exception as e:
            logger.error(f"Failed saving document record: {e}")
    logger.info(f"Saved {len(document_records)} document extraction records")

    # 5. Scrape web content (local single+multi and dynamic JSON/JS flows)
    scraped_records = []
    dynamic_records = []
    try:
        scraped_records = scrape_local_html_samples(pages=3)
    except Exception as e:
        logger.error(f"Static/local scraping stage failed: {e}")

    try:
        dynamic_records = scrape_dynamic_content()
    except Exception as e:
        logger.error(f"Dynamic scraping stage failed: {e}")

    all_scraped = scraped_records + dynamic_records
    try:
        save_scraped_json(all_scraped, "all_scraped_records.json")
    except Exception as e:
        logger.error(f"Failed saving scraped JSON file: {e}")

    for record in all_scraped:
        try:
            save_document_to_mongo(record, "scraped_web_data")
        except Exception as e:
            logger.error(f"Failed saving scraped record to MongoDB: {e}")
    logger.info(f"Saved {len(all_scraped)} scraped web records")

    # 6. OCR image + scanned PDF and store outputs
    ocr_records = []
    try:
        ocr_records = process_ocr_assets()
    except Exception as e:
        logger.error(f"OCR stage failed: {e}")

    for record in ocr_records:
        try:
            save_document_to_mongo(record, "ocr_results")
        except Exception as e:
            logger.error(f"Failed saving OCR record: {e}")
    logger.info(f"Saved {len(ocr_records)} OCR records")

    # 7. Image processing stage (download, process, EXIF, optional Google Drive upload)
    image_records = []
    try:
        image_records = batch_process_images(max_images=50, upload_to_drive=False)
    except Exception as e:
        logger.error(f"Image processing stage failed: {e}")

    for record in image_records:
        try:
            save_image_metadata(record, "image_metadata")
        except Exception as e:
            logger.error(f"Failed saving image metadata: {e}")
    logger.info(f"Saved {len(image_records)} image metadata records")

    # 8. Audio/Video processing + transcription stage
    media_summary = {}
    try:
        media_summary = run_media_pipeline()
        logger.info(
            "Media stage summary: "
            f"audio_inspection={len(media_summary.get('audio_inspection', []))}, "
            f"video_inspection={len(media_summary.get('video_inspection', []))}, "
            f"transcripts={len(media_summary.get('transcripts', []))}, "
            f"frames={len(media_summary.get('frames', []))}"
        )
    except Exception as e:
        logger.error(f"Media pipeline stage failed: {e}")

    # Persist generated transcript payloads if available in summary files.
    try:
        transcript_items = media_summary.get("transcripts", []) if media_summary else []
        for item in transcript_items:
            json_path = item.get("outputs", {}).get("json")
            if not json_path:
                continue
            try:
                import json

                with open(json_path, "r", encoding="utf-8") as fh:
                    payload = json.load(fh)
                save_transcript_to_mongo(payload, "transcripts")
            except Exception as inner_exc:
                logger.error(f"Failed persisting transcript JSON {json_path}: {inner_exc}")
    except Exception as e:
        logger.error(f"Transcript persistence stage failed: {e}")

    # 9. Analytics stage (NumPy, pandas EDA, filtering, regex, quality reports)
    try:
        run_analytics_stage()
    except Exception as e:
        logger.error(f"Analytics stage failed: {e}")

    logger.info("Pipeline finished")

if __name__ == "__main__":
    run_pipeline()

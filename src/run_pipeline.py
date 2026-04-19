import sys
import os

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

    logger.info("Pipeline finished")

if __name__ == "__main__":
    run_pipeline()

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple

import pandas as pd
from pymongo import MongoClient

from utils.logger import logger


ROOT_DIR = Path(__file__).resolve().parents[2]
ANALYTICS_DIR = ROOT_DIR / "data" / "processed" / "analytics"


def _memory_usage_mb(df: pd.DataFrame) -> float:
    return float(df.memory_usage(deep=True).sum() / (1024 ** 2))


def get_mongo_client(uri: str = "mongodb://localhost:27017/") -> MongoClient:
    return MongoClient(uri, serverSelectionTimeoutMS=3000)


def load_mongo_collection(
    collection_name: str,
    db_name: str = "music_pipeline",
    uri: str = "mongodb://localhost:27017/",
) -> pd.DataFrame:
    """Load a MongoDB collection and flatten nested records."""
    client = get_mongo_client(uri)
    try:
        records = list(client[db_name][collection_name].find({}, {"_id": 0}))
    finally:
        client.close()

    if not records:
        return pd.DataFrame()

    return pd.json_normalize(records)


def load_available_mongo_collections(
    preferred_collections: Optional[Iterable[str]] = None,
    db_name: str = "music_pipeline",
    uri: str = "mongodb://localhost:27017/",
) -> pd.DataFrame:
    """Load and combine available collections with provenance column."""
    preferred = list(
        preferred_collections
        or [
            "tmdb_movies",
            "movies",
            "scraped_web_data",
            "lastfm_api",
            "lastfm_json",
            "lastfm_csv",
            "lastfm_xml",
            "document_extractions",
            "ocr_results",
            "image_metadata",
            "transcripts",
        ]
    )

    client = get_mongo_client(uri)
    try:
        available = set(client[db_name].list_collection_names())
    finally:
        client.close()

    frames = []
    for name in preferred:
        if name not in available:
            continue
        df = load_mongo_collection(name, db_name=db_name, uri=uri)
        if df.empty:
            continue
        df["source_collection"] = name
        frames.append(df)

    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True, sort=False)
    logger.info("Loaded %s rows from %s collections", len(combined), len(frames))
    return combined


def save_dataframe_csv(df: pd.DataFrame, output_path: str | Path) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)
    logger.info("Saved CSV export: %s", output)
    return output


def load_csv_data(csv_path: str | Path, **kwargs) -> pd.DataFrame:
    return pd.read_csv(csv_path, **kwargs)


def process_csv_in_chunks(
    csv_path: str | Path,
    rating_col: str,
    language_col: str = "original_language",
    chunksize: int = 2000,
) -> Dict[str, object]:
    """Compute global rating mean and per-language stats from chunked reads."""
    total_sum = 0.0
    total_count = 0
    language_sums: Dict[str, float] = {}
    language_counts: Dict[str, int] = {}

    for chunk in pd.read_csv(csv_path, chunksize=chunksize):
        if rating_col not in chunk.columns:
            continue

        ratings = pd.to_numeric(chunk[rating_col], errors="coerce").dropna()
        total_sum += float(ratings.sum())
        total_count += int(ratings.count())

        if language_col in chunk.columns:
            grouped = chunk.assign(
                _rating_num=pd.to_numeric(chunk[rating_col], errors="coerce"),
                _lang=chunk[language_col].fillna("unknown").astype(str),
            )[["_lang", "_rating_num"]].dropna(subset=["_rating_num"])

            agg = grouped.groupby("_lang")["_rating_num"].agg(["sum", "count"])
            for lang, row in agg.iterrows():
                language_sums[lang] = language_sums.get(lang, 0.0) + float(row["sum"])
                language_counts[lang] = language_counts.get(lang, 0) + int(row["count"])

    global_mean = total_sum / total_count if total_count else None
    per_language_mean = {
        lang: (language_sums[lang] / language_counts[lang])
        for lang in language_sums
        if language_counts.get(lang)
    }

    return {
        "global_mean": global_mean,
        "rating_count": total_count,
        "per_language_mean": dict(sorted(per_language_mean.items(), key=lambda x: x[0])),
    }


def optimize_dataframe_dtypes(
    df: pd.DataFrame,
    category_threshold: float = 0.3,
) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """Downcast numerics and convert low-cardinality objects to category."""
    optimized = df.copy()
    before_mb = _memory_usage_mb(optimized)

    for col in optimized.select_dtypes(include=["int64", "int32"]).columns:
        optimized[col] = pd.to_numeric(optimized[col], downcast="integer")

    for col in optimized.select_dtypes(include=["float64", "float32"]).columns:
        optimized[col] = pd.to_numeric(optimized[col], downcast="float")

    for col in optimized.select_dtypes(include=["object"]).columns:
        unique_ratio = optimized[col].nunique(dropna=False) / max(len(optimized), 1)
        if unique_ratio <= category_threshold:
            optimized[col] = optimized[col].astype("category")

    after_mb = _memory_usage_mb(optimized)
    reduction_mb = before_mb - after_mb
    reduction_pct = (reduction_mb / before_mb * 100) if before_mb else 0.0

    stats = {
        "before_mb": round(before_mb, 4),
        "after_mb": round(after_mb, 4),
        "reduction_mb": round(reduction_mb, 4),
        "reduction_pct": round(reduction_pct, 2),
    }
    logger.info("Memory usage before=%sMB after=%sMB reduction=%s%%", stats["before_mb"], stats["after_mb"], stats["reduction_pct"])
    return optimized, stats

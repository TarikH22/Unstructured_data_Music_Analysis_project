from __future__ import annotations

import re
from collections import Counter
from typing import Dict, Iterable, List

import pandas as pd


YEAR_PATTERN = re.compile(r"\b(19\d{2}|20\d{2})\b")
NUMBER_PATTERN = re.compile(r"\b\d+(?:\.\d+)?\b")
CRIME_PATTERN = re.compile(r"\b(crime|murder|police|detective|gang|mafia|heist|court|trial|prison)\b", re.IGNORECASE)

TMDB_ID_PATTERN = re.compile(r"^\d{1,10}$")
SCRAPED_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{3,50}$")
LOCAL_ID_PATTERN = re.compile(r"^(movie|mv|id)?[_-]?\d{1,10}$", re.IGNORECASE)

TMDB_GENRE_MAP = {
    28: "Action",
    12: "Adventure",
    16: "Animation",
    35: "Comedy",
    80: "Crime",
    99: "Documentary",
    18: "Drama",
    10751: "Family",
    14: "Fantasy",
    36: "History",
    27: "Horror",
    10402: "Music",
    9648: "Mystery",
    10749: "Romance",
    878: "Sci-Fi",
    53: "Thriller",
    10752: "War",
    37: "Western",
}


def extract_year_from_titles(series: pd.Series) -> pd.Series:
    return series.astype(str).str.extract(YEAR_PATTERN, expand=False)


def extract_numbers_from_titles(series: pd.Series) -> pd.Series:
    return series.astype(str).str.findall(NUMBER_PATTERN)


def filter_titles_by_prefix(series: pd.Series, prefix: str, case_sensitive: bool = False) -> pd.Series:
    escaped = re.escape(prefix)
    flags = 0 if case_sensitive else re.IGNORECASE
    matcher = re.compile(rf"^{escaped}", flags=flags)
    return series[series.astype(str).str.match(matcher, na=False)]


def count_crime_terms(series: pd.Series) -> pd.Series:
    return series.astype(str).str.count(CRIME_PATTERN)


def short_overviews(series: pd.Series, max_words: int = 8) -> pd.Series:
    word_count = series.fillna("").astype(str).str.split().str.len()
    return series[word_count <= max_words]


def _parse_genre_entry(value) -> List[str]:
    if pd.isna(value):
        return []

    if isinstance(value, list):
        parsed: List[str] = []
        for item in value:
            if isinstance(item, dict) and "name" in item:
                parsed.append(str(item["name"]))
            elif isinstance(item, int):
                parsed.append(TMDB_GENRE_MAP.get(item, f"genre_{item}"))
            else:
                parsed.append(str(item))
        return parsed

    text = str(value).strip()
    if text.startswith("[") and text.endswith("]"):
        nums = [int(x) for x in re.findall(r"\d+", text)]
        if nums:
            return [TMDB_GENRE_MAP.get(x, f"genre_{x}") for x in nums]

    parts = re.split(r"[,|;/]", text)
    return [p.strip() for p in parts if p.strip()]


def parse_genres(df: pd.DataFrame, genre_columns: Iterable[str] = ("genres", "genre_ids", "genre", "metadata.genres")) -> pd.Series:
    collected: List[str] = []
    for col in genre_columns:
        if col not in df.columns:
            continue
        for value in df[col]:
            collected.extend(_parse_genre_entry(value))
    return pd.Series(collected, dtype="object", name="genre_name")


def most_common_genres(df: pd.DataFrame, top_n: int = 10) -> pd.Series:
    parsed = parse_genres(df)
    if parsed.empty:
        return pd.Series(dtype="int64")
    return parsed.value_counts().head(top_n)


def validate_ids(df: pd.DataFrame, column: str, source: str = "tmdb") -> pd.DataFrame:
    if column not in df.columns:
        return pd.DataFrame(columns=[column, "id_valid"])

    pattern_map = {
        "tmdb": TMDB_ID_PATTERN,
        "scraped": SCRAPED_ID_PATTERN,
        "local": LOCAL_ID_PATTERN,
    }
    pattern = pattern_map.get(source, SCRAPED_ID_PATTERN)

    out = df[[column]].copy()
    out["id_valid"] = out[column].astype(str).str.match(pattern, na=False)
    return out


# LAB 9: CLEANING HELPER FUNCTIONS

def validate_date_format(series: pd.Series) -> pd.Series:
    """Returns boolean mask where True means valid YYYY-MM-DD pattern."""
    return series.astype(str).str.match(r'^\d{4}-\d{2}-\d{2}$')

def validate_language_codes(series: pd.Series) -> pd.Series:
    """Returns boolean mask where True means valid 2-letter language code."""
    return series.astype(str).str.match(r'^[a-zA-Z]{2}$')

def extract_numeric_from_text(series: pd.Series) -> pd.Series:
    """Extracts first numeric group/pattern from string."""
    return series.astype(str).str.extract(r'(\d+\.?\d*)', expand=False)

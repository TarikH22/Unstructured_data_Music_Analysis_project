from __future__ import annotations

from io import StringIO
from pathlib import Path
from typing import Dict, Iterable

import matplotlib.pyplot as plt
import pandas as pd

from utils.logger import logger


def inspect_structure(df: pd.DataFrame) -> Dict[str, object]:
    return {
        "shape": df.shape,
        "columns": list(df.columns),
        "dtypes": {k: str(v) for k, v in df.dtypes.items()},
        "nunique": df.nunique(dropna=False).to_dict(),
    }


def dataframe_info_text(df: pd.DataFrame) -> str:
    buffer = StringIO()
    df.info(buf=buffer)
    return buffer.getvalue()


def describe_dataframe(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    numeric = df.describe(include=["number"]).transpose() if not df.empty else pd.DataFrame()
    categorical = df.describe(include=["object", "category", "bool"]).transpose() if not df.empty else pd.DataFrame()
    return {"numeric": numeric, "categorical": categorical}


def value_counts_report(df: pd.DataFrame, columns: Iterable[str], top_n: int = 10) -> Dict[str, pd.Series]:
    report: Dict[str, pd.Series] = {}
    for col in columns:
        if col in df.columns:
            report[col] = df[col].astype(str).value_counts(dropna=False).head(top_n)
    return report


def extract_release_year(df: pd.DataFrame, date_col: str = "release_date") -> pd.DataFrame:
    out = df.copy()
    if date_col in out.columns:
        out["release_year"] = pd.to_datetime(out[date_col], errors="coerce").dt.year
    return out


def _save_hist(series: pd.Series, path: Path, title: str) -> None:
    plt.figure(figsize=(9, 5))
    plt.hist(series.dropna(), bins=30, edgecolor="black")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(path, dpi=120)
    plt.close()


def _save_bar(series: pd.Series, path: Path, title: str, top_n: int = 12) -> None:
    counts = series.astype(str).value_counts(dropna=False).head(top_n)
    plt.figure(figsize=(10, 5))
    counts.plot(kind="bar")
    plt.title(title)
    plt.ylabel("count")
    plt.tight_layout()
    plt.savefig(path, dpi=120)
    plt.close()


def save_distribution_charts(
    df: pd.DataFrame,
    output_dir: str | Path,
    rating_cols: Iterable[str] = ("vote_average", "rating_imdb", "rating"),
    popularity_cols: Iterable[str] = ("popularity",),
    language_cols: Iterable[str] = ("original_language", "language"),
) -> Dict[str, str]:
    """Save distribution charts for available columns and return output map."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    saved: Dict[str, str] = {}

    for col in rating_cols:
        if col in df.columns:
            numeric = pd.to_numeric(df[col], errors="coerce")
            if numeric.notna().any():
                path = out / f"distribution_{col}.png"
                _save_hist(numeric, path, f"Distribution: {col}")
                saved[col] = str(path)

    for col in popularity_cols:
        if col in df.columns:
            numeric = pd.to_numeric(df[col], errors="coerce")
            if numeric.notna().any():
                path = out / f"distribution_{col}.png"
                _save_hist(numeric, path, f"Distribution: {col}")
                saved[col] = str(path)

    for col in language_cols:
        if col in df.columns:
            path = out / f"distribution_{col}.png"
            _save_bar(df[col], path, f"Top values: {col}")
            saved[col] = str(path)

    if "release_year" in df.columns:
        numeric_year = pd.to_numeric(df["release_year"], errors="coerce")
        if numeric_year.notna().any():
            path = out / "distribution_release_year.png"
            _save_hist(numeric_year, path, "Distribution: release_year")
            saved["release_year"] = str(path)

    logger.info("Saved %s EDA charts", len(saved))
    return saved

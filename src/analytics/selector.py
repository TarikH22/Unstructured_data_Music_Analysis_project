from __future__ import annotations

from typing import Iterable, Optional

import pandas as pd


def select_columns(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    keep = [c for c in columns if c in df.columns]
    return df.loc[:, keep].copy()


def filter_with_loc(df: pd.DataFrame, mask: pd.Series, columns: Optional[Iterable[str]] = None) -> pd.DataFrame:
    if columns is None:
        return df.loc[mask].copy()
    keep = [c for c in columns if c in df.columns]
    return df.loc[mask, keep].copy()


def sample_with_iloc(
    df: pd.DataFrame,
    row_start: int = 0,
    row_stop: int = 10,
    row_step: int = 1,
    col_start: Optional[int] = None,
    col_stop: Optional[int] = None,
) -> pd.DataFrame:
    if col_start is None and col_stop is None:
        return df.iloc[row_start:row_stop:row_step].copy()
    return df.iloc[row_start:row_stop:row_step, col_start:col_stop].copy()


def filter_quality_popularity(
    df: pd.DataFrame,
    rating_col: str,
    popularity_col: str,
    min_rating: float = 6.5,
    min_popularity: float = 20.0,
    language_col: Optional[str] = None,
    language_value: Optional[str] = None,
) -> pd.DataFrame:
    out = df.copy()

    if rating_col in out.columns:
        out = out[pd.to_numeric(out[rating_col], errors="coerce") >= min_rating]
    if popularity_col in out.columns:
        out = out[pd.to_numeric(out[popularity_col], errors="coerce") >= min_popularity]

    if language_col and language_value and language_col in out.columns:
        out = out[out[language_col].astype(str).str.lower() == language_value.lower()]

    return out.copy()


def filter_by_isin(
    df: pd.DataFrame,
    column: str,
    values: Iterable,
    exclude: bool = False,
) -> pd.DataFrame:
    if column not in df.columns:
        return df.iloc[0:0].copy()
    mask = df[column].isin(values)
    if exclude:
        mask = ~mask
    return df.loc[mask].copy()


def filter_by_between(
    df: pd.DataFrame,
    column: str,
    low: float,
    high: float,
    inclusive: str = "both",
) -> pd.DataFrame:
    if column not in df.columns:
        return df.iloc[0:0].copy()
    numeric = pd.to_numeric(df[column], errors="coerce")
    mask = numeric.between(low, high, inclusive=inclusive)
    return df.loc[mask].copy()

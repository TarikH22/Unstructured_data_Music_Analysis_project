from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Optional

import matplotlib.pyplot as plt
import pandas as pd

from utils.logger import logger


def missing_value_report(df: pd.DataFrame) -> pd.DataFrame:
    total = len(df)
    missing = df.isna().sum()
    pct = (missing / total * 100).round(2) if total else pd.Series(0, index=df.columns)

    report = pd.DataFrame(
        {
            "column": df.columns,
            "missing_count": missing.values,
            "missing_pct": pct.values,
        }
    )

    def severity(score: float) -> str:
        if score >= 40:
            return "high"
        if score >= 15:
            return "medium"
        if score > 0:
            return "low"
        return "none"

    report["severity"] = report["missing_pct"].apply(severity)
    return report.sort_values(["missing_pct", "missing_count"], ascending=False).reset_index(drop=True)


def detect_zero_as_missing(df: pd.DataFrame, columns: Optional[Iterable[str]] = None) -> pd.DataFrame:
    if columns is None:
        financial_like = [c for c in df.columns if any(k in c.lower() for k in ("revenue", "budget", "gross", "income"))]
        columns = financial_like

    rows: List[Dict[str, object]] = []
    for col in columns:
        if col not in df.columns:
            continue
        numeric = pd.to_numeric(df[col], errors="coerce")
        valid = numeric.dropna()
        zero_count = int((valid == 0).sum())
        rows.append(
            {
                "column": col,
                "non_null_count": int(valid.count()),
                "zero_count": zero_count,
                "zero_pct": round((zero_count / max(int(valid.count()), 1)) * 100, 2),
            }
        )

    return pd.DataFrame(rows)


def iqr_outlier_detection(df: pd.DataFrame, numeric_columns: Optional[Iterable[str]] = None) -> pd.DataFrame:
    if numeric_columns is None:
        numeric_columns = df.select_dtypes(include=["number"]).columns

    rows: List[Dict[str, object]] = []
    for col in numeric_columns:
        if col not in df.columns:
            continue
        series = pd.to_numeric(df[col], errors="coerce").dropna()
        if series.empty:
            continue
        q1 = float(series.quantile(0.25))
        q3 = float(series.quantile(0.75))
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outliers = series[(series < lower) | (series > upper)]

        rows.append(
            {
                "column": col,
                "q1": round(q1, 4),
                "q3": round(q3, 4),
                "iqr": round(iqr, 4),
                "lower_bound": round(lower, 4),
                "upper_bound": round(upper, 4),
                "outlier_count": int(outliers.count()),
                "outlier_pct": round((outliers.count() / max(series.count(), 1)) * 100, 2),
            }
        )

    return pd.DataFrame(rows).sort_values("outlier_pct", ascending=False)


def rating_validity_report(df: pd.DataFrame, rating_columns: Optional[Iterable[str]] = None) -> pd.DataFrame:
    if rating_columns is None:
        rating_columns = [c for c in df.columns if any(k in c.lower() for k in ("rating", "vote_average", "score"))]

    rows: List[Dict[str, object]] = []
    for col in rating_columns:
        if col not in df.columns:
            continue
        numeric = pd.to_numeric(df[col], errors="coerce")
        non_null = numeric.dropna()
        invalid = non_null[(non_null < 0) | (non_null > 10)]
        rows.append(
            {
                "column": col,
                "non_null_count": int(non_null.count()),
                "invalid_count": int(invalid.count()),
                "invalid_pct": round((invalid.count() / max(non_null.count(), 1)) * 100, 2),
            }
        )

    return pd.DataFrame(rows)


def id_and_title_checks(
    df: pd.DataFrame,
    id_columns: Optional[Iterable[str]] = None,
    title_column: str = "title",
) -> pd.DataFrame:
    if id_columns is None:
        id_columns = [c for c in df.columns if c.lower() in {"id", "movie_id", "tmdb_id", "imdb_id", "local_id"}]

    rows: List[Dict[str, object]] = []

    for col in id_columns:
        if col not in df.columns:
            continue
        duplicated = int(df[col].duplicated(keep=False).sum())
        rows.append({"check": "duplicate_ids", "column": col, "issue_count": duplicated})

    if title_column in df.columns:
        title_series = df[title_column].astype(str)
        missing_titles = int(df[title_column].isna().sum())
        empty_titles = int((title_series.str.strip() == "").sum())
        weird_titles = int((~title_series.str.match(r"^[\w\s\-:,.!?()'\"&/]+$", na=False)).sum())
        rows.extend(
            [
                {"check": "missing_titles", "column": title_column, "issue_count": missing_titles},
                {"check": "empty_titles", "column": title_column, "issue_count": empty_titles},
                {"check": "inconsistent_title_format", "column": title_column, "issue_count": weird_titles},
            ]
        )

    return pd.DataFrame(rows)


def save_missing_heatmap(df: pd.DataFrame, output_path: str | Path, max_rows: int = 250, max_cols: int = 30) -> Path:
    sample = df.copy()
    if len(sample) > max_rows:
        sample = sample.sample(max_rows, random_state=42)
    if sample.shape[1] > max_cols:
        sample = sample.iloc[:, :max_cols]

    matrix = sample.isna().astype(int)

    plt.figure(figsize=(12, 6))
    plt.imshow(matrix, aspect="auto", interpolation="nearest")
    plt.title("Missing Data Heatmap (1 = missing)")
    plt.xlabel("columns")
    plt.ylabel("rows")
    plt.tight_layout()

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out, dpi=120)
    plt.close()
    return out


def run_full_quality_audit(
    df: pd.DataFrame,
    output_dir: str | Path,
    id_columns: Optional[Iterable[str]] = None,
    title_column: str = "title",
) -> Dict[str, object]:
    """Run all quality checks and save CSV reports + heatmap."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    missing = missing_value_report(df)
    zeros = detect_zero_as_missing(df)
    outliers = iqr_outlier_detection(df)
    ratings = rating_validity_report(df)
    id_title = id_and_title_checks(df, id_columns=id_columns, title_column=title_column)

    heatmap_path = save_missing_heatmap(df, out / "missing_heatmap.png")

    missing.to_csv(out / "missing_value_report.csv", index=False)
    zeros.to_csv(out / "zero_as_missing_report.csv", index=False)
    outliers.to_csv(out / "outlier_report.csv", index=False)
    ratings.to_csv(out / "rating_validity_report.csv", index=False)
    id_title.to_csv(out / "id_title_quality_report.csv", index=False)

    combined = pd.concat(
        [
            missing.assign(report="missing"),
            zeros.assign(report="zero_as_missing"),
            outliers.assign(report="outliers"),
            ratings.assign(report="rating_validity"),
            id_title.assign(report="id_title_checks"),
        ],
        ignore_index=True,
        sort=False,
    )
    combined_path = out / "full_quality_issues_report.csv"
    combined.to_csv(combined_path, index=False)

    logger.info("Saved full quality report to %s", combined_path)

    return {
        "missing": missing,
        "zeros": zeros,
        "outliers": outliers,
        "ratings": ratings,
        "id_title": id_title,
        "combined_path": str(combined_path),
        "heatmap_path": str(heatmap_path),
    }

from __future__ import annotations

import os
from io import StringIO
from pathlib import Path
from typing import Dict, Iterable, Optional

import matplotlib.pyplot as plt
import pandas as pd
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

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


def get_google_drive_service():
    """Authenticate with Google Drive API using service account or application default credentials."""
    try:
        # Try service account credentials first
        creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if creds_path and Path(creds_path).exists():
            creds = Credentials.from_service_account_file(
                creds_path,
                scopes=["https://www.googleapis.com/auth/drive"],
            )
            service = build("drive", "v3", credentials=creds)
            logger.info("Google Drive service authenticated with service account")
            return service
    except Exception as e:
        logger.warning("Service account authentication failed: %s", e)

    try:
        # Try application default credentials
        from google.auth import default

        creds, _ = default(scopes=["https://www.googleapis.com/auth/drive"])
        service = build("drive", "v3", credentials=creds)
        logger.info("Google Drive service authenticated with application default credentials")
        return service
    except Exception as e:
        logger.warning("Application default credentials failed: %s", e)
        return None


def upload_charts_to_google_drive(
    chart_dir: str | Path,
    folder_name: str = "Movie Analytics EDA Charts",
    share_email: Optional[str] = None,
) -> Dict[str, object]:
    """Upload EDA charts to Google Drive and optionally share with an email.
    
    Args:
        chart_dir: Directory containing PNG chart files
        folder_name: Name of Google Drive folder to create
        share_email: Email to share the folder with (default: Amila's email from env or None)
    
    Returns:
        Dictionary with folder_id, uploaded_files, and share_results
    """
    service = get_google_drive_service()
    if service is None:
        logger.warning("Could not authenticate with Google Drive. Charts saved locally but not uploaded.")
        return {
            "folder_id": None,
            "uploaded_files": [],
            "share_results": [],
            "status": "skipped_no_credentials",
        }

    chart_path = Path(chart_dir)
    if not chart_path.exists():
        logger.warning("Chart directory does not exist: %s", chart_path)
        return {"folder_id": None, "uploaded_files": [], "share_results": [], "status": "failed_no_dir"}

    chart_files = sorted(chart_path.glob("*.png"))
    if not chart_files:
        logger.warning("No PNG files found in %s", chart_path)
        return {"folder_id": None, "uploaded_files": [], "share_results": [], "status": "no_charts"}

    try:
        # Create folder in Google Drive
        folder_metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        folder = service.files().create(body=folder_metadata, fields="id").execute()
        folder_id = folder.get("id")
        logger.info("Created Google Drive folder: %s (id=%s)", folder_name, folder_id)

        # Upload charts
        uploaded_files = []
        for chart_file in chart_files:
            file_metadata = {
                "name": chart_file.name,
                "parents": [folder_id],
            }
            media = MediaFileUpload(str(chart_file), mimetype="image/png")
            uploaded = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
            uploaded_files.append({
                "filename": chart_file.name,
                "drive_id": uploaded.get("id"),
            })
            logger.info("Uploaded chart to Google Drive: %s", chart_file.name)

        # Share folder with email if provided
        share_results = []
        if share_email:
            try:
                share_body = {
                    "role": "reader",
                    "type": "user",
                    "emailAddress": share_email,
                }
                service.permissions().create(
                    fileId=folder_id,
                    body=share_body,
                    fields="id",
                ).execute()
                share_results.append({
                    "email": share_email,
                    "status": "success",
                })
                logger.info("Shared Google Drive folder with %s", share_email)
            except Exception as e:
                logger.warning("Failed to share folder with %s: %s", share_email, e)
                share_results.append({
                    "email": share_email,
                    "status": "failed",
                    "error": str(e),
                })

        return {
            "folder_id": folder_id,
            "folder_name": folder_name,
            "uploaded_files": uploaded_files,
            "share_results": share_results,
            "status": "success",
        }

    except Exception as e:
        logger.error("Error uploading charts to Google Drive: %s", e)
        return {
            "folder_id": None,
            "uploaded_files": [],
            "share_results": [],
            "status": "failed",
            "error": str(e),
        }

"""
io_utils.py
Utility functions for reading various unstructured file types used in the
Unstructured Data Music Analysis pipeline.

Supported file types:
    - JSON   (artist info, top tracks)
    - Text   (artist bio, lyrics)
    - Image  (artist photo, album art)  — requires Pillow
    - SRT    (video subtitles)

All functions use the shared logger; call setup_logging() once at the
start of your script to route logs to a file.
"""
from __future__ import annotations  # enables str | Path union syntax on Python 3.9

import json
import logging
from pathlib import Path

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


# ── Logging setup ─────────────────────────────────────────────────────────────

def setup_logging(log_file: str = "pipeline.log") -> None:
    """
    Configure file-based logging for the pipeline.

    Args:
        log_file: Path to the log file (relative to cwd or absolute).

    Log format example:
        2026-03-04 15:45:02,051 - INFO - Successfully read JSON file: ...
    """
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )


# ── JSON reader ───────────────────────────────────────────────────────────────

def read_json(file_path: str | Path) -> dict | None:
    """
    Read a JSON file and return its contents as a Python dictionary.

    Handles:
        - FileNotFoundError  → logs error, returns None
        - JSONDecodeError    → logs error, returns None

    Args:
        file_path: Path to the .json file.

    Returns:
        Parsed dictionary, or None on failure.

    Example log (success):
        2026-03-04 15:45:02 - INFO - Successfully read JSON file: data/raw/lastfm/artist_coldplay.json
    Example log (failure):
        2026-03-04 15:40:38 - ERROR - File not found: data/raw/lastfm/artist_coldplay.json
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logging.info(f"Successfully read JSON file: {file_path}")
        return data
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON format in file: {file_path}")
    return None


# ── Text reader ───────────────────────────────────────────────────────────────

def read_text(file_path: str | Path) -> str | None:
    """
    Read a plain-text file (bio, lyrics, review) and return its content.

    Handles:
        - FileNotFoundError → logs error, returns None

    Args:
        file_path: Path to the .txt file.

    Returns:
        Full file content as a string, or None on failure.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        logging.info(f"Successfully read text file: {file_path}")
        return text
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
    return None


# ── Image reader ──────────────────────────────────────────────────────────────

def read_image(file_path: str | Path):
    """
    Open an image file (artist photo, album art) using Pillow.

    If Pillow is not installed, returns a basic dict with file metadata
    instead of raising an error.

    Handles:
        - FileNotFoundError → logs error, returns None
        - Any PIL exception  → logs error, returns None

    Args:
        file_path: Path to the image file (.jpg, .png, etc.).

    Returns:
        PIL.Image.Image object if Pillow is available,
        dict {"path": ..., "bytes": ...} if Pillow is missing,
        or None on failure.
    """
    file_path = Path(file_path)

    if not file_path.exists():
        logging.error(f"File not found: {file_path}")
        return None

    if PIL_AVAILABLE:
        try:
            img = Image.open(file_path)
            logging.info(
                f"Successfully read image: {file_path} "
                f"| size={img.size} | mode={img.mode}"
            )
            return img
        except Exception as exc:
            logging.error(f"Failed to open image {file_path}: {exc}")
            return None
    else:
        size = file_path.stat().st_size
        logging.info(
            f"Read image (Pillow not installed): {file_path} | bytes={size}"
        )
        return {"path": str(file_path), "bytes": size}


# ── SRT reader ────────────────────────────────────────────────────────────────

def read_srt(file_path: str | Path) -> list[dict] | None:
    """
    Parse an SRT subtitle file into a list of structured entries.

    SRT block format:
        1
        00:00:01,000 --> 00:00:04,000
        Subtitle text here

    Each entry in the returned list has keys:
        index (int), start (str), end (str), text (str)

    Handles:
        - FileNotFoundError → logs error, returns None
        - Malformed blocks  → silently skipped

    Args:
        file_path: Path to the .srt file.

    Returns:
        List of subtitle entry dicts, or None on failure.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        logging.info(f"Successfully read SRT file: {file_path}")
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        return None

    entries = []
    for block in content.strip().split("\n\n"):
        lines = block.strip().splitlines()
        if len(lines) < 3:
            continue
        try:
            index = int(lines[0].strip())
            start, end = lines[1].strip().split(" --> ")
            text = " ".join(lines[2:]).strip()
            entries.append({"index": index, "start": start, "end": end, "text": text})
        except (ValueError, IndexError):
            continue

    logging.info(f"Parsed {len(entries)} subtitle entries from: {file_path}")
    return entries

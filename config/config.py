"""
Central configuration for the Unstructured Data Music Analysis project.
Loads settings from environment variables (via .env file).
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Resolve project root (one level up from config/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load .env from project root
load_dotenv(PROJECT_ROOT / ".env")

# ---------------------------------------------------------------------------
# Last.fm API
# ---------------------------------------------------------------------------
LASTFM_API_KEY: str = os.getenv("LASTFM_API_KEY", "")
LASTFM_API_SECRET: str = os.getenv("LASTFM_API_SECRET", "")
LASTFM_BASE_URL: str = "https://ws.audioscrobbler.com/2.0/"

# ---------------------------------------------------------------------------
# Data paths
# ---------------------------------------------------------------------------
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

RAW_TEXT_DIR = RAW_DIR / "text"
RAW_VIDEO_DIR = RAW_DIR / "video"
RAW_JSON_DIR = RAW_DIR / "json"
RAW_IMAGES_DIR = RAW_DIR / "images"

PROCESSED_TEXT_DIR = PROCESSED_DIR / "text"
PROCESSED_VIDEO_DIR = PROCESSED_DIR / "video"
PROCESSED_JSON_DIR = PROCESSED_DIR / "json"
PROCESSED_IMAGES_DIR = PROCESSED_DIR / "images"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

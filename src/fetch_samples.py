# fetch_samples.py — pulls data from Last.fm and saves raw files
# Run: python src/fetch_samples.py

import json
import logging
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

API_KEY  = os.getenv("LASTFM_API_KEY", "")
BASE_URL = "https://ws.audioscrobbler.com/2.0/"

RAW_DIR     = PROJECT_ROOT / "data" / "raw"
LASTFM_DIR  = RAW_DIR / "lastfm"
IMAGES_DIR  = RAW_DIR / "images"
VIDEO_DIR   = RAW_DIR / "video"
REVIEWS_DIR = RAW_DIR / "reviews"
ALBUMS_DIR  = RAW_DIR / "albums"
LOGS_DIR    = PROJECT_ROOT / "logs"

for d in [LASTFM_DIR, IMAGES_DIR, VIDEO_DIR, REVIEWS_DIR, ALBUMS_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "fetch_samples.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

ARTIST = "Coldplay"


def _safe_name(name: str) -> str:
    return name.lower().replace(" ", "_")


def fetch_artist_info(artist: str) -> dict:
    """artist.getinfo → data/raw/lastfm/artist_<name>.json"""
    params = {"method": "artist.getinfo", "artist": artist, "api_key": API_KEY, "format": "json"}
    resp = requests.get(BASE_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    out_path = LASTFM_DIR / f"artist_{_safe_name(artist)}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    logging.info(f"[1/5] Saved artist info  → {out_path}")
    return data


def fetch_top_tracks(artist: str) -> dict:
    """artist.gettoptracks → data/raw/lastfm/artist_<name>_toptracks.json"""
    params = {"method": "artist.gettoptracks", "artist": artist, "api_key": API_KEY, "format": "json", "limit": 5}
    resp = requests.get(BASE_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    out_path = LASTFM_DIR / f"artist_{_safe_name(artist)}_toptracks.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    logging.info(f"[2/5] Saved top tracks   → {out_path}")
    return data


def fetch_top_albums(artist: str) -> dict:
    """artist.gettopalbums → data/raw/albums/artist_<name>_albums.json"""
    params = {"method": "artist.gettopalbums", "artist": artist, "api_key": API_KEY, "format": "json", "limit": 5}
    resp = requests.get(BASE_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    out_path = ALBUMS_DIR / f"artist_{_safe_name(artist)}_albums.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    logging.info(f"[3/5] Saved top albums   → {out_path}")
    return data


def save_artist_image(artist_data: dict, artist: str) -> None:
    """Downloads the largest artist image → data/raw/images/artist_<name>.<ext>"""
    images = artist_data.get("artist", {}).get("image", [])
    url = next((img["#text"] for img in reversed(images) if img.get("#text")), None)

    if not url:
        logging.warning("[4/5] No image URL found — skipping.")
        return

    resp = requests.get(url, stream=True, timeout=15)
    resp.raise_for_status()

    ext = url.split(".")[-1].split("?")[0] or "jpg"
    out_path = IMAGES_DIR / f"artist_{_safe_name(artist)}.{ext}"
    with open(out_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)

    logging.info(f"[4/5] Saved artist image → {out_path}")


def save_artist_bio(artist_data: dict, artist: str) -> None:
    """Extracts bio text from artist info → data/raw/reviews/<name>_bio.txt"""
    bio = artist_data.get("artist", {}).get("bio", {}).get("content", "").strip()

    if not bio:
        logging.warning("[5/5] No bio content found — skipping.")
        return

    out_path = REVIEWS_DIR / f"{_safe_name(artist)}_bio.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(bio)

    logging.info(f"[5/5] Saved artist bio   → {out_path}")


# ── 5. Video / SRT (manual step) ─────────────────────────────────────────────
def print_video_instructions(tracks_data: dict, artist: str) -> None:
    """
    Prints instructions for obtaining the YouTube SRT subtitle file.
    Last.fm does not host video — the workflow is:
      1. Take the top track name from the toptracks response.
      2. Search YouTube for the official music video.
      3. Download subtitles as .srt using a tool like yt-dlp or
         https://downsub.com / https://www.savesubs.com/
      4. Save the .srt file to data/raw/video/<artist>_<track>.srt
    """
    tracks = tracks_data.get("toptracks", {}).get("track", [])
    if tracks:
        top = tracks[0].get("name", "unknown")
        youtube_search = (
            f"https://www.youtube.com/results?search_query="
            f"{artist.replace(' ', '+')}+{top.replace(' ', '+')}+official"
        )
        srt_path = VIDEO_DIR / f"{_safe_name(artist)}_{top.lower().replace(' ', '_')}.srt"
        print("\n" + "=" * 60)
        print("VIDEO / SRT — manual step required")
        print("=" * 60)
        print(f"  Top track : {top}")
        print(f"  Search    : {youtube_search}")
        print(f"  1. Open the YouTube link above")
        print(f"  2. Copy the video URL")
        print(f"  3. Go to https://downsub.com and paste the URL")
        print(f"  4. Download the English .srt file")
        print(f"  5. Save it as:\n     {srt_path}")
        print("=" * 60 + "\n")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if not API_KEY:
        sys.exit(
            "ERROR: LASTFM_API_KEY is not set.\n"
            "Add your key to the .env file and try again."
        )

    logging.info(f"Starting data fetch for artist: {ARTIST}")

    artist_data  = fetch_artist_info(ARTIST)
    tracks_data  = fetch_top_tracks(ARTIST)
    save_artist_image(artist_data, ARTIST)
    save_artist_bio(artist_data, ARTIST)
    print_video_instructions(tracks_data, ARTIST)

    logging.info("fetch_samples.py completed successfully.")
    print("Done! Check data/raw/ for all saved files.")

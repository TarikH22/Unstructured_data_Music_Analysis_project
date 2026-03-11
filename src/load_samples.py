"""
load_samples.py
Reads all sample data files saved by fetch_samples.py and prints a summary
of each one to verify the pipeline is working end-to-end.

Run from the project root:
    python src/load_samples.py

Expected output (once sample files exist):
    === ARTIST INFO ===
    Name       : Coldplay
    Listeners  : 6500000
    ...

Logs are written to: pipeline.log
"""

import sys
from pathlib import Path

# Allow running from project root without installing as a package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.io_utils import setup_logging, read_json, read_text, read_image, read_srt

# ── Paths ─────────────────────────────────────────────────────────────────────
RAW         = Path("data/raw")
LASTFM_DIR  = RAW / "lastfm"
IMAGES_DIR  = RAW / "images"
VIDEO_DIR   = RAW / "video"
REVIEWS_DIR = RAW / "reviews"

ARTIST_SAFE = "coldplay"   # change to match whichever artist you fetched


if __name__ == "__main__":
    setup_logging("pipeline.log")

    # ── 1. Artist Details (JSON) ──────────────────────────────────────────────
    artist_data = read_json(LASTFM_DIR / f"artist_{ARTIST_SAFE}.json")
    if artist_data:
        artist = artist_data.get("artist", {})
        print("=== ARTIST INFO ===")
        print("Name       :", artist.get("name"))
        print("Listeners  :", artist.get("stats", {}).get("listeners"))
        print("Play count :", artist.get("stats", {}).get("playcount"))
        tags = [t["name"] for t in artist.get("tags", {}).get("tag", [])]
        print("Tags       :", ", ".join(tags))

    # ── 2. Top Tracks (JSON) ──────────────────────────────────────────────────
    tracks_data = read_json(LASTFM_DIR / f"artist_{ARTIST_SAFE}_toptracks.json")
    if tracks_data:
        tracks = tracks_data.get("toptracks", {}).get("track", [])
        print("\n=== TOP 5 TRACKS ===")
        for i, track in enumerate(tracks[:5], 1):
            print(f"  {i}. {track.get('name'):<35}  {track.get('playcount')} plays")

    # ── 3. Artist Bio (Text) ──────────────────────────────────────────────────
    bio_text = read_text(REVIEWS_DIR / f"{ARTIST_SAFE}_bio.txt")
    if bio_text:
        print("\n=== BIO (first 200 characters) ===")
        print(bio_text[:200])

    # ── 4. Artist Image ───────────────────────────────────────────────────────
    # Try common extensions
    img_obj = None
    for ext in ("jpg", "png", "gif"):
        candidate = IMAGES_DIR / f"artist_{ARTIST_SAFE}.{ext}"
        if candidate.exists():
            img_obj = read_image(candidate)
            break

    if img_obj:
        print("\n=== ARTIST IMAGE ===")
        if hasattr(img_obj, "size"):
            print(f"  Dimensions : {img_obj.size[0]}x{img_obj.size[1]} px")
            print(f"  Mode       : {img_obj.mode}")
        else:
            print(f"  File size  : {img_obj['bytes']} bytes")
            print(f"  Path       : {img_obj['path']}")

    # ── 5. SRT Subtitles (Video) ──────────────────────────────────────────────
    # Scan the video directory for any .srt file
    srt_files = list(VIDEO_DIR.glob("*.srt"))
    if srt_files:
        subtitles = read_srt(srt_files[0])
        if subtitles:
            print(f"\n=== SUBTITLES — {srt_files[0].name} ({len(subtitles)} entries) ===")
            for entry in subtitles[:3]:
                print(f"  [{entry['start']} --> {entry['end']}]")
                print(f"  {entry['text']}")
                print()
    else:
        print("\n=== SUBTITLES ===")
        print("  No .srt file found in data/raw/video/")
        print("  Run fetch_samples.py for instructions on downloading one.")

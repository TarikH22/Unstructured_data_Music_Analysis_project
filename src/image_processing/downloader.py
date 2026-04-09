import json
import os
from urllib.parse import urlparse

import requests

from utils.logger import logger


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
RAW_DIR = os.path.join(ROOT_DIR, "data", "raw")
RAW_IMAGES_DIR = os.path.join(RAW_DIR, "images")
RAW_API_DIR = os.path.join(RAW_DIR, "api")
COVERS_FILE = os.path.join(RAW_DIR, "covers", "coldplay_a_rush_cover_metadata.json")
MAX_IMAGES_DEFAULT = 50


def _ensure_dir():
    os.makedirs(RAW_IMAGES_DIR, exist_ok=True)


def _safe_extension(url):
    path = urlparse(url).path.lower()
    for ext in [".jpg", ".jpeg", ".png", ".webp"]:
        if path.endswith(ext):
            return ext
    return ".jpg"


def _collect_image_urls(limit=MAX_IMAGES_DEFAULT):
    urls = []

    if os.path.exists(COVERS_FILE):
        with open(COVERS_FILE, "r", encoding="utf-8") as f:
            cover_data = json.load(f)
        cover = cover_data.get("album_cover", {})
        if cover.get("cover_url"):
            urls.append(cover["cover_url"])
        for value in cover.get("sizes", {}).values():
            if value:
                urls.append(value)

    if os.path.isdir(RAW_API_DIR):
        for name in sorted(os.listdir(RAW_API_DIR)):
            if not name.endswith(".json"):
                continue
            with open(os.path.join(RAW_API_DIR, name), "r", encoding="utf-8") as f:
                page = json.load(f)
            artists = page.get("artists", {}).get("artist", [])
            for artist in artists:
                for image_item in artist.get("image", []):
                    image_url = image_item.get("#text", "").strip()
                    if image_url:
                        urls.append(image_url)

    deduped = []
    seen = set()
    for url in urls:
        if url not in seen:
            deduped.append(url)
            seen.add(url)
        if len(deduped) >= limit:
            break

    # Ensure we can still process a full batch when Last.fm image coverage is sparse.
    # Picsum seeded URLs are deterministic and provide stable public test images.
    if len(deduped) < limit:
        seed_index = 1
        while len(deduped) < limit:
            fallback_url = f"https://picsum.photos/seed/udma-{seed_index:03d}/800/1200.jpg"
            if fallback_url not in seen:
                deduped.append(fallback_url)
                seen.add(fallback_url)
            seed_index += 1

    return deduped


def download_poster_images(max_images=MAX_IMAGES_DEFAULT):
    _ensure_dir()
    max_images = min(max_images, MAX_IMAGES_DEFAULT)
    image_urls = _collect_image_urls(limit=max_images)
    manifest = []

    headers = {"User-Agent": "ResearchBot/1.0"}
    for idx, url in enumerate(image_urls, start=1):
        ext = _safe_extension(url)
        file_name = f"poster_{idx:03d}{ext}"
        output_path = os.path.join(RAW_IMAGES_DIR, file_name)
        status = "downloaded"

        try:
            response = requests.get(url, timeout=20, headers=headers)
            response.raise_for_status()
            with open(output_path, "wb") as f:
                f.write(response.content)
        except Exception as e:
            status = "failed"
            logger.error(f"Failed image download {url}: {e}")

        manifest.append(
            {
                "source_url": url,
                "file_name": file_name,
                "path": output_path,
                "status": status,
            }
        )

    manifest_path = os.path.join(RAW_IMAGES_DIR, "download_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    downloaded_paths = [m["path"] for m in manifest if m["status"] == "downloaded" and os.path.exists(m["path"])]
    logger.info(f"Downloaded {len(downloaded_paths)} images (max cap: {MAX_IMAGES_DEFAULT})")
    return downloaded_paths

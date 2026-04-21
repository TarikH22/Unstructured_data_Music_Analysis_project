import json
import os
import importlib
from pathlib import Path
from typing import Dict, List, Optional

import requests

from utils.logger import logger


ROOT_DIR = Path(__file__).resolve().parents[2]
RAW_AUDIO_DIR = ROOT_DIR / "data" / "raw" / "audio"
PROCESSED_AUDIO_DIR = ROOT_DIR / "data" / "processed" / "audio"
SUPPORTED_AUDIO_EXTS = {".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aac"}
DEFAULT_USER_AGENT = "ResearchBot/1.0"


def _safe_import_pydub():
    AudioSegment = importlib.import_module("pydub").AudioSegment
    Sine = importlib.import_module("pydub.generators").Sine

    return AudioSegment, Sine


def ensure_audio_dirs() -> None:
    RAW_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_AUDIO_DIR.mkdir(parents=True, exist_ok=True)


def list_audio_files(directory: Path = RAW_AUDIO_DIR) -> List[Path]:
    ensure_audio_dirs()
    return sorted(
        [p for p in directory.glob("**/*") if p.is_file() and p.suffix.lower() in SUPPORTED_AUDIO_EXTS]
    )


def download_preview_audio_from_api(
    search_term: str = "coldplay", output_name: str = "api_preview.m4a"
) -> Optional[Path]:
    ensure_audio_dirs()
    endpoint = "https://itunes.apple.com/search"
    params = {"term": search_term, "entity": "song", "limit": 5}
    headers = {"User-Agent": DEFAULT_USER_AGENT}

    try:
        response = requests.get(endpoint, params=params, headers=headers, timeout=20)
        response.raise_for_status()
        payload = response.json()
        results = payload.get("results", [])
        if not results:
            logger.warning("No iTunes API results available for preview audio")
            return None

        preview_url = next((item.get("previewUrl") for item in results if item.get("previewUrl")), None)
        if not preview_url:
            logger.warning("No previewUrl found in iTunes API results")
            return None

        audio_resp = requests.get(preview_url, headers=headers, timeout=30)
        audio_resp.raise_for_status()

        output_path = RAW_AUDIO_DIR / output_name
        output_path.write_bytes(audio_resp.content)

        metadata_path = RAW_AUDIO_DIR / "api_preview_metadata.json"
        metadata_path.write_text(json.dumps(results[0], indent=2), encoding="utf-8")

        logger.info(f"Downloaded API preview audio: {output_path}")
        return output_path
    except Exception as exc:
        logger.warning(f"Failed to download preview audio from API: {exc}")
        return None


def generate_synthetic_audio_sample(output_name: str = "synthetic_tone.wav", duration_ms: int = 8000) -> Path:
    ensure_audio_dirs()
    AudioSegment, Sine = _safe_import_pydub()

    tone = Sine(440).to_audio_segment(duration=duration_ms).apply_gain(-8)
    tone = tone.fade_in(500).fade_out(500)
    output_path = RAW_AUDIO_DIR / output_name
    tone.export(output_path, format="wav")
    logger.info(f"Generated synthetic audio sample: {output_path}")
    return output_path


def ensure_audio_sources() -> List[Path]:
    """Ensure at least one raw audio source exists by trying API pull first, then synthetic generation."""
    files = list_audio_files(RAW_AUDIO_DIR)
    if files:
        return files

    api_file = download_preview_audio_from_api()
    if api_file:
        return list_audio_files(RAW_AUDIO_DIR)

    generate_synthetic_audio_sample()
    return list_audio_files(RAW_AUDIO_DIR)


def ensure_minimum_audio_formats(required_formats: List[str] = None) -> List[Path]:
    """Ensure required formats are present in raw/audio by converting the first available source."""
    if required_formats is None:
        required_formats = ["wav", "mp3", "flac"]

    ensure_audio_dirs()
    files = ensure_audio_sources()
    if not files:
        return []

    AudioSegment, _ = _safe_import_pydub()
    source = files[0]
    audio = AudioSegment.from_file(source)

    existing_exts = {p.suffix.lower().lstrip(".") for p in list_audio_files(RAW_AUDIO_DIR)}
    for fmt in required_formats:
        if fmt in existing_exts:
            continue
        out_path = RAW_AUDIO_DIR / f"sample_from_{source.stem}.{fmt}"
        export_kwargs = {"format": fmt}
        if fmt == "mp3":
            export_kwargs["bitrate"] = "192k"
        audio.export(out_path, **export_kwargs)
        logger.info(f"Created required audio format: {out_path}")

    return list_audio_files(RAW_AUDIO_DIR)


def inspect_audio_file(file_path: Path) -> Dict:
    AudioSegment, _ = _safe_import_pydub()
    audio = AudioSegment.from_file(file_path)

    bit_depth = audio.sample_width * 8
    summary = {
        "filename": file_path.name,
        "format": file_path.suffix.lstrip(".").upper(),
        "duration_sec": round(len(audio) / 1000.0, 2),
        "channels": audio.channels,
        "channel_type": "Mono" if audio.channels == 1 else "Stereo",
        "frame_rate_hz": audio.frame_rate,
        "bit_depth": bit_depth,
        "file_size_kb": round(file_path.stat().st_size / 1024.0, 1),
        "path": str(file_path),
    }
    return summary


def inspect_all_audio_files() -> List[Dict]:
    files = ensure_minimum_audio_formats(["wav", "mp3", "flac"])
    summaries = []
    for file_path in files:
        try:
            info = inspect_audio_file(file_path)
            summaries.append(info)
            logger.info(f"Audio inspection: {info['filename']} ({info['format']}) {info['duration_sec']}s")
        except Exception as exc:
            logger.error(f"Failed to inspect audio file {file_path}: {exc}")
    return summaries


if __name__ == "__main__":
    rows = inspect_all_audio_files()
    for row in rows:
        print("-" * 45)
        for key, value in row.items():
            print(f"{key:22}: {value}")

from pathlib import Path
from typing import Dict, List

from utils.logger import logger
from audio_processing.loader import inspect_all_audio_files
from audio_processing.processor import process_audio_lab_samples
from audio_processing.transcriber import (
    chunked_transcribe,
    save_transcript_all_formats,
    transcribe_audio_file,
)
from video_processing.frame_extractor import extract_keyframes
from video_processing.loader import extract_audio_from_video, inspect_all_video_files, list_video_files


ROOT_DIR = Path(__file__).resolve().parents[1]
PROCESSED_AUDIO_DIR = ROOT_DIR / "data" / "processed" / "audio"


def run_media_pipeline() -> Dict:
    """Run audio/video processing milestone and return summary artifacts."""
    summary: Dict = {
        "audio_inspection": [],
        "audio_outputs": {},
        "video_inspection": [],
        "frames": [],
        "transcripts": [],
        "errors": [],
    }

    logger.info("Media pipeline stage started")

    try:
        summary["audio_inspection"] = inspect_all_audio_files()
    except Exception as exc:
        logger.error(f"Audio inspection failed: {exc}")
        summary["errors"].append(f"audio_inspection: {exc}")

    try:
        summary["audio_outputs"] = process_audio_lab_samples()
    except Exception as exc:
        logger.error(f"Audio processing failed: {exc}")
        summary["errors"].append(f"audio_processing: {exc}")

    processed_audio_candidates = []
    for ext in ("*.wav", "*.mp3", "*.flac", "*.ogg"):
        processed_audio_candidates.extend(PROCESSED_AUDIO_DIR.glob(ext))

    if processed_audio_candidates:
        short_audio = processed_audio_candidates[0]
        try:
            short_transcript = transcribe_audio_file(short_audio, model_name="base")
            out_paths = save_transcript_all_formats(short_transcript, base_name=f"short_{short_audio.stem}")
            summary["transcripts"].append({"source": str(short_audio), "outputs": out_paths})
        except Exception as exc:
            logger.error(f"Short audio transcription failed: {exc}")
            summary["errors"].append(f"short_transcription: {exc}")

        # Chunked transcription uses the longest candidate file.
        long_audio = max(processed_audio_candidates, key=lambda p: p.stat().st_size)
        try:
            chunked = chunked_transcribe(long_audio, model_name="base", chunk_minutes=5, use_cache=True)
            summary["transcripts"].append(
                {
                    "source": str(long_audio),
                    "type": "chunked",
                    "segments": len(chunked.get("segments", [])),
                }
            )
        except Exception as exc:
            logger.error(f"Chunked transcription failed: {exc}")
            summary["errors"].append(f"chunked_transcription: {exc}")

    try:
        summary["video_inspection"] = inspect_all_video_files()
    except Exception as exc:
        logger.error(f"Video inspection failed: {exc}")
        summary["errors"].append(f"video_inspection: {exc}")

    for video_path in list_video_files():
        try:
            extracted_audio = extract_audio_from_video(video_path)
            frames = extract_keyframes(video_path, interval_seconds=5)
            summary["frames"].extend([str(p) for p in frames])

            if extracted_audio:
                vtx = transcribe_audio_file(extracted_audio, model_name="base")
                out_paths = save_transcript_all_formats(vtx, base_name=f"video_audio_{video_path.stem}")
                summary["transcripts"].append({"source": str(extracted_audio), "outputs": out_paths})
        except Exception as exc:
            logger.error(f"Video processing/transcription failed for {video_path}: {exc}")
            summary["errors"].append(f"video_{video_path.name}: {exc}")

    logger.info("Media pipeline stage finished")
    return summary

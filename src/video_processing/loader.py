from pathlib import Path
from typing import Dict, List, Optional

from utils.logger import logger


ROOT_DIR = Path(__file__).resolve().parents[2]
RAW_VIDEO_DIR = ROOT_DIR / "data" / "raw" / "video"
PROCESSED_AUDIO_DIR = ROOT_DIR / "data" / "processed" / "audio"
SUPPORTED_VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}


def _import_video_file_clip():
    try:
        from moviepy import VideoFileClip

        return VideoFileClip
    except Exception:
        from moviepy.editor import VideoFileClip

        return VideoFileClip


def ensure_video_dirs() -> None:
    RAW_VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_AUDIO_DIR.mkdir(parents=True, exist_ok=True)


def list_video_files(directory: Path = RAW_VIDEO_DIR) -> List[Path]:
    ensure_video_dirs()
    return sorted([p for p in directory.glob("**/*") if p.is_file() and p.suffix.lower() in SUPPORTED_VIDEO_EXTS])


def inspect_video_file(video_path: Path) -> Dict:
    VideoFileClip = _import_video_file_clip()
    clip = None
    try:
        clip = VideoFileClip(str(video_path))
        width, height = clip.size
        info = {
            "file_name": video_path.name,
            "path": str(video_path),
            "duration_sec": round(float(clip.duration or 0.0), 2),
            "fps": float(getattr(clip, "fps", 0.0) or 0.0),
            "resolution": f"{width}x{height}",
            "audio_present": clip.audio is not None,
            "codec": "unknown",
        }
        return info
    finally:
        if clip is not None:
            clip.close()


def inspect_all_video_files() -> List[Dict]:
    rows = []
    for video_path in list_video_files():
        try:
            info = inspect_video_file(video_path)
            rows.append(info)
            logger.info(
                f"Video inspection: {info['file_name']} duration={info['duration_sec']} fps={info['fps']} res={info['resolution']}"
            )
        except Exception as exc:
            logger.error(f"Failed to inspect video {video_path}: {exc}")
    return rows


def extract_audio_from_video(video_path: Path, output_audio_path: Optional[Path] = None) -> Optional[Path]:
    VideoFileClip = _import_video_file_clip()
    clip = None
    try:
        ensure_video_dirs()
        clip = VideoFileClip(str(video_path))
        if clip.audio is None:
            logger.warning(f"No audio track in video: {video_path}")
            return None

        if output_audio_path is None:
            output_audio_path = PROCESSED_AUDIO_DIR / f"{video_path.stem}_audio.mp3"
        output_audio_path.parent.mkdir(parents=True, exist_ok=True)

        clip.audio.write_audiofile(str(output_audio_path), bitrate="192k", logger=None)
        logger.info(f"Extracted audio from video: {video_path} -> {output_audio_path}")
        return output_audio_path
    except Exception as exc:
        logger.error(f"Failed extracting audio from video {video_path}: {exc}")
        return None
    finally:
        if clip is not None:
            clip.close()

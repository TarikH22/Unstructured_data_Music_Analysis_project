from pathlib import Path
from typing import List

from utils.logger import logger
from video_processing.loader import RAW_VIDEO_DIR


ROOT_DIR = Path(__file__).resolve().parents[2]
PROCESSED_FRAMES_DIR = ROOT_DIR / "data" / "processed" / "frames"


def _import_video_file_clip():
    try:
        from moviepy import VideoFileClip

        return VideoFileClip
    except Exception:
        from moviepy.editor import VideoFileClip

        return VideoFileClip


def extract_frame(video_path: Path, t_seconds: float, output_path: Path) -> Path:
    VideoFileClip = _import_video_file_clip()
    clip = None
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        clip = VideoFileClip(str(video_path))
        clip.save_frame(str(output_path), t=t_seconds)
        logger.info(f"Saved frame at {t_seconds:.2f}s: {output_path}")
        return output_path
    finally:
        if clip is not None:
            clip.close()


def extract_keyframes(video_path: Path, interval_seconds: int = 5, max_frames: int = 120) -> List[Path]:
    VideoFileClip = _import_video_file_clip()
    clip = None
    frames = []
    try:
        PROCESSED_FRAMES_DIR.mkdir(parents=True, exist_ok=True)
        clip = VideoFileClip(str(video_path))
        duration = float(clip.duration or 0.0)
        t = 0.0
        frame_idx = 0
        while t <= duration and frame_idx < max_frames:
            output_name = f"{video_path.stem}_frame_{frame_idx:04}_{int(t)}s.png"
            output_path = PROCESSED_FRAMES_DIR / output_name
            clip.save_frame(str(output_path), t=t)
            frames.append(output_path)
            t += interval_seconds
            frame_idx += 1
        logger.info(f"Extracted {len(frames)} keyframes from {video_path}")
        return frames
    except Exception as exc:
        logger.error(f"Failed keyframe extraction for {video_path}: {exc}")
        return frames
    finally:
        if clip is not None:
            clip.close()

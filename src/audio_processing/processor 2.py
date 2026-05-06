from pathlib import Path
from typing import Dict, List

from utils.logger import logger
from audio_processing.loader import RAW_AUDIO_DIR, PROCESSED_AUDIO_DIR, ensure_minimum_audio_formats


def _safe_import_pydub():
    from pydub import AudioSegment

    return AudioSegment


def trim_audio(audio, start_ms: int, end_ms: int):
    return audio[start_ms:end_ms]


def concatenate_audio(audio_segments: List):
    if not audio_segments:
        raise ValueError("No audio segments provided for concatenation")
    combined = audio_segments[0]
    for seg in audio_segments[1:]:
        combined += seg
    return combined


def adjust_volume(audio, db_change: float):
    return audio + db_change


def apply_fade(audio, fade_in_ms: int = 1000, fade_out_ms: int = 1000):
    return audio.fade_in(fade_in_ms).fade_out(fade_out_ms)


def convert_audio(audio, output_path: Path, fmt: str, bitrate: str = "192k") -> Path:
    kwargs = {"format": fmt}
    if fmt.lower() in {"mp3", "ogg", "aac"}:
        kwargs["bitrate"] = bitrate
    audio.export(output_path, **kwargs)
    logger.info(f"Exported audio: {output_path}")
    return output_path


def process_audio_lab_samples() -> Dict[str, str]:
    """Run all required audio operations and export artifacts to data/processed/audio."""
    AudioSegment = _safe_import_pydub()
    PROCESSED_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    files = ensure_minimum_audio_formats(["wav", "mp3", "flac"])
    if len(files) < 2:
        raise RuntimeError("At least one source audio file is required")

    # Prefer WAV source for processing fidelity; fallback to first file.
    source_path = next((p for p in files if p.suffix.lower() == ".wav"), files[0])
    source_audio = AudioSegment.from_file(source_path)

    outputs: Dict[str, str] = {}

    trimmed = trim_audio(source_audio, start_ms=1000, end_ms=min(len(source_audio), 6000))
    outputs["trimmed_wav"] = str(convert_audio(trimmed, PROCESSED_AUDIO_DIR / "trimmed_sample.wav", "wav"))

    # Concatenate first two files.
    clip_a = AudioSegment.from_file(files[0])
    clip_b = AudioSegment.from_file(files[1])
    concatenated = concatenate_audio([clip_a, clip_b])
    outputs["concatenated_wav"] = str(
        convert_audio(concatenated, PROCESSED_AUDIO_DIR / "concatenated_sample.wav", "wav")
    )

    louder = adjust_volume(trimmed, db_change=6)
    quieter = adjust_volume(trimmed, db_change=-6)
    outputs["louder_mp3"] = str(convert_audio(louder, PROCESSED_AUDIO_DIR / "louder_sample.mp3", "mp3"))
    outputs["quieter_mp3"] = str(convert_audio(quieter, PROCESSED_AUDIO_DIR / "quieter_sample.mp3", "mp3"))

    faded = apply_fade(trimmed, fade_in_ms=1200, fade_out_ms=1200)
    outputs["faded_flac"] = str(convert_audio(faded, PROCESSED_AUDIO_DIR / "faded_sample.flac", "flac"))

    converted_mp3 = convert_audio(trimmed, PROCESSED_AUDIO_DIR / "trimmed_converted.mp3", "mp3")
    outputs["converted_mp3"] = str(converted_mp3)

    logger.info(f"Audio processing outputs generated: {len(outputs)} files")
    return outputs


if __name__ == "__main__":
    result = process_audio_lab_samples()
    for key, value in result.items():
        print(f"{key}: {value}")

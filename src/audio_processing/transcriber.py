import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from utils.logger import logger


ROOT_DIR = Path(__file__).resolve().parents[2]
PROCESSED_AUDIO_DIR = ROOT_DIR / "data" / "processed" / "audio"
TRANSCRIPTS_DIR = ROOT_DIR / "data" / "processed" / "transcripts"

_MODEL_CACHE = {}


def _safe_import_faster_whisper():
    from faster_whisper import WhisperModel

    return WhisperModel


def _safe_import_pydub():
    from pydub import AudioSegment

    return AudioSegment


def _word_to_dict(word) -> Dict:
    if word is None:
        return {}
    if is_dataclass(word):
        return asdict(word)
    # Compatible with namedtuple-like whisper word objects.
    return {
        "word": getattr(word, "word", ""),
        "start": float(getattr(word, "start", 0.0) or 0.0),
        "end": float(getattr(word, "end", 0.0) or 0.0),
        "probability": float(getattr(word, "probability", 0.0) or 0.0),
    }


def load_model(model_name: str = "base", device: str = "cpu", compute_type: str = "int8"):
    cache_key = (model_name, device, compute_type)
    if cache_key in _MODEL_CACHE:
        return _MODEL_CACHE[cache_key]

    WhisperModel = _safe_import_faster_whisper()
    model = WhisperModel(model_name, device=device, compute_type=compute_type)
    _MODEL_CACHE[cache_key] = model
    logger.info(f"Loaded faster-whisper model: {model_name} ({device}/{compute_type})")
    return model


def _serialize_segments(segments, time_offset: float = 0.0) -> List[Dict]:
    serialized = []
    for seg in segments:
        words = [_word_to_dict(w) for w in (getattr(seg, "words", None) or [])]
        if time_offset and words:
            for w in words:
                w["start"] = round(float(w.get("start", 0.0)) + time_offset, 3)
                w["end"] = round(float(w.get("end", 0.0)) + time_offset, 3)
        item = {
            "id": int(getattr(seg, "id", 0) or 0),
            "start": round(float(getattr(seg, "start", 0.0) or 0.0) + time_offset, 3),
            "end": round(float(getattr(seg, "end", 0.0) or 0.0) + time_offset, 3),
            "text": (getattr(seg, "text", "") or "").strip(),
            "avg_logprob": float(getattr(seg, "avg_logprob", 0.0) or 0.0),
            "no_speech_prob": float(getattr(seg, "no_speech_prob", 0.0) or 0.0),
            "words": words,
        }
        serialized.append(item)
    return serialized


def transcribe_audio_file(
    audio_path: Path,
    model_name: str = "base",
    language: Optional[str] = None,
    word_timestamps: bool = True,
    task: str = "transcribe",
) -> Dict:
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

    model = load_model(model_name=model_name)
    segments_gen, info = model.transcribe(
        str(audio_path),
        task=task,
        language=language,
        word_timestamps=word_timestamps,
        vad_filter=True,
    )

    # Consume generator to run transcription work.
    segments = _serialize_segments(list(segments_gen))
    full_text = " ".join([seg["text"] for seg in segments]).strip()

    result = {
        "source_path": str(audio_path),
        "language": getattr(info, "language", None),
        "language_probability": float(getattr(info, "language_probability", 0.0) or 0.0),
        "duration": float(getattr(info, "duration", 0.0) or 0.0),
        "duration_after_vad": float(getattr(info, "duration_after_vad", 0.0) or 0.0),
        "model": model_name,
        "segments": segments,
        "full_text": full_text,
        "metadata": {
            "file_name": Path(audio_path).name,
            "source": str(audio_path),
            "type": "transcript",
            "extraction_timestamp": datetime.utcnow().isoformat() + "Z",
        },
    }

    logger.info(f"Transcribed audio: {audio_path} ({len(segments)} segments)")
    return result


def _format_srt_time(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h = ms // 3600000
    ms %= 3600000
    m = ms // 60000
    ms %= 60000
    s = ms // 1000
    ms %= 1000
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def save_transcript_json(transcript: Dict, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(transcript, indent=2, ensure_ascii=False), encoding="utf-8")
    return output_path


def save_transcript_txt(transcript: Dict, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(transcript.get("full_text", ""), encoding="utf-8")
    return output_path


def save_transcript_srt(transcript: Dict, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for i, seg in enumerate(transcript.get("segments", []), start=1):
        lines.append(str(i))
        lines.append(f"{_format_srt_time(seg['start'])} --> {_format_srt_time(seg['end'])}")
        lines.append(seg.get("text", ""))
        lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def save_transcript_all_formats(transcript: Dict, base_name: str) -> Dict[str, str]:
    json_path = save_transcript_json(transcript, TRANSCRIPTS_DIR / f"{base_name}.json")
    txt_path = save_transcript_txt(transcript, TRANSCRIPTS_DIR / f"{base_name}.txt")
    srt_path = save_transcript_srt(transcript, TRANSCRIPTS_DIR / f"{base_name}.srt")
    logger.info(f"Saved transcript outputs for {base_name}")
    return {"json": str(json_path), "txt": str(txt_path), "srt": str(srt_path)}


def chunked_transcribe(
    audio_path: Path,
    model_name: str = "base",
    chunk_minutes: int = 5,
    use_cache: bool = True,
) -> Dict:
    AudioSegment = _safe_import_pydub()
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

    audio = AudioSegment.from_file(audio_path)
    chunk_ms = chunk_minutes * 60 * 1000

    chunks_dir = TRANSCRIPTS_DIR / f"{audio_path.stem}_chunks"
    chunks_dir.mkdir(parents=True, exist_ok=True)

    combined_segments: List[Dict] = []
    chunk_count = (len(audio) + chunk_ms - 1) // chunk_ms

    model = load_model(model_name=model_name)
    for idx in range(chunk_count):
        start_ms = idx * chunk_ms
        end_ms = min((idx + 1) * chunk_ms, len(audio))
        offset_seconds = start_ms / 1000.0

        chunk_audio = audio[start_ms:end_ms]
        chunk_wav_path = chunks_dir / f"chunk_{idx:04}.wav"
        chunk_json_path = chunks_dir / f"chunk_{idx:04}.json"

        if not chunk_wav_path.exists():
            chunk_audio.export(chunk_wav_path, format="wav")

        if use_cache and chunk_json_path.exists():
            chunk_payload = json.loads(chunk_json_path.read_text(encoding="utf-8"))
            chunk_segments = chunk_payload.get("segments", [])
            logger.info(f"Chunk cache hit: {chunk_json_path.name}")
        else:
            seg_gen, info = model.transcribe(
                str(chunk_wav_path),
                task="transcribe",
                word_timestamps=True,
                vad_filter=True,
            )
            chunk_segments = _serialize_segments(list(seg_gen), time_offset=offset_seconds)
            chunk_payload = {
                "chunk_index": idx,
                "source_path": str(audio_path),
                "chunk_path": str(chunk_wav_path),
                "language": getattr(info, "language", None),
                "language_probability": float(getattr(info, "language_probability", 0.0) or 0.0),
                "segments": chunk_segments,
            }
            chunk_json_path.write_text(json.dumps(chunk_payload, indent=2), encoding="utf-8")

        combined_segments.extend(chunk_segments)
        logger.info(f"Chunked transcription progress: {idx + 1}/{chunk_count}")

    full_text = " ".join([seg.get("text", "") for seg in combined_segments]).strip()
    combined = {
        "source_path": str(audio_path),
        "model": model_name,
        "chunk_minutes": chunk_minutes,
        "segments": combined_segments,
        "full_text": full_text,
        "metadata": {
            "file_name": audio_path.name,
            "source": str(audio_path),
            "type": "transcript-chunked",
            "extraction_timestamp": datetime.utcnow().isoformat() + "Z",
        },
    }

    combined_json = TRANSCRIPTS_DIR / f"{audio_path.stem}_chunked_combined.json"
    combined_json.write_text(json.dumps(combined, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"Chunked transcription completed: {audio_path} ({len(combined_segments)} segments)")
    return combined


if __name__ == "__main__":
    candidates = sorted(PROCESSED_AUDIO_DIR.glob("*.wav")) + sorted(PROCESSED_AUDIO_DIR.glob("*.mp3"))
    if not candidates:
        print("No processed audio file found. Run audio processor first.")
    else:
        chosen = candidates[0]
        short_result = transcribe_audio_file(chosen, model_name="base")
        paths = save_transcript_all_formats(short_result, base_name=f"short_{chosen.stem}")
        print(paths)

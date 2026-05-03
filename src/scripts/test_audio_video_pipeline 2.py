import json
from pathlib import Path

from audio_processing.loader import inspect_all_audio_files
from audio_processing.processor import process_audio_lab_samples
from audio_processing.transcriber import chunked_transcribe, save_transcript_all_formats, transcribe_audio_file
from video_processing.loader import extract_audio_from_video, inspect_all_video_files, list_video_files
from video_processing.frame_extractor import extract_keyframes


def main():
    audio_info = inspect_all_audio_files()
    print("Audio files inspected:", len(audio_info))
    for row in audio_info:
        print(row)

    outputs = process_audio_lab_samples()
    print("Audio outputs:")
    print(json.dumps(outputs, indent=2))

    processed_audio_dir = Path(__file__).resolve().parents[2] / "data" / "processed" / "audio"
    candidate = sorted(list(processed_audio_dir.glob("*.wav")) + list(processed_audio_dir.glob("*.mp3")))
    if candidate:
        short = candidate[0]
        short_tx = transcribe_audio_file(short, model_name="base")
        short_out = save_transcript_all_formats(short_tx, f"short_{short.stem}")
        print("Short transcript outputs:", short_out)

        long_audio = max(candidate, key=lambda p: p.stat().st_size)
        chunked = chunked_transcribe(long_audio, model_name="base", chunk_minutes=5, use_cache=True)
        print("Chunked segments:", len(chunked.get("segments", [])))

    videos = inspect_all_video_files()
    print("Videos inspected:", len(videos))
    for row in videos:
        print(row)

    for video in list_video_files():
        audio_path = extract_audio_from_video(video)
        frames = extract_keyframes(video, interval_seconds=5)
        print(f"{video.name}: extracted audio={audio_path}, frames={len(frames)}")


if __name__ == "__main__":
    main()

# Unstructured Data Music Analysis Project

This repository contains a full unstructured-data pipeline, including the image processing assignment requirements (tasks 1-11).



## Evidence Screenshots

The following screenshots were provided and added from docs/screenshots/:

![Screenshot 1](docs/screenshots/Screenshot%202026-04-09%20at%2022.35.12.png)
![Screenshot 2](docs/screenshots/Screenshot%202026-04-09%20at%2023.27.11.png)
![Screenshot 3](docs/screenshots/Screenshot%202026-04-10%20at%2000.32.06.png)


## Recent Milestone Updates (Lab 6 & 7)
The pipeline now supports **Advanced Web Scraping & OCR (Lab 6)** and **Music & Video Processing + Transcription (Lab 7)**.

### Architecture Highlights
- **Audio Processing (`pydub`)**: Inspect, trim, apply fades, adjust volume, format conversion.
- **Video Processing (`moviepy`, `OpenCV`)**: Extract keyframes, strip audio tracks to MP3.
- **Transcription (`faster-whisper`)**: Highly efficient CTranslate2 transcriptions, supporting short audio and long chunked outputs (JSON, TXT, SRT).
- **Web Scraping & OCR (`playwright`, `pytesseract`)**: Dynamically extract JS-rendered textual data and scan multi-page PDFs directly into Mongo.

### Environment Requirements
- **Python**: **3.12** is strictly required (Python 3.13+ deprecated `audioop` and breaks `pydub`).
- **Dependencies**: `brew install ffmpeg tesseract poppler`
- **Execution**: Run `PYTHONPATH=src .venv/bin/python src/run_pipeline.py`


# Unstructured Data Music Analysis Project

A music analysis pipeline using the Last.fm API to fetch and process unstructured music data including artist info, tracks, albums, images, and reviews.

## Project Structure

```
data/
├── raw/
│   ├── lastfm/       # Artist & track metadata (JSON)
│   ├── albums/       # Album data (JSON)
│   ├── songs/        # Song details (JSON)
│   ├── images/       # Artist photos
│   ├── covers/       # Album cover art metadata
│   ├── text/         # Lyrics and text content
│   ├── reviews/      # Reviews and bios
│   └── video/        # Video subtitles (SRT)
└── processed/        # Processed output

src/
├── fetch_samples.py  # Fetch data from Last.fm API
├── io_utils.py       # Read JSON, text, images, SRT files
└── load_samples.py   # Load and display sample data

config/
└── config.py         # Configuration & paths
```

## Setup

1. Copy `.env.example` to `.env` and add your Last.fm API credentials
2. Install dependencies: `pip install -r requirements.txt`
3. Run fetch script: `python src/fetch_samples.py`
4. Load samples: `python src/load_samples.py`

## Logging

All pipeline operations are logged to `pipeline.log`.

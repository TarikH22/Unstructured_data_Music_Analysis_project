# Unstructured Data Music Analysis Project

This repository contains a full unstructured-data pipeline, including the image processing assignment requirements (tasks 1-11).

## Analytics Lab Extension

This project now includes a complete analytics stage for NumPy + pandas based exploration, selection, regex analysis, and data quality auditing.

### New Analytics Package

- `src/analytics/__init__.py`
- `src/analytics/numpy_ops.py`
- `src/analytics/data_loader.py`
- `src/analytics/explorer.py`
- `src/analytics/selector.py`
- `src/analytics/regex_ops.py`
- `src/analytics/quality_report.py`

### Analytics Outputs

Generated artifacts are stored in:

- `data/processed/analytics/`
- `data/processed/analytics/charts/`
- `data/processed/analytics/quality/`

### Notebook Submission

Use this notebook as the lab deliverable:

- [Movie Analytics Lab Notebook](docs/movie_analytics_lab.ipynb)

### Visible Logs (Assignment 7)

Analytics execution log evidence is provided here:

- [Assignment 7 Pipeline Log Evidence](docs/assignment7_pipeline_log_evidence.txt)

### Run Instructions

1. Install dependencies:

	`pip install -r requirements.txt`

2. Run the end-to-end pipeline (includes analytics stage):

	`python src/run_pipeline.py`

3. Check logs:

	`logs/pipeline.log`



## Evidence Screenshots

The following screenshots were provided and added from docs/screenshots/:

![Screenshot 1](docs/screenshots/Screenshot%202026-04-09%20at%2022.35.12.png)
![Screenshot 2](docs/screenshots/Screenshot%202026-04-09%20at%2023.27.11.png)
![Screenshot 3](docs/screenshots/Screenshot%202026-04-10%20at%2000.32.06.png)

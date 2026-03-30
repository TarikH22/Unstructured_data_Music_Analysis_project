import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from utils.logger import logger
from storage.mongo import save_document_to_mongo, save_to_mongo
from storage.s3 import upload_file_to_s3
from api.client import fetch_artists
from documents.extractor import process_documents
from parsing.parsers import extract_artist_fields

def run_pipeline():
    logger.info("Starting pipeline...")
    
    # 1. Fetch data
    artists = fetch_artists(3)
    logger.info(f"Fetched {len(artists)} artists from API")

    # 2. Parse and Save to MongoDB
    for artist in artists:
        parsed = extract_artist_fields(artist)
        save_to_mongo(parsed, "lastfm_api")

    # 3. Upload one raw page to LocalStack S3
    raw_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/raw/api/artists_page_1.json'))
    upload_file_to_s3(raw_file, "artists_page_1.json")

    # 4. Extract documents (PDF, DOCX, XLSX, encoding-check TXT) and store in MongoDB
    document_records = process_documents()
    for record in document_records:
        save_document_to_mongo(record, "document_extractions")
    logger.info(f"Saved {len(document_records)} document extraction records")

    logger.info("Pipeline finished successfully")

if __name__ == "__main__":
    run_pipeline()

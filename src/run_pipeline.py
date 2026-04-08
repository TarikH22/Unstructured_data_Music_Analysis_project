import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from utils.logger import logger
from storage.mongo import save_document_to_mongo, save_to_mongo
from storage.s3 import upload_file_to_s3
from api.client import fetch_artists
from documents.extractor import process_documents
from scraping.dynamic_scraper import scrape_dynamic_content
from scraping.scraper import scrape_local_html_samples, save_scraped_json
from ocr.ocr_utils import process_ocr_assets
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

    # 5. Scrape web content (single+multi via local HTML samples, plus dynamic endpoint strategy)
    scraped_records = scrape_local_html_samples(pages=3)
    dynamic_records = scrape_dynamic_content()
    all_scraped = scraped_records + dynamic_records
    save_scraped_json(all_scraped, "all_scraped_records.json")
    for record in all_scraped:
        save_document_to_mongo(record, "scraped_web_data")
    logger.info(f"Saved {len(all_scraped)} scraped web records")

    # 6. OCR image + scanned PDF and store outputs
    ocr_records = process_ocr_assets()
    for record in ocr_records:
        save_document_to_mongo(record, "ocr_results")
    logger.info(f"Saved {len(ocr_records)} OCR records")

    logger.info("Pipeline finished successfully")

if __name__ == "__main__":
    run_pipeline()

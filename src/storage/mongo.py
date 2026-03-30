from pymongo import MongoClient
from datetime import datetime

from utils.logger import logger

try:
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
    db = client["music_pipeline"]
except Exception as e:
    logger.error(f"MongoDB connection failed: {e}")

def save_to_mongo(data, collection_name="raw_artists"):
    try:
        collection = db[collection_name]
        collection.insert_one(data)
        logger.info(f"Saved record to MongoDB collection: {collection_name}")
    except Exception as e:
        logger.error(f"Failed to insert data: {e}")


def save_document_to_mongo(data, collection_name="document_extractions"):
    try:
        metadata = data.get("metadata", {})
        required_fields = ["file_name", "document_type", "source", "extraction_timestamp"]
        missing = [field for field in required_fields if not metadata.get(field)]
        if missing:
            for field in missing:
                if field == "extraction_timestamp":
                    metadata[field] = datetime.utcnow().isoformat() + "Z"
                else:
                    metadata[field] = "unknown"
            data["metadata"] = metadata

        collection = db[collection_name]
        collection.insert_one(data)
        logger.info(
            f"Saved document extraction: {metadata.get('file_name')} ({metadata.get('document_type')})"
        )
    except Exception as e:
        logger.error(f"Failed to save document extraction: {e}")

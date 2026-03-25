from pymongo import MongoClient
import logging

try:
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
    db = client["music_pipeline"]
except Exception as e:
    logging.error(f"MongoDB connection failed: {e}")

def save_to_mongo(data, collection_name="raw_artists"):
    try:
        collection = db[collection_name]
        collection.insert_one(data)
    except Exception as e:
        print(f"Failed to insert data: {e}")

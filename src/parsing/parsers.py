import json
import csv
import xml.etree.ElementTree as ET
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from storage.mongo import save_to_mongo

BASE_RAW_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/raw'))

def extract_artist_fields(artist):
    """Extract required fields from artist dict"""
    return {
        "name": artist.get("name"),
        "listeners": int(artist.get("listeners", 0)) if artist.get("listeners") else 0,
        "playcount": int(artist.get("playcount", 0)) if artist.get("playcount") else 0,
        "url": artist.get("url")
    }

def parse_json_files():
    api_dir = os.path.join(BASE_RAW_DIR, 'api')
    if not os.path.exists(api_dir):
        return
        
    for filename in os.listdir(api_dir):
        if filename.endswith(".json"):
            file_path = os.path.join(api_dir, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                artists = data.get("artists", {}).get("artist", [])
                for artist in artists:
                    parsed = extract_artist_fields(artist)
                    save_to_mongo(parsed, "lastfm_json")
                    
def parse_csv_file(file_path):
    if not os.path.exists(file_path):
        return
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            save_to_mongo(row, "lastfm_csv")
            
def parse_xml_file(file_path):
    if not os.path.exists(file_path):
        return
    tree = ET.parse(file_path)
    root = tree.getroot()
    for child in root:
        data = {sub.tag: sub.text for sub in child}
        save_to_mongo(data, "lastfm_xml")

if __name__ == "__main__":
    csv_path = os.path.join(BASE_RAW_DIR, "csv", "sample.csv")
    xml_path = os.path.join(BASE_RAW_DIR, "xml", "sample.xml")
    parse_json_files()
    parse_csv_file(csv_path)
    parse_xml_file(xml_path)

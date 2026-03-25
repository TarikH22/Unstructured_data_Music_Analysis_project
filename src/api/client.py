import os
import json
import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

load_dotenv()

API_KEY = os.getenv("LASTFM_API_KEY")
BASE_URL = "https://ws.audioscrobbler.com/2.0/"
API_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/raw/api'))
os.makedirs(API_DIR, exist_ok=True)


def create_session():
    session = requests.Session()
    retry = Retry(
        total=5,
        connect=5,
        read=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def fetch_artists(pages=3):
    all_artists = []
    session = create_session()
    
    for page in range(1, pages + 1):
        params = {
            "method": "chart.gettopartists",
            "api_key": API_KEY,
            "format": "json",
            "page": page,
            "limit": 50
        }
        
        response = session.get(BASE_URL, params=params, timeout=20)
        response.raise_for_status() 
        data = response.json()
        
        # Save raw data
        file_path = os.path.join(API_DIR, f"artists_page_{page}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
            
        artists = data.get("artists", {}).get("artist", [])
        all_artists.extend(artists)
        
    return all_artists

if __name__ == "__main__":
    artists = fetch_artists(pages=3)
    print(f"Fetched {len(artists)} artists.")
    if artists:
        print("Here are some artist names:")
        for artist in artists[:5]:
            print(artist["name"])

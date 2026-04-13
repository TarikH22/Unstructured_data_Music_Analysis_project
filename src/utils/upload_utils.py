import os
from dotenv import load_dotenv

from utils.logger import logger


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
TOKEN_FILE = os.path.join(ROOT_DIR, "config", "google_drive", "token.json")
load_dotenv(os.path.join(ROOT_DIR, ".env"))


def authenticate_drive(client_secret_file, scopes):
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except Exception as e:
        logger.warning(f"Google Drive upload skipped: missing Google SDK packages ({e})")
        return None

    os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, scopes)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, scopes)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    return build("drive", "v3", credentials=creds)


def upload_image(service, file_path, folder_id):
    try:
        from googleapiclient.http import MediaFileUpload
    except Exception as e:
        logger.warning(f"Google Drive upload skipped for {file_path}: missing MediaFileUpload ({e})")
        return None

    file_name = os.path.basename(file_path)
    media = MediaFileUpload(file_path, resumable=True)
    metadata = {"name": file_name, "parents": [folder_id]}
    created = service.files().create(body=metadata, media_body=media, fields="id,name,webViewLink").execute()
    logger.info(f"Uploaded to Google Drive: {file_name} ({created.get('id')})")
    return created


def upload_batch(file_paths):
    client_secret_file = os.getenv("CLIENT_SECRET_FILE", "").strip()
    folder_id = os.getenv("FOLDER_ID", "").strip()
    scopes_env = os.getenv("SCOPES", "https://www.googleapis.com/auth/drive.file")
    scopes = [s.strip() for s in scopes_env.split(",") if s.strip()]

    if not client_secret_file or not folder_id:
        logger.warning("Google Drive upload skipped: CLIENT_SECRET_FILE or FOLDER_ID missing")
        return []

    if not os.path.isabs(client_secret_file):
        client_secret_file = os.path.join(ROOT_DIR, client_secret_file)

    if not os.path.exists(client_secret_file):
        logger.warning(f"Google Drive upload skipped: credentials not found at {client_secret_file}")
        return []

    service = authenticate_drive(client_secret_file, scopes)
    if service is None:
        return []

    results = []
    for file_path in file_paths:
        if os.path.exists(file_path):
            try:
                created = upload_image(service, file_path, folder_id)
                if created:
                    results.append(created)
            except Exception as e:
                logger.error(f"Failed Drive upload for {file_path}: {e}")
    return results

import boto3
from botocore.exceptions import NoCredentialsError
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.logger import logger

S3_ENDPOINT = "http://localhost:4566"
S3_BUCKET_NAME = "music-pipeline-bucket"

def create_s3_client():
    return boto3.client(
        's3',
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id='test',
        aws_secret_access_key='test',
    )

def upload_file_to_s3(file_path, file_name):
    s3 = create_s3_client()
    try:
        logger.info(f"Started uploading {file_name} to {S3_BUCKET_NAME}")
        s3.upload_file(file_path, S3_BUCKET_NAME, file_name)
        logger.info(f"Successfully uploaded {file_name} to {S3_BUCKET_NAME}")
    except FileNotFoundError:
        logger.error(f"The file {file_path} was not found.")
    except NoCredentialsError:
        logger.error("Credentials not available.")

if __name__ == "__main__":
    file_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '../../data/raw/api/artists_page_1.json')
    )
    file_name = "artists_page_1.json"
    upload_file_to_s3(file_path, file_name)

"""
Storage module for uploading files to Google Cloud Storage.
"""
import os
import logging
from dotenv import load_dotenv
from google.cloud import storage

# Load environment variables
load_dotenv()

# Get environment variables
GOOGLE_CLOUD_PROJECT = os.getenv('GOOGLE_CLOUD_PROJECT')
if not GOOGLE_CLOUD_PROJECT:
    raise ValueError("Google Cloud Project hasn't been set in the environment variables.")

BUCKET = os.getenv("BUCKET")
if not BUCKET:
    raise ValueError("Google GCS Bucket not specified in env")

# Configure logging
logger = logging.getLogger(__name__)

async def upload_to_bucket(local_file_path: str, blob_name: str, bucket_name: str = BUCKET) -> str:
    """
    Upload a file to Google Cloud Storage.
    
    Args:
        local_file_path: Path to the local file
        blob_name: Name of the blob in GCS
        bucket_name: Name of the GCS bucket (default: from env)
        
    Returns:
        str: GCS URI of the uploaded file
    """
    try:
        # Initialize GCS client
        storage_client = storage.Client(project=GOOGLE_CLOUD_PROJECT)
        bucket = storage_client.bucket(bucket_name)
        
        # Upload file
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(local_file_path)
        logger.info(f"Uploaded {local_file_path} to gs://{bucket_name}/{blob_name}")
        
        # Return GCS URI
        gcs_uri = f"gs://{bucket_name}/{blob_name}"
        return gcs_uri
        
    except Exception as e:
        logger.error(f"Error uploading to bucket: {str(e)}")
        raise ValueError(f"Error uploading to bucket: {str(e)}")

async def download_from_bucket(gcs_uri: str, local_file_path: str) -> str:
    """
    Download a file from Google Cloud Storage.
    
    Args:
        gcs_uri: GCS URI of the file to download
        local_file_path: Path to save the downloaded file
        
    Returns:
        str: Path to the downloaded file
    """
    try:
        # Parse GCS URI
        bucket_name = gcs_uri.split('/')[2]
        blob_name = '/'.join(gcs_uri.split('/')[3:])
        
        # Initialize GCS client
        storage_client = storage.Client(project=GOOGLE_CLOUD_PROJECT)
        bucket = storage_client.bucket(bucket_name)
        
        # Download file
        blob = bucket.blob(blob_name)
        os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
        blob.download_to_filename(local_file_path)
        logger.info(f"Downloaded gs://{bucket_name}/{blob_name} to {local_file_path}")
        
        return local_file_path
        
    except Exception as e:
        logger.error(f"Error downloading from bucket: {str(e)}")
        raise ValueError(f"Error downloading from bucket: {str(e)}")

async def list_bucket_files(prefix: str, bucket_name: str = BUCKET) -> list:
    """
    List files in a GCS bucket with a given prefix.
    
    Args:
        prefix: Prefix to filter files
        bucket_name: Name of the GCS bucket (default: from env)
        
    Returns:
        list: List of file URIs
    """
    try:
        # Initialize GCS client
        storage_client = storage.Client(project=GOOGLE_CLOUD_PROJECT)
        bucket = storage_client.bucket(bucket_name)
        
        # List blobs
        blobs = bucket.list_blobs(prefix=prefix)
        file_list = [f"gs://{bucket_name}/{blob.name}" for blob in blobs]
        
        return file_list
        
    except Exception as e:
        logger.error(f"Error listing bucket files: {str(e)}")
        raise ValueError(f"Error listing bucket files: {str(e)}")
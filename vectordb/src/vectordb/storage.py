"""
Storage module for backing up and restoring ChromaDB collections.
"""
import os
import logging
import json
import tempfile
import shutil
from typing import List, Dict, Any
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

async def backup_collection(collection_name: str) -> str:
    """
    Backup a ChromaDB collection to GCS.
    
    Args:
        collection_name: Name of the collection
        
    Returns:
        str: GCS URI of the backup
    """
    try:
        # Create a temporary directory for the backup
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a subdirectory for the collection
            collection_dir = os.path.join(temp_dir, collection_name)
            os.makedirs(collection_dir, exist_ok=True)
            
            # Copy the collection data
            source_dir = f"/app/data/{collection_name}"
            if os.path.exists(source_dir):
                shutil.copytree(source_dir, collection_dir, dirs_exist_ok=True)
            
            # Create a metadata file
            metadata = {
                "collection_name": collection_name,
                "backup_time": str(os.path.getctime(collection_dir))
            }
            
            with open(os.path.join(collection_dir, "metadata.json"), "w") as f:
                json.dump(metadata, f)
                
            # Create an archive
            archive_path = os.path.join(temp_dir, f"{collection_name}.tar.gz")
            shutil.make_archive(
                os.path.join(temp_dir, collection_name),
                "gztar",
                root_dir=temp_dir,
                base_dir=collection_name
            )
            
            # Upload to GCS
            storage_client = storage.Client(project=GOOGLE_CLOUD_PROJECT)
            bucket = storage_client.bucket(BUCKET)
            blob_name = f"backups/{collection_name}.tar.gz"
            blob = bucket.blob(blob_name)
            blob.upload_from_filename(archive_path)
            
            # Return GCS URI
            gcs_uri = f"gs://{BUCKET}/{blob_name}"
            logger.info(f"Backed up collection {collection_name} to {gcs_uri}")
            
            return gcs_uri
            
    except Exception as e:
        logger.error(f"Error backing up collection: {str(e)}")
        raise

async def restore_collection(gcs_uri: str) -> str:
    """
    Restore a ChromaDB collection from GCS.
    
    Args:
        gcs_uri: GCS URI of the backup
        
    Returns:
        str: Name of the restored collection
    """
    try:
        # Parse GCS URI
        bucket_name = gcs_uri.split('/')[2]
        blob_name = '/'.join(gcs_uri.split('/')[3:])
        
        # Create a temporary directory for the restore
        with tempfile.TemporaryDirectory() as temp_dir:
            #
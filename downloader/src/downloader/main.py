"""
Main module for the YouTube downloader service.
Provides an API for downloading YouTube videos to GCS.
"""
import os
import uuid
import logging
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
import uvicorn
from dotenv import load_dotenv

from downloader.youtube import download_audio
from downloader.storage import upload_to_bucket

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="YouTube Downloader Service")

class DownloadRequest(BaseModel):
    """Request model for downloading YouTube videos."""
    urls: List[HttpUrl]
    collection_name: str

class DownloadResponse(BaseModel):
    """Response model for download operations."""
    collection_id: str
    video_ids: List[str]
    status: str
    gcs_paths: Optional[List[str]] = None

@app.post("/download", response_model=DownloadResponse)
async def download_videos(request: DownloadRequest):
    """Download YouTube videos and upload to GCS bucket."""
    try:
        # Create a unique collection ID
        collection_id = f"{request.collection_name}_{uuid.uuid4()}"
        video_ids = []
        gcs_paths = []
        
        for url in request.urls:
            # Extract video ID from URL
            video_id = str(url).split("v=")[-1].split("&")[0]
            video_ids.append(video_id)
            
            # Download audio
            logger.info(f"Downloading audio for video ID: {video_id}")
            local_path = await download_audio(url)
            
            # Upload to GCS
            gcs_path = await upload_to_bucket(
                local_path, 
                f"{collection_id}/{video_id}.mp3"
            )
            gcs_paths.append(gcs_path)
            
            # Remove local file
            os.remove(local_path)
            
        return DownloadResponse(
            collection_id=collection_id,
            video_ids=video_ids,
            status="completed",
            gcs_paths=gcs_paths
        )
            
    except Exception as e:
        logger.error(f"Error downloading videos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "youtube-downloader"}

if __name__ == "__main__":
    uvicorn.run("downloader.main:app", host="0.0.0.0", port=8001, reload=False)
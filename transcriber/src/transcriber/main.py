"""
Main module for the YouTube transcriber service.
"""
import logging
import os
import tempfile
import uuid
from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException
import uvicorn
from dotenv import load_dotenv

from transcriber.models import TranscriptionRequest, TranscriptionResponse, AudioChunk
from transcriber.chunker import chunk_audio
from transcriber.transcribe import process_audio
from transcriber.utils import download_from_bucket

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="YouTube Transcriber Service")

@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_videos(request: TranscriptionRequest):
    """
    Transcribe YouTube videos from GCS bucket.
    
    1. Download each audio file
    2. Split into 10-minute chunks
    3. Transcribe each chunk with Gemini
    4. Return transcriptions
    """
    try:
        chunks_list = []
        
        # Process each video in the collection
        for i, gcs_path in enumerate(request.gcs_paths):
            video_id = request.video_ids[i]
            logger.info(f"Processing video {video_id} from {gcs_path}")
            
            # Download audio from GCS
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                local_path = temp_file.name
                
            await download_from_bucket(gcs_path, local_path)
            
            # Split audio into 10-minute chunks
            chunks = await chunk_audio(
                local_path, 
                f"{request.collection_id}/{video_id}", 
                chunk_duration_ms=10*60*1000
            )
            
            # Process each chunk
            for chunk in chunks:
                # Generate a unique job ID for this chunk
                job_id = uuid.uuid4()
                
                # Transcribe the chunk
                transcript = await process_audio(
                    chunk.gcs_uri,
                    job_id,
                    start_timestamp=chunk.start_time,
                    end_timestamp=chunk.end_time
                )
                
                # Update chunk with transcript
                chunk.transcript = transcript
                chunks_list.append(chunk)
                
            # Clean up temporary file
            os.unlink(local_path)
            
        # Return response
        return TranscriptionResponse(
            collection_id=request.collection_id,
            video_ids=request.video_ids,
            status="completed",
            chunks=chunks_list
        )
        
    except Exception as e:
        logger.error(f"Error transcribing videos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "youtube-transcriber"}

if __name__ == "__main__":
    uvicorn.run("transcriber.main:app", host="0.0.0.0", port=8002, reload=False)
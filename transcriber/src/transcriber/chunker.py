"""
Module for chunking audio files.
"""
import os
import logging
import tempfile
import uuid
from typing import List
from pydub import AudioSegment

from transcriber.models import AudioChunk
from transcriber.utils import upload_to_bucket

logger = logging.getLogger(__name__)

async def chunk_audio(
    audio_path: str,
    base_name: str,
    chunk_duration_ms: int = 10 * 60 * 1000  # Default: 10 minutes
) -> List[AudioChunk]:
    """
    Split an audio file into chunks of specified duration.
    
    Args:
        audio_path: Path to the audio file
        base_name: Base name for the chunks
        chunk_duration_ms: Duration of each chunk in milliseconds
        
    Returns:
        List[AudioChunk]: List of audio chunks with GCS URIs
    """
    try:
        # Load audio file
        logger.info(f"Loading audio file: {audio_path}")
        audio = AudioSegment.from_file(audio_path)
        
        # Calculate chunk boundaries
        total_duration_ms = len(audio)
        chunks = []
        
        for start_ms in range(0, total_duration_ms, chunk_duration_ms):
            # Calculate chunk end time
            end_ms = min(start_ms + chunk_duration_ms, total_duration_ms)
            
            # Extract chunk
            chunk_audio = audio[start_ms:end_ms]
            
            # Create a unique ID for this chunk
            chunk_id = str(uuid.uuid4())
            
            # Save chunk to a temporary file
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                chunk_path = temp_file.name
                chunk_audio.export(chunk_path, format="mp3")
                
                # Upload chunk to GCS
                blob_name = f"chunks/{base_name}/{chunk_id}.mp3"
                gcs_uri = await upload_to_bucket(chunk_path, blob_name)
                
                # Create AudioChunk object
                chunk_obj = AudioChunk(
                    chunk_id=chunk_id,
                    start_time=start_ms / 1000.0,  # Convert to seconds
                    end_time=end_ms / 1000.0,      # Convert to seconds
                    gcs_uri=gcs_uri
                )
                chunks.append(chunk_obj)
                
                # Clean up temporary file
                os.unlink(chunk_path)
                
        logger.info(f"Split audio into {len(chunks)} chunks")
        return chunks
        
    except Exception as e:
        logger.error(f"Error chunking audio: {str(e)}")
        raise
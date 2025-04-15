"""
Models for the Transcriber service.
"""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

class Transcript(BaseModel):
    """Model for a transcript."""
    text: str = Field(description="The transcription of audio in SRT format")
    duration: float = Field(description="Total duration of audio in seconds")

class AudioChunk(BaseModel):
    """Model for an audio chunk."""
    chunk_id: str
    start_time: float  # In seconds
    end_time: float    # In seconds
    gcs_uri: str
    transcript: Optional[Transcript] = None

class TranscriptionRequest(BaseModel):
    """Model for a transcription request."""
    collection_id: str
    video_ids: List[str]
    gcs_paths: List[str]

class TranscriptionResponse(BaseModel):
    """Model for a transcription response."""
    collection_id: str
    video_ids: List[str]
    status: str
    chunks: List[AudioChunk]
    transcripts: Optional[List[Dict[str, str]]] = None  # video_id -> transcript
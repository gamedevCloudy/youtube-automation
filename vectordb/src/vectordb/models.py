"""
Models for the VectorDB service.
"""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

class Transcript(BaseModel):
    """Model for a transcript chunk."""
    text: str
    start_time: float
    end_time: float
    video_id: str
    chunk_id: str

class UpsertRequest(BaseModel):
    """Model for upserting documents into the vector store."""
    collection_id: str
    video_ids: List[str]
    transcripts: List[Transcript]

class QueryRequest(BaseModel):
    """Model for querying the vector store."""
    collection_ids: List[str]  # Support querying multiple collections
    query: str
    top_k: int = Field(default=5, description="Number of results to return")

class SearchResult(BaseModel):
    """Model for a single search result."""
    text: str
    video_id: str
    collection_id: str
    start_time: float
    end_time: float
    score: float

class QueryResponse(BaseModel):
    """Model for query response."""
    results: List[SearchResult]
"""
Main module for the VectorDB service.
"""
import logging
import os
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

from vectordb.embeddings import (
    create_collection,
    add_documents_to_collection,
    get_collections,
    delete_collection,
    get_collection_info
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="YouTube VectorDB Service")

class TranscriptChunk(BaseModel):
    """Model for a transcript chunk."""
    chunk_id: str
    video_id: str
    start_time: float
    end_time: float
    text: str
    metadata: Optional[Dict[str, Any]] = None

class VectorizeRequest(BaseModel):
    """Model for a vectorize request."""
    collection_id: str
    transcript_chunks: List[TranscriptChunk]

class VectorizeResponse(BaseModel):
    """Model for a vectorize response."""
    collection_id: str
    status: str
    num_chunks: int
    
class CollectionInfo(BaseModel):
    """Model for collection information."""
    collection_id: str
    count: int
    metadata: Optional[Dict[str, Any]] = None

class CollectionsResponse(BaseModel):
    """Model for a collections response."""
    collections: List[CollectionInfo]

@app.post("/vectorize", response_model=VectorizeResponse)
async def vectorize_transcripts(request: VectorizeRequest):
    """
    Create vector embeddings for transcript chunks.
    
    1. Create a ChromaDB collection if it doesn't exist
    2. Add transcript chunks to the collection
    3. Return status
    """
    try:
        # Create collection if it doesn't exist
        await create_collection(request.collection_id)
        
        # Convert transcript chunks to documents
        documents = []
        metadatas = []
        ids = []
        
        for chunk in request.transcript_chunks:
            # Create document
            documents.append(chunk.text)
            
            # Create metadata
            metadata = {
                "video_id": chunk.video_id,
                "chunk_id": chunk.chunk_id,
                "start_time": chunk.start_time,
                "end_time": chunk.end_time
            }
            
            # Add additional metadata if provided
            if chunk.metadata:
                metadata.update(chunk.metadata)
                
            metadatas.append(metadata)
            ids.append(chunk.chunk_id)
        
        # Add documents to collection
        await add_documents_to_collection(
            request.collection_id,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        # Return response
        return VectorizeResponse(
            collection_id=request.collection_id,
            status="completed",
            num_chunks=len(request.transcript_chunks)
        )
        
    except Exception as e:
        logger.error(f"Error vectorizing transcripts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/collections", response_model=CollectionsResponse)
async def list_collections():
    """
    List all collections in ChromaDB.
    """
    try:
        # Get collections
        collections = await get_collections()
        
        # Convert to response model
        collection_infos = []
        for collection_id in collections:
            info = await get_collection_info(collection_id)
            collection_infos.append(
                CollectionInfo(
                    collection_id=collection_id,
                    count=info["count"],
                    metadata=info.get("metadata")
                )
            )
        
        # Return response
        return CollectionsResponse(collections=collection_infos)
        
    except Exception as e:
        logger.error(f"Error listing collections: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/collections/{collection_id}")
async def remove_collection(collection_id: str):
    """
    Delete a collection from ChromaDB.
    """
    try:
        # Delete collection
        await delete_collection(collection_id)
        
        # Return response
        return {"status": "deleted", "collection_id": collection_id}
        
    except Exception as e:
        logger.error(f"Error deleting collection: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "youtube-vectordb"}

if __name__ == "__main__":
    uvicorn.run("vectordb.main:app", host="0.0.0.0", port=8003, reload=False)
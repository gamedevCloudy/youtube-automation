"""
Main module for the VectorDB service.
"""
import logging
from typing import List

from fastapi import FastAPI, HTTPException
import uvicorn
from dotenv import load_dotenv

from vectordb.models import (
    UpsertRequest,
    QueryRequest,
    QueryResponse,
    SearchResult
)
from vectordb.store import VectorStore

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="VectorDB Service")

# Initialize vector store
store = VectorStore(persist_directory="./data")

@app.post("/upsert")
async def upsert_documents(request: UpsertRequest):
    """
    Upsert documents into the vector store.
    """
    try:
        await store.upsert_documents(
            request.collection_id,
            request.video_ids,
            request.transcripts
        )
        
        return {
            "status": "success",
            "message": f"Upserted documents for collection {request.collection_id}"
        }
        
    except Exception as e:
        logger.error(f"Error upserting documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=QueryResponse)
async def query_store(request: QueryRequest):
    """
    Query the vector store.
    """
    try:
        results = await store.query(
            request.collection_ids,
            request.query,
            request.top_k
        )
        
        return QueryResponse(results=results)
        
    except Exception as e:
        logger.error(f"Error querying vector store: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "vectordb"}

if __name__ == "__main__":
    uvicorn.run("vectordb.main:app", host="0.0.0.0", port=8003, reload=False)
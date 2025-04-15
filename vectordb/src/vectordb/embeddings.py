"""
Module for creating and managing embeddings with ChromaDB.
"""
import os
import logging
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

# Configure logging
logger = logging.getLogger(__name__)

# Initialize ChromaDB client
chroma_client = chromadb.PersistentClient(
    path="/app/data",
    settings=Settings(
        allow_reset=True,
        anonymized_telemetry=False
    )
)

# Initialize embedding function
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

async def create_collection(collection_name: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
    """
    Create a ChromaDB collection if it doesn't exist.
    
    Args:
        collection_name: Name of the collection
        metadata: Optional metadata for the collection
        
    Returns:
        bool: True if created, False if already exists
    """
    try:
        # Check if collection exists
        collections = chroma_client.list_collections()
        if any(c.name == collection_name for c in collections):
            logger.info(f"Collection {collection_name} already exists")
            return False
        
        # Create collection
        chroma_client.create_collection(
            name=collection_name,
            embedding_function=sentence_transformer_ef,
            metadata=metadata or {}
        )
        logger.info(f"Created collection {collection_name}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating collection: {str(e)}")
        raise

async def add_documents_to_collection(
    collection_name: str,
    documents: List[str],
    metadatas: List[Dict[str, Any]],
    ids: List[str]
) -> int:
    """
    Add documents to a ChromaDB collection.
    
    Args:
        collection_name: Name of the collection
        documents: List of document texts
        metadatas: List of document metadata
        ids: List of document IDs
        
    Returns:
        int: Number of documents added
    """
    try:
        # Get collection
        collection = chroma_client.get_collection(
            name=collection_name,
            embedding_function=sentence_transformer_ef
        )
        
        # Add documents
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        logger.info(f"Added {len(documents)} documents to collection {collection_name}")
        
        return len(documents)
        
    except Exception as e:
        logger.error(f"Error adding documents to collection: {str(e)}")
        raise

async def get_collections() -> List[str]:
    """
    Get a list of all collections in ChromaDB.
    
    Returns:
        List[str]: List of collection names
    """
    try:
        # Get collections
        collections = chroma_client.list_collections()
        return [c.name for c in collections]
        
    except Exception as e:
        logger.error(f"Error getting collections: {str(e)}")
        raise

async def delete_collection(collection_name: str) -> bool:
    """
    Delete a ChromaDB collection.
    
    Args:
        collection_name: Name of the collection
        
    Returns:
        bool: True if deleted
    """
    try:
        # Delete collection
        chroma_client.delete_collection(collection_name)
        logger.info(f"Deleted collection {collection_name}")
        return True
        
    except Exception as e:
        logger.error(f"Error deleting collection: {str(e)}")
        raise

async def get_collection_info(collection_name: str) -> Dict[str, Any]:
    """
    Get information about a ChromaDB collection.
    
    Args:
        collection_name: Name of the collection
        
    Returns:
        Dict[str, Any]: Collection information
    """
    try:
        # Get collection
        collection = chroma_client.get_collection(
            name=collection_name,
            embedding_function=sentence_transformer_ef
        )
        
        # Get count
        count = collection.count()
        
        # Get metadata
        # Note: ChromaDB doesn't provide direct access to collection metadata
        # We'll use a placeholder here
        
        return {
            "count": count,
            "metadata": {}
        }
        
    except Exception as e:
        logger.error(f"Error getting collection info: {str(e)}")
        raise

async def query_collection(
    collection_name: str,
    query_text: str,
    n_results: int = 5,
    metadata_filter: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Query a ChromaDB collection.
    
    Args:
        collection_name: Name of the collection
        query_text: Query text
        n_results: Number of results to return
        metadata_filter: Filter for metadata
        
    Returns:
        Dict[str, Any]: Query results
    """
    try:
        # Get collection
        collection = chroma_client.get_collection(
            name=collection_name,
            embedding_function=sentence_transformer_ef
        )
        
        # Query collection
        results = collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=metadata_filter
        )
        
        return results
        
    except Exception as e:
        logger.error(f"Error querying collection: {str(e)}")
        raise
"""
Vector store operations using LangChain and ChromaDB.
"""
import logging
import os
from typing import List, Dict, Any

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_vertexai.embeddings import VertexAIEmbeddings
from langchain.schema import Document

from vectordb.models import Transcript, SearchResult

# Configure logging
logger = logging.getLogger(__name__)

class VectorStore:
    """Vector store manager using ChromaDB."""
    
    def __init__(self, persist_directory: str = "./data"):
        """Initialize the vector store."""
        self.persist_directory = persist_directory
        
        # Initialize embeddings model
        self.embeddings = VertexAIEmbeddings(model="text-embedding-004")
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        # Create persist directory if it doesn't exist
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize ChromaDB
        self.db = Chroma(
            persist_directory=persist_directory,
            embedding_function=self.embeddings
        )
        
    async def upsert_documents(
        self,
        collection_id: str,
        video_ids: List[str],
        transcripts: List[Transcript]
    ) -> None:
        """
        Upsert documents into the vector store.
        
        Args:
            collection_id: Collection identifier
            video_ids: List of video IDs
            transcripts: List of transcripts
        """
        try:
            # Convert transcripts to documents
            documents = []
            
            for transcript in transcripts:
                # Create document
                doc = Document(
                    page_content=transcript.text,
                    metadata={
                        "video_id": transcript.video_id,
                        "collection_id": collection_id,
                        "start_time": transcript.start_time,
                        "end_time": transcript.end_time,
                        "chunk_id": transcript.chunk_id
                    }
                )
                documents.append(doc)
            
            # Split documents if needed
            split_docs = self.text_splitter.split_documents(documents)
            
            # Add documents to vector store
            self.db.add_documents(split_docs)
            
            # Persist to disk
            self.db.persist()
            
            logger.info(
                f"Upserted {len(split_docs)} chunks for collection {collection_id}"
            )
            
        except Exception as e:
            logger.error(f"Error upserting documents: {str(e)}")
            raise
            
    async def query(
        self,
        collection_ids: List[str],
        query: str,
        top_k: int = 5
    ) -> List[SearchResult]:
        """
        Query the vector store across multiple collections.
        
        Args:
            collection_ids: List of collection IDs to search
            query: Query string
            top_k: Number of results to return
            
        Returns:
            List[SearchResult]: List of search results
        """
        try:
            # Create filter for collections
            filter_dict = {
                "collection_id": {"$in": collection_ids}
            }
            
            # Search vector store
            results = self.db.similarity_search_with_score(
                query,
                k=top_k,
                filter=filter_dict
            )
            
            # Convert to SearchResult objects
            search_results = []
            
            for doc, score in results:
                result = SearchResult(
                    text=doc.page_content,
                    video_id=doc.metadata["video_id"],
                    collection_id=doc.metadata["collection_id"],
                    start_time=doc.metadata["start_time"],
                    end_time=doc.metadata["end_time"],
                    score=float(score)
                )
                search_results.append(result)
                
            return search_results
            
        except Exception as e:
            logger.error(f"Error querying vector store: {str(e)}")
            raise
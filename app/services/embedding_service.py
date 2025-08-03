from typing import List, Dict, Any
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.core.exceptions import EmbeddingError, ConfigurationError
from app.models.mcp import DocumentChunk
import os


class EmbeddingService:
    """Service for generating and managing embeddings"""
    
    def __init__(self):
        self._embeddings = None
        self._initialized = False
    
    def _initialize(self):
        """Lazy initialization of the embedding service"""
        if self._initialized:
            return
            
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        
        if not self.google_api_key:
            raise ConfigurationError(
                "GOOGLE_API_KEY not found in environment variables", 
                config_key="GOOGLE_API_KEY"
            )
        
        self._embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        self._initialized = True
    
    @property
    def embeddings(self):
        """Get the embeddings instance, initializing if needed"""
        if not self._initialized:
            self._initialize()
        return self._embeddings
    
    def create_embeddings(self, document_chunks: List[DocumentChunk]) -> List[Dict[str, Any]]:
        """
        Convert document chunks to embeddings
        
        Args:
            document_chunks: List of DocumentChunk objects
            
        Returns:
            List of dictionaries containing embeddings and metadata
        """
        embed_docs = []
        
        for i, chunk in enumerate(document_chunks):
            try:
                embed = self.embeddings.embed_query(chunk.content)
                
                # Filter out None values from metadata for Pinecone compatibility
                metadata = {
                    "text": chunk.content,
                    "source": chunk.source,  # This is already just filename
                    "chunk_index": chunk.chunk_index,
                }
                
                # Only add page_number if it's not None
                if chunk.page_number is not None:
                    metadata["page_number"] = chunk.page_number
                
                # Add other metadata fields, filtering out None values
                for key, value in chunk.metadata.items():
                    if value is not None:
                        metadata[key] = value
                
                embed_docs.append({
                    "id": chunk.id,
                    "values": embed,
                    "metadata": metadata
                })
                
            except Exception as e:
                raise EmbeddingError(
                    f"Error embedding document chunk {i}: {str(e)}", 
                    chunk_id=chunk.id
                )
        
        return embed_docs
    



# Global instance
embedding_service = EmbeddingService() 
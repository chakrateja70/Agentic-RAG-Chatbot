from pinecone import Pinecone, ServerlessSpec
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv
from app.core.exceptions import VectorStoreError, ConfigurationError

load_dotenv(override=True)


class VectorStoreManager:
    """Manages vector store operations using Pinecone"""
    
    def __init__(self):
        self.pinecone_api_key = None
        self.google_api_key = None
        self.index_name = "nabla-rag-poc"
        self.namespace = "EZTask"
        self.pc = None
        self._embeddings = None
        self._initialized = False
    
    def _initialize(self):
        """Lazy initialization of the vector store"""
        if self._initialized:
            return
            
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        
        if not self.pinecone_api_key:
            raise ConfigurationError("PINECONE_API_KEY not found in environment variables", 
                                   config_key="PINECONE_API_KEY")
        
        if not self.google_api_key:
            raise ConfigurationError("GOOGLE_API_KEY not found in environment variables", 
                                   config_key="GOOGLE_API_KEY")
        
        self.pc = Pinecone(self.pinecone_api_key)
        self._embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        self._initialize_index()
        self._initialized = True
    
    def _initialize_index(self):
        """Initialize Pinecone index if it doesn't exist"""
        try:
            if not self.pc.has_index(self.index_name):
                self.pc.create_index(
                    name=self.index_name,
                    dimension=768,
                    metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region="us-east-1"),
                )
        except Exception as e:
            raise VectorStoreError(f"Failed to initialize Pinecone index: {str(e)}", 
                                 operation="index_initialization")
    
    @property
    def index(self):
        """Get the Pinecone index instance"""
        if not self._initialized:
            self._initialize()
        return self.pc.Index(self.index_name)
    
    @property
    def embeddings(self):
        """Get the embeddings instance"""
        if not self._initialized:
            self._initialize()
        return self._embeddings
    
    def add_embeddings(self, embeddings: List[Dict[str, Any]]) -> bool:
        """
        Add embeddings to the vector store
        
        Args:
            embeddings: List of dictionaries with 'id', 'values', and 'metadata'
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            vectors = [(doc["id"], doc["values"], doc["metadata"]) for doc in embeddings]
            self.index.upsert(vectors, namespace=self.namespace)
            return True
        except Exception as e:
            raise VectorStoreError(f"Failed to add embeddings: {str(e)}", 
                                 operation="add_embeddings")
    
    def search(self, query: str, top_k: int = 8, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for similar documents in the vector store
        
        Args:
            query: Search query string
            top_k: Number of top results to return
            namespace: Namespace to search in (defaults to self.namespace)
        
        Returns:
            List of search results with metadata
        """
        try:
            query_embedding = self.embeddings.embed_query(query)
            search_namespace = namespace or self.namespace
            
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                namespace=search_namespace,
                include_metadata=True
            )
            
            return results.get('matches', [])
        except Exception as e:
            raise VectorStoreError(f"Failed to search vector store: {str(e)}", 
                                 operation="search")
    



# Global instance
vector_store = VectorStoreManager() 
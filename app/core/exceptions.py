from typing import Optional, Dict, Any
from app.models.mcp import AgentType, MessageType


class RAGException(Exception):
    """Base exception for RAG system"""
    def __init__(self, message: str, agent: Optional[AgentType] = None, 
                 message_type: Optional[MessageType] = None, 
                 trace_id: Optional[str] = None):
        self.message = message
        self.agent = agent
        self.message_type = message_type
        self.trace_id = trace_id
        super().__init__(self.message)


class DocumentProcessingError(RAGException):
    """Raised when document processing fails"""
    def __init__(self, message: str, file_path: Optional[str] = None, **kwargs):
        self.file_path = file_path
        super().__init__(f"Document processing error: {message}", **kwargs)


class EmbeddingError(RAGException):
    """Raised when embedding generation fails"""
    def __init__(self, message: str, chunk_id: Optional[str] = None, **kwargs):
        self.chunk_id = chunk_id
        super().__init__(f"Embedding error: {message}", **kwargs)


class VectorStoreError(RAGException):
    """Raised when vector store operations fail"""
    def __init__(self, message: str, operation: Optional[str] = None, **kwargs):
        self.operation = operation
        super().__init__(f"Vector store error: {message}", **kwargs)


class RetrievalError(RAGException):
    """Raised when document retrieval fails"""
    def __init__(self, message: str, query: Optional[str] = None, **kwargs):
        self.query = query
        super().__init__(f"Retrieval error: {message}", **kwargs)


class LLMError(RAGException):
    """Raised when LLM operations fail"""
    def __init__(self, message: str, model: Optional[str] = None, **kwargs):
        self.model = model
        super().__init__(f"LLM error: {message}", **kwargs)


class MCPError(RAGException):
    """Raised when MCP message handling fails"""
    def __init__(self, message: str, message_id: Optional[str] = None, **kwargs):
        self.message_id = message_id
        super().__init__(f"MCP error: {message}", **kwargs)


class AgentCommunicationError(RAGException):
    """Raised when agent communication fails"""
    def __init__(self, message: str, sender: Optional[AgentType] = None, 
                 receiver: Optional[AgentType] = None, **kwargs):
        self.sender = sender
        self.receiver = receiver
        super().__init__(f"Agent communication error: {message}", **kwargs)


class ConfigurationError(RAGException):
    """Raised when configuration is invalid"""
    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        self.config_key = config_key
        super().__init__(f"Configuration error: {message}", **kwargs) 
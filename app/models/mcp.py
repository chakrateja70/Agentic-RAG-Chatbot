from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from enum import Enum
import uuid
from datetime import datetime


class MessageType(str, Enum):
    """Types of MCP messages"""
    DOCUMENT_INGESTION_REQUEST = "DOCUMENT_INGESTION_REQUEST"
    DOCUMENT_INGESTION_RESPONSE = "DOCUMENT_INGESTION_RESPONSE"
    RETRIEVAL_REQUEST = "RETRIEVAL_REQUEST"
    RETRIEVAL_RESPONSE = "RETRIEVAL_RESPONSE"
    LLM_QUERY_REQUEST = "LLM_QUERY_REQUEST"
    LLM_QUERY_RESPONSE = "LLM_QUERY_RESPONSE"
    ERROR = "ERROR"


class AgentType(str, Enum):
    """Types of agents in the system"""
    INGESTION_AGENT = "IngestionAgent"
    RETRIEVAL_AGENT = "RetrievalAgent"
    LLM_RESPONSE_AGENT = "LLMResponseAgent"
    COORDINATOR_AGENT = "CoordinatorAgent"


class MCPMessage(BaseModel):
    """Base MCP message structure"""
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sender: AgentType
    receiver: AgentType
    message_type: MessageType
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    payload: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentChunk(BaseModel):
    """Represents a document chunk with metadata"""
    id: str
    content: str
    source: str
    page_number: Optional[int] = None
    chunk_index: int
    metadata: Dict[str, Any] = Field(default_factory=dict)


 
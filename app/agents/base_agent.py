from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.models.mcp import MCPMessage, AgentType, MessageType
from app.core.message_broker import message_broker
from app.core.exceptions import AgentCommunicationError, MCPError
import threading
import time
import uuid


class BaseAgent(ABC):
    """Base class for all agents in the RAG system"""
    
    def __init__(self, agent_type: AgentType):
        self.agent_type = agent_type
        self.is_running = False
        self.message_thread = None
        self.handlers: Dict[MessageType, callable] = {}
        self.trace_id = str(uuid.uuid4())
        
        # Register with message broker
        message_broker.register_agent(agent_type)
        
        # Register default handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default message handlers"""
        # Override in subclasses to register specific handlers
        pass
    
    def register_handler(self, message_type: MessageType, handler: callable):
        """Register a message handler for a specific message type"""
        self.handlers[message_type] = handler
        message_broker.register_handler(self.agent_type, message_type, handler)
    
    def send_message(self, receiver: AgentType, message_type: MessageType, 
                    payload: Dict[str, Any], trace_id: Optional[str] = None) -> bool:
        """
        Send a message to another agent
        
        Args:
            receiver: Target agent
            message_type: Type of message
            payload: Message payload
            trace_id: Optional trace ID for tracking
            
        Returns:
            bool: True if message sent successfully
        """
        try:
            message = MCPMessage(
                sender=self.agent_type,
                receiver=receiver,
                message_type=message_type,
                trace_id=trace_id or self.trace_id,
                payload=payload
            )
            
            return message_broker.send_message(message)
            
        except Exception as e:
            raise AgentCommunicationError(
                f"Failed to send message: {str(e)}",
                sender=self.agent_type,
                receiver=receiver
            )
    
    def receive_message(self, timeout: float = 1.0) -> Optional[MCPMessage]:
        """
        Receive a message for this agent
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            MCPMessage or None if no message received
        """
        return message_broker.receive_message(self.agent_type, timeout)
    
    def process_message(self, message: MCPMessage) -> Any:
        """
        Process a received message using registered handlers
        
        Args:
            message: Message to process
            
        Returns:
            Result from message handler
        """
        if message.message_type in self.handlers:
            return self.handlers[message.message_type](message)
        else:
            raise MCPError(f"No handler registered for message type {message.message_type.value}")
    
    def start(self):
        """Start the agent's message processing loop"""
        if self.is_running:
            return
        
        self.is_running = True
        self.message_thread = threading.Thread(target=self._message_loop, daemon=True)
        self.message_thread.start()
    
    def stop(self):
        """Stop the agent's message processing loop"""
        self.is_running = False
        if self.message_thread:
            self.message_thread.join(timeout=5.0)
        message_broker.unregister_agent(self.agent_type)
    
    def _message_loop(self):
        """Main message processing loop"""
        while self.is_running:
            try:
                message = self.receive_message(timeout=1.0)
                if message:
                    self.process_message(message)
            except Exception as e:
                time.sleep(0.1)
    
    @abstractmethod
    def handle_document_ingestion_request(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle document ingestion requests"""
        pass
    
    @abstractmethod
    def handle_retrieval_request(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle retrieval requests"""
        pass
    
    @abstractmethod
    def handle_llm_query_request(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle LLM query requests"""
        pass
    

    
    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop() 
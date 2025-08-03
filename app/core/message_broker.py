from typing import Dict, List, Any, Callable, Optional
from app.models.mcp import MCPMessage, AgentType, MessageType
from app.core.exceptions import MCPError, AgentCommunicationError

import threading
import queue



class MCPMessageBroker:
    """Message broker for Model Context Protocol communication between agents"""
    
    def __init__(self):
        self.message_queues: Dict[AgentType, queue.Queue] = {}
        self.message_handlers: Dict[AgentType, Dict[MessageType, Callable]] = {}
        self.message_history: List[MCPMessage] = []
        self.active_agents: set = set()
        self.lock = threading.Lock()
        
        # Initialize queues for all agent types
        for agent_type in AgentType:
            self.message_queues[agent_type] = queue.Queue()
            self.message_handlers[agent_type] = {}
    
    def register_agent(self, agent_type: AgentType) -> None:
        """Register an agent with the message broker"""
        with self.lock:
            self.active_agents.add(agent_type)
    
    def unregister_agent(self, agent_type: AgentType) -> None:
        """Unregister an agent from the message broker"""
        with self.lock:
            self.active_agents.discard(agent_type)
    
    def register_handler(self, agent_type: AgentType, message_type: MessageType, 
                        handler: Callable[[MCPMessage], Any]) -> None:
        """Register a message handler for a specific agent and message type"""
        if agent_type not in self.message_handlers:
            self.message_handlers[agent_type] = {}
        
        self.message_handlers[agent_type][message_type] = handler
    
    def send_message(self, message: MCPMessage) -> bool:
        """
        Send a message to the specified receiver agent
        
        Args:
            message: MCP message to send
            
        Returns:
            bool: True if message was sent successfully
        """
        try:
            if message.receiver not in self.active_agents:
                raise AgentCommunicationError(
                    f"Receiver agent {message.receiver.value} is not active",
                    sender=message.sender,
                    receiver=message.receiver
                )
            
            # Add message to receiver's queue
            self.message_queues[message.receiver].put(message)
            
            # Store in message history
            with self.lock:
                self.message_history.append(message)
            
            return True
            
        except Exception as e:
            raise MCPError(f"Failed to send message: {str(e)}", message_id=message.message_id)
    
    def receive_message(self, agent_type: AgentType, timeout: float = 1.0) -> Optional[MCPMessage]:
        """
        Receive a message for the specified agent
        
        Args:
            agent_type: Type of agent receiving the message
            timeout: Timeout in seconds for waiting for a message
            
        Returns:
            MCPMessage or None if no message received within timeout
        """
        try:
            message = self.message_queues[agent_type].get(timeout=timeout)
            return message
        except queue.Empty:
            return None
        except Exception as e:
            raise MCPError(f"Failed to receive message: {str(e)}")
    
    def process_message(self, agent_type: AgentType, message: MCPMessage) -> Any:
        """
        Process a message using the registered handler
        
        Args:
            agent_type: Type of agent processing the message
            message: Message to process
            
        Returns:
            Result from the message handler
        """
        try:
            if agent_type not in self.message_handlers:
                raise MCPError(f"No handlers registered for agent {agent_type.value}")
            
            if message.message_type not in self.message_handlers[agent_type]:
                raise MCPError(f"No handler registered for message type {message.message_type.value}")
            
            handler = self.message_handlers[agent_type][message.message_type]
            result = handler(message)
            
            return result
            
        except Exception as e:
            raise MCPError(f"Failed to process message: {str(e)}", message_id=message.message_id)
    

    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all registered agents"""
        with self.lock:
            return {
                "active_agents": [agent.value for agent in self.active_agents],
                "total_messages": len(self.message_history),
                "queue_sizes": {agent.value: self.message_queues[agent].qsize() 
                              for agent in self.message_queues}
            }
    



# Global message broker instance
message_broker = MCPMessageBroker() 
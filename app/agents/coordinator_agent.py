from typing import Dict, Any, List

import threading
import time
import uuid
from app.agents.base_agent import BaseAgent
from app.models.mcp import AgentType, MessageType, MCPMessage
from app.core.message_broker import message_broker
from app.core.exceptions import AgentCommunicationError, MCPError


class CoordinatorAgent(BaseAgent):
    """Agent responsible for orchestrating the workflow between all other agents"""
    
    def __init__(self):
        super().__init__(AgentType.COORDINATOR_AGENT)
        self.pending_requests: Dict[str, Dict[str, Any]] = {}
        self.request_lock = threading.Lock()
    
    def _register_default_handlers(self):
        """Register message handlers for this agent"""
        self.register_handler(MessageType.DOCUMENT_INGESTION_RESPONSE, self.handle_document_ingestion_response)
        self.register_handler(MessageType.RETRIEVAL_RESPONSE, self.handle_retrieval_response)
        self.register_handler(MessageType.LLM_QUERY_RESPONSE, self.handle_llm_query_response)
    
    def process_document_upload(self, file_paths: List[str], processing_options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process document upload by coordinating with IngestionAgent
        
        Args:
            file_paths: List of file paths to process
            processing_options: Options for processing
            
        Returns:
            Dictionary with processing results
        """
        # trace_id = str(time.time())
        trace_id = str(uuid.uuid4())
        # Prepare request payload
        payload = {
            "file_paths": file_paths,
            "processing_options": processing_options or {}
        }
        
        # Store pending request
        with self.request_lock:
            self.pending_requests[trace_id] = {
                "type": "document_ingestion",
                "status": "pending",
                "start_time": time.time()
            }
        
        # Send request to IngestionAgent
        self.send_message(
            receiver=AgentType.INGESTION_AGENT,
            message_type=MessageType.DOCUMENT_INGESTION_REQUEST,
            payload=payload,
            trace_id=trace_id
        )
        
        # Wait for response (with timeout)
        return self._wait_for_response(trace_id, timeout=300)  # 5 minutes timeout
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a user query by coordinating with RetrievalAgent and LLMResponseAgent
        
        Args:
            query: User's query
            
        Returns:
            Dictionary with query results
        """
        start_time = time.time()
        retrieval_trace_id = str(uuid.uuid4())
        llm_trace_id = str(uuid.uuid4())  # Different trace ID for LLM request

        # Store pending requests
        with self.request_lock:
            self.pending_requests[retrieval_trace_id] = {
                "type": "retrieval",
                "status": "pending",
                "start_time": start_time,
                "query": query
            }
            
            self.pending_requests[llm_trace_id] = {
                "type": "llm_query",
                "status": "pending",
                "start_time": start_time,
                "query": query
            }
        
        # Step 1: Retrieve relevant chunks
        retrieval_payload = {
            "query": query,
            "top_k": 8
        }
        
        self.send_message(
            receiver=AgentType.RETRIEVAL_AGENT,
            message_type=MessageType.RETRIEVAL_REQUEST,
            payload=retrieval_payload,
            trace_id=retrieval_trace_id
        )
        
        # Wait for retrieval response
        retrieval_response = self._wait_for_response(retrieval_trace_id, timeout=30)
        
        if not retrieval_response.get("success", False):
            return retrieval_response
        
        # Step 2: Generate LLM response
        retrieved_chunks = retrieval_response.get("retrieved_chunks", [])
        context = "\n".join(retrieved_chunks)
        sources = retrieval_response.get("sources", [])
        metadata = retrieval_response.get("metadata", [])  # Get metadata from retrieval
        
        llm_payload = {
            "query": query,
            "context": context,
            "sources": sources,
            "metadata": metadata
        }
        
        self.send_message(
            receiver=AgentType.LLM_RESPONSE_AGENT,
            message_type=MessageType.LLM_QUERY_REQUEST,
            payload=llm_payload,
            trace_id=llm_trace_id
        )
        
        # Wait for LLM response
        llm_response = self._wait_for_response(llm_trace_id, timeout=30)
        
        # Calculate total processing time
        total_processing_time = time.time() - start_time
        
        # Combine results
        if llm_response.get("success", False):
            return {
                "success": True,
                "query": query,
                "answer": llm_response.get("response", {}),
                "sources": retrieval_response.get("sources", []),
                "context_chunks": retrieved_chunks,
                "processing_time": total_processing_time
            }
        else:
            return llm_response
    
    def handle_document_ingestion_response(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle response from IngestionAgent"""
        trace_id = message.trace_id
        
        with self.request_lock:
            if trace_id in self.pending_requests:
                self.pending_requests[trace_id]["status"] = "completed"
                self.pending_requests[trace_id]["response"] = message.payload
                self.pending_requests[trace_id]["end_time"] = time.time()
        
        return message.payload
    
    def handle_retrieval_response(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle response from RetrievalAgent"""
        trace_id = message.trace_id
        
        with self.request_lock:
            if trace_id in self.pending_requests:
                self.pending_requests[trace_id]["status"] = "completed"
                self.pending_requests[trace_id]["response"] = message.payload
                self.pending_requests[trace_id]["end_time"] = time.time()
                print(f"Retrieval response received for trace_id: {trace_id}")
            else:
                print(f"Warning: Received retrieval response for unknown trace_id: {trace_id}")
        
        return message.payload
    
    def handle_llm_query_response(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle response from LLMResponseAgent"""
        trace_id = message.trace_id
        
        with self.request_lock:
            if trace_id in self.pending_requests:
                self.pending_requests[trace_id]["status"] = "completed"
                self.pending_requests[trace_id]["response"] = message.payload
                self.pending_requests[trace_id]["end_time"] = time.time()
                print(f"LLM response received for trace_id: {trace_id}")
            else:
                print(f"Warning: Received LLM response for unknown trace_id: {trace_id}")
        
        return message.payload
    
    def _wait_for_response(self, trace_id: str, timeout: float = 60) -> Dict[str, Any]:
        """
        Wait for a response for a specific trace ID
        
        Args:
            trace_id: Trace ID to wait for
            timeout: Timeout in seconds
            
        Returns:
            Response data or error
        """
        start_time = time.time()
        print(f"Waiting for response with trace_id: {trace_id}, timeout: {timeout}s")
        
        while time.time() - start_time < timeout:
            with self.request_lock:
                if trace_id in self.pending_requests:
                    request = self.pending_requests[trace_id]
                    if request["status"] == "completed":
                        response = request.get("response", {})
                        # Clean up
                        del self.pending_requests[trace_id]
                        print(f"Response received for trace_id: {trace_id} after {time.time() - start_time:.2f}s")
                        return response
                    else:
                        print(f"Request {trace_id} still pending, status: {request['status']}")
            
            time.sleep(0.1)
        
        # Timeout occurred
        print(f"Timeout occurred for trace_id: {trace_id} after {timeout}s")
        with self.request_lock:
            if trace_id in self.pending_requests:
                del self.pending_requests[trace_id]
        
        return {
            "success": False,
            "error": f"Request timed out after {timeout} seconds",
            "trace_id": trace_id
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        agent_status = message_broker.get_agent_status()
        
        with self.request_lock:
            pending_count = len([req for req in self.pending_requests.values() if req["status"] == "pending"])
            completed_count = len([req for req in self.pending_requests.values() if req["status"] == "completed"])
        
        return {
            "agent_status": agent_status,
            "pending_requests": pending_count,
            "completed_requests": completed_count,
            "total_requests": len(self.pending_requests)
        }
    
    def handle_document_ingestion_request(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle document ingestion requests (not implemented for this agent)"""
        raise NotImplementedError("CoordinatorAgent does not handle document ingestion requests")
    
    def handle_retrieval_request(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle retrieval requests (not implemented for this agent)"""
        raise NotImplementedError("CoordinatorAgent does not handle retrieval requests")
    
    def handle_llm_query_request(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle LLM query requests (not implemented for this agent)"""
        raise NotImplementedError("CoordinatorAgent does not handle LLM query requests") 
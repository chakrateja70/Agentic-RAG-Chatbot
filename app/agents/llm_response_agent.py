from typing import Dict, Any, List
from app.agents.base_agent import BaseAgent
from app.models.mcp import AgentType, MessageType, MCPMessage
from app.services.llm_service import llm_service
from app.core.exceptions import LLMError


class LLMResponseAgent(BaseAgent):
    """Agent responsible for LLM interactions and response generation"""
    
    def __init__(self):
        super().__init__(AgentType.LLM_RESPONSE_AGENT)
    
    def _register_default_handlers(self):
        """Register message handlers for this agent"""
        self.register_handler(MessageType.LLM_QUERY_REQUEST, self.handle_llm_query_request)
    
    def handle_llm_query_request(self, message: MCPMessage) -> Dict[str, Any]:
        """
        Handle LLM query requests
        
        Args:
            message: MCP message containing LLM query request
            
        Returns:
            Dictionary with LLM response
        """
        try:
            payload = message.payload
            query = payload.get("query", "")
            context = payload.get("context", "")
            sources = payload.get("sources", [])  # Get sources from payload
            metadata = payload.get("metadata", [])  # Get metadata from payload
            

            
            # Generate answer
            result = self._generate_answer(query, context, sources, metadata)
            
            # Prepare response payload
            response_payload = {
                "success": True,
                "query": query,
                "response": result,
                "model": llm_service.model,
                "trace_id": message.trace_id
            }
            
            # Send response to coordinator
            self.send_message(
                receiver=AgentType.COORDINATOR_AGENT,
                message_type=MessageType.LLM_QUERY_RESPONSE,
                payload=response_payload,
                trace_id=message.trace_id
            )
            
            return response_payload
            
        except Exception as e:
            error_payload = {
                "success": False,
                "error": str(e),
                "query": payload.get("query", ""),
                "trace_id": message.trace_id
            }
            
            # Send error response
            self.send_message(
                receiver=AgentType.COORDINATOR_AGENT,
                message_type=MessageType.LLM_QUERY_RESPONSE,
                payload=error_payload,
                trace_id=message.trace_id
            )
            
            raise LLMError(f"LLM query failed: {str(e)}", model=llm_service.model)
    
    def _generate_answer(self, query: str, context: str, sources: List[str] = None, metadata: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate an answer to a question based on context
        
        Args:
            query: User's question
            context: Relevant document context
            sources: List of source file names
            metadata: List of metadata dictionaries for context chunks
            
        Returns:
            Dictionary with answer and metadata
        """
        return llm_service.answer_question(query, context, sources, metadata)
    

    
    def handle_document_ingestion_request(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle document ingestion requests (not implemented for this agent)"""
        raise NotImplementedError("LLMResponseAgent does not handle document ingestion requests")
    
    def handle_retrieval_request(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle retrieval requests (not implemented for this agent)"""
        raise NotImplementedError("LLMResponseAgent does not handle retrieval requests") 
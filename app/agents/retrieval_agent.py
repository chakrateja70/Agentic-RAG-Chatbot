from typing import Dict, Any, List
from app.agents.base_agent import BaseAgent
from app.models.mcp import AgentType, MessageType, MCPMessage
from app.db.vector_store import vector_store

from app.core.exceptions import RetrievalError


class RetrievalAgent(BaseAgent):
    """Agent responsible for document retrieval and similarity search"""
    
    def __init__(self):
        super().__init__(AgentType.RETRIEVAL_AGENT)
    
    def _register_default_handlers(self):
        """Register message handlers for this agent"""
        self.register_handler(MessageType.RETRIEVAL_REQUEST, self.handle_retrieval_request)
    
    def handle_retrieval_request(self, message: MCPMessage) -> Dict[str, Any]:
        """
        Handle retrieval requests
        
        Args:
            message: MCP message containing retrieval request
            
        Returns:
            Dictionary with retrieval results
        """
        try:
            payload = message.payload
            query = payload.get("query", "")
            top_k = payload.get("top_k", 8)
            namespace = payload.get("namespace", None)
            

            
            # Perform retrieval
            results = self._retrieve_relevant_chunks(query, top_k, namespace)
            
            # Prepare response payload
            response_payload = {
                "success": True,
                "query": query,
                "retrieved_chunks": results["chunks"],
                "scores": results["scores"],
                "sources": results["sources"],
                "total_results": len(results["chunks"]),
                "trace_id": message.trace_id
            }
            
            # Send response to coordinator
            self.send_message(
                receiver=AgentType.COORDINATOR_AGENT,
                message_type=MessageType.RETRIEVAL_RESPONSE,
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
                message_type=MessageType.RETRIEVAL_RESPONSE,
                payload=error_payload,
                trace_id=message.trace_id
            )
            
            raise RetrievalError(f"Retrieval failed: {str(e)}", query=payload.get("query", ""))
    
    def _retrieve_relevant_chunks(self, query: str, top_k: int = 8, namespace: str = None) -> Dict[str, Any]:
        """
        Retrieve relevant document chunks based on query
        
        Args:
            query: Search query
            top_k: Number of top results to return
            namespace: Vector store namespace
            
        Returns:
            Dictionary with retrieval results
        """
        try:
            # Search vector store
            search_results = vector_store.search(query, top_k, namespace)
            
            if not search_results:
                return {
                    "chunks": [],
                    "scores": [],
                    "sources": []
                }
            
            # Extract chunks, scores, and sources
            chunks = []
            scores = []
            sources = []
            
            for result in search_results:
                chunk_text = result.get('metadata', {}).get('text', '')
                score = result.get('score', 0.0)
                source = result.get('metadata', {}).get('source', 'Unknown')
                
                chunks.append(chunk_text)
                scores.append(score)
                sources.append(source)
            
            # Find the most relevant source based on highest score
            most_relevant_source = None
            if scores and sources:
                # Find the index of the highest score
                max_score_index = scores.index(max(scores))
                most_relevant_source = sources[max_score_index]
            
            return {
                "chunks": chunks,
                "scores": scores,
                "sources": [most_relevant_source] if most_relevant_source else []  # Only the most relevant source
            }
            
        except Exception as e:
            raise RetrievalError(f"Failed to retrieve relevant chunks: {str(e)}", query=query)
    
    def handle_document_ingestion_request(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle document ingestion requests (not implemented for this agent)"""
        raise NotImplementedError("RetrievalAgent does not handle document ingestion requests")
    
    def handle_llm_query_request(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle LLM query requests (not implemented for this agent)"""
        raise NotImplementedError("RetrievalAgent does not handle LLM query requests") 
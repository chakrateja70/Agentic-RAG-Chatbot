from typing import Dict, Any, List
import os
import tempfile
from app.agents.base_agent import BaseAgent
from app.models.mcp import AgentType, MessageType, MCPMessage
from app.utils.document_processor import document_processor
from app.services.embedding_service import embedding_service
from app.db.vector_store import vector_store
from app.core.exceptions import DocumentProcessingError

class IngestionAgent(BaseAgent):
    """Agent responsible for document ingestion and processing"""
    
    def __init__(self):
        super().__init__(AgentType.INGESTION_AGENT)
    
    def _register_default_handlers(self):
        """Register message handlers for this agent"""
        self.register_handler(MessageType.DOCUMENT_INGESTION_REQUEST, self.handle_document_ingestion_request)
    
    def handle_document_ingestion_request(self, message: MCPMessage) -> Dict[str, Any]:
        """
        Handle document ingestion requests
        
        Args:
            message: MCP message containing document ingestion request
            
        Returns:
            Dictionary with processing results
        """
        try:
            payload = message.payload
            file_paths = payload.get("file_paths", [])
            processing_options = payload.get("processing_options", {})
            

            
            # Process documents
            result = self._process_documents(file_paths, processing_options)
            
            # Send response back to coordinator
            response_payload = {
                "success": True,
                "documents_processed": result["documents_processed"],
                "chunks_created": result["chunks_created"],
                "vectors_stored": result["vectors_stored"],
                "files_processed": result["files_processed"],
                "processing_time": result["processing_time"],
                "trace_id": message.trace_id
            }
            
            # Send response to coordinator
            self.send_message(
                receiver=AgentType.COORDINATOR_AGENT,
                message_type=MessageType.DOCUMENT_INGESTION_RESPONSE,
                payload=response_payload,
                trace_id=message.trace_id
            )
            
            return response_payload
            
        except Exception as e:
            error_payload = {
                "success": False,
                "error": str(e),
                "trace_id": message.trace_id
            }
            
            # Send error response
            self.send_message(
                receiver=AgentType.COORDINATOR_AGENT,
                message_type=MessageType.DOCUMENT_INGESTION_RESPONSE,
                payload=error_payload,
                trace_id=message.trace_id
            )
            
            raise DocumentProcessingError(f"Document ingestion failed: {str(e)}")
    
    def _process_documents(self, file_paths: List[str], processing_options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process documents through the complete pipeline
        
        Args:
            file_paths: List of file paths to process
            processing_options: Options for processing
            
        Returns:
            Dictionary with processing results
        """
        import time
        start_time = time.time()
        
        try:
            # Create temporary directory for processing
            with tempfile.TemporaryDirectory() as tmpdirname:
                # Copy files to temporary directory
                temp_file_paths = []
                for file_path in file_paths:
                    if os.path.isfile(file_path):
                        temp_file_path = os.path.join(tmpdirname, os.path.basename(file_path))
                        # Copy file to temp directory
                        with open(file_path, 'rb') as src, open(temp_file_path, 'wb') as dst:
                            dst.write(src.read())
                        temp_file_paths.append(temp_file_path)
                
                if not temp_file_paths:
                    return {
                        "success": False,
                        "message": "No valid files found",
                        "documents_processed": 0,
                        "chunks_created": 0,
                        "vectors_stored": 0,
                        "files_processed": [],
                        "processing_time": time.time() - start_time
                    }
                
                # Step 1: Load documents
                pages = document_processor.load_documents(tmpdirname)
                
                if not pages:
                    return {
                        "success": False,
                        "message": "No valid documents found in uploaded files",
                        "documents_processed": 0,
                        "chunks_created": 0,
                        "vectors_stored": 0,
                        "files_processed": [],
                        "processing_time": time.time() - start_time
                    }
                
                # Step 2: Split documents into chunks
                chunks = document_processor.split_chunks(pages)
                
                if not chunks:
                    return {
                        "success": False,
                        "message": "Failed to create chunks from documents",
                        "documents_processed": len(pages),
                        "chunks_created": 0,
                        "vectors_stored": 0,
                        "files_processed": [],
                        "processing_time": time.time() - start_time
                    }
                
                # Step 3: Create document chunks
                document_chunks = document_processor.create_document_chunks(chunks)
                
                # Step 4: Convert chunks to embeddings
                try:
                    embeddings = embedding_service.create_embeddings(document_chunks)
                except Exception as e:
                    return {
                        "success": False,
                        "message": f"Failed to create embeddings from chunks: {str(e)}",
                        "documents_processed": len(pages),
                        "chunks_created": len(chunks),
                        "vectors_stored": 0,
                        "files_processed": [],
                        "processing_time": time.time() - start_time
                    }
                
                if not embeddings:
                    return {
                        "success": False,
                        "message": "Failed to create embeddings from chunks",
                        "documents_processed": len(pages),
                        "chunks_created": len(chunks),
                        "vectors_stored": 0,
                        "files_processed": [],
                        "processing_time": time.time() - start_time
                    }
                
                # Step 5: Store embeddings in vector store
                try:
                    vector_store.add_embeddings(embeddings)
                except Exception as e:
                    return {
                        "success": False,
                        "message": f"Failed to store embeddings: {str(e)}",
                        "documents_processed": len(pages),
                        "chunks_created": len(chunks),
                        "vectors_stored": 0,
                        "files_processed": [],
                        "processing_time": time.time() - start_time
                    }
                
                processing_time = time.time() - start_time
                
                return {
                    "success": True,
                    "message": "Documents successfully processed and stored in vector database",
                    "documents_processed": len(pages),
                    "chunks_created": len(chunks),
                    "vectors_stored": len(embeddings),
                    "files_processed": [os.path.basename(fp) for fp in file_paths],
                    "processing_time": processing_time
                }
                
        except Exception as e:
            processing_time = time.time() - start_time
            return {
                "success": False,
                "message": f"Error processing files: {str(e)}",
                "documents_processed": 0,
                "chunks_created": 0,
                "vectors_stored": 0,
                "files_processed": [],
                "processing_time": processing_time
            }
    
    def handle_retrieval_request(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle retrieval requests (not implemented for this agent)"""
        raise NotImplementedError("IngestionAgent does not handle retrieval requests")
    
    def handle_llm_query_request(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle LLM query requests (not implemented for this agent)"""
        raise NotImplementedError("IngestionAgent does not handle LLM query requests") 
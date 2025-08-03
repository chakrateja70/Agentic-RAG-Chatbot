import sys
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from typing import List, Dict, Any
import os
import tempfile
import shutil
import logging

from pydantic import BaseModel

# Load environment variables first
from dotenv import load_dotenv
load_dotenv(override=True)

from app.agents.coordinator_agent import CoordinatorAgent
from app.agents.ingestion_agent import IngestionAgent
from app.agents.retrieval_agent import RetrievalAgent
from app.agents.llm_response_agent import LLMResponseAgent
from app.core.status_codes import ResponseStatus
from app.core.exceptions import RAGException


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Agentic RAG Chatbot API",
    description="API for the Agentic RAG Chatbot with Model Context Protocol (MCP)",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for request/response
class QueryRequest(BaseModel):
    query: str


class SystemStatusResponse(BaseModel):
    status: str
    message: str
    data: Dict[str, Any]


# Global agent instances
coordinator_agent = None
ingestion_agent = None
retrieval_agent = None
llm_response_agent = None


@app.on_event("startup")
async def startup_event():
    """Initialize all agents on startup"""
    global coordinator_agent, ingestion_agent, retrieval_agent, llm_response_agent
    
    try:
        logger.info("Starting agent initialization...")
        
        # Initialize all agents
        logger.info("Initializing IngestionAgent...")
        ingestion_agent = IngestionAgent()
        ingestion_agent.start()
        
        logger.info("Initializing RetrievalAgent...")
        retrieval_agent = RetrievalAgent()
        retrieval_agent.start()
        
        logger.info("Initializing LLMResponseAgent...")
        llm_response_agent = LLMResponseAgent()
        llm_response_agent.start()
        
        logger.info("Initializing CoordinatorAgent...")
        coordinator_agent = CoordinatorAgent()
        coordinator_agent.start()
        
        logger.info("All agents started successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize agents: {str(e)}")
        coordinator_agent = None
        ingestion_agent = None
        retrieval_agent = None
        llm_response_agent = None


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up all agents on shutdown"""
    global coordinator_agent, ingestion_agent, retrieval_agent, llm_response_agent
    
    agents = [coordinator_agent, ingestion_agent, retrieval_agent, llm_response_agent]
    
    for agent in agents:
        if agent:
            try:
                agent.stop()
                logger.info(f"Stopped {agent.__class__.__name__}")
            except Exception as e:
                logger.error(f"Error stopping {agent.__class__.__name__}: {str(e)}")


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "Agentic RAG Chatbot API",
        "version": "1.0.0",
        "status": "running"
    }


@app.post("/upload", response_model=Dict[str, Any])
async def upload_documents(
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = None
):
    """
    Upload and process documents
    
    Args:
        files: List of files to upload
        background_tasks: FastAPI background tasks
        
    Returns:
        Upload processing results
    """
    try:
        logger.info(f"Upload request received for {len(files)} files")
        
        if not coordinator_agent:
            logger.error("Coordinator agent not initialized")
            raise HTTPException(status_code=503, detail="Coordinator agent not initialized")
        
        # Validate file types
        allowed_extensions = {'.pdf', '.docx', '.pptx', '.csv', '.txt', '.md', '.markdown'}
        file_paths = []
        
        for file in files:
            logger.info(f"Processing file: {file.filename}")
            file_extension = os.path.splitext(file.filename)[1].lower()
            if file_extension not in allowed_extensions:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Unsupported file type: {file_extension}. Supported types: {allowed_extensions}"
                )
        
        # Save files to temporary directory
        temp_dir = tempfile.mkdtemp()
        logger.info(f"Created temporary directory: {temp_dir}")
        
        try:
            for file in files:
                file_path = os.path.join(temp_dir, file.filename)
                logger.info(f"Saving file to: {file_path}")
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                file_paths.append(file_path)
            
            logger.info(f"All files saved. Processing {len(file_paths)} files...")
            
            # Process documents using coordinator agent
            result = coordinator_agent.process_document_upload(file_paths)
            logger.info(f"Document processing result: {result}")
            
            if result.get("success", False):
                return {
                    "status": ResponseStatus.SUCCESS,
                    "message": "Documents uploaded and processed successfully",
                    "data": {
                        "documents_processed": result.get("documents_processed", 0),
                        "chunks_created": result.get("chunks_created", 0),
                        "vectors_stored": result.get("vectors_stored", 0),
                        "files_processed": result.get("files_processed", []),
                        "processing_time": result.get("processing_time", 0)
                    }
                }
            else:
                error_msg = result.get('message', 'Unknown error')
                logger.error(f"Document processing failed: {error_msg}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Document processing failed: {error_msg}"
                )
                
        finally:
            # Clean up temporary directory
            logger.info(f"Cleaning up temporary directory: {temp_dir}")
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed with exception: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/query", response_model=Dict[str, Any])
async def query_documents(request: QueryRequest):
    """
    Query the document knowledge base
    
    Args:
        request: Query request with question and type
        
    Returns:
        Query response with answer and sources
    """
    try:
        logger.info(f"Query request received: {request.query[:50]}...")
        
        if not coordinator_agent:
            logger.error("Coordinator agent not initialized")
            raise HTTPException(status_code=503, detail="Coordinator agent not initialized")
        
        # Process query using coordinator agent
        result = coordinator_agent.process_query(
            query=request.query
        )
        
        logger.info(f"Query processing result: {result.get('success', False)}")
        
        if result.get("success", False):
            return {
                "status": ResponseStatus.SUCCESS,
                "message": "Query processed successfully",
                "data": {
                    "query": result.get("query", ""),
                    "answer": result.get("answer", {}),
                    "sources": result.get("sources", []),
                    "processing_time": result.get("processing_time", 0),
                    "source_files": result.get("sources", [])  # Add explicit source files field
                }
            }
        else:
            error_msg = result.get('error', 'Unknown error')
            logger.error(f"Query processing failed: {error_msg}")
            raise HTTPException(
                status_code=500,
                detail=f"Query processing failed: {error_msg}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query failed with exception: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@app.get("/status", response_model=SystemStatusResponse)
async def get_system_status():
    """
    Get system status and health information
    
    Returns:
        System status information
    """
    try:
        if not coordinator_agent:
            return SystemStatusResponse(
                status=ResponseStatus.ERROR,
                message="Coordinator agent not initialized",
                data={"error": "Agent not available"}
            )
        
        status = coordinator_agent.get_system_status()
        
        return SystemStatusResponse(
            status=ResponseStatus.SUCCESS,
            message="System status retrieved successfully",
            data=status
        )
        
    except Exception as e:
        logger.error(f"Failed to get system status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get system status: {str(e)}")


@app.get("/health", response_model=Dict[str, Any])
async def health_check():
    """
    Health check endpoint
    
    Returns:
        Health status
    """
    all_agents_running = all([
        coordinator_agent,
        ingestion_agent,
        retrieval_agent,
        llm_response_agent
    ])
    
    agent_status = "healthy" if all_agents_running else "unhealthy"
    
    return {
        "status": agent_status,
        "message": f"Agentic RAG Chatbot is {agent_status}",
        "agents": {
            "coordinator_agent": "running" if coordinator_agent else "not running",
            "ingestion_agent": "running" if ingestion_agent else "not running",
            "retrieval_agent": "running" if retrieval_agent else "not running",
            "llm_response_agent": "running" if llm_response_agent else "not running"
        }
    }


# Error handlers
@app.exception_handler(RAGException)
async def rag_exception_handler(request, exc):
    """Handle RAG-specific exceptions"""
    logger.error(f"RAG Exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": ResponseStatus.ERROR,
            "message": str(exc),
            "error_code": exc.__class__.__name__,
            "trace_id": getattr(exc, 'trace_id', None)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"General Exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": ResponseStatus.ERROR,
            "message": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "details": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000) 
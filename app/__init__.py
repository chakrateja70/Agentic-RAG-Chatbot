"""
Agentic RAG Chatbot with Model Context Protocol (MCP)

This package implements an agent-based Retrieval-Augmented Generation (RAG) system
that uses Model Context Protocol (MCP) for communication between agents.

Architecture:
- IngestionAgent: Parses & preprocesses documents
- RetrievalAgent: Handles embedding + semantic retrieval
- LLMResponseAgent: Forms final LLM query using retrieved context
- CoordinatorAgent: Orchestrates the workflow

Supported document formats:
- PDF, DOCX, PPTX, CSV, TXT, Markdown
"""

__version__ = "1.0.0"
__author__ = "Agentic RAG Team"
__description__ = "Agentic RAG Chatbot with Model Context Protocol (MCP)" 
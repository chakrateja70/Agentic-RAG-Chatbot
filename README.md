# 🤖 Agentic RAG Chatbot with Model Context Protocol (MCP)

A sophisticated agent-based Retrieval-Augmented Generation (RAG) chatbot that uses Model Context Protocol (MCP) for communication between agents. This system supports multiple document formats and provides an intelligent question-answering interface.

## 🏗️ Architecture Overview

The system implements a multi-agent architecture with the following components:

### 🤖 Agents
- **IngestionAgent**: Parses & preprocesses documents (PDF, DOCX, PPTX, CSV, TXT, Markdown)
- **RetrievalAgent**: Handles embedding generation and semantic retrieval
- **LLMResponseAgent**: Forms final LLM queries using retrieved context
- **CoordinatorAgent**: Orchestrates the workflow between all agents

### 📡 Model Context Protocol (MCP)
All agents communicate using structured MCP messages:
```json
{
  "sender": "RetrievalAgent",
  "receiver": "LLMResponseAgent", 
  "type": "RETRIEVAL_RESPONSE",
  "trace_id": "abc-123",
  "payload": {
    "retrieved_chunks": ["...", "..."],
    "query": "What are the KPIs?"
  }
}
```

### 🔄 System Flow
1. **Document Upload** → CoordinatorAgent → IngestionAgent
2. **Query Processing** → CoordinatorAgent → RetrievalAgent → LLMResponseAgent
3. **Response Generation** → LLMResponseAgent → CoordinatorAgent → UI

## 📁 Project Structure

```
Agentic-RAG-Chatbot/
├── app/
│   ├── api/                 # FastAPI endpoints
│   │   └── main.py
│   ├── agents/              # Agent implementations
│   │   ├── base_agent.py
│   │   ├── coordinator_agent.py
│   │   ├── ingestion_agent.py
│   │   ├── retrieval_agent.py
│   │   └── llm_response_agent.py
│   ├── core/                # Core functionality
│   │   ├── exceptions.py
│   │   ├── message_broker.py
│   │   └── status_codes.py
│   ├── db/                  # Database connections
│   │   └── vector_store.py
│   ├── models/              # Pydantic models
│   │   └── mcp.py
│   ├── services/            # Business logic services
│   │   ├── embedding_service.py
│   │   └── llm_service.py
│   ├── ui/                  # Streamlit UI
│   │   └── main.py
│   └── utils/               # Utility functions
│       └── document_processor.py
├── run_api.py              # API server startup script
├── run_ui.py               # UI startup script
├── requirements.txt        # Python dependencies
├── setup.py                # Installation script
├── architecture.pptx       # Architecture presentation
└── README.md              # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Groq API Key (for Llama LLM)
- Google API Key (for embeddings)
- Pinecone API Key (for vector database)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/chakrateja70/Agentic-RAG-Chatbot.git
   cd Agentic-RAG-Chatbot
   ```

2. **Create and activate virtual environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Create .env file
   echo "GROQ_API_KEY=your_groq_api_key_here" > .env
   echo "GOOGLE_API_KEY=your_google_api_key_here" >> .env
   echo "PINECONE_API_KEY=your_pinecone_api_key_here" >> .env
   ```

5. **Start the API server**
   ```bash
   python run_api.py
   ```
   The API will be available at: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

6. **Start the UI (in a new terminal)**
   ```bash
   # Make sure to activate the virtual environment in the new terminal
   # On Windows: venv\Scripts\activate
   # On macOS/Linux: source venv/bin/activate
   
   python run_ui.py
   ```
   The UI will be available at: http://localhost:8501

## 📚 Supported Document Formats

- **PDF** (.pdf) - Research papers, reports, manuals
- **DOCX** (.docx) - Word documents
- **PPTX** (.pptx) - PowerPoint presentations
- **CSV** (.csv) - Data tables and spreadsheets
- **TXT** (.txt) - Plain text files
- **Markdown** (.md, .markdown) - Documentation and notes

## 🎯 Features

### Document Processing
- Multi-format document parsing
- Intelligent text chunking with overlap
- Vector embedding generation
- Pinecone vector database storage

### Query Types
- **Answer**: Direct question answering with source citations
- **Challenge**: Generate comprehension questions
- **Summary**: Create concise document summaries
- **Evaluate**: Assess user answers to questions

### Agent Communication
- Real-time MCP message passing
- Traceable request/response flows
- Error handling and recovery
- System status monitoring

### User Interface
- Modern Streamlit-based UI
- Real-time document upload
- Interactive chat interface
- Query history and source tracking
- System health monitoring

## 🔧 API Endpoints

### Document Upload
```http
POST /upload
Content-Type: multipart/form-data

files: [document files]
```

### Query Documents
```http
POST /query
Content-Type: application/json

{
  "query": "What are the main KPIs?",
  "query_type": "answer",
  "additional_params": {}
}
```

### System Status
```http
GET /status
```

### Health Check
```http
GET /health
```

## 🧠 MCP Message Examples

### Document Ingestion Request
```json
{
  "sender": "CoordinatorAgent",
  "receiver": "IngestionAgent",
  "type": "DOCUMENT_INGESTION_REQUEST",
  "trace_id": "upload-123",
  "payload": {
    "file_paths": ["/path/to/document.pdf"],
    "processing_options": {}
  }
}
```

### Retrieval Response
```json
{
  "sender": "RetrievalAgent",
  "receiver": "CoordinatorAgent",
  "type": "RETRIEVAL_RESPONSE",
  "trace_id": "query-456",
  "payload": {
    "retrieved_chunks": ["Revenue increased by 15%...", "Q1 performance..."],
    "sources": ["sales_report.pdf", "quarterly_metrics.csv"],
    "scores": [0.95, 0.87]
  }
}
```

## 🛠️ Development

### Code Structure
- **Agents**: Inherit from `BaseAgent` and implement specific message handlers
- **Services**: Business logic for embeddings, LLM interactions, etc.
- **Models**: Pydantic models for MCP message structures
- **Core**: Exception handling, message broker, status codes

## 📊 Performance

- **Document Processing**: ~2-5 seconds per document (depending on size)
- **Query Response**: ~1-3 seconds (including retrieval and LLM generation)
- **Concurrent Requests**: Supports multiple simultaneous users
- **Vector Search**: Sub-second retrieval from Pinecone

## 🔒 Security

- API key management through environment variables
- Input validation and sanitization
- Error handling without exposing sensitive information
## 🚧 Troubleshooting

### Common Issues

1. **API Connection Failed**
   - Ensure API server is running: `python run_api.py`
   - Check port 8000 is available

2. **Document Upload Fails**
   - Verify file format is supported
   - Check file size (recommended < 50MB)
   - Ensure API keys are properly configured

3. **Query Returns No Results**
   - Verify documents were successfully uploaded
   - Check vector database connection
   - Review query specificity

4. **LLM Errors**
   - Verify Groq API key is valid
   - Check API quota limits
   - Review query content for inappropriate content


## 🎯 Challenges Faced & Improvements

### Challenges Encountered

1. **Agent Communication Complexity**: Implementing the Model Context Protocol (MCP) for inter-agent communication was initially complex. The challenge was ensuring reliable message passing while maintaining loose coupling between agents.

2. **Document Processing Performance**: Processing large documents (especially PDFs with complex layouts) was slow. Implementing efficient chunking strategies and parallel processing helped improve performance.

3. **Vector Database Integration**: Setting up Pinecone with proper indexing and similarity search required careful tuning of embedding dimensions and metadata handling.

4. **Error Handling Across Agents**: Coordinating error handling across multiple agents while maintaining system stability was challenging. Implementing proper exception propagation and recovery mechanisms was crucial.

### Suggested Improvements

1. **Advanced Document Processing**: Add support for more document formats (Excel, images with OCR) and implement better table extraction from PDFs.

2. **User Authentication**: Add user authentication and document ownership to support multi-tenant usage.

3. **Advanced Query Types**: Implement more sophisticated query types like "compare documents", "timeline analysis", and "trend detection".

4. **Monitoring & Analytics**: Add comprehensive logging, metrics collection, and performance monitoring dashboards.


## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- LangChain for document processing and LLM integration
- Pinecone for vector database services
- Groq for Llama LLM capabilities
- Google for embedding services
- Streamlit for the user interface
- FastAPI for the REST API

---

**Note**: This project is actively being developed. For the latest updates and features, please check the repository regularly.
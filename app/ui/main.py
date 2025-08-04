import streamlit as st
import requests
import streamlit.components.v1 as components
import os
from typing import Dict, Any, List
import time


# Configuration
API_BASE_URL = "http://localhost:8000"
SUPPORTED_FORMATS = ["pdf", "docx", "pptx", "csv", "txt", "md", "markdown"]


def init_session_state():
    """Initialize session state variables"""
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = []
    if 'system_status' not in st.session_state:
        st.session_state.system_status = None
    if 'show_architecture' not in st.session_state:
        st.session_state.show_architecture = False


def check_api_health():
    """Check if the API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def upload_documents(files: List[Any]) -> Dict[str, Any]:
    """Upload documents to the API"""
    try:
        files_data = []
        for file in files:
            files_data.append(('files', (file.name, file.getvalue(), file.type)))
        
        response = requests.post(f"{API_BASE_URL}/upload", files=files_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Upload failed: {str(e)}")
        return None


def query_documents(query: str) -> Dict[str, Any]:
    """Query the document knowledge base"""
    try:
        payload = {
            "query": query
        }
        
        response = requests.post(f"{API_BASE_URL}/query", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Query failed: {str(e)}")
        return None


def get_system_status() -> Dict[str, Any]:
    """Get system status from the API"""
    try:
        response = requests.get(f"{API_BASE_URL}/status")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to get system status: {str(e)}")
        return None


def load_mermaid_diagram() -> str:
    """Load the document_upload_architecture.mermaid file content"""
    try:
        # Get the path to document_upload_architecture.mermaid in the ui folder
        current_dir = os.path.dirname(os.path.abspath(__file__))
        mermaid_path = os.path.join(current_dir, "document_upload_architecture.mermaid")
        
        if os.path.exists(mermaid_path):
            with open(mermaid_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            return None
    except Exception as e:
        st.error(f"Failed to load mermaid diagram file: {str(e)}")
        return None


def load_query_mermaid_diagram() -> str:
    """Load the document_query_architecture.mermaid file content"""
    try:
        # Get the path to document_query_architecture.mermaid in the ui folder
        current_dir = os.path.dirname(os.path.abspath(__file__))
        mermaid_path = os.path.join(current_dir, "document_query_architecture.mermaid")
        
        if os.path.exists(mermaid_path):
            with open(mermaid_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            return None
    except Exception as e:
        st.error(f"Failed to load query mermaid diagram file: {str(e)}")
        return None


def show_architecture():
    """Display the architecture using Mermaid diagram"""
    upload_mermaid_content = load_mermaid_diagram()
    query_mermaid_content = load_query_mermaid_diagram()
    
    if upload_mermaid_content and query_mermaid_content:
        # Display the Mermaid diagram using Streamlit's native support
        st.subheader("📊 System Architecture Overview")
        st.write("**Complete workflow diagrams for document upload and query processing:**")
        
        # Create HTML content with Mermaid.js to render diagrams
        mermaid_html_upload = f"""
        <div style="background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; margin: 20px 0;">
            <h4 style="color: #333; margin-bottom: 15px;">Document Upload Flow</h4>
            <div class="mermaid" style="background-color: white;">
                {upload_mermaid_content}
            </div>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
        <script>
            mermaid.initialize({{
                startOnLoad: true, 
                theme: 'base',
                themeVariables: {{
                    primaryColor: '#ffffff',
                    primaryTextColor: '#333333',
                    primaryBorderColor: '#cccccc',
                    lineColor: '#666666',
                    background: '#ffffff',
                    mainBkg: '#ffffff',
                    secondBkg: '#f8f9fa',
                    tertiaryColor: '#ffffff'
                }}
            }});
        </script>
        """
        
        mermaid_html_query = f"""
        <div style="background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; margin: 20px 0;">
            <h4 style="color: #333; margin-bottom: 15px;">Query Processing Flow</h4>
            <div class="mermaid" style="background-color: white;">
                {query_mermaid_content}
            </div>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
        <script>
            mermaid.initialize({{
                startOnLoad: true, 
                theme: 'base',
                themeVariables: {{
                    primaryColor: '#ffffff',
                    primaryTextColor: '#333333',
                    primaryBorderColor: '#cccccc',
                    lineColor: '#666666',
                    background: '#ffffff',
                    mainBkg: '#ffffff',
                    secondBkg: '#f8f9fa',
                    tertiaryColor: '#ffffff'
                }}
            }});
        </script>
        """
        
        # Create two columns for the diagrams
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Document Upload Flow:**")
            # Display the Mermaid diagram using HTML components
            components.html(mermaid_html_upload, height=600, scrolling=True)
        
        with col2:
            st.write("**Query Processing Flow:**")
            # Display the query Mermaid diagram using HTML components
            components.html(mermaid_html_query, height=600, scrolling=True)
        
        # Add workflow explanations
        st.markdown("---")
        st.subheader("🔍 Workflow Details")
        
        # Upload workflow explanation
        with st.expander("📤 Document Upload Workflow", expanded=False):
            st.markdown("""
            **Step-by-step process:**
            1. **Client Upload**: User selects and uploads documents via Streamlit UI
            2. **API Validation**: FastAPI validates file types and creates temporary storage
            3. **Coordinator Agent**: Orchestrates the entire upload process with trace ID tracking
            4. **Ingestion Agent**: Handles document processing pipeline:
               - Document loading (PDF, DOCX, PPTX, CSV, TXT, Markdown)
               - Text chunking with overlap (500 chars, 100 overlap)
               - Parallel processing for performance
            5. **Document Processor**: Extracts and cleans text content
            6. **Embedding Service**: Converts text chunks to vector embeddings (Google AI)
            7. **Vector Store**: Stores embeddings in Pinecone with metadata
            8. **Response Chain**: Success/failure status propagated back to client
            """)
        
        # Query workflow explanation
        with st.expander("🔍 Query Processing Workflow", expanded=False):
            st.markdown("""
            **Step-by-step process:**
            1. **Client Query**: User submits question via Streamlit chat interface
            2. **API Processing**: FastAPI receives and validates query request
            3. **Coordinator Agent**: Manages two-stage process:
               - **Stage 1**: Document retrieval with separate trace ID
               - **Stage 2**: LLM response generation with separate trace ID
            4. **Retrieval Agent**: 
               - Converts query to embeddings
               - Performs similarity search in Pinecone (top-k=8)
               - Returns most relevant chunks and sources
            5. **LLM Response Agent**:
               - Combines query + retrieved context
               - Sends structured prompt to Groq Llama model
               - Generates contextual answer (max 300 tokens)
            6. **Response Assembly**: Coordinator combines results with metadata
            7. **Client Response**: Structured answer with sources and processing time
            """)
        
        # Technical details
        with st.expander("⚙️ Technical Implementation", expanded=False):
            st.markdown("""
            **Key Technologies:**
            - **Framework**: FastAPI + Streamlit
            - **Architecture**: Agent-based with Model Context Protocol (MCP)
            - **Vector Database**: Pinecone (cosine similarity)
            - **Embeddings**: Google Generative AI (models/embedding-001)
            - **LLM**: Groq Llama (meta-llama/llama-4-scout-17b-16e-instruct)
            - **Processing**: Parallel document processing with ThreadPoolExecutor
            - **Monitoring**: End-to-end trace ID tracking
            
            **Performance Features:**
            - Parallel document loading and chunking
            - Lazy initialization of services
            - Background task support
            - Comprehensive error handling
            - Request timeout management (5min upload, 30s query)
            """)
        
        # Alternative: Show code view for users who want to see the raw Mermaid code
        with st.expander("📋 View Mermaid Code", expanded=False):
            col1_code, col2_code = st.columns(2)
            with col1_code:
                st.write("**Upload Flow Code:**")
                st.code(upload_mermaid_content, language="mermaid")
            with col2_code:
                st.write("**Query Flow Code:**")
                st.code(query_mermaid_content, language="mermaid")
    else:
        st.error("❌ Mermaid diagram files not found. Please ensure both diagram files exist in the UI folder.")
        st.info("Expected files:")
        st.write("• app/ui/document_upload_architecture.mermaid")
        st.write("• app/ui/document_query_architecture.mermaid")


def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="Agentic RAG Chatbot",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    init_session_state()
    
    # Sidebar
    with st.sidebar:
        st.title("🤖 Agentic RAG Chatbot")
        st.markdown("""
        **Agentic RAG with Model Context Protocol (MCP)**
        
        This system uses an agent-based architecture with:
        - **IngestionAgent**: Parses & preprocesses documents
        - **RetrievalAgent**: Handles embedding + semantic retrieval  
        - **LLMResponseAgent**: Forms final LLM query using retrieved context
        - **CoordinatorAgent**: Orchestrates the workflow
        
        **Supported Formats:**
        - PDF, DOCX, PPTX, CSV, TXT, Markdown
        """)
        st.markdown("---")
        
        # Architecture/Workflow Button
        st.subheader("🏗️ System Overview")
        if st.button("📊 View Architecture & Workflow", type="secondary"):
            st.session_state.show_architecture = not st.session_state.show_architecture
        
        st.markdown("---")
        
        # System Status
        st.subheader("🔧 System Status")
        if st.button("Check Status"):
            st.session_state.system_status = get_system_status()
        
        if st.session_state.system_status:
            status_data = st.session_state.system_status.get("data", {})
            agent_status = status_data.get("agent_status", {})
            
            if agent_status.get("active_agents"):
                st.success("✅ All agents active")
                for agent in agent_status["active_agents"]:
                    st.write(f"• {agent}")
            else:
                st.error("❌ No agents active")
            
            st.write(f"**Total Messages:** {agent_status.get('total_messages', 0)}")
            st.write(f"**Pending Requests:** {status_data.get('pending_requests', 0)}")
        
        # API Health Check
        if check_api_health():
            st.success("✅ API Connected")
        else:
            st.error("❌ API Not Available")
            st.info("Please start the API server: `uvicorn app.api.main:app --reload`")
    
    # Main content
    st.title("🤖 Agentic RAG Chatbot")
    st.markdown("Upload documents and ask questions using our agent-based RAG system with Model Context Protocol (MCP)")
    
    # Check if architecture should be displayed
    if st.session_state.show_architecture:
        st.subheader("🏗️ System Architecture & Workflow")
        
        # Add close button
        col1, col2 = st.columns([6, 1])
        with col2:
            if st.button("❌ Close", key="close_architecture"):
                st.session_state.show_architecture = False
                st.rerun()
        
        with col1:
            st.markdown("**Complete system architecture with technical implementation details**")
        
        # Display the architecture
        show_architecture()
        
        st.markdown("---")
        
        # Add a button to return to main interface
        if st.button("🔙 Back to Main Interface", type="primary"):
            st.session_state.show_architecture = False
            st.rerun()
            
        return  # Don't show the rest of the interface when architecture is displayed
    
    # Navigation buttons
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        if st.button("🏗️ View Architecture", type="secondary"):
            st.session_state.show_architecture = True
            st.rerun()
    with col2:
        if st.button("💬 Chat Interface", type="primary", disabled=True):
            pass  # Already on main interface
    
    st.markdown("---")
    
    # File Upload Section
    st.subheader("📁 Upload Documents")
    
    uploaded_files = st.file_uploader(
        "Choose files to upload",
        type=SUPPORTED_FORMATS,
        accept_multiple_files=True,
        help=f"Supported formats: {', '.join(SUPPORTED_FORMATS).upper()}"
    )
    
    if uploaded_files:
        with st.expander("View selected files"):
            for file in uploaded_files:
                st.write(f"• {file.name} ({file.size/1024:.1f} KB)")
        
        if st.button("🚀 Process and Upload", type="primary"):
            with st.spinner("Processing documents..."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Upload files
                status_text.text("📤 Uploading files...")
                progress_bar.progress(25)
                
                result = upload_documents(uploaded_files)
                
                if result and result.get("status") == "success":
                    progress_bar.progress(100)
                    status_text.text("✅ Processing complete!")
                    
                    data = result.get("data", {})
                    st.success(f"✅ Successfully processed {data.get('documents_processed', 0)} documents!")
                    st.write(f"• Chunks created: {data.get('chunks_created', 0)}")
                    st.write(f"• Vectors stored: {data.get('vectors_stored', 0)}")
                    st.write(f"• Processing time: {data.get('processing_time', 0):.2f}s")
                    
                    # Update session state
                    st.session_state.uploaded_files.extend([f.name for f in uploaded_files])
                else:
                    st.error("❌ Upload failed")
                
                progress_bar.empty()
                status_text.empty()
    
    # Chat Interface
    st.subheader("💬 Chat Interface")
    
    # Query Input
    query = st.text_input("Ask a question about your documents:", placeholder="What are the main points discussed?")
    
    # Send Query Button
    if st.button("🔍 Send Query", type="primary") and query:
        with st.spinner("Processing query..."):
            result = query_documents(query)
            
            if result and result.get("status") == "success":
                data = result.get("data", {})
                
                # Display response
                st.subheader("📝 Response")
                
                answer = data.get("answer", {})
                st.write("**Answer:**")
                st.write(answer.get("answer", "No answer generated"))
                
                if answer.get("has_justification"):
                    st.success("✅ Answer includes document justification")
                else:
                    st.warning("⚠️ Answer lacks document justification")
                
                # # Display sources
                # sources = data.get("sources", [])
                # if sources:
                #     st.subheader("📚 Sources")
                #     for source in sources:
                #         st.write(f"• {source}")
                
                # Display processing time
                processing_time = data.get("processing_time", 0)
                st.info(f"⏱️ Processing time: {processing_time:.2f}s")
                
                # Add to chat history
                st.session_state.chat_history.append({
                    "query": query,
                    "response": data,
                    "timestamp": time.time()
                })
            else:
                st.error("❌ Query failed")
    
    # Chat History
    if st.session_state.chat_history:
        st.subheader("📜 Chat History")
        
        # Show only the 4 most recent chats
        recent_chats = st.session_state.chat_history[-4:]  # Get last 4 chats
        
        for i, chat in enumerate(reversed(recent_chats)):
            chat_index = len(st.session_state.chat_history) - (len(recent_chats) - i) + 1
            with st.expander(f"Query {chat_index}: {chat['query'][:50]}..."):
                st.write(f"**Query:** {chat['query']}")
                
                response = chat.get("response", {})
                answer = response.get("answer", {})
                st.write(f"**Answer:** {answer.get('answer', 'No answer')}")
                
                # sources = response.get("sources", [])
                # if sources:
                #     st.write("**Sources:**")
                #     for source in sources:
                #         st.write(f"• {source}")
        
        # Show total count if there are more than 4 chats
        if len(st.session_state.chat_history) > 4:
            st.info(f"Showing 4 most recent chats out of {len(st.session_state.chat_history)} total chats")
        
        if st.button("🗑️ Clear History"):
            st.session_state.chat_history = []
            st.rerun()


if __name__ == "__main__":
    main() 
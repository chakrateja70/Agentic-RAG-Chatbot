import streamlit as st
import requests

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
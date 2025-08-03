#!/usr/bin/env python3
"""
Script to run the Agentic RAG Chatbot Streamlit UI
"""

import subprocess
import sys
import os

def main():
    print("🎨 Starting Agentic RAG Chatbot Streamlit UI...")
    print("🌐 UI will be available at: http://localhost:8501")
    print("⚠️  Make sure the API server is running first: python run_api.py")
    
    # Add the app directory to the Python path
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    # Run Streamlit
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", "app/ui/main.py",
        "--server.port", "8501",
        "--server.address", "127.0.0.1"
    ])

if __name__ == "__main__":
    main() 
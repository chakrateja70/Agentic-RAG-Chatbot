#!/usr/bin/env python3
"""
Setup script for Smart Research Assistant - Agentic RAG Chatbot
"""

import os
import subprocess
import sys
import shutil

def create_venv():
    """Create a virtual environment if it doesn't exist"""
    if not os.path.exists("venv"):
        print("Creating virtual environment in ./venv ...")
        subprocess.check_call([sys.executable, "-m", "venv", "venv"])
        print("Virtual environment created.")
    else:
        print("Virtual environment already exists.")

def get_venv_python():
    """Get the path to the Python executable in the venv"""
    if os.name == "nt":
        return os.path.join("venv", "Scripts", "python.exe")
    else:
        return os.path.join("venv", "bin", "python")

def install_requirements():
    """Install required packages using venv Python"""
    print("Installing required packages in virtual environment...")
    venv_python = get_venv_python()
    try:
        # Upgrade pip first
        subprocess.check_call([venv_python, "-m", "pip", "install", "--upgrade", "pip"])
        # Install requirements
        subprocess.check_call([venv_python, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Requirements installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install requirements: {e}")
        return False
    return True

def create_env_example():
    """Create .env.example file if it doesn't exist"""
    if not os.path.exists(".env.example"):
        env_content = """# Smart Research Assistant - Environment Variables
# Copy this file to .env and add your actual API keys

# Groq API Key for LLM (Llama model)
# Get your key from: https://console.groq.com/
GROQ_API_KEY=your_groq_api_key_here

# Google AI API Key for embeddings
# Get your key from: https://makersuite.google.com/app/apikey
GOOGLE_API_KEY=your_google_api_key_here

# Pinecone API Key for vector database
# Get your key from: https://app.pinecone.io/
PINECONE_API_KEY=your_pinecone_api_key_here

# Optional: Pinecone Environment (usually 'gcp-starter' for free tier)
PINECONE_ENVIRONMENT=gcp-starter

# Optional: Logging level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Optional: API server settings
API_HOST=127.0.0.1
API_PORT=8000

# Optional: UI server settings
UI_HOST=127.0.0.1
UI_PORT=8501
"""
        with open(".env.example", "w") as f:
            f.write(env_content)
        print(".env.example file created.")

def check_env_file():
    """Check if .env file exists and has required keys"""
    if not os.path.exists(".env"):
        print(".env file not found.")
        print("Please create .env file with your API keys:")
        print("   - GROQ_API_KEY (from https://console.groq.com/)")
        print("   - GOOGLE_API_KEY (from https://makersuite.google.com/app/apikey)")
        print("   - PINECONE_API_KEY (from https://app.pinecone.io/)")
        print("   - PINECONE_ENVIRONMENT (usually 'gcp-starter')")
        return False
    else:
        print(".env file found.")
        # Check if required keys are present
        with open(".env", "r") as f:
            content = f.read()
            required_keys = ["GROQ_API_KEY", "GOOGLE_API_KEY", "PINECONE_API_KEY"]
            missing_keys = [key for key in required_keys if key not in content or f"{key}=" in content and "your_" in content]
            
            if missing_keys:
                print(f"Warning: Missing or incomplete API keys: {', '.join(missing_keys)}")
                return False
            else:
                print("All required API keys appear to be configured.")
                return True

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required.")
        print(f"Current version: {sys.version}")
        return False
    else:
        print(f"Python version check passed: {sys.version}")
        return True

def is_venv_active():
    """Check if the script is running inside the venv"""
    return (
        hasattr(sys, 'real_prefix') or
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) or
        os.environ.get('VIRTUAL_ENV')
    )

def test_imports():
    """Test if key packages can be imported"""
    print("Testing package imports...")
    venv_python = get_venv_python()
    try:
        # Test key imports
        test_script = """
import fastapi
import streamlit
import langchain
import pinecone
import groq
import google.generativeai
print("All key packages imported successfully!")
"""
        subprocess.check_call([venv_python, "-c", test_script])
        return True
    except subprocess.CalledProcessError:
        print("Warning: Some packages may not be properly installed.")
        return False

def main():
    print("🤖 Setting up Smart Research Assistant...")
    print("=" * 60)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create virtual environment if needed
    create_venv()

    # Check if running inside the venv
    if not is_venv_active():
        print("\n⚠️  Virtual environment is not active.")
        print("Please activate the virtual environment before continuing:")
        if os.name == "nt":
            print("   venv\\Scripts\\activate")
        else:
            print("   source venv/bin/activate")
        print("\nAfter activation, re-run this setup script to install requirements.")
        sys.exit(1)
    else:
        print("✅ Virtual environment is active.")

    # Create .env.example if it doesn't exist
    create_env_example()

    # Install requirements in venv
    if not install_requirements():
        sys.exit(1)
    
    # Test package imports
    test_imports()
    
    # Check environment file
    env_configured = check_env_file()
    
    print("\n" + "=" * 60)
    if env_configured:
        print("🎉 Setup complete! Your Smart Research Assistant is ready to use.")
        print("\n🚀 To start the application:")
        print("   1. Start the API server:")
        print("      python run_api.py")
        print("   2. In a new terminal, start the UI:")
        print("      python run_ui.py")
        print("\n📖 Access points:")
        print("   - Web UI: http://localhost:8501")
        print("   - API Docs: http://localhost:8000/docs")
        print("   - Health Check: http://localhost:8000/health")
    else:
        print("⚠️  Setup incomplete. Please configure your .env file first.")
        print("\n📋 Steps to complete setup:")
        print("   1. Copy .env.example to .env:")
        print("      cp .env.example .env")
        print("   2. Edit .env and add your API keys:")
        print("      - GROQ_API_KEY (from https://console.groq.com/)")
        print("      - GOOGLE_API_KEY (from https://makersuite.google.com/app/apikey)")
        print("      - PINECONE_API_KEY (from https://app.pinecone.io/)")
        print("      - PINECONE_ENVIRONMENT (usually 'gcp-starter')")
        print("   3. Re-run this setup script to verify configuration")
        print("   4. Start the application:")
        print("      python run_api.py  # API server")
        print("      python run_ui.py   # Web UI")

if __name__ == "__main__":
    main()

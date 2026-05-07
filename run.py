#!/usr/bin/env python3
"""
Quick start script for Customer Support Escalation Assistant
Cross-platform Python launcher
"""
import os
import sys
import subprocess
from pathlib import Path


def check_dependencies():
    """Check if dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import pydantic
        import anthropic
        return True
    except ImportError:
        return False


def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    requirements_file = Path(__file__).parent / "requirements.txt"
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "-q", "-r", str(requirements_file)
    ])


def check_api_key():
    """Check if API key is set"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("\n" + "="*60)
        print("WARNING: ANTHROPIC_API_KEY not set")
        print("="*60)
        print("The system will run in MOCK mode (no real LLM calls)")
        print("To use real LLM, set your API key:")
        print("  - On Mac/Linux: export ANTHROPIC_API_KEY='your-key-here'")
        print("  - On Windows: set ANTHROPIC_API_KEY=your-key-here")
        print("="*60 + "\n")


def start_server():
    """Start the FastAPI server"""
    print("\n" + "="*60)
    print("Customer Support Escalation Assistant")
    print("="*60)
    print("\nStarting server at http://localhost:8000")
    print("Press Ctrl+C to stop\n")

    # Change to backend/src directory
    backend_src = Path(__file__).parent / "backend" / "src"
    os.chdir(backend_src)

    # Import and run
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)


def main():
    """Main entry point"""
    # Check and install dependencies
    if not check_dependencies():
        print("Dependencies not found. Installing...")
        install_dependencies()
    else:
        print("Dependencies already installed.")

    # Check API key
    check_api_key()

    # Start server
    try:
        start_server()
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
        sys.exit(0)


if __name__ == "__main__":
    main()

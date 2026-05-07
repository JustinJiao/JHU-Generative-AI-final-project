#!/bin/bash

# Quick start script for Customer Support Escalation Assistant

echo "=================================="
echo "Customer Support Escalation Assistant"
echo "=================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "Installing dependencies..."
    source venv/bin/activate
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
else
    # Activate virtual environment
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Check if API key is set
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo ""
    echo "⚠️  WARNING: ANTHROPIC_API_KEY not set"
    echo "The system will run in MOCK mode (no real LLM calls)"
    echo "To use real LLM, set your API key:"
    echo "  export ANTHROPIC_API_KEY='your-key-here'"
    echo ""
fi

# Initialize demo data if database doesn't exist or is empty
if [ ! -f "escalation.db" ] || [ ! -s "escalation.db" ]; then
    echo "📊 Initializing demo data..."
    python3 init_demo_data.py
    echo ""
fi

# Start the server
echo "🚀 Starting server at http://localhost:8000"
echo "Press Ctrl+C to stop"
echo ""
cd backend/src && python3 app.py

#!/bin/bash

# Cleanup script: Stop all Python processes and start server

echo "=========================================="
echo "Customer Support Escalation System"
echo "=========================================="
echo ""

# 1. Clean up background processes
echo "Step 1: Cleaning background processes..."
pkill -9 python 2>/dev/null
pkill -9 uvicorn 2>/dev/null
sleep 2

# 2. Clean up port
echo "Step 2: Releasing port 8000..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
sleep 1

# 3. Check port status
if lsof -i:8000 >/dev/null 2>&1; then
    echo "Error: Port 8000 still in use!"
    echo "   Please manually run: lsof -i:8000"
    exit 1
fi

echo "Port 8000 released"
echo ""

# 4. Get script directory and navigate to project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 5. Create and activate virtual environment if needed
echo "Step 3: Setting up environment..."
if [ ! -d "venv" ]; then
    echo "   Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "   Installing dependencies..."
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
else
    echo "   Activating virtual environment..."
    source venv/bin/activate
fi

# 6. Initialize demo data if needed
if [ ! -f "escalation.db" ] || [ ! -s "escalation.db" ]; then
    echo "Step 4: Initializing demo data..."
    python3 init_demo_data.py
    echo ""
fi

# 7. Start server
echo "Step 5: Starting server..."
echo ""
echo "=========================================="
echo "Server starting at: http://localhost:8000"
echo ""
echo "Available pages:"
echo "  • http://localhost:8000/static/demo.html  (Interactive Demo)"
echo "  • http://localhost:8000/static/monitor.html  (Real-time Monitor)"
echo "  • http://localhost:8000  (Batch Analysis)"
echo ""
echo "Press Ctrl+C to stop server"
echo "=========================================="
echo ""

python backend/src/app.py

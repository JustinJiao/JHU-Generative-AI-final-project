#!/bin/bash

echo "========================================"
echo "Starting System with OpenAI (ChatGPT)"
echo "========================================"
echo ""

# Get script directory and navigate to project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 1. Kill all processes
echo "Step 1: Cleaning up background processes..."
killall -9 python python3 Python 2>/dev/null
lsof -ti:8000 | xargs kill -9 2>/dev/null
sleep 2
echo "   Processes cleaned"
echo ""

# 2. Create and activate virtual environment if needed
echo "Step 2: Setting up environment..."
if [ ! -d "venv" ]; then
    echo "   Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "   Installing dependencies..."
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
else
    source venv/bin/activate
fi

# 3. Check API key
echo "Step 3: Checking OpenAI API Key..."
if [ -f ".env" ] && grep -q "^OPENAI_API_KEY=" .env && ! grep -q "^#.*OPENAI_API_KEY=" .env; then
    echo "   OpenAI API Key configured"
else
    echo "   OPENAI_API_KEY not found in .env file"
    echo "   Please create .env file and add: OPENAI_API_KEY=your-key-here"
    echo "   You can copy .env.example to .env and edit it"
    exit 1
fi
echo ""

# 4. Delete old database and reinitialize (for fresh start)
echo "Step 4: Preparing database..."
rm -f escalation.db backend/src/escalation.db
echo "   Database reset for fresh start"
echo ""

# 5. Initialize demo data
echo "Step 5: Initializing demo data..."
python3 init_demo_data.py
echo ""

# 6. Start server
echo "========================================"
echo "Starting Server (OpenAI gpt-4o-mini)"
echo "========================================"
echo ""
echo "LLM Mode: OpenAI (ChatGPT)"
echo "Model: gpt-4o-mini"
echo "All features enabled"
echo ""
echo "Press Ctrl+C to stop server"
echo "========================================"
echo ""

python backend/src/app.py

# Customer Support Escalation Decision Assistant

An AI-powered system to automatically determine whether customer support cases should be escalated to specialized teams, using LLM + policy retrieval.

## Features

- **Main System**: LLM + Policy Retrieval for intelligent escalation decisions
- **Real-time Monitoring**: Monitor live conversations and auto-escalate when policies match
- **Database Integration**: SQLite database tracks customer history and improves decisions
- **Baseline Methods**: Prompt-only LLM and keyword-based rule matching for comparison
- **Triple Web Interface**:
  - Batch Analysis UI for completed conversations
  - Real-time Monitor UI for live conversation tracking
  - Interactive Demo UI with pre-configured scenarios
- **Test Dataset**: 15 labeled test cases covering various scenarios
- **Analytics API**: Query conversation history, escalation stats, and customer patterns

## Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation & Running

**The easiest way:** Just clone and run the startup script!

```bash
# Clone the repository
git clone https://github.com/JustinJiao/JHU-Generative-AI-final-project.git
cd JHU-Generative-AI-final-project

# Run the automated setup script
./run.sh
```

**That's it!** The script will automatically:
- Create a virtual environment (`venv/`)
- Install all dependencies from `requirements.txt`
- Start the server at `http://localhost:8000`

### Alternative Startup Scripts

```bash
# Option 1: Quick start (recommended for first-time users)
./run.sh

# Option 2: Start with cleanup (if port 8000 is busy)
./start_server.sh

# Option 3: Start with OpenAI (requires .env setup)
./START_WITH_OPENAI.sh

# Option 4: Cross-platform Python launcher
python run.py
```

### Manual Setup (If Needed)

If the automated scripts don't work:

```bash
# 1. Create virtual environment
python3 -m venv venv

# 2. Activate virtual environment
source venv/bin/activate          # Mac/Linux
# OR
venv\Scripts\activate              # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start server
cd backend/src
python app.py
```

### API Key Configuration (Optional)

The system works in **two modes**:

**1. Mock Mode (Default - No Setup Required)**
- ✅ Perfect for testing and demos
- ✅ Works immediately after cloning
- Uses rule-based intelligent responses
- No external API calls or costs

**2. Full LLM Mode (OpenAI API Key Required)**
- Real AI-powered decisions using GPT-4o-mini
- More sophisticated reasoning
- Requires OpenAI API key

**To enable Full LLM Mode:**

```bash
# Step 1: Create .env file from template
cp .env.example .env

# Step 2: Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-your-actual-key-here

# Step 3: Run with OpenAI
./START_WITH_OPENAI.sh
```

Or set environment variable:
```bash
export OPENAI_API_KEY="sk-your-key"    # Mac/Linux
set OPENAI_API_KEY=sk-your-key         # Windows
```

## Usage

Once the server is running, **open your browser** to:

### 🌐 Main Dashboard
**URL:** `http://localhost:8000`

### Available Web Interfaces

#### 1. **Interactive Demo** (Recommended for First-Time Users)
**URL:** `http://localhost:8000/static/demo.html`

Pre-configured scenarios for quick testing:
- Security Threat Detection
- Repeat Issue Escalation
- Legal Threat Handling
- VIP Customer Support
- Large Refund Requests
- Normal Issue Resolution

Features:
- Click a scenario to auto-fill conversation
- Real-time workflow visualization
- Live escalation decision display
- Statistics dashboard

#### 2. **Real-time Monitor**
**URL:** `http://localhost:8000/static/monitor.html`

For monitoring live conversations:
1. Click "Start New Conversation"
2. Add messages as conversation progresses
3. System automatically detects escalation triggers
4. View customer history from database
5. All conversations saved for analysis

**Key Advantage:** Automatically loads customer history - repeat customers detected without manual input!

#### 3. **Batch Analysis**
**URL:** `http://localhost:8000` (Main page)

For analyzing completed conversations:
1. Enter full conversation text
2. Fill in case metadata
3. Click "Analyze Case" for decision
4. Or "Compare All Methods" to see all three approaches side-by-side

### API Endpoints

#### Main Decision Endpoint
```bash
POST /api/decide
Content-Type: application/json

{
  "messages": [
    {"role": "customer", "content": "I was charged twice"},
    {"role": "agent", "content": "Let me help you with that"}
  ],
  "metadata": {
    "case_id": "CASE-001",
    "prior_contact_count": 3,
    "initial_category": "billing"
  }
}
```

#### Baseline Comparisons
```bash
POST /api/baseline1    # Prompt-only LLM
POST /api/baseline2    # Keyword rules
```

#### System Information
```bash
GET /api/health        # Health check
GET /api/policies      # Get all escalation policies
GET /api/stats         # System statistics
```

#### Database Queries
```bash
GET /api/conversations/recent?limit=10
GET /api/customer/{customer_id}/history
```

#### Real-time Monitoring
```bash
POST /api/monitor/start       # Start conversation monitoring
POST /api/monitor/message     # Add message and check escalation
POST /api/monitor/end         # End conversation
GET  /api/monitor/summary/{id} # Get conversation summary
```

## Project Structure

```
Project/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
├── run.sh                       # Quick start script (recommended)
├── start_server.sh              # Start with cleanup
├── START_WITH_OPENAI.sh         # Start with OpenAI mode
├── run.py                       # Cross-platform Python launcher
├── escalation.db                # SQLite database (auto-created)
├── backend/
│   ├── src/
│   │   ├── app.py              # FastAPI server
│   │   ├── models.py           # Pydantic data models
│   │   ├── decision_engine.py  # LLM decision engine
│   │   ├── policy_retriever.py # Policy matching
│   │   ├── database.py         # SQLite operations
│   │   ├── conversation_monitor.py  # Real-time monitoring
│   │   ├── issue_similarity.py      # Similarity detection
│   │   ├── metadata_extractor.py    # Metadata extraction
│   │   ├── baselines.py             # Baseline implementations
│   │   └── evaluate.py              # Evaluation metrics
│   └── data/
│       ├── escalation_policies.json # Policy rules
│       └── test_cases.json          # Test dataset
└── static/
    ├── index.html               # Batch analysis UI
    ├── monitor.html             # Real-time monitor UI
    └── demo.html                # Interactive demo UI
```

## System Architecture

### Decision Flow

1. **Input**: Conversation messages + metadata
2. **Policy Retrieval**: Find relevant escalation policies
3. **LLM Analysis**: Intelligent decision using GPT + policies
4. **Output**: Structured decision with reasoning and citations

### Key Components

- **PolicyRetriever**: Matches input against policy rules using keywords and metadata
- **DecisionEngine**: Uses LLM to make intelligent, context-aware decisions
- **ConversationMonitor**: Real-time monitoring with automatic escalation detection
- **Database**: SQLite for customer history and pattern recognition
- **Baselines**: Simple alternatives for comparison (prompt-only, keyword-based)

## Example Test Cases

The system includes 15 pre-configured test cases covering:

- ✅ Repeated unresolved issues
- ✅ Fraud and security threats
- ✅ Legal threats and complaints
- ✅ Large refund requests
- ✅ VIP customer handling
- ✅ Technical emergencies
- ✅ Simple inquiries (no escalation)

## Policy Configuration

Policies are defined in `backend/data/escalation_policies.json`. Each policy includes:

- **id**: Unique identifier
- **condition**: Matching rules (keyword, metadata, composite)
- **action**: escalate / no_escalate / conditional_escalate
- **target_team**: Which team to route to
- **priority**: critical / high / medium / low
- **description**: Explanation of the policy

### Example Policy

```json
{
  "id": "POLICY-001",
  "name": "Repeated Unresolved Issues",
  "condition": {
    "type": "metadata",
    "field": "prior_contact_count",
    "operator": ">=",
    "value": 3
  },
  "action": "escalate",
  "target_team": "Senior Support",
  "priority": "high",
  "description": "Escalate when customer has contacted 3+ times"
}
```

## Evaluation Metrics

The system supports evaluation on:

- **Decision Accuracy**: Correct escalate/no_escalate decisions
- **False Positive Rate**: Unnecessary escalations
- **False Negative Rate**: Missed escalations
- **Policy Grounding**: Decisions properly cited with policies
- **Consistency**: Same input → same output

## Troubleshooting

### Server won't start
```bash
# Check if port 8000 is already in use
lsof -i:8000

# Kill the process using port 8000
kill -9 <PID>

# Or use the cleanup script
./start_server.sh
```

### Dependencies not installing
```bash
# Update pip first
pip install --upgrade pip

# Install dependencies with verbose output
pip install -r requirements.txt -v
```

### Virtual environment issues
```bash
# Delete and recreate venv
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### API key not working
```bash
# Check if .env file exists and has correct format
cat .env

# Ensure no spaces around the = sign
# Correct:   OPENAI_API_KEY=sk-abc123
# Wrong:     OPENAI_API_KEY = sk-abc123

# Test if key is loaded
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('OPENAI_API_KEY'))"
```

## Development

### Adding New Policies

Edit `backend/data/escalation_policies.json` to add new rules.

### Running Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run evaluation
cd backend/src
python evaluate.py
```

### API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## License

This is an academic project for the JHU Generative AI course.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the code documentation
3. Open an issue in the repository

---

**Ready to start?** Just run `./run.sh` and open `http://localhost:8000/static/demo.html` in your browser! 🚀

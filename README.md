# Customer Support Escalation Decision Assistant

An AI-powered system that automatically determines whether customer support cases should be escalated to specialized teams, using LLM + policy retrieval architecture.

---

## 1. Context, User, and Problem

### The User
**Customer support managers and agents** in high-volume service environments who handle hundreds of cases daily across billing, technical, security, and legal issues.

### The Workflow Challenge
Traditional escalation systems suffer from:
- **Manual decision-making bottlenecks**: Agents must manually read policies and decide if cases warrant escalation
- **Inconsistent decisions**: Different agents interpret escalation criteria differently
- **Missed critical cases**: High-value refunds, security threats, or repeat issues may slip through
- **Delayed escalations**: Time spent deliberating means customers wait longer for proper help

### Why It Matters
**Impact on business and customers:**
- Delayed escalations increase customer churn and damage brand reputation
- Over-escalation wastes specialist team resources
- Under-escalation allows critical issues (fraud, legal threats) to worsen
- Inconsistent handling creates poor customer experiences

**The opportunity:** An AI system that instantly analyzes conversations against company policies can:
- Reduce escalation decision time from minutes to seconds
- Ensure consistent, policy-grounded decisions 24/7
- Catch critical patterns (repeat contacts, high-value issues) that humans might miss
- Free agents to focus on customer empathy rather than policy memorization

---

## 2. Solution and Design

### What We Built

A **three-tier escalation decision system** with:

1. **Main System (LLM + Policy Retrieval)**: Combines intelligent policy matching with GPT-4o-mini reasoning
2. **Baseline 1 (Prompt-Only LLM)**: Simple LLM without structured policy retrieval
3. **Baseline 2 (Keyword Rules)**: Traditional rule-based matching

Plus **three web interfaces** for different use cases:
- **Batch Analysis UI**: Analyze completed conversations
- **Real-time Monitor UI**: Track live conversations with automatic escalation detection
- **Interactive Demo UI**: Pre-configured scenarios for quick testing

### How It Works

#### Main System Architecture

```
Input: Conversation + Metadata
         ↓
    Policy Retrieval
    (Match relevant policies)
         ↓
    LLM Decision Engine
    (Reason with policies)
         ↓
Output: Decision + Team + Reasoning
```

**Step 1: Policy Retrieval**
- Matches conversation against 8 escalation policies using keyword and metadata filters
- Policies cover: repeat issues, fraud/security, legal threats, high-value refunds, VIP customers, data privacy, manager requests, technical emergencies
- Returns only relevant policies to focus LLM attention

**Step 2: LLM Decision Making**
- GPT-4o-mini analyzes conversation with retrieved policies
- Generates structured decision: escalate/no_escalate
- Provides reasoning grounded in specific policies
- Assigns target team and priority level

**Step 3: Database Integration**
- Stores all conversations in SQLite database
- Tracks customer history for repeat issue detection
- Enables pattern analysis and analytics

#### Key Design Choices

**1. Why LLM + Retrieval vs. Pure LLM?**
- **Policy grounding**: Retrieved policies force LLM to cite specific rules, increasing transparency
- **Consistency**: Same policy set ensures all decisions follow company guidelines
- **Efficiency**: Only relevant policies in prompt reduces token usage
- **Maintainability**: Update policies without retraining models

**2. Why SQLite Database?**
- **Customer history**: Track prior_contact_count to detect repeat issues (critical for escalation)
- **Pattern detection**: Identify customers with recurring problems
- **Analytics**: Query escalation trends over time
- **Zero setup**: No external database required for deployment

**3. Why Three Interfaces?**
- **Batch Analysis**: For reviewing completed cases in bulk
- **Real-time Monitor**: For agents monitoring live conversations
- **Interactive Demo**: For stakeholders and quick testing

**4. Metadata Extraction with LLM**
- Uses GPT-4o-mini to extract structured metadata (customer_id, issue_type, refund_amount)
- Enables policy rules based on values not explicitly stated
- Example: "I want my $600 back" → refund_amount: 600 → triggers high-value refund policy

#### System Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| **PolicyRetriever** | Match conversations to policies | Keyword + metadata filtering |
| **DecisionEngine** | Make escalation decisions | GPT-4o-mini + structured prompts |
| **MetadataExtractor** | Extract key details from text | GPT-4o-mini |
| **ConversationMonitor** | Real-time conversation tracking | In-memory state + event detection |
| **Database** | Customer history & analytics | SQLite |
| **Baselines** | Comparison methods | Rule-based + simple prompting |

---

## 3. Evaluation and Results

### Test Dataset
**15 labeled test cases** covering:
- Clear escalations: Repeat issues, fraud, legal threats, high refunds
- Edge cases: Angry but simple issues, polite but complex issues
- No-escalation cases: Simple FAQs, routine inquiries
- Mixed issues: Multiple problem types in one conversation

### Evaluation Metrics
- **Accuracy**: Correct escalate/no_escalate decisions
- **False Positive Rate**: Unnecessary escalations (wastes specialist resources)
- **False Negative Rate**: Missed escalations (critical for customer safety)

### Results Summary

| System | Accuracy | FP Rate | FN Rate | Correct |
|--------|----------|---------|---------|---------|
| **Main (LLM + Retrieval)** | **86.7%** | 6.7% | 6.7% | 13/15 |
| Baseline 1 (Prompt-Only) | 80.0% | 13.3% | 6.7% | 12/15 |
| Baseline 2 (Keyword Rules) | 73.3% | 13.3% | 13.3% | 11/15 |

### Key Findings

**1. Main System Outperforms Baselines**
- 6.7% higher accuracy than Prompt-Only LLM
- 13.4% higher accuracy than Keyword Rules
- **Balanced FP/FN rates**: Low false positives (6.7%) avoid specialist overload
- **Best recall**: Only 6.7% false negatives minimize missed critical cases

**2. Policy Retrieval Improves Consistency**
- Baseline 1 (Prompt-Only) has 2x false positive rate (13.3% vs 6.7%)
- Main system's structured policy matching reduces over-escalation
- Example: "Angry But Simple Issue" (TEST-009) correctly not escalated by Main, incorrectly escalated by both baselines

**3. Keyword Rules Miss Nuance**
- Baseline 2 (Keyword Rules) worst performance (73.3%)
- Misses data privacy request (TEST-011) - requires semantic understanding
- Over-escalates angry customers with simple issues
- Cannot handle context or tone

**4. Remaining Challenges**
Both Main system errors are edge cases:
- **TEST-008 (Account Cancellation)**: System didn't escalate to Retention Team
  - *Root cause*: Requires business logic (retention value) not explicit in policies
- **TEST-014 (Payment Failed - First Contact)**: System over-escalated
  - *Root cause*: Payment issues flagged by multiple policies even for first contact

### Comparison Baseline
We compared against:
1. **Prompt-Only LLM**: Same GPT-4o-mini model without structured policy retrieval
2. **Keyword Rule Baseline**: Traditional rule-based system matching keywords like "fraud", "legal", "manager"

This demonstrates that **LLM + Retrieval architecture** combines the best of both worlds:
- Semantic understanding from LLM
- Structured consistency from policy retrieval

---

## 4. Artifact Snapshot

### Video Demo

**[Watch the demo video on YouTube](https://youtu.be/AapmiImXPpM)**

This 2-minute demo shows:
- Full system walkthrough with all three interfaces
- Cloning the repository and running `./run.sh`
- Testing pre-configured escalation scenarios
- Real-time decision outputs with reasoning and policy citations
- Side-by-side comparison of Main System vs Baselines

### Sample Input/Output

**Example 1: Repeat Issue Escalation**
```json
INPUT:
{
  "messages": [
    {"role": "customer", "content": "I was charged twice for my subscription."},
    {"role": "agent", "content": "I apologize. Can you provide your order number?"},
    {"role": "customer", "content": "This is my third time contacting support! Order #12345"}
  ],
  "metadata": {
    "case_id": "CASE-001",
    "prior_contact_count": 3,
    "initial_category": "billing"
  }
}

OUTPUT:
{
  "decision": "escalate",
  "target_team": "Senior Support",
  "priority": "high",
  "confidence": 0.95,
  "reasoning": "Customer has contacted support 3 times about the same billing issue...",
  "policy_citations": ["POLICY-001: Repeated Unresolved Issues"],
  "recommended_actions": [
    "Prioritize immediate resolution",
    "Review prior contact history",
    "Consider compensation"
  ]
}
```

**Example 2: Security Threat Escalation**
```json
INPUT:
{
  "messages": [
    {"role": "customer", "content": "I see unauthorized charges on my account!"},
    {"role": "customer", "content": "Someone hacked my account and made fraudulent purchases"}
  ],
  "metadata": {
    "case_id": "CASE-002",
    "initial_category": "security"
  }
}

OUTPUT:
{
  "decision": "escalate",
  "target_team": "Security Team",
  "priority": "critical",
  "confidence": 0.98,
  "reasoning": "Potential account breach with fraudulent activity...",
  "policy_citations": ["POLICY-002: Security and Fraud Threats"],
  "recommended_actions": [
    "Freeze account immediately",
    "Initiate fraud investigation",
    "Issue temporary credentials"
  ]
}
```

---

## Setup and Usage Instructions

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Git (to clone repository)

### Installation

**Option 1: Automated Setup (Recommended)**

```bash
# Clone the repository
git clone https://github.com/JustinJiao/JHU-Generative-AI-final-project.git
cd JHU-Generative-AI-final-project

# Run automated setup script
./run.sh
```

**That's it!** The script automatically:
- Creates a virtual environment (`venv/`)
- Installs dependencies from `requirements.txt`
- Starts the server at `http://localhost:8000`

**Option 2: Manual Setup**

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

### Configuration

The system works in **two modes**:

#### Mode 1: Mock Mode (No API Key) - Works Immediately
- Uses rule-based pattern matching
- No external API calls or costs
- Suitable for testing and demonstration
- Automatically enabled if no API key provided

#### Mode 2: Full LLM Mode (OpenAI API Key) - Recommended for Best Performance

**Why use Full LLM Mode:**
- Real AI-powered decisions using GPT-4o-mini
- Intelligent metadata extraction from conversations
- Context-aware reasoning for escalation decisions
- Dynamic policy interpretation
- Much more accurate than rule-based approach (86.7% vs 73.3% accuracy)

**Setup Full LLM Mode:**

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

---

## Usage Examples

### Example 1: Interactive Demo (Quickest Way to Test)

1. **Start the server** (if not already running):
   ```bash
   ./run.sh
   ```

2. **Open Interactive Demo** in your browser:
   ```
   http://localhost:8000/static/demo.html
   ```

3. **Try a scenario:**
   - Click "Security Threat Detection" scenario
   - Conversation auto-fills with pre-configured messages
   - See instant escalation decision with:
     - Decision: escalate / no_escalate
     - Target team assignment
     - Priority level
     - Reasoning and policy citations
     - Recommended actions

4. **Try other scenarios:**
   - Repeat Issue Escalation
   - Legal Threat Handling
   - VIP Customer Support
   - Large Refund Requests
   - Normal Issue (No Escalation)

### Example 2: Real-time Conversation Monitoring

1. **Open Real-time Monitor**:
   ```
   http://localhost:8000/static/monitor.html
   ```

2. **Start a new conversation:**
   - Click "Start New Conversation"
   - Enter customer ID (e.g., "CUST-001")

3. **Add messages as conversation progresses:**
   - Type customer message → Click "Add Customer Message"
   - Type agent response → Click "Add Agent Message"
   - System automatically checks for escalation triggers after each message

4. **View results:**
   - Real-time escalation detection
   - Customer history automatically loaded from database
   - Full conversation summary with decision reasoning

### Example 3: Batch Analysis

1. **Open Batch Analysis UI**:
   ```
   http://localhost:8000
   ```

2. **Enter a conversation:**
   ```
   Customer: I was charged twice for my subscription
   Agent: I apologize. Can you provide your order number?
   Customer: This is my third time contacting support! Order #12345
   ```

3. **Fill metadata:**
   - Case ID: CASE-001
   - Prior Contact Count: 3
   - Category: billing

4. **Click "Analyze Case"** or **"Compare All Methods"** to see:
   - Main System decision
   - Baseline 1 (Prompt-Only) decision
   - Baseline 2 (Keyword Rules) decision
   - Side-by-side comparison

### Example 4: API Usage (For Developers)

**Make a decision via API:**

```bash
curl -X POST http://localhost:8000/api/decide \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "customer", "content": "I see unauthorized charges on my account!"},
      {"role": "customer", "content": "Someone hacked my account"}
    ],
    "metadata": {
      "case_id": "CASE-002",
      "customer_id": "CUST-002",
      "initial_category": "security"
    }
  }'
```

**Response:**
```json
{
  "decision": "escalate",
  "target_team": "Security Team",
  "priority": "critical",
  "confidence": 0.98,
  "reasoning": "Potential account breach with fraudulent activity...",
  "policy_citations": ["POLICY-002: Security and Fraud Threats"],
  "recommended_actions": [...]
}
```

### Example 5: Running Evaluation Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run evaluation on all 15 test cases
cd backend/src
python evaluate.py
```

**Output:**
```
EVALUATION SUMMARY
+-----------+-----------+------------+-----------+-----------+
| System    | Correct   | Accuracy   | FP Rate   | FN Rate   |
+-----------+-----------+------------+-----------+-----------+
| MAIN      | 13/15     | 86.7%      | 6.7%      | 6.7%      |
| BASELINE1 | 12/15     | 80.0%      | 13.3%     | 6.7%      |
| BASELINE2 | 11/15     | 73.3%      | 13.3%     | 13.3%     |
+-----------+-----------+------------+-----------+-----------+
```

Results exported to `backend/evaluation_results.json`

---

## API Documentation

### Core Endpoints

#### `POST /api/decide`
Main decision endpoint using LLM + Policy Retrieval

**Request Body:**
```json
{
  "messages": [
    {"role": "customer", "content": "..."},
    {"role": "agent", "content": "..."}
  ],
  "metadata": {
    "case_id": "CASE-001",
    "customer_id": "CUST-001",
    "prior_contact_count": 3,
    "initial_category": "billing"
  }
}
```

**Response:**
```json
{
  "decision": "escalate",
  "target_team": "Senior Support",
  "priority": "high",
  "confidence": 0.95,
  "reasoning": "...",
  "policy_citations": ["POLICY-001"],
  "recommended_actions": ["..."]
}
```

#### `POST /api/baseline1`
Prompt-only LLM baseline (no policy retrieval)

#### `POST /api/baseline2`
Keyword rule-based baseline

#### `GET /api/policies`
Get all escalation policies

#### `GET /api/stats`
Get system statistics (total conversations, escalation rate, etc.)

#### `GET /api/health`
Health check endpoint

### Real-time Monitoring Endpoints

#### `POST /api/monitor/start`
Start monitoring a new conversation

#### `POST /api/monitor/message`
Add message and check for escalation triggers

#### `POST /api/monitor/end`
End conversation monitoring

#### `GET /api/monitor/summary/{conversation_id}`
Get full conversation summary

### Database Query Endpoints

#### `GET /api/conversations/recent?limit=10`
Get recent conversations

#### `GET /api/customer/{customer_id}/history`
Get customer conversation history

---

## Project Structure

```
Project/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
├── run.sh                       # Quick start script (recommended)
├── start_server.sh              # Start with port cleanup
├── START_WITH_OPENAI.sh         # Start with OpenAI mode
├── run.py                       # Cross-platform Python launcher
├── escalation.db                # SQLite database (auto-created)
├── backend/
│   ├── src/
│   │   ├── app.py              # FastAPI server
│   │   ├── models.py           # Pydantic data models
│   │   ├── decision_engine.py  # LLM decision engine
│   │   ├── policy_retriever.py # Policy matching logic
│   │   ├── database.py         # SQLite operations
│   │   ├── conversation_monitor.py  # Real-time monitoring
│   │   ├── issue_similarity.py      # Repeat issue detection
│   │   ├── metadata_extractor.py    # LLM metadata extraction
│   │   ├── baselines.py             # Baseline implementations
│   │   └── evaluate.py              # Evaluation script
│   └── data/
│       ├── escalation_policies.json # 8 escalation policies
│       └── test_cases.json          # 15 test cases
└── static/
    ├── index.html               # Batch analysis UI
    ├── monitor.html             # Real-time monitor UI
    └── demo.html                # Interactive demo UI
```

---

## Troubleshooting

### Server won't start - Port 8000 already in use
```bash
# Check what's using port 8000
lsof -i:8000

# Kill the process
kill -9 <PID>

# Or use the cleanup script
./start_server.sh
```

### Dependencies not installing
```bash
# Update pip first
pip install --upgrade pip

# Install with verbose output
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

### OpenAI API key not working
```bash
# Check .env file format (no spaces around =)
cat .env

# Correct format:
# OPENAI_API_KEY=sk-abc123

# Wrong format:
# OPENAI_API_KEY = sk-abc123

# Test if key is loaded
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('OPENAI_API_KEY'))"
```

### Browser shows "Connection refused"
- Make sure server is running: Check terminal for "Uvicorn running on http://0.0.0.0:8000"
- Try http://127.0.0.1:8000 instead of localhost
- Check firewall isn't blocking port 8000

---

## Technical Implementation Details

### Policy Configuration

Policies are defined in `backend/data/escalation_policies.json`. Each policy includes:

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

**Policy types:**
- **keyword**: Match text patterns (e.g., "fraud", "legal")
- **metadata**: Match metadata fields (e.g., prior_contact_count >= 3)
- **composite**: Combine multiple conditions with AND/OR logic

### Adding New Policies

Edit `backend/data/escalation_policies.json`:

```json
{
  "id": "POLICY-009",
  "name": "Your New Policy",
  "condition": {
    "type": "keyword",
    "keywords": ["urgent", "emergency"]
  },
  "action": "escalate",
  "target_team": "Emergency Response",
  "priority": "critical",
  "description": "Handle urgent emergencies"
}
```

No code changes required - policies are loaded dynamically!

### Extending the System

**Add new metadata fields:**
1. Update `CaseMetadata` in `backend/src/models.py`
2. Update metadata extraction in `backend/src/metadata_extractor.py`
3. Add policies that use the new field

**Add new decision logic:**
1. Modify prompt in `backend/src/decision_engine.py`
2. Update `DecisionOutput` model if needed

**Add new baseline:**
1. Create new class in `backend/src/baselines.py`
2. Add endpoint in `backend/src/app.py`
3. Update evaluation script

---

## Development

### Running Tests
```bash
source venv/bin/activate
cd backend/src
python evaluate.py
```

### API Documentation
Visit when server is running:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Database Inspection
```bash
sqlite3 escalation.db
sqlite> .tables
sqlite> SELECT * FROM conversations LIMIT 5;
sqlite> .quit
```

---

## License

This is an academic project for the JHU Generative AI course.

---

## Support

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review API documentation at http://localhost:8000/docs
3. Open an issue in the repository

---

**Ready to start?** Just run `./run.sh` and open http://localhost:8000/static/demo.html in your browser!

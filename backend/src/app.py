"""
Main application file - FastAPI server
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from models import EscalationInput, EscalationOutput, Message
from policy_retriever import PolicyRetriever
from decision_engine import DecisionEngine
from baselines import PromptOnlyBaseline, KeywordRuleBaseline
from metadata_extractor import MetadataExtractor
from conversation_monitor import ConversationMonitor

# Initialize FastAPI app
app = FastAPI(
    title="Customer Support Escalation Decision Assistant",
    description="AI-powered system to determine whether support cases should be escalated",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get paths
BASE_DIR = Path(__file__).parent.parent
POLICY_FILE = BASE_DIR / "data" / "escalation_policies.json"
STATIC_DIR = BASE_DIR.parent / "static"

# Initialize components
policy_retriever = PolicyRetriever(str(POLICY_FILE))
decision_engine = DecisionEngine(policy_retriever)
baseline_1 = PromptOnlyBaseline()
baseline_2 = KeywordRuleBaseline()
metadata_extractor = MetadataExtractor()
conversation_monitor = ConversationMonitor(str(POLICY_FILE))

# Serve static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def root():
    """Serve the main HTML page"""
    html_file = STATIC_DIR / "index.html"
    if html_file.exists():
        return FileResponse(str(html_file))
    return {"message": "Customer Support Escalation Decision Assistant API"}


@app.post("/api/decide", response_model=EscalationOutput)
async def make_decision(escalation_input: EscalationInput):
    """
    Main endpoint: Make escalation decision using LLM + Policy system
    """
    try:
        result = decision_engine.make_decision(escalation_input)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/baseline1", response_model=EscalationOutput)
async def baseline_1_decision(escalation_input: EscalationInput):
    """
    Baseline 1: Prompt-only LLM without policy retrieval
    """
    try:
        result = baseline_1.make_decision(escalation_input)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/baseline2", response_model=EscalationOutput)
async def baseline_2_decision(escalation_input: EscalationInput):
    """
    Baseline 2: Keyword-based rule matching
    """
    try:
        result = baseline_2.make_decision(escalation_input)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "api_key_set": decision_engine.client is not None
    }


@app.get("/api/policies")
async def get_policies():
    """Get all escalation policies"""
    return policy_retriever.policies.dict()


@app.post("/api/extract-metadata")
async def extract_metadata(messages: list):
    """
    Extract metadata from conversation using LLM/rules

    Input: List of messages [{"role": "customer", "content": "..."}, ...]
    Output: Extracted metadata
    """
    try:
        # Convert to Message objects
        message_objects = [Message(**msg) for msg in messages]

        # Extract metadata
        metadata = metadata_extractor.extract_metadata(message_objects)

        return {
            "success": True,
            "metadata": metadata
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Real-time Monitoring API ====================

@app.post("/api/monitor/start")
async def start_monitoring(data: dict):
    """
    Start monitoring a new conversation

    Input: {"conversation_id": "CONV-001", "customer_id": "CUST-123"}
    """
    try:
        conversation_id = data.get("conversation_id")
        customer_id = data.get("customer_id")

        conversation_monitor.start_conversation(conversation_id, customer_id)

        return {
            "success": True,
            "message": f"Started monitoring conversation {conversation_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/monitor/message")
async def add_message_to_monitor(data: dict):
    """
    Add new message to monitored conversation and check if escalation needed

    Input: {
        "conversation_id": "CONV-001",
        "role": "customer",  # or "agent"
        "content": "Message content"
    }

    Output: {
        "should_escalate": bool,
        "decision": {...},
        "continue_ai": bool
    }
    """
    try:
        conversation_id = data.get("conversation_id")
        role = data.get("role")
        content = data.get("content")

        result = conversation_monitor.add_message(conversation_id, role, content)

        return {
            "success": True,
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/monitor/summary/{conversation_id}")
async def get_conversation_summary(conversation_id: str):
    """
    Get conversation summary

    Returns: {
        "conversation_id": "...",
        "message_count": 5,
        "escalated": true/false,
        "escalation_reason": "..."
    }
    """
    try:
        summary = conversation_monitor.get_conversation_summary(conversation_id)
        return {"success": True, **summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/monitor/end")
async def end_monitoring(data: dict):
    """
    End conversation monitoring

    Input: {"conversation_id": "CONV-001"}
    """
    try:
        conversation_id = data.get("conversation_id")
        conversation_monitor.end_conversation(conversation_id)

        return {
            "success": True,
            "message": f"Ended monitoring for {conversation_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Database Statistics API ====================

@app.get("/api/stats")
async def get_stats():
    """
    Get system statistics

    Returns: {
        "total_conversations": 100,
        "escalated_conversations": 25,
        "escalation_rate": 25.0,
        "team_stats": [...]
    }
    """
    try:
        stats = conversation_monitor.db.get_escalation_stats()
        return {"success": True, **stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/conversations/recent")
async def get_recent_conversations(limit: int = 10):
    """
    Get recent conversation records

    Query params: limit (default: 10)
    """
    try:
        conversations = conversation_monitor.db.get_recent_conversations(limit)
        return {"success": True, "conversations": conversations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/customer/{customer_id}/history")
async def get_customer_history(customer_id: str):
    """
    Get customer conversation history and issue records

    Returns: Customer info, conversation count, and past issues
    """
    try:
        customer_info = conversation_monitor.db.get_customer(customer_id)
        past_issues = conversation_monitor.db.get_customer_past_issues(customer_id)
        escalation_history = conversation_monitor.db.get_customer_escalation_history(customer_id)

        return {
            "success": True,
            "customer_info": customer_info,
            "past_issues": past_issues,
            "escalation_history": escalation_history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

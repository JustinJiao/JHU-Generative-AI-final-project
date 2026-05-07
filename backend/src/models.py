"""
Data models for the Customer Support Escalation Decision Assistant
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class MessageRole(str, Enum):
    """Message role in conversation"""
    CUSTOMER = "customer"
    AGENT = "agent"


class Message(BaseModel):
    """Single message in a conversation"""
    role: MessageRole
    content: str


class CaseMetadata(BaseModel):
    """Metadata about a support case"""
    case_id: str = Field(..., description="Unique case identifier")
    customer_id: Optional[str] = Field(None, description="Anonymized customer ID")
    prior_contact_count: int = Field(0, description="Number of previous contacts")
    created_at: Optional[str] = Field(None, description="Case creation timestamp")
    initial_category: Optional[str] = Field(None, description="Initial issue category")


class EscalationInput(BaseModel):
    """Input data for escalation decision"""
    messages: List[Message] = Field(..., description="Conversation history")
    metadata: CaseMetadata = Field(..., description="Case metadata")


class DecisionType(str, Enum):
    """Type of escalation decision"""
    ESCALATE = "escalate"
    NO_ESCALATE = "no_escalate"


class PolicyCitation(BaseModel):
    """Citation of a policy rule"""
    policy_id: str
    rule_text: str


class ExtractedInfo(BaseModel):
    """Information extracted from conversation"""
    issue_type: Optional[str] = None
    sentiment: Optional[str] = None
    urgency: Optional[str] = None
    keywords: List[str] = []
    detected_amount: Optional[float] = None


class EscalationOutput(BaseModel):
    """Output of escalation decision"""
    decision: DecisionType = Field(..., description="Escalation decision")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    target_team: Optional[str] = Field(None, description="Target team if escalating")
    reasoning: str = Field(..., description="Explanation for the decision")
    policy_citations: List[PolicyCitation] = Field(default_factory=list, description="Cited policy rules")
    extracted_info: Optional[ExtractedInfo] = Field(None, description="Extracted information from conversation")
    flag: Optional[str] = Field(None, description="Special flag (e.g., 'low_confidence')")


class EscalationPolicy(BaseModel):
    """Escalation policy definition"""
    id: str
    name: str
    condition: Dict[str, Any]
    action: str
    target_team: Optional[str]
    priority: str
    description: str
    escalation_threshold: Optional[Dict[str, Any]] = None


class PolicyDatabase(BaseModel):
    """Collection of escalation policies"""
    escalation_policies: List[EscalationPolicy]
    default_policy: EscalationPolicy

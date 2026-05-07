"""
Baseline methods for comparison
"""
import os
import json
import re
from typing import List
from openai import OpenAI
from models import (
    EscalationInput,
    EscalationOutput,
    DecisionType,
    PolicyCitation,
    ExtractedInfo,
    Message
)


class PromptOnlyBaseline:
    """Baseline 1: Simple prompt-only LLM without policy retrieval"""

    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model

        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None
            print("Warning: No API key provided. Using mock responses.")

    def make_decision(self, escalation_input: EscalationInput) -> EscalationOutput:
        """Make decision using only simple prompt"""
        conversation_text = self._format_conversation(escalation_input.messages)
        metadata = escalation_input.metadata

        prompt = f"""You are a customer support supervisor. Based on the conversation below, decide if this case should be escalated to a specialized team or handled by automated support.

CONVERSATION:
{conversation_text}

METADATA:
- Prior contacts: {metadata.prior_contact_count}
- Case ID: {metadata.case_id}

Should this be escalated? If yes, to which team?

Respond in JSON format:
{{
  "decision": "escalate" or "no_escalate",
  "target_team": "<team name>" or null,
  "reasoning": "<explanation>"
}}"""

        if self.client:
            try:
                message = self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=512,
                    messages=[{"role": "user", "content": prompt}]
                )
                response_text = message.choices[0].message.content
            except Exception as e:
                print(f"Error calling LLM: {e}")
                response_text = self._mock_response(metadata.prior_contact_count)
        else:
            response_text = self._mock_response(metadata.prior_contact_count)

        return self._parse_response(response_text)

    def _format_conversation(self, messages: List[Message]) -> str:
        """Format conversation"""
        lines = []
        for msg in messages:
            role = "Customer" if msg.role.value == "customer" else "Agent"
            lines.append(f"{role}: {msg.content}")
        return "\n".join(lines)

    def _mock_response(self, prior_contacts: int) -> str:
        """Mock response for testing"""
        if prior_contacts >= 2:
            return json.dumps({
                "decision": "escalate",
                "target_team": "Support Team",
                "reasoning": "Customer has contacted multiple times."
            })
        return json.dumps({
            "decision": "no_escalate",
            "target_team": None,
            "reasoning": "Seems like a simple inquiry."
        })

    def _parse_response(self, response_text: str) -> EscalationOutput:
        """Parse response into EscalationOutput"""
        try:
            # Extract JSON
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                json_str = json_match.group(0) if json_match else "{}"

            data = json.loads(json_str)

            return EscalationOutput(
                decision=DecisionType(data.get("decision", "escalate")),
                confidence=0.7,  # Arbitrary medium confidence
                target_team=data.get("target_team"),
                reasoning=data.get("reasoning", "No reasoning provided"),
                policy_citations=[],  # No policy citations in baseline
                extracted_info=None,
                flag="baseline_1"
            )
        except Exception as e:
            print(f"Error parsing baseline response: {e}")
            return EscalationOutput(
                decision=DecisionType.ESCALATE,
                confidence=0.5,
                target_team="Human Review Queue",
                reasoning="Error in baseline processing",
                policy_citations=[],
                flag="baseline_1_error"
            )


class KeywordRuleBaseline:
    """Baseline 2: Simple keyword-based rule matching"""

    # Define escalation keywords and their target teams
    ESCALATION_RULES = {
        "Security Team": ["fraud", "fraudulent", "hacked", "unauthorized", "security", "stolen"],
        "Legal Team": ["lawyer", "attorney", "lawsuit", "legal action", "sue", "court"],
        "Financial Team": ["refund", "money back", "charge back", "charged twice"],
        "Supervisor": ["manager", "supervisor", "speak to manager"],
        "Technical Support": ["bug", "crash", "error", "broken", "not working"],
    }

    THRESHOLD_CONTACTS = 2  # Escalate if >= this many prior contacts

    def make_decision(self, escalation_input: EscalationInput) -> EscalationOutput:
        """Make decision based on keyword rules"""
        conversation_text = self._format_conversation(escalation_input.messages).lower()
        metadata = escalation_input.metadata

        # Check metadata-based rules first
        if metadata.prior_contact_count >= self.THRESHOLD_CONTACTS:
            return EscalationOutput(
                decision=DecisionType.ESCALATE,
                confidence=1.0,
                target_team="Senior Support",
                reasoning=f"Prior contact count ({metadata.prior_contact_count}) >= threshold ({self.THRESHOLD_CONTACTS})",
                policy_citations=[],
                extracted_info=ExtractedInfo(
                    issue_type="repeated_contact",
                    keywords=[],
                    urgency="high"
                ),
                flag="baseline_2"
            )

        # Check keyword-based rules
        for team, keywords in self.ESCALATION_RULES.items():
            matched_keywords = []
            for keyword in keywords:
                if keyword in conversation_text:
                    matched_keywords.append(keyword)

            if matched_keywords:
                return EscalationOutput(
                    decision=DecisionType.ESCALATE,
                    confidence=1.0,
                    target_team=team,
                    reasoning=f"Matched keywords: {', '.join(matched_keywords)}",
                    policy_citations=[],
                    extracted_info=ExtractedInfo(
                        issue_type="keyword_match",
                        keywords=matched_keywords,
                        urgency="medium"
                    ),
                    flag="baseline_2"
                )

        # No rules matched - don't escalate
        return EscalationOutput(
            decision=DecisionType.NO_ESCALATE,
            confidence=1.0,
            target_team=None,
            reasoning="No escalation keywords or conditions detected",
            policy_citations=[],
            extracted_info=ExtractedInfo(
                issue_type="simple_inquiry",
                keywords=[],
                urgency="low"
            ),
            flag="baseline_2"
        )

    def _format_conversation(self, messages: List[Message]) -> str:
        """Format conversation into text"""
        return " ".join([msg.content for msg in messages])

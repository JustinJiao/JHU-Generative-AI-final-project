"""
LLM-based decision engine for escalation decisions
"""
import os
import json
import re
from typing import Optional, List, Tuple
from openai import OpenAI
from models import (
    EscalationInput,
    EscalationOutput,
    DecisionType,
    PolicyCitation,
    ExtractedInfo,
    Message
)
from policy_retriever import PolicyRetriever


class DecisionEngine:
    """Main decision engine using LLM + policy retrieval"""

    def __init__(
        self,
        policy_retriever: PolicyRetriever,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini"
    ):
        """
        Initialize decision engine

        Args:
            policy_retriever: Policy retriever instance
            api_key: Anthropic API key (or set OPENAI_API_KEY env var)
            model: Model name to use
        """
        self.policy_retriever = policy_retriever
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model

        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None
            print("Warning: No API key provided. Using mock responses for testing.")

    def make_decision(self, escalation_input: EscalationInput) -> EscalationOutput:
        """
        Make escalation decision based on input

        Args:
            escalation_input: Input containing conversation and metadata

        Returns:
            Escalation decision output
        """
        # Step 1: Format conversation
        conversation_text = self._format_conversation(escalation_input.messages)

        # Step 2: Retrieve relevant policies
        relevant_policies = self.policy_retriever.retrieve_relevant_policies(
            escalation_input,
            conversation_text
        )

        # Step 3: Format policies for LLM
        policy_context = self.policy_retriever.format_policies_for_llm(relevant_policies)

        # Step 4: Create prompt and call LLM
        prompt = self._create_decision_prompt(
            escalation_input,
            conversation_text,
            policy_context,
            relevant_policies
        )

        # Step 5: Get LLM response
        if self.client:
            llm_response = self._call_llm(prompt)
        else:
            llm_response = self._mock_llm_response(escalation_input, relevant_policies)

        # Step 6: Parse LLM response into structured output
        decision_output = self._parse_llm_response(llm_response, relevant_policies)

        return decision_output

    def _format_conversation(self, messages: List[Message]) -> str:
        """Format messages into readable conversation"""
        lines = []
        for msg in messages:
            role_label = "Customer" if msg.role.value == "customer" else "Agent"
            lines.append(f"{role_label}: {msg.content}")
        return "\n".join(lines)

    def _create_decision_prompt(
        self,
        escalation_input: EscalationInput,
        conversation_text: str,
        policy_context: str,
        relevant_policies: List[Tuple]
    ) -> str:
        """Create prompt for LLM"""
        metadata = escalation_input.metadata

        prompt = f"""You are an expert customer support escalation analyst. Your task is to determine whether a customer support case should be escalated to a specialized team based on the conversation and company escalation policies.

CONVERSATION:
{conversation_text}

CASE METADATA:
- Case ID: {metadata.case_id}
- Prior Contact Count: {metadata.prior_contact_count}
- Initial Category: {metadata.initial_category or "Unknown"}

{policy_context}

INSTRUCTIONS:
1. Analyze the conversation to understand:
   - The customer's issue and needs
   - The sentiment and urgency
   - Any explicit escalation requests
   - Technical complexity
   - Financial implications

2. Evaluate which policies apply to this case

3. Make a decision: ESCALATE or NO_ESCALATE

4. If escalating, determine the most appropriate target team

5. Provide clear reasoning citing specific policies

OUTPUT FORMAT (respond in valid JSON):
{{
  "decision": "escalate" or "no_escalate",
  "confidence": <float between 0 and 1>,
  "target_team": "<team name>" or null,
  "reasoning": "<detailed explanation>",
  "policy_ids": ["POLICY-XXX", ...],
  "extracted_info": {{
    "issue_type": "<type>",
    "sentiment": "<sentiment>",
    "urgency": "<low/medium/high>",
    "keywords": ["<keyword1>", "<keyword2>"],
    "detected_amount": <float or null>
  }}
}}

IMPORTANT:
- Always cite policy IDs that support your decision
- If confidence is below 0.6, set target_team to "Human Review Queue"
- Be conservative: when in doubt about high-risk issues (fraud, legal, security), escalate
- Consider the context: repeated contacts increase escalation likelihood

Analyze the case and provide your decision:"""

        return prompt

    def _call_llm(self, prompt: str) -> str:
        """Call Anthropic Claude API"""
        try:
            message = self.client.chat.completions.create(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return message.choices[0].message.content
        except Exception as e:
            print(f"Error calling LLM: {e}")
            return self._fallback_response()

    def _mock_llm_response(
        self,
        escalation_input: EscalationInput,
        relevant_policies: List[Tuple]
    ) -> str:
        """Generate mock response for testing without API key"""
        # Simple rule-based mock
        metadata = escalation_input.metadata

        if metadata.prior_contact_count >= 3:
            return json.dumps({
                "decision": "escalate",
                "confidence": 0.9,
                "target_team": "Senior Support",
                "reasoning": "Customer has contacted 3+ times. According to POLICY-001, this should be escalated to Senior Support.",
                "policy_ids": ["POLICY-001"],
                "extracted_info": {
                    "issue_type": "unresolved",
                    "sentiment": "frustrated",
                    "urgency": "high",
                    "keywords": ["third time", "still not resolved"],
                    "detected_amount": None
                }
            })
        elif relevant_policies and relevant_policies[0][0].priority == "critical":
            policy = relevant_policies[0][0]
            return json.dumps({
                "decision": "escalate",
                "confidence": 0.95,
                "target_team": policy.target_team,
                "reasoning": f"Critical issue detected. Policy {policy.id} requires immediate escalation.",
                "policy_ids": [policy.id],
                "extracted_info": {
                    "issue_type": "critical",
                    "sentiment": "concerned",
                    "urgency": "critical",
                    "keywords": [],
                    "detected_amount": None
                }
            })
        else:
            return json.dumps({
                "decision": "no_escalate",
                "confidence": 0.85,
                "target_team": None,
                "reasoning": "Simple inquiry that can be handled by automated systems.",
                "policy_ids": [],
                "extracted_info": {
                    "issue_type": "simple_inquiry",
                    "sentiment": "neutral",
                    "urgency": "low",
                    "keywords": [],
                    "detected_amount": None
                }
            })

    def _fallback_response(self) -> str:
        """Fallback response if LLM fails"""
        return json.dumps({
            "decision": "escalate",
            "confidence": 0.5,
            "target_team": "Human Review Queue",
            "reasoning": "Unable to make automated decision. Routing to human review.",
            "policy_ids": [],
            "extracted_info": {
                "issue_type": "unknown",
                "sentiment": "unknown",
                "urgency": "medium",
                "keywords": [],
                "detected_amount": None
            }
        })

    def _parse_llm_response(
        self,
        llm_response: str,
        relevant_policies: List[Tuple]
    ) -> EscalationOutput:
        """Parse LLM JSON response into EscalationOutput"""
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', llm_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON object directly
                json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    raise ValueError("No JSON found in response")

            data = json.loads(json_str)

            # Build policy citations
            policy_citations = []
            for policy_id in data.get("policy_ids", []):
                policy = self.policy_retriever.get_policy_by_id(policy_id)
                policy_citations.append(PolicyCitation(
                    policy_id=policy_id,
                    rule_text=policy.description
                ))

            # Build extracted info
            extracted_info_data = data.get("extracted_info", {})
            extracted_info = ExtractedInfo(**extracted_info_data) if extracted_info_data else None

            # Check for low confidence
            confidence = data.get("confidence", 0.5)
            flag = None
            if confidence < 0.6:
                flag = "low_confidence"
                if data.get("decision") == "no_escalate":
                    # Override to escalate for human review
                    data["decision"] = "escalate"
                    data["target_team"] = "Human Review Queue"
                    data["reasoning"] += " [Low confidence - routing to human review]"

            return EscalationOutput(
                decision=DecisionType(data.get("decision", "escalate")),
                confidence=confidence,
                target_team=data.get("target_team"),
                reasoning=data.get("reasoning", "No reasoning provided"),
                policy_citations=policy_citations,
                extracted_info=extracted_info,
                flag=flag
            )

        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            print(f"Response was: {llm_response}")
            # Return safe fallback
            return EscalationOutput(
                decision=DecisionType.ESCALATE,
                confidence=0.5,
                target_team="Human Review Queue",
                reasoning="Error processing automated decision. Routing to human review for safety.",
                policy_citations=[],
                flag="error"
            )

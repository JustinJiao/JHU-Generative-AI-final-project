"""
Intelligent metadata extraction from conversation
"""
import os
import json
import re
from typing import List, Dict, Optional
from openai import OpenAI
from models import Message


class MetadataExtractor:
    """Extract case metadata from conversation using LLM"""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model

        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None
            print("Warning: No API key for metadata extraction. Using rule-based extraction.")

    def extract_metadata(self, messages: List[Message]) -> Dict[str, any]:
        """
        Extract metadata from conversation

        Returns:
            {
                "prior_contact_count": int,
                "issue_category": str,
                "estimated_severity": str,
                "extracted_keywords": List[str]
            }
        """
        conversation_text = self._format_conversation(messages)

        if self.client:
            return self._extract_with_llm(conversation_text)
        else:
            return self._extract_with_rules(conversation_text, messages)

    def _format_conversation(self, messages: List[Message]) -> str:
        """Format messages into readable text"""
        lines = []
        for msg in messages:
            role = "Customer" if msg.role.value == "customer" else "Agent"
            lines.append(f"{role}: {msg.content}")
        return "\n".join(lines)

    def _extract_with_llm(self, conversation_text: str) -> Dict[str, any]:
        """Use LLM to extract metadata"""
        prompt = f"""Analyze this customer support conversation and extract metadata.

CONVERSATION:
{conversation_text}

Extract the following information:

1. Prior Contact Count: How many times has the customer mentioned contacting support before?
   - Look for phrases like "third time", "contacted again", "called yesterday", etc.
   - If not mentioned, estimate based on context (0 = first time, likely)

2. Issue Category: What type of issue is this?
   - Options: billing, technical, shipping, account, general, security, legal, privacy

3. Estimated Severity: How severe is this issue?
   - Options: low, medium, high, critical

4. Keywords: List important keywords that indicate the issue type

Respond in JSON format:
{{
  "prior_contact_count": <number>,
  "issue_category": "<category>",
  "estimated_severity": "<severity>",
  "extracted_keywords": ["keyword1", "keyword2"],
  "reasoning": "<brief explanation>"
}}"""

        try:
            message = self.client.chat.completions.create(
                model=self.model,
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.choices[0].message.content

            # Extract JSON from response
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                json_str = json_match.group(0) if json_match else "{}"

            metadata = json.loads(json_str)
            return metadata

        except Exception as e:
            print(f"Error extracting metadata with LLM: {e}")
            return self._extract_with_rules(conversation_text, [])

    def _extract_with_rules(self, conversation_text: str, messages: List[Message]) -> Dict[str, any]:
        """Rule-based metadata extraction (fallback)"""
        conversation_lower = conversation_text.lower()

        # Extract prior contact count
        prior_contact_count = self._extract_contact_count(conversation_lower)

        # Extract category
        issue_category = self._extract_category(conversation_lower)

        # Estimate severity
        estimated_severity = self._estimate_severity(conversation_lower)

        # Extract keywords
        extracted_keywords = self._extract_keywords(conversation_lower)

        return {
            "prior_contact_count": prior_contact_count,
            "issue_category": issue_category,
            "estimated_severity": estimated_severity,
            "extracted_keywords": extracted_keywords,
            "reasoning": "Extracted using rule-based analysis"
        }

    def _extract_contact_count(self, text: str) -> int:
        """Extract how many times customer contacted support"""
        # Look for explicit mentions
        patterns = [
            (r'third time', 3),
            (r'3rd time', 3),
            (r'fourth time', 4),
            (r'4th time', 4),
            (r'second time', 2),
            (r'2nd time', 2),
            (r'again', 2),
            (r'called yesterday', 2),
            (r'contacted before', 2),
            (r'multiple times', 3),
            (r'several times', 3),
        ]

        for pattern, count in patterns:
            if pattern in text:
                return count

        # Default: first contact
        return 1

    def _extract_category(self, text: str) -> str:
        """Extract issue category"""
        category_keywords = {
            "billing": ["bill", "charge", "charged", "payment", "refund", "money", "invoice", "subscription"],
            "technical": ["bug", "crash", "error", "not working", "broken", "technical", "app", "software"],
            "shipping": ["order", "shipping", "delivery", "tracking", "arrive", "package"],
            "security": ["fraud", "hacked", "unauthorized", "security", "stolen", "scam"],
            "legal": ["lawyer", "attorney", "lawsuit", "legal", "sue", "court"],
            "account": ["password", "login", "account", "access", "username"],
            "privacy": ["gdpr", "privacy", "data", "personal information"],
        }

        # Count keyword matches
        scores = {}
        for category, keywords in category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                scores[category] = score

        if scores:
            return max(scores, key=scores.get)

        return "general"

    def _estimate_severity(self, text: str) -> str:
        """Estimate issue severity"""
        # Critical indicators
        critical_keywords = ["fraud", "hacked", "lawsuit", "emergency", "critical", "urgent"]
        if any(keyword in text for keyword in critical_keywords):
            return "critical"

        # High severity indicators
        high_keywords = ["third time", "unacceptable", "angry", "frustrated", "manager", "supervisor"]
        if any(keyword in text for keyword in high_keywords):
            return "high"

        # Medium severity indicators
        medium_keywords = ["again", "still", "problem", "issue", "concern"]
        if any(keyword in text for keyword in medium_keywords):
            return "medium"

        return "low"

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords"""
        important_patterns = [
            "fraud", "hacked", "unauthorized", "charged twice", "refund",
            "third time", "manager", "supervisor", "bug", "crash",
            "lawsuit", "lawyer", "password", "order"
        ]

        found_keywords = []
        for pattern in important_patterns:
            if pattern in text:
                found_keywords.append(pattern)

        return found_keywords[:5]  # Return top 5

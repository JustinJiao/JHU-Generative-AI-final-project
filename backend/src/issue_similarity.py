"""
Issue similarity detection module
Used to detect if the customer's current issue is similar to historical issues
"""
import os
from typing import List, Dict, Optional
from openai import OpenAI


class IssueSimilarityChecker:
    """Detects issue similarity"""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """
        Initialize the similarity checker

        Args:
            api_key: OpenAI API key (optional, priority: parameter > environment variable)
            model: OpenAI model name (default: gpt-4o-mini)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.use_llm = bool(self.api_key)

        if self.use_llm:
            self.client = OpenAI(api_key=self.api_key)
            print(f"✅ use OpenAI model: {self.model}")
        else:
            print("⚠️ API key not provided, similarity detection will use rule-based mode")

    def check_similarity(
        self,
        current_messages: List,
        past_issues: List[Dict]
    ) -> Dict:
        """
        Check if the current conversation issue is similar to historical issues

        Args:
            current_messages: Current conversation message list [{"role": "customer", "content": "..."}]
            past_issues: Historical issue list [{"issue_summary": "...", "issue_category": "..."}]

        Returns:
            {
                "is_similar": bool,  # Whether it's similar to historical issues
                "similar_count": int,  # Number of similar issues
                "matched_issues": List[Dict],  # Matched historical issues
                "current_issue_summary": str,  # Current issue summary
                "current_issue_category": str  # Current issue category
            }
        """
        if not past_issues:
            # No historical records, return current issue summary
            current_summary = self._summarize_current_issue(current_messages)
            return {
                "is_similar": False,
                "similar_count": 0,
                "matched_issues": [],
                "current_issue_summary": current_summary["summary"],
                "current_issue_category": current_summary["category"]
            }

        if self.use_llm:
            return self._llm_similarity_check(current_messages, past_issues)
        else:
            return self._rule_based_similarity_check(current_messages, past_issues)

    def _summarize_current_issue(self, messages: List) -> Dict:
        """
        Summarize the issue from the current conversation

        Returns:
            {"summary": str, "category": str}
        """
        if self.use_llm:
            try:
                # Build conversation text
                conversation_text = "\n".join([
                    f"[{msg.role}]: {msg.content}"
                    for msg in messages
                ])

                prompt = f"""Please summarize the customer's core issue from the following customer service conversation.

Conversation content:
{conversation_text}

Return in JSON format:
{{
  "summary": "Brief summary of the customer's issue (1-2 sentences)",
  "category": "Issue category (e.g., billing, technical, account, shipping, etc.)"
}}

Return only JSON, no other content."""

                response = self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=500,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )

                import json
                result = json.loads(response.choices[0].message.content)
                return result

            except Exception as e:
                print(f"Error summarizing issue with LLM: {e}")
                return self._rule_based_summary(messages)
        else:
            return self._rule_based_summary(messages)

    def _rule_based_summary(self, messages: List) -> Dict:
        """Rule-based issue summary"""
        # Get the customer's first message as the summary
        customer_messages = [msg.content for msg in messages if msg.role == "customer"]
        summary = customer_messages[0] if customer_messages else "Unknown issue"

        # Simple category detection
        text_lower = summary.lower()
        if any(word in text_lower for word in ["charge", "bill", "refund", "payment", "price"]):
            category = "billing"
        elif any(word in text_lower for word in ["login", "password", "account", "access"]):
            category = "account"
        elif any(word in text_lower for word in ["ship", "deliver", "order", "tracking"]):
            category = "shipping"
        elif any(word in text_lower for word in ["broken", "not work", "error", "bug"]):
            category = "technical"
        elif any(word in text_lower for word in ["fraud", "hack", "unauthorized", "security"]):
            category = "security"
        else:
            category = "general"

        return {"summary": summary[:200], "category": category}

    def _llm_similarity_check(
        self,
        current_messages: List,
        past_issues: List[Dict]
    ) -> Dict:
        """Use LLM to detect similarity"""
        try:
            # First summarize the current issue
            current_summary = self._summarize_current_issue(current_messages)

            # Build historical issues list
            past_issues_text = "\n".join([
                f"{i+1}. {issue['issue_summary']} (category: {issue['issue_category']})"
                for i, issue in enumerate(past_issues)
            ])

            prompt = f"""You are a customer service issue similarity detection expert.

Current customer issue:
Category: {current_summary['category']}
Summary: {current_summary['summary']}

This customer's historical issues:
{past_issues_text}

Please determine if the current issue is similar to any historical issue.
If the core concerns are the same or highly related, consider them similar.

Return in JSON format:
{{
  "is_similar": true/false,
  "similar_count": number of similar issues,
  "matched_issue_numbers": [matched historical issue numbers (starting from 1)],
  "reasoning": "reasoning for the judgment"
}}

Return only JSON, no other content."""

            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )

            import json
            result = json.loads(response.choices[0].message.content)

            # Build matched issues list
            matched_issues = []
            if result.get("matched_issue_numbers"):
                for num in result["matched_issue_numbers"]:
                    if 1 <= num <= len(past_issues):
                        matched_issues.append(past_issues[num - 1])

            return {
                "is_similar": result.get("is_similar", False),
                "similar_count": result.get("similar_count", 0),
                "matched_issues": matched_issues,
                "current_issue_summary": current_summary["summary"],
                "current_issue_category": current_summary["category"],
                "reasoning": result.get("reasoning", "")
            }

        except Exception as e:
            print(f"Error in LLM similarity check: {e}")
            return self._rule_based_similarity_check(current_messages, past_issues)

    def _rule_based_similarity_check(
        self,
        current_messages: List,
        past_issues: List[Dict]
    ) -> Dict:
        """Rule-based similarity detection (keyword matching)"""
        current_summary = self._rule_based_summary(current_messages)

        current_category = current_summary["category"]
        current_text = current_summary["summary"].lower()

        matched_issues = []
        for issue in past_issues:
            past_category = issue.get("issue_category", "").lower()
            past_summary = issue.get("issue_summary", "").lower()

            # Check if categories are the same
            if past_category == current_category:
                # Check keyword overlap
                current_words = set(current_text.split())
                past_words = set(past_summary.split())
                overlap = current_words & past_words

                # If there are more than 3 matching keywords, consider them similar
                if len(overlap) >= 3:
                    matched_issues.append(issue)

        return {
            "is_similar": len(matched_issues) > 0,
            "similar_count": len(matched_issues),
            "matched_issues": matched_issues,
            "current_issue_summary": current_summary["summary"],
            "current_issue_category": current_summary["category"]
        }

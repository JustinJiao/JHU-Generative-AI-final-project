"""
Policy retrieval and matching module
"""
import json
import re
from typing import List, Dict, Any, Tuple
from pathlib import Path
from models import EscalationInput, EscalationPolicy, PolicyDatabase


class PolicyRetriever:
    """Retrieves and matches relevant escalation policies"""

    def __init__(self, policy_file_path: str):
        """
        Initialize policy retriever

        Args:
            policy_file_path: Path to the escalation policies JSON file
        """
        self.policy_file_path = policy_file_path
        self.policies = self._load_policies()

    def _load_policies(self) -> PolicyDatabase:
        """Load policies from JSON file"""
        with open(self.policy_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return PolicyDatabase(**data)

    def retrieve_relevant_policies(
        self,
        escalation_input: EscalationInput,
        conversation_text: str = None
    ) -> List[Tuple[EscalationPolicy, float]]:
        """
        Retrieve policies relevant to the given input

        Args:
            escalation_input: Input data containing conversation and metadata
            conversation_text: Full conversation as a single string (optional)

        Returns:
            List of (policy, relevance_score) tuples, sorted by relevance
        """
        if conversation_text is None:
            conversation_text = self._format_conversation(escalation_input.messages)

        conversation_lower = conversation_text.lower()
        metadata = escalation_input.metadata

        relevant_policies = []

        for policy in self.policies.escalation_policies:
            score = self._calculate_relevance(
                policy,
                conversation_lower,
                metadata
            )
            if score > 0:
                relevant_policies.append((policy, score))

        # Sort by relevance score (descending) and priority
        priority_weights = {
            "critical": 4,
            "high": 3,
            "medium": 2,
            "low": 1
        }

        relevant_policies.sort(
            key=lambda x: (x[1], priority_weights.get(x[0].priority, 0)),
            reverse=True
        )

        return relevant_policies

    def _calculate_relevance(
        self,
        policy: EscalationPolicy,
        conversation_lower: str,
        metadata: Any
    ) -> float:
        """
        Calculate relevance score for a policy

        Args:
            policy: Policy to evaluate
            conversation_lower: Lowercased conversation text
            metadata: Case metadata

        Returns:
            Relevance score (0 if not relevant)
        """
        condition = policy.condition
        condition_type = condition.get("type")

        if condition_type == "keyword":
            return self._check_keyword_condition(condition, conversation_lower)

        elif condition_type == "metadata":
            return self._check_metadata_condition(condition, metadata)

        elif condition_type == "composite":
            return self._check_composite_condition(condition, conversation_lower, metadata)

        elif condition_type == "sentiment":
            # Simplified sentiment check based on keywords
            return self._check_sentiment_keywords(conversation_lower)

        return 0.0

    def _check_keyword_condition(self, condition: Dict, conversation_lower: str) -> float:
        """Check if keywords are present in conversation"""
        keywords = condition.get("keywords", [])
        match_type = condition.get("match_type", "any")

        matched_keywords = []
        for keyword in keywords:
            if keyword.lower() in conversation_lower:
                matched_keywords.append(keyword)

        if match_type == "any" and len(matched_keywords) > 0:
            # Score based on number of matches
            return min(1.0, len(matched_keywords) / len(keywords) + 0.5)

        elif match_type == "all" and len(matched_keywords) == len(keywords):
            return 1.0

        return 0.0

    def _check_metadata_condition(self, condition: Dict, metadata: Any) -> float:
        """Check if metadata meets condition"""
        field = condition.get("field")
        operator = condition.get("operator")
        value = condition.get("value")

        if not hasattr(metadata, field):
            return 0.0

        field_value = getattr(metadata, field)

        if operator == ">=":
            return 1.0 if field_value >= value else 0.0
        elif operator == ">":
            return 1.0 if field_value > value else 0.0
        elif operator == "<=":
            return 1.0 if field_value <= value else 0.0
        elif operator == "<":
            return 1.0 if field_value < value else 0.0
        elif operator == "==":
            return 1.0 if field_value == value else 0.0

        return 0.0

    def _check_composite_condition(
        self,
        condition: Dict,
        conversation_lower: str,
        metadata: Any
    ) -> float:
        """Check composite condition with multiple rules"""
        rules = condition.get("rules", [])
        logic = condition.get("logic", "AND")

        scores = []
        for rule in rules:
            rule_type = rule.get("type")

            if rule_type == "keyword":
                score = self._check_keyword_condition(rule, conversation_lower)
            elif rule_type == "metadata":
                score = self._check_metadata_condition(rule, metadata)
            elif rule_type == "sentiment":
                score = self._check_sentiment_keywords(conversation_lower)
            elif rule_type == "amount":
                # Extract amount from conversation
                score = self._check_amount_in_conversation(rule, conversation_lower)
            else:
                score = 0.0

            scores.append(score)

        if logic == "AND":
            # All rules must match
            return min(scores) if scores else 0.0
        elif logic == "OR":
            # At least one rule must match
            return max(scores) if scores else 0.0

        return 0.0

    def _check_sentiment_keywords(self, conversation_lower: str) -> float:
        """Check for sentiment indicators"""
        frustrated_keywords = [
            "angry", "frustrated", "disappointed", "upset", "ridiculous",
            "unacceptable", "terrible", "horrible", "worst", "disgusting"
        ]

        for keyword in frustrated_keywords:
            if keyword in conversation_lower:
                return 0.8

        return 0.0

    def _check_amount_in_conversation(self, rule: Dict, conversation_lower: str) -> float:
        """Extract and check monetary amounts in conversation"""
        # Simple regex to find amounts like $500, 500 dollars, etc.
        patterns = [
            r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*dollars?',
        ]

        amounts = []
        for pattern in patterns:
            matches = re.findall(pattern, conversation_lower)
            for match in matches:
                try:
                    amount = float(match.replace(',', ''))
                    amounts.append(amount)
                except ValueError:
                    continue

        if not amounts:
            return 0.0

        max_amount = max(amounts)
        operator = rule.get("operator")
        value = rule.get("value")

        if operator == ">":
            return 1.0 if max_amount > value else 0.0
        elif operator == ">=":
            return 1.0 if max_amount >= value else 0.0
        elif operator == "<":
            return 1.0 if max_amount < value else 0.0
        elif operator == "<=":
            return 1.0 if max_amount <= value else 0.0

        return 0.0

    def _format_conversation(self, messages: List[Any]) -> str:
        """Format messages into a single conversation string"""
        lines = []
        for msg in messages:
            lines.append(f"{msg.role.value}: {msg.content}")
        return "\n".join(lines)

    def get_policy_by_id(self, policy_id: str) -> EscalationPolicy:
        """Get a specific policy by ID"""
        for policy in self.policies.escalation_policies:
            if policy.id == policy_id:
                return policy
        return self.policies.default_policy

    def format_policies_for_llm(
        self,
        relevant_policies: List[Tuple[EscalationPolicy, float]]
    ) -> str:
        """
        Format relevant policies as text for LLM context

        Args:
            relevant_policies: List of (policy, score) tuples

        Returns:
            Formatted policy text
        """
        if not relevant_policies:
            return "No specific policies matched. Use general judgment."

        lines = ["RELEVANT ESCALATION POLICIES:\n"]

        for i, (policy, score) in enumerate(relevant_policies[:5], 1):  # Top 5
            lines.append(f"{i}. {policy.id} - {policy.name}")
            lines.append(f"   Priority: {policy.priority}")
            lines.append(f"   Action: {policy.action}")
            if policy.target_team:
                lines.append(f"   Target Team: {policy.target_team}")
            lines.append(f"   Description: {policy.description}")
            lines.append(f"   Relevance: {score:.2f}\n")

        return "\n".join(lines)

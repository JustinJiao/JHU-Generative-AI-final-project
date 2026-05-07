"""
Real-time conversation monitoring and escalation
Real-time conversation monitoring and escalation decision system
"""
import os
from typing import List, Dict, Optional
from datetime import datetime
from models import Message, EscalationInput, CaseMetadata
from metadata_extractor import MetadataExtractor
from policy_retriever import PolicyRetriever
from decision_engine import DecisionEngine
from database import Database
from issue_similarity import IssueSimilarityChecker


class ConversationMonitor:
    """
    Real-time monitoring of conversations between users and AI customer service
    Automatically triggers human intervention when escalation conditions are met
    """

    def __init__(
        self,
        policy_file: str,
        api_key: Optional[str] = None,
        db_path: Optional[str] = None
    ):
        """
        Initialize the conversation monitor

        Args:
            policy_file: Policy file path
            api_key: Anthropic API key (optional)
            db_path: Database file path
        """
        self.metadata_extractor = MetadataExtractor(api_key=api_key)
        self.policy_retriever = PolicyRetriever(policy_file)
        self.decision_engine = DecisionEngine(
            self.policy_retriever,
            api_key=api_key
        )
        self.similarity_checker = IssueSimilarityChecker(api_key=api_key)

        # Database (use None to auto-detect project root)
        self.db = Database(db_path) if db_path else Database()

        # Conversation state storage
        self.active_conversations: Dict[str, ConversationState] = {}

    def start_conversation(self, conversation_id: str, customer_id: str = None):
        """
        Start a new conversation

        Args:
            conversation_id: Unique conversation ID
            customer_id: Customer ID (optional, used for querying history)
        """
        # Get customer history information from database
        prior_contact_count = 0
        past_issues = []
        if customer_id:
            prior_contact_count = self.db.get_customer_history_count(customer_id)
            past_issues = self.db.get_customer_past_issues(customer_id)
            print(f"📊 Customer {customer_id} prior contact count: {prior_contact_count}, historical issues: {len(past_issues)}")

        self.active_conversations[conversation_id] = ConversationState(
            conversation_id=conversation_id,
            customer_id=customer_id,
            messages=[],
            started_at=datetime.now(),
            prior_contact_count=prior_contact_count,
            past_issues=past_issues
        )

        # Save to database
        self.db.create_conversation(conversation_id, customer_id or "UNKNOWN")

        print(f"✅ New conversation started: {conversation_id}")

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str
    ) -> Dict:
        """
        Add a new message and check if escalation is needed

        Args:
            conversation_id: Conversation ID
            role: "customer" or "agent"
            content: Message content

        Returns:
            {
                "should_escalate": bool,
                "decision": EscalationOutput (if escalation is needed),
                "continue_ai": bool
            }
        """
        if conversation_id not in self.active_conversations:
            raise ValueError(f"Conversation {conversation_id} does not exist, please call start_conversation() first")

        conv_state = self.active_conversations[conversation_id]

        # Add message
        message = Message(role=role, content=content)
        conv_state.messages.append(message)

        # Save to database
        self.db.add_message(conversation_id, role, content)

        print(f"📝 [{role}]: {content[:50]}...")

        # Check if escalation is needed after each message
        result = self._check_escalation(conversation_id)

        # If escalation occurs, record it to database
        if result.get("should_escalate") and result.get("decision"):
            decision = result["decision"]
            self.db.record_escalation(
                conversation_id=conversation_id,
                customer_id=conv_state.customer_id or "UNKNOWN",
                target_team=decision.target_team,
                reason=decision.reasoning,
                confidence=decision.confidence,
                policy_ids=[c.policy_id for c in decision.policy_citations]
            )

            # Add extracted information for frontend display
            result["decision"].extracted_info = {
                "prior_contact_count": conv_state.prior_contact_count,
                "customer_id": conv_state.customer_id
            }

        return result

    def _check_escalation(self, conversation_id: str) -> Dict:
        """
        Check if the current conversation needs escalation

        Returns:
            {
                "should_escalate": bool,
                "decision": EscalationOutput,
                "reason": str,
                "continue_ai": bool
            }
        """
        conv_state = self.active_conversations[conversation_id]

        # If too few messages, don't evaluate
        if len(conv_state.messages) < 2:
            return {
                "should_escalate": False,
                "continue_ai": True,
                "reason": "Conversation just started, continue AI conversation"
            }

        try:
            # 1. Extract metadata
            extracted_metadata = self.metadata_extractor.extract_metadata(
                conv_state.messages
            )

            # 2. Quick pre-check (rule-based) - inject prior_contact_count from database
            extracted_metadata["prior_contact_count"] = conv_state.prior_contact_count

            quick_check = self._quick_escalation_check(
                conv_state.messages,
                extracted_metadata
            )

            if quick_check["immediate_escalate"]:
                # Emergency situation, escalate immediately
                print(f"⚠️ Emergency detected: {quick_check['reason']}")
                return self._perform_full_analysis(
                    conversation_id,
                    extracted_metadata,
                    quick_check
                )

            # 3. Detect repeated issues (core logic!)
            if conv_state.past_issues and len(conv_state.messages) >= 4:  # Detect after at least 4 messages
                print(f"🔍 Detecting repeated issues (message count: {len(conv_state.messages)})")
                similarity_result = self.similarity_checker.check_similarity(
                    conv_state.messages,
                    conv_state.past_issues
                )

                # If similar issues detected >= 2 times (plus current makes 3 times)
                if similarity_result["is_similar"] and similarity_result["similar_count"] >= 2:
                    print(f"🚨 Repeated issue detected! Similar historical issues: {similarity_result['similar_count']}")
                    print(f"   Current issue: {similarity_result['current_issue_summary'][:100]}")

                    # Build detailed reason explanation
                    matched_summaries = [issue['issue_summary'][:80] for issue in similarity_result.get('matched_issues', [])]
                    reason_detail = f"Repeated issue detection: Customer contacted about the same issue for the {similarity_result['similar_count'] + 1}th time.\n"
                    reason_detail += f"Current issue: {similarity_result['current_issue_summary']}\n"
                    reason_detail += f"Historical similar issues ({len(matched_summaries)} times):\n"
                    for i, summary in enumerate(matched_summaries, 1):
                        reason_detail += f"  {i}. {summary}...\n"
                    reason_detail += f"Recommendation: Since the customer has contacted multiple times about the same unresolved issue, recommend escalation to human customer service for in-depth handling."

                    # Escalate immediately
                    return self._perform_full_analysis(
                        conversation_id,
                        extracted_metadata,
                        {"immediate_escalate": True, "reason": reason_detail}
                    )

            # 4. Perform full analysis every N messages (reduce frequency to avoid over-detection)
            if len(conv_state.messages) % 5 == 0:  # Analyze every 5 messages
                print(f"🔍 Performing full analysis (message count: {len(conv_state.messages)})")
                return self._perform_full_analysis(
                    conversation_id,
                    extracted_metadata
                )

            # Otherwise continue AI conversation
            return {
                "should_escalate": False,
                "continue_ai": True,
                "reason": "No escalation signal detected, continue AI conversation"
            }

        except Exception as e:
            print(f"❌ Analysis error: {e}")
            return {
                "should_escalate": False,
                "continue_ai": True,
                "error": str(e)
            }

    def _quick_escalation_check(
        self,
        messages: List[Message],
        metadata: Dict
    ) -> Dict:
        """
        Quick check for obvious escalation signals

        Returns:
            {
                "immediate_escalate": bool,
                "reason": str
            }
        """
        conversation_text = " ".join([msg.content.lower() for msg in messages])

        # Critical keywords
        critical_keywords = {
            "fraud": "Fraud keyword detected",
            "hacked": "Account hacked detected",
            "lawsuit": "Legal threat detected",
            "lawyer": "Customer mentioned lawyer",
            "sue": "Customer threatened lawsuit",
            "manager": "Customer requested manager",
            "supervisor": "Customer requested supervisor",
            "emergency": "Emergency situation",
            "urgent": "Urgent situation"
        }

        for keyword, reason in critical_keywords.items():
            if keyword in conversation_text:
                return {
                    "immediate_escalate": True,
                    "reason": reason,
                    "keyword": keyword
                }

        # Check for high-value refund (POLICY-003)
        refund_keywords = ["refund", "money back", "charge back"]
        has_refund_keyword = any(keyword in conversation_text for keyword in refund_keywords)

        if has_refund_keyword:
            # Extract dollar amounts from conversation
            import re
            amounts = re.findall(r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)', " ".join([msg.content for msg in messages]))
            if amounts:
                max_amount = max([float(a.replace(',', '')) for a in amounts])
                if max_amount > 500:
                    return {
                        "immediate_escalate": True,
                        "reason": f"High-value refund request detected (${max_amount:.2f})",
                        "keyword": "high_value_refund"
                    }

        # Note: No longer checking prior_contact_count, because the current logic is:
        # One complete conversation = one contact, not 3 messages = 3 contacts
        # Repeated issue detection will be done through similarity analysis in _check_escalation

        return {
            "immediate_escalate": False,
            "reason": "No obvious escalation signal"
        }

    def _perform_full_analysis(
        self,
        conversation_id: str,
        extracted_metadata: Dict,
        quick_check: Dict = None
    ) -> Dict:
        """
        Perform full LLM analysis

        Returns:
            {
                "should_escalate": bool,
                "decision": EscalationOutput,
                "reason": str,
                "continue_ai": bool
            }
        """
        conv_state = self.active_conversations[conversation_id]

        # If quick_check indicates immediate escalation (e.g., repeated issue detection), use preset detailed reason
        if quick_check and quick_check.get("immediate_escalate"):
            detailed_reason = quick_check.get("reason", "Emergency detected, escalation needed")

            print(f"🚨 Immediate escalation: {detailed_reason.split('.')[0]}...")

            # Still call LLM to get full decision, but prioritize preset reason
            metadata = CaseMetadata(
                case_id=conversation_id,
                customer_id=conv_state.customer_id or "UNKNOWN",
                prior_contact_count=conv_state.prior_contact_count,
                initial_category=extracted_metadata.get("issue_category", "general")
            )

            escalation_input = EscalationInput(
                messages=conv_state.messages,
                metadata=metadata
            )

            decision = self.decision_engine.make_decision(escalation_input)

            # Replace LLM's reasoning with preset detailed reason
            decision.reasoning = detailed_reason

            # Mark conversation state
            conv_state.escalated = True
            conv_state.escalation_reason = detailed_reason
            conv_state.target_team = decision.target_team or "Customer Support"

            return {
                "should_escalate": True,
                "decision": decision,
                "reason": detailed_reason,
                "continue_ai": False,
                "target_team": decision.target_team or "Customer Support"
            }

        # Otherwise perform normal LLM analysis
        metadata = CaseMetadata(
            case_id=conversation_id,
            customer_id=conv_state.customer_id or "UNKNOWN",
            prior_contact_count=conv_state.prior_contact_count,  # Use database value
            initial_category=extracted_metadata.get("issue_category", "general")
        )

        # Build input
        escalation_input = EscalationInput(
            messages=conv_state.messages,
            metadata=metadata
        )

        # LLM decision
        decision = self.decision_engine.make_decision(escalation_input)

        # Determine if escalation is needed
        should_escalate = (decision.decision.value == "escalate")

        if should_escalate:
            print(f"🚨 Decided to escalate to: {decision.target_team}")
            print(f"📋 Reason: {decision.reasoning}")

            # Mark conversation state
            conv_state.escalated = True
            conv_state.escalation_reason = decision.reasoning
            conv_state.target_team = decision.target_team

        return {
            "should_escalate": should_escalate,
            "decision": decision,
            "reason": decision.reasoning,
            "continue_ai": not should_escalate,
            "target_team": decision.target_team if should_escalate else None
        }

    def end_conversation(self, conversation_id: str):
        """End conversation and cleanup"""
        if conversation_id in self.active_conversations:
            conv_state = self.active_conversations[conversation_id]

            # Generate issue summary (for next similarity detection)
            issue_summary = None
            issue_category = None
            if conv_state.messages:
                try:
                    summary_result = self.similarity_checker.check_similarity(
                        conv_state.messages,
                        []  # Empty list, just to get current issue summary
                    )
                    issue_summary = summary_result.get("current_issue_summary")
                    issue_category = summary_result.get("current_issue_category")
                    print(f"📝 Issue summary: {issue_summary[:80] if issue_summary else 'N/A'}...")
                    print(f"📂 Issue category: {issue_category}")
                except Exception as e:
                    print(f"⚠️ Unable to generate issue summary: {e}")

            # Save to database
            self.db.end_conversation(
                conversation_id=conversation_id,
                escalated=conv_state.escalated,
                escalation_reason=conv_state.escalation_reason,
                target_team=conv_state.target_team,
                issue_summary=issue_summary,
                issue_category=issue_category
            )

            print(f"✅ Conversation ended: {conversation_id}")
            print(f"   Message count: {len(conv_state.messages)}")
            print(f"   Escalated: {conv_state.escalated}")
            del self.active_conversations[conversation_id]

    def get_conversation_summary(self, conversation_id: str) -> Dict:
        """Get conversation summary"""
        if conversation_id not in self.active_conversations:
            return {"error": "Conversation does not exist"}

        conv_state = self.active_conversations[conversation_id]
        return {
            "conversation_id": conversation_id,
            "customer_id": conv_state.customer_id,
            "message_count": len(conv_state.messages),
            "started_at": conv_state.started_at.isoformat(),
            "escalated": conv_state.escalated,
            "escalation_reason": conv_state.escalation_reason,
            "target_team": conv_state.target_team
        }


class ConversationState:
    """Conversation state"""

    def __init__(
        self,
        conversation_id: str,
        customer_id: str,
        messages: List[Message],
        started_at: datetime,
        prior_contact_count: int = 0,
        past_issues: List[Dict] = None
    ):
        self.conversation_id = conversation_id
        self.customer_id = customer_id
        self.messages = messages
        self.started_at = started_at
        self.prior_contact_count = prior_contact_count
        self.past_issues = past_issues or []  # Customer's historical issues list

        # Escalation state
        self.escalated = False
        self.escalation_reason = None
        self.target_team = None

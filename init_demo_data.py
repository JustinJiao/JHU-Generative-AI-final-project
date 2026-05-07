#!/usr/bin/env python3
"""
Initialize demo data for the Customer Support Escalation System
Creates sample customers and conversation history for testing
"""
import sys
import os
from pathlib import Path

# Add backend/src to path
backend_src = Path(__file__).parent / "backend" / "src"
sys.path.insert(0, str(backend_src))

from database import Database


def init_demo_data():
    """Initialize demo customers and conversation history"""
    print("=" * 60)
    print("Initializing Demo Data")
    print("=" * 60)
    print()

    # Delete existing database to ensure clean start
    db_path = "escalation.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"🗑️  Removed existing database")
        print()

    # Initialize database
    db = Database(db_path)

    # Demo customers with history
    demo_customers = [
        {
            "customer_id": "DEMO-CUSTOMER",
            "notes": "Demo customer for testing repeat issues"
        },
        {
            "customer_id": "VIP-001",
            "notes": "VIP customer with high priority"
        },
        {
            "customer_id": "CUST-123",
            "notes": "Regular customer"
        },
        {
            "customer_id": "CUST-456",
            "notes": "New customer"
        }
    ]

    print("📝 Creating demo customers...")
    for customer in demo_customers:
        db.create_customer(
            customer_id=customer["customer_id"],
            notes=customer.get("notes")
        )
        print(f"   ✅ Created: {customer['customer_id']}")

    print()
    print("📚 Creating sample conversation history...")

    # Sample conversation history for DEMO-CUSTOMER
    demo_conversations = [
        {
            "conversation_id": "CONV-DEMO-001",
            "customer_id": "DEMO-CUSTOMER",
            "messages": [
                {"role": "customer", "content": "My account was charged twice for the same order"},
                {"role": "agent", "content": "I apologize for the inconvenience. Let me check your account."},
                {"role": "customer", "content": "I've been waiting for 3 days now"},
                {"role": "agent", "content": "I understand your frustration. I'll escalate this to our billing team."}
            ],
            "issue_summary": "Double charge on order - billing issue",
            "issue_category": "billing",
            "escalated": True,
            "escalation_reason": "Billing error with delayed resolution",
            "target_team": "Billing Team"
        },
        {
            "conversation_id": "CONV-DEMO-002",
            "customer_id": "DEMO-CUSTOMER",
            "messages": [
                {"role": "customer", "content": "I'm still seeing the duplicate charge from last week"},
                {"role": "agent", "content": "Let me look into this for you."},
                {"role": "customer", "content": "This is the second time I'm contacting about this"},
                {"role": "agent", "content": "I sincerely apologize. Let me get a supervisor to help."}
            ],
            "issue_summary": "Follow-up on duplicate charge - still unresolved",
            "issue_category": "billing",
            "escalated": True,
            "escalation_reason": "Repeat issue - second contact about same problem",
            "target_team": "Senior Support"
        }
    ]

    for conv in demo_conversations:
        # Create conversation
        db.create_conversation(conv["conversation_id"], conv["customer_id"])

        # Add messages
        for msg in conv["messages"]:
            db.add_message(conv["conversation_id"], msg["role"], msg["content"])

        # End conversation with metadata
        db.end_conversation(
            conversation_id=conv["conversation_id"],
            escalated=conv["escalated"],
            escalation_reason=conv["escalation_reason"],
            target_team=conv["target_team"],
            issue_summary=conv["issue_summary"],
            issue_category=conv["issue_category"]
        )

        print(f"   ✅ Created conversation: {conv['conversation_id']}")

    # Create some history for VIP customer
    vip_conversation = {
        "conversation_id": "CONV-VIP-001",
        "customer_id": "VIP-001",
        "messages": [
            {"role": "customer", "content": "I need help with my premium account setup"},
            {"role": "agent", "content": "Of course! I'll assist you right away."}
        ],
        "issue_summary": "Premium account setup assistance",
        "issue_category": "account",
        "escalated": False,
        "escalation_reason": None,
        "target_team": None
    }

    db.create_conversation(vip_conversation["conversation_id"], vip_conversation["customer_id"])
    for msg in vip_conversation["messages"]:
        db.add_message(vip_conversation["conversation_id"], msg["role"], msg["content"])
    db.end_conversation(
        conversation_id=vip_conversation["conversation_id"],
        escalated=vip_conversation["escalated"],
        escalation_reason=vip_conversation["escalation_reason"],
        target_team=vip_conversation["target_team"],
        issue_summary=vip_conversation["issue_summary"],
        issue_category=vip_conversation["issue_category"]
    )
    print(f"   ✅ Created conversation: {vip_conversation['conversation_id']}")

    print()
    print("=" * 60)
    print("✅ Demo Data Initialization Complete!")
    print("=" * 60)
    print()
    print("Demo customers created:")
    print("  • DEMO-CUSTOMER (has 2 previous billing issues)")
    print("  • VIP-001 (has 1 previous interaction)")
    print("  • CUST-123 (regular customer)")
    print("  • CUST-456 (new customer)")
    print()
    print("You can now test:")
    print("  1. Real-time Monitor: Use 'DEMO-CUSTOMER' to see repeat issue detection")
    print("  2. Real-time Monitor: Use 'VIP-001' for VIP customer handling")
    print("  3. Interactive Demo: Pre-configured scenarios")
    print()


if __name__ == "__main__":
    try:
        init_demo_data()
    except Exception as e:
        print(f"❌ Error initializing demo data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

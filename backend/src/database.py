"""
SQLite database for storing conversation history and customer information
"""
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
import json


class Database:
    """Lightweight SQLite database"""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database

        Args:
            db_path: Path to database file. If None, uses escalation.db in project root
        """
        if db_path is None:
            # Get project root (two levels up from backend/src)
            project_root = Path(__file__).parent.parent.parent
            db_path = str(project_root / "escalation.db")

        self.db_path = db_path
        self._init_database()

    def _get_connection(self):
        """Get database connection (with timeout and WAL mode)"""
        conn = sqlite3.connect(self.db_path, timeout=30.0, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_database(self):
        """Create database tables"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL")  # Enable WAL mode for better concurrency
        cursor = conn.cursor()

        # Customer table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                customer_id TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_conversations INTEGER DEFAULT 0,
                total_escalations INTEGER DEFAULT 0,
                last_contact_at TIMESTAMP,
                notes TEXT
            )
        ''')

        # Conversation table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                conversation_id TEXT PRIMARY KEY,
                customer_id TEXT,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ended_at TIMESTAMP,
                message_count INTEGER DEFAULT 0,
                issue_summary TEXT,
                issue_category TEXT,
                escalated BOOLEAN DEFAULT 0,
                escalation_reason TEXT,
                target_team TEXT,
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
            )
        ''')

        # Message table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT,
                role TEXT,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id)
            )
        ''')

        # Escalation records table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS escalation_records (
                record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT,
                customer_id TEXT,
                escalated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                target_team TEXT,
                reason TEXT,
                confidence REAL,
                policy_ids TEXT,
                FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id),
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
            )
        ''')

        conn.commit()
        conn.close()
        print(f"✅ Database initialization complete: {self.db_path}")

    # ==================== Customer Operations ====================

    def create_customer(self, customer_id: str, notes: str = None) -> bool:
        """Create new customer"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO customers (customer_id, notes)
                VALUES (?, ?)
            ''', (customer_id, notes))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Customer already exists
            return False
        finally:
            conn.close()

    def get_customer(self, customer_id: str) -> Optional[Dict]:
        """Get customer information"""
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM customers WHERE customer_id = ?
        ''', (customer_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def get_customer_history_count(self, customer_id: str) -> int:
        """Get customer historical contact count"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT total_conversations FROM customers WHERE customer_id = ?
        ''', (customer_id,))

        result = cursor.fetchone()
        conn.close()

        return result[0] if result else 0

    def get_customer_past_issues(self, customer_id: str) -> List[Dict]:
        """
        Get customer historical issue list (for similarity detection)

        Returns:
            List of {"issue_summary": str, "issue_category": str, "conversation_id": str, "ended_at": str}
        """
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT conversation_id, issue_summary, issue_category, ended_at
            FROM conversations
            WHERE customer_id = ? AND ended_at IS NOT NULL AND issue_summary IS NOT NULL
            ORDER BY ended_at DESC
        ''', (customer_id,))

        issues = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return issues

    def update_customer_stats(self, customer_id: str, conversation_ended: bool = False, escalated: bool = False):
        """Update customer statistics"""
        conn = self._get_connection()
        cursor = conn.cursor()

        if conversation_ended:
            cursor.execute('''
                UPDATE customers
                SET total_conversations = total_conversations + 1,
                    last_contact_at = CURRENT_TIMESTAMP
                WHERE customer_id = ?
            ''', (customer_id,))

        if escalated:
            cursor.execute('''
                UPDATE customers
                SET total_escalations = total_escalations + 1
                WHERE customer_id = ?
            ''', (customer_id,))

        conn.commit()
        conn.close()

    # ==================== Conversation Operations ====================

    def create_conversation(self, conversation_id: str, customer_id: str) -> bool:
        """Create new conversation"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Ensure customer exists
        self.create_customer(customer_id)

        try:
            cursor.execute('''
                INSERT INTO conversations (conversation_id, customer_id)
                VALUES (?, ?)
            ''', (conversation_id, customer_id))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def add_message(self, conversation_id: str, role: str, content: str):
        """Add message to conversation"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Add message
        cursor.execute('''
            INSERT INTO messages (conversation_id, role, content)
            VALUES (?, ?, ?)
        ''', (conversation_id, role, content))

        # Update conversation message count
        cursor.execute('''
            UPDATE conversations
            SET message_count = message_count + 1
            WHERE conversation_id = ?
        ''', (conversation_id,))

        conn.commit()
        conn.close()

    def get_conversation_messages(self, conversation_id: str) -> List[Dict]:
        """Get all messages for a conversation"""
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM messages
            WHERE conversation_id = ?
            ORDER BY created_at ASC
        ''', (conversation_id,))

        messages = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return messages

    def end_conversation(
        self,
        conversation_id: str,
        escalated: bool = False,
        escalation_reason: str = None,
        target_team: str = None,
        issue_summary: str = None,
        issue_category: str = None
    ):
        """End conversation"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE conversations
            SET ended_at = CURRENT_TIMESTAMP,
                escalated = ?,
                escalation_reason = ?,
                target_team = ?,
                issue_summary = ?,
                issue_category = ?
            WHERE conversation_id = ?
        ''', (1 if escalated else 0, escalation_reason, target_team, issue_summary, issue_category, conversation_id))

        # Get customer ID
        cursor.execute('''
            SELECT customer_id FROM conversations WHERE conversation_id = ?
        ''', (conversation_id,))
        result = cursor.fetchone()

        # Update customer stats in the same connection
        if result:
            customer_id = result[0]
            cursor.execute('''
                UPDATE customers
                SET total_conversations = total_conversations + 1,
                    last_contact_at = CURRENT_TIMESTAMP
                WHERE customer_id = ?
            ''', (customer_id,))

            if escalated:
                cursor.execute('''
                    UPDATE customers
                    SET total_escalations = total_escalations + 1
                    WHERE customer_id = ?
                ''', (customer_id,))

        conn.commit()
        conn.close()

    # ==================== Escalation Records ====================

    def record_escalation(
        self,
        conversation_id: str,
        customer_id: str,
        target_team: str,
        reason: str,
        confidence: float = None,
        policy_ids: List[str] = None
    ):
        """Record escalation decision"""
        conn = self._get_connection()
        cursor = conn.cursor()

        policy_ids_json = json.dumps(policy_ids) if policy_ids else None

        cursor.execute('''
            INSERT INTO escalation_records
            (conversation_id, customer_id, target_team, reason, confidence, policy_ids)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (conversation_id, customer_id, target_team, reason, confidence, policy_ids_json))

        conn.commit()
        conn.close()

    def get_customer_escalation_history(self, customer_id: str) -> List[Dict]:
        """Get customer's escalation history"""
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM escalation_records
            WHERE customer_id = ?
            ORDER BY escalated_at DESC
            LIMIT 10
        ''', (customer_id,))

        records = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return records

    # ==================== Statistics Queries ====================

    def get_escalation_stats(self) -> Dict:
        """Get escalation statistics"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Total conversations
        cursor.execute('SELECT COUNT(*) FROM conversations')
        total_conversations = cursor.fetchone()[0]

        # Escalated conversations
        cursor.execute('SELECT COUNT(*) FROM conversations WHERE escalated = 1')
        escalated_conversations = cursor.fetchone()[0]

        # Escalation rate
        escalation_rate = (escalated_conversations / total_conversations * 100) if total_conversations > 0 else 0

        # Team statistics
        cursor.execute('''
            SELECT target_team, COUNT(*) as count
            FROM escalation_records
            GROUP BY target_team
            ORDER BY count DESC
        ''')
        team_stats = [{"team": row[0], "count": row[1]} for row in cursor.fetchall()]

        conn.close()

        return {
            "total_conversations": total_conversations,
            "escalated_conversations": escalated_conversations,
            "escalation_rate": round(escalation_rate, 2),
            "team_stats": team_stats
        }

    def get_recent_conversations(self, limit: int = 10) -> List[Dict]:
        """Get recent conversations"""
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT c.*, cu.total_conversations as customer_total_contacts
            FROM conversations c
            LEFT JOIN customers cu ON c.customer_id = cu.customer_id
            ORDER BY c.started_at DESC
            LIMIT ?
        ''', (limit,))

        conversations = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return conversations

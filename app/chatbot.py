import streamlit as st
import logging
import re
from database import ComplianceDB

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# List of 50 question patterns (greetings + compliance queries)
QUESTION_PATTERNS = [
    # Greetings
    r"\b(hi|hello|hey|hai|good morning|good afternoon|good evening)\b",
    r"\bhow are you\b",
    r"\bwho are you\b",
    r"\bwhat can you do\b",
    r"\bhelp\b",
    r"\bhow can you help\b",
    r"\bthank you\b",
    r"\bthanks\b",
    r"\bbye\b",
    r"\bexit\b",
    # Compliance queries (examples)
    r"\btotal violations\b",
    r"\btotal checks\b",
    r"\bcompliance rate\b",
    r"\bshow compliance\b",
    r"\bshow violations\b",
    r"\bshow status\b",
    r"\bstatus\b",
    r"\bviolations today\b",
    r"\bviolations yesterday\b",
    r"\bviolations this week\b",
    r"\bviolations last week\b",
    r"\bcompliance today\b",
    r"\bcompliance yesterday\b",
    r"\bcompliance this week\b",
    r"\bcompliance last week\b",
    r"\bcritical violations\b",
    r"\bwarning violations\b",
    r"\bdepartment\b",
    r"\bmost common violation\b",
    r"\bleast compliant\b",
    r"\bmost compliant\b",
    r"\btrend\b",
    r"\bexport\b",
    r"\bdownload\b",
    r"\bsummary\b",
    r"\bmonthly report\b",
    r"\bweekly report\b",
    r"\bdaily report\b",
    r"\bshow logs\b",
    r"\bshow recent\b",
    r"\bshow analytics\b",
    r"\bshow dashboard\b",
    r"\bshow chart\b",
    r"\bshow graph\b",
    r"\bshow data\b",
    r"\bshow details\b",
    r"\bshow ppe\b",
    r"\bshow anomaly\b",
    r"\bshow non-compliant\b",
    r"\bshow compliant\b",
    r"\bshow critical\b",
    r"\bshow warning\b",
    r"\bshow helmet\b",
    r"\bshow gloves\b",
    r"\bshow mask\b",
    r"\bshow goggles\b",
    r"\bshow suit\b",
    r"\bshow shoes\b",
]

DEFAULT_ASSISTANT_MESSAGE = (
    "Hello! I'm your PPE compliance assistant. "
    "You can ask me about compliance rates, total violations, recent logs, or status. "
    "How can I help you today?"
)

def match_pattern(question):
    for pattern in QUESTION_PATTERNS:
        if re.search(pattern, question, re.IGNORECASE):
            return pattern
    return None

class PPEComplianceChatbot:
    def __init__(self):
        self.db = ComplianceDB()

    def query(self, question: str) -> dict:
        q = question.strip().lower()
        pattern = match_pattern(q)

        # Greetings and unrelated questions
        if pattern and re.search(r"\b(hi|hello|hey|hai|good morning|good afternoon|good evening|how are you|who are you|help|thank you|thanks|bye|exit)\b", q):
            return {
                'success': True,
                'answer': DEFAULT_ASSISTANT_MESSAGE,
                'type': 'assistant'
            }

        # Compliance queries
        try:
            with self.db._managed_cursor() as cur:
                # Total violations
                if "total violations" in q:
                    cur.execute("SELECT SUM(violations_count) FROM compliance_logs;")
                    total = cur.fetchone()[0] or 0
                    return {'success': True, 'answer': f"Total violations recorded: {total}.", 'type': 'db'}

                # Total checks
                if "total checks" in q:
                    cur.execute("SELECT COUNT(*) FROM compliance_logs;")
                    total = cur.fetchone()[0] or 0
                    return {'success': True, 'answer': f"Total compliance checks performed: {total}.", 'type': 'db'}

                # Compliance rate
                if "compliance rate" in q:
                    cur.execute("SELECT COUNT(*) FROM compliance_logs;")
                    total = cur.fetchone()[0] or 0
                    cur.execute("SELECT COUNT(*) FROM compliance_logs WHERE violations_count=0;")
                    compliant = cur.fetchone()[0] or 0
                    rate = (compliant / total * 100) if total else 0
                    return {'success': True, 'answer': f"Compliance rate is {rate:.2f}%.", 'type': 'db'}

                # Violations today
                if "violations today" in q:
                    cur.execute("SELECT SUM(violations_count) FROM compliance_logs WHERE DATE(timestamp) = CURRENT_DATE;")
                    total = cur.fetchone()[0] or 0
                    return {'success': True, 'answer': f"Violations detected today: {total}.", 'type': 'db'}

                # Violations yesterday
                if "violations yesterday" in q:
                    cur.execute("SELECT SUM(violations_count) FROM compliance_logs WHERE DATE(timestamp) = CURRENT_DATE - INTERVAL '1 day';")
                    total = cur.fetchone()[0] or 0
                    return {'success': True, 'answer': f"Violations detected yesterday: {total}.", 'type': 'db'}

                # Violations this week
                if "violations this week" in q:
                    cur.execute("SELECT SUM(violations_count) FROM compliance_logs WHERE DATE_TRUNC('week', timestamp) = DATE_TRUNC('week', CURRENT_DATE);")
                    total = cur.fetchone()[0] or 0
                    return {'success': True, 'answer': f"Violations detected this week: {total}.", 'type': 'db'}

                # Compliance today
                if "compliance today" in q:
                    cur.execute("SELECT COUNT(*) FROM compliance_logs WHERE DATE(timestamp) = CURRENT_DATE AND violations_count=0;")
                    compliant = cur.fetchone()[0] or 0
                    cur.execute("SELECT COUNT(*) FROM compliance_logs WHERE DATE(timestamp) = CURRENT_DATE;")
                    total = cur.fetchone()[0] or 0
                    rate = (compliant / total * 100) if total else 0
                    return {'success': True, 'answer': f"Compliance rate today is {rate:.2f}%.", 'type': 'db'}

                # Status (summary)
                if "status" in q or "show status" in q:
                    cur.execute("SELECT COUNT(*) FROM compliance_logs;")
                    total = cur.fetchone()[0] or 0
                    cur.execute("SELECT COUNT(*) FROM compliance_logs WHERE violations_count=0;")
                    compliant = cur.fetchone()[0] or 0
                    cur.execute("SELECT SUM(violations_count) FROM compliance_logs;")
                    violations = cur.fetchone()[0] or 0
                    return {
                        'success': True,
                        'answer': f"Total checks: {total}, Compliant: {compliant}, Violations: {violations}.",
                        'type': 'db'
                    }

                # Recent logs
                if "show logs" in q or "show recent" in q:
                    cur.execute("SELECT to_char(timestamp, 'YYYY-MM-DD HH24:MI'), violations_count FROM compliance_logs ORDER BY timestamp DESC LIMIT 5;")
                    rows = cur.fetchall()
                    if not rows:
                        return {'success': True, 'answer': "No recent logs found.", 'type': 'db'}
                    msg = "Recent compliance logs:\n"
                    for ts, v in rows:
                        msg += f"- {ts}: {v} violations\n"
                    return {'success': True, 'answer': msg, 'type': 'db'}

                # Default for other compliance queries
                if pattern:
                    return {
                        'success': True,
                        'answer': "I can provide compliance rates, total violations, and recent logs. Please specify your query.",
                        'type': 'assistant'
                    }

        except Exception as e:
            logger.exception("Database error in chatbot")
            return {
                'success': False,
                'answer': "Sorry, I couldn't fetch the data due to a system error.",
                'type': 'error'
            }

        # Fallback for unrelated questions
        return {
            'success': True,
            'answer': DEFAULT_ASSISTANT_MESSAGE,
            'type': 'assistant'
        }

# Singleton instance
_chatbot_instance = None

def get_chatbot_response(question: str) -> dict:
    global _chatbot_instance
    try:
        if _chatbot_instance is None:
            _chatbot_instance = PPEComplianceChatbot()
        response = _chatbot_instance.query(question)
        return response
    except Exception as e:
        logger.exception("System failure")
        return {
            'success': False,
            'answer': "System error. Notified support team.",
            'error': "Internal server error",
            'response_time': 0
        }

# Streamlit UI for chatbot

def main():
    st.title("💬 Intelliguard PPE Compliance Chatbot")
    st.write("""
**Welcome to Intelliguard!**

This AI assistant can help you:
- Query PPE compliance and violation data (e.g., "Show helmet violations this week", "Compliance rate for welding department")
- Get analytics on safety trends, department performance, and audit logs
- Understand model accuracy, face login, automation, and reporting features
- Learn about automated email alerts, CSV exports, and dashboard usage

*Ask your question below to get started!*""")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        st.session_state.chat_history.append({"role": "assistant", "content": "Hello! I'm your PPE compliance assistant. How can I help you today?"})
    # Only show last user-bot exchange
    last_user = None
    last_bot = None
    for i in range(len(st.session_state.chat_history) - 1, -1, -1):
        msg = st.session_state.chat_history[i]
        if last_bot is None and msg["role"] == "bot":
            last_bot = msg
        elif last_user is None and msg["role"] == "user":
            last_user = msg
        if last_user and last_bot:
            break
    if last_user:
        st.markdown(f"**You:** {last_user['content']}")
    if last_bot:
        st.markdown(f"**Intelliguard:** {last_bot['content']}")
    user_input = st.text_input("Type your question here...")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        response = get_chatbot_response(user_input)
        st.session_state.chat_history.append({"role": "bot", "content": response["answer"]})
        # Remove st.rerun() to prevent infinite rerun loop
        # st.rerun()

if __name__ == "__main__":
    main()
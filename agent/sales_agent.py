"""
agent/sales_agent.py
Core autonomous sales agent — orchestrates the full sales cycle.
"""
import os
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from services.gemini_ai import GeminiAI
from services.email_service import build_outreach_email, send_email
from services.whatsapp import send_whatsapp
from agent.decision_engine import DecisionEngine
from agent.action_executor import ActionExecutor

logger = logging.getLogger(__name__)

# Data file paths
DATA_DIR = Path(__file__).parent.parent / "data"
LEADS_FILE = DATA_DIR / "leads.json"
CONVERSATIONS_FILE = DATA_DIR / "conversations.json"
OUTCOMES_FILE = DATA_DIR / "outcomes.json"

# System prompt path
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
SYSTEM_PROMPT_FILE = PROMPTS_DIR / "sales_agent_prompt.txt"


def _load_json(filepath: Path, default) -> any:
    """Load JSON file, returning default if not found."""
    try:
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading {filepath}: {e}")
    return default


def _save_json(filepath: Path, data: any):
    """Save data to JSON file."""
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving {filepath}: {e}")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SalesAgent:
    """
    The core autonomous agent that runs the full sales cycle.
    Coordinates Gemini AI, DecisionEngine, and ActionExecutor.
    """

    def __init__(self):
        self.gemini = GeminiAI()
        self.decision_engine = DecisionEngine()
        self.executor = ActionExecutor()
        self._system_prompt = self._load_system_prompt()

        # Ensure data files exist
        self._init_data_files()

    def _load_system_prompt(self) -> str:
        """Load the sales agent system prompt from file."""
        try:
            with open(SYSTEM_PROMPT_FILE, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error loading system prompt: {e}")
            return "You are Paytm AI Sales Teammate, a helpful Paytm sales AI. Be friendly, speak Hinglish, keep messages short."

    def _init_data_files(self):
        """Create conversations.json and outcomes.json if they don't exist."""
        if not CONVERSATIONS_FILE.exists():
            _save_json(CONVERSATIONS_FILE, {})
        if not OUTCOMES_FILE.exists():
            _save_json(OUTCOMES_FILE, {})

    # ─── Lead Data Access ──────────────────────────────────────────────────────

    def _load_leads(self) -> list:
        return _load_json(LEADS_FILE, [])

    def _save_leads(self, leads: list):
        _save_json(LEADS_FILE, leads)

    def _get_lead_by_id(self, lead_id: str) -> dict | None:
        leads = self._load_leads()
        for lead in leads:
            if lead.get("id") == lead_id:
                return lead
        return None

    def _get_lead_by_phone(self, phone: str) -> dict | None:
        """Find a lead by phone number (normalizes formats)."""
        clean_phone = phone.replace("whatsapp:", "").replace(" ", "").replace("-", "")
        leads = self._load_leads()
        for lead in leads:
            lead_phone = lead.get("phone", "").replace(" ", "").replace("-", "")
            if lead_phone == clean_phone:
                return lead
        return None

    def _update_lead(self, updated_lead: dict):
        """Update a specific lead in the leads.json file."""
        leads = self._load_leads()
        for i, lead in enumerate(leads):
            if lead.get("id") == updated_lead.get("id"):
                leads[i] = updated_lead
                break
        self._save_leads(leads)

        # Also update outcomes
        outcomes = _load_json(OUTCOMES_FILE, {})
        outcomes[updated_lead["id"]] = {
            "id": updated_lead["id"],
            "name": updated_lead["name"],
            "business": updated_lead["business"],
            "status": updated_lead.get("status"),
            "qualification": updated_lead.get("qualification"),
            "last_contacted": updated_lead.get("last_contacted"),
            "follow_up_count": updated_lead.get("follow_up_count", 0),
            "conversation_turns": len(updated_lead.get("conversation_history", [])),
        }
        _save_json(OUTCOMES_FILE, outcomes)

    # ─── Core Agent Methods ────────────────────────────────────────────────────

    def initiate_outreach(self, lead_id: str) -> dict:
        """
        Start contact with a new lead — sends WhatsApp + Email.
        
        Returns:
            Dict with result details
        """
        lead = self._get_lead_by_id(lead_id)
        if not lead:
            logger.error(f"Lead {lead_id} not found")
            return {"success": False, "error": f"Lead {lead_id} not found"}

        if lead.get("status") not in ("new", "follow_up_scheduled"):
            logger.info(f"Lead {lead_id} already contacted (status: {lead.get('status')})")
            return {"success": False, "error": f"Lead already in status: {lead.get('status')}"}

        logger.info(f"Initiating outreach for {lead.get('name')} ({lead_id})")

        # 1. Generate personalized opening message via Gemini
        opening_message = self.gemini.generate_opening_message(lead, self._system_prompt)

        # 2. Send WhatsApp message
        wa_success = send_whatsapp(lead.get("phone", ""), opening_message)

        # 3. Send outreach email
        email_subject, email_body = build_outreach_email(lead)
        email_success = send_email(lead.get("email", ""), email_subject, email_body)

        # 4. Update lead
        if "conversation_history" not in lead:
            lead["conversation_history"] = []

        lead["conversation_history"].append({
            "role": "agent",
            "message": opening_message,
            "timestamp": _now(),
        })
        lead["status"] = "contacted"
        lead["last_contacted"] = _now()

        # 5. Save
        self._update_lead(lead)

        return {
            "success": True,
            "lead_id": lead_id,
            "lead_name": lead.get("name"),
            "whatsapp_sent": wa_success,
            "email_sent": email_success,
            "opening_message": opening_message,
        }

    def handle_reply(self, phone: str, message: str) -> dict:
        """
        Called when a merchant replies on WhatsApp.
        
        Args:
            phone: Merchant's phone number
            message: Their message text
            
        Returns:
            Dict with action taken and response sent
        """
        # 1. Find lead by phone
        lead = self._get_lead_by_phone(phone)
        if not lead:
            logger.warning(f"No lead found for phone: {phone}")
            # Send a generic helpful reply
            generic_reply = (
                "Namaste! Paytm Business Team se message hai. 😊\n"
                "Aapka number hamare system mein nahi hai abhi.\n"
                "Please paytm.com/business pe visit karein ya 1800-102-6480 pe call karein!"
            )
            send_whatsapp(phone, generic_reply)
            return {"success": False, "error": "Lead not found", "generic_reply_sent": True}

        logger.info(f"Handling reply from {lead.get('name')} ({lead.get('id')}): {message[:50]}...")

        # 2. Add merchant message to conversation history
        if "conversation_history" not in lead:
            lead["conversation_history"] = []

        lead["conversation_history"].append({
            "role": "merchant",
            "message": message,
            "timestamp": _now(),
        })

        # 3. Analyze the reply with Gemini
        ai_analysis = self.gemini.analyze_lead_response(message, lead)
        logger.info(f"AI Analysis for {lead.get('name')}: {ai_analysis}")

        # 4. Generate conversational reply via Gemini
        ai_reply = self.gemini.chat(
            system_prompt=self._system_prompt,
            conversation_history=lead["conversation_history"],
            user_message=message,
            lead=lead,
        )

        # 5. DecisionEngine decides next action
        action = self.decision_engine.decide_next_action(lead, ai_analysis)
        qualification = self.decision_engine.qualify_lead(lead, ai_analysis)

        logger.info(f"Decision for {lead.get('name')}: action={action}, qualification={qualification}")

        # 6. Update qualification
        lead["qualification"] = qualification

        # 7. ActionExecutor executes the action
        if action in ("send_product_info", "send_whatsapp_reply", "schedule_follow_up"):
            lead = self.executor.execute(action, lead, ai_reply)
        elif action == "send_demo_link":
            lead = self.executor.send_demo_link(lead)
        elif action == "escalate_to_human":
            lead = self.executor.escalate_to_human(lead)
        elif action == "close_won":
            lead = self.executor.close_lead(lead, "won")
        elif action == "close_lost":
            lead = self.executor.close_lead(lead, "lost")
        else:
            # Default: send AI reply
            lead = self.executor.send_product_info(lead, ai_reply)

        # 8. Save everything
        self._update_lead(lead)

        return {
            "success": True,
            "lead_id": lead.get("id"),
            "lead_name": lead.get("name"),
            "merchant_message": message,
            "action_taken": action,
            "qualification": qualification,
            "ai_analysis": ai_analysis,
        }

    def run_follow_ups(self) -> dict:
        """
        Check all leads and send follow-ups for those that are due.
        Called manually via API or could be scheduled via cron.
        
        Returns:
            Summary dict with counts
        """
        leads = self._load_leads()
        now = datetime.now(timezone.utc)
        results = {
            "checked": 0,
            "follow_ups_sent": 0,
            "leads_closed": 0,
            "errors": 0,
        }

        for lead in leads:
            status = lead.get("status", "")
            results["checked"] += 1

            try:
                # Case 1: Scheduled follow-up is due
                if status == "follow_up_scheduled":
                    scheduled_at = lead.get("follow_up_scheduled_at")
                    if scheduled_at:
                        scheduled_dt = datetime.fromisoformat(scheduled_at.replace("Z", "+00:00"))
                        if now >= scheduled_dt:
                            self._send_follow_up(lead)
                            results["follow_ups_sent"] += 1

                # Case 2: Contacted but no reply in 24+ hours
                elif status == "contacted":
                    last_contacted = lead.get("last_contacted")
                    if last_contacted:
                        last_dt = datetime.fromisoformat(last_contacted.replace("Z", "+00:00"))
                        hours_since = (now - last_dt).total_seconds() / 3600
                        if hours_since >= 24:
                            self._send_follow_up(lead)
                            results["follow_ups_sent"] += 1

            except Exception as e:
                logger.error(f"Follow-up error for lead {lead.get('id')}: {e}")
                results["errors"] += 1

        # Save any updated leads
        _save_json(LEADS_FILE, leads)
        return results

    def _send_follow_up(self, lead: dict):
        """Send a follow-up message to a lead."""
        follow_up_count = lead.get("follow_up_count", 0) + 1
        lead["follow_up_count"] = follow_up_count

        # Too many follow-ups → close as lost
        if follow_up_count > 3:
            lead = self.executor.close_lead(lead, "lost")
            return

        # Generate follow-up message
        follow_up_msg = self.decision_engine.get_follow_up_message(lead)

        # Send WhatsApp
        send_whatsapp(lead.get("phone", ""), follow_up_msg)

        # Send follow-up email
        from services.email_service import build_follow_up_email
        subject, body = build_follow_up_email(lead, follow_up_count)
        send_email(lead.get("email", ""), subject, body)

        # Update lead
        lead["conversation_history"] = lead.get("conversation_history", [])
        lead["conversation_history"].append({
            "role": "agent",
            "message": f"[FOLLOW-UP #{follow_up_count}] {follow_up_msg}",
            "timestamp": _now(),
        })
        lead["status"] = "follow_up_sent"
        lead["last_contacted"] = _now()
        lead["follow_up_scheduled_at"] = None

        self._update_lead(lead)
        logger.info(f"Follow-up #{follow_up_count} sent to {lead.get('name')}")

    def get_stats(self) -> dict:
        """Get dashboard statistics."""
        leads = self._load_leads()

        total = len(leads)
        hot = sum(1 for l in leads if l.get("qualification") == "hot")
        warm = sum(1 for l in leads if l.get("qualification") == "warm")
        cold = sum(1 for l in leads if l.get("qualification") == "cold")
        converted = sum(1 for l in leads if l.get("status") == "converted")
        contacted = sum(1 for l in leads if l.get("status") not in ("new",))
        escalated = sum(1 for l in leads if l.get("status") == "escalated")

        conversion_rate = round((converted / total * 100), 1) if total > 0 else 0

        return {
            "total_leads": total,
            "hot": hot,
            "warm": warm,
            "cold": cold,
            "new": sum(1 for l in leads if l.get("status") == "new"),
            "contacted": contacted,
            "converted": converted,
            "escalated": escalated,
            "closed_lost": sum(1 for l in leads if l.get("status") == "closed_lost"),
            "conversion_rate": conversion_rate,
        }

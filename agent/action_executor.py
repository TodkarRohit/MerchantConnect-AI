"""
agent/action_executor.py
Executes actions determined by the DecisionEngine.
"""
import os
import logging
from datetime import datetime, timedelta

from services.whatsapp import send_whatsapp, send_whatsapp_template
from services.email_service import send_email, build_outreach_email, build_follow_up_email, send_manager_notification

logger = logging.getLogger(__name__)

DEMO_LINK = "https://paytm.com/business/demo"
SIGNUP_LINK = "https://paytm.com/business"


class ActionExecutor:
    """
    Executes sales actions: send messages, escalate, schedule follow-ups, close leads.
    All methods update lead data in-place and return the modified lead dict.
    """

    def execute(self, action: str, lead: dict, ai_response: str) -> dict:
        """
        Dispatch to the appropriate action handler.

        Args:
            action: One of the action strings from DecisionEngine
            lead: Lead data dict (modified in-place)
            ai_response: The AI-generated reply message

        Returns:
            Updated lead dict
        """
        logger.info(f"Executing action '{action}' for lead {lead.get('id')} ({lead.get('name')})")

        action_map = {
            "send_whatsapp_reply": lambda: self.send_whatsapp_reply(lead, ai_response),
            "send_demo_link": lambda: self.send_demo_link(lead),
            "send_product_info": lambda: self.send_product_info(lead, ai_response),
            "escalate_to_human": lambda: self.escalate_to_human(lead),
            "schedule_follow_up": lambda: self.schedule_follow_up(lead),
            "close_won": lambda: self.close_lead(lead, "won"),
            "close_lost": lambda: self.close_lead(lead, "lost"),
        }

        handler = action_map.get(action)
        if handler:
            return handler()
        else:
            logger.warning(f"Unknown action: {action}. Defaulting to send_product_info.")
            return self.send_product_info(lead, ai_response)

    def send_whatsapp_reply(self, lead: dict, message: str) -> dict:
        """Send a plain WhatsApp reply."""
        phone = lead.get("phone", "")
        success = send_whatsapp(phone, message)

        if success:
            self._add_to_conversation(lead, "agent", message)
            lead["last_contacted"] = _now()

        return lead

    def send_demo_link(self, lead: dict) -> dict:
        """Send WhatsApp + Email with demo booking link."""
        name = lead.get("name", "").split()[0]
        phone = lead.get("phone", "")
        email = lead.get("email", "")

        # WhatsApp message
        wa_message = (
            f"🎉 {name} ji, bahut accha laga sun ke!\n\n"
            f"👉 *Demo Book Karein (FREE, 15 min):*\n{DEMO_LINK}\n\n"
            f"👉 *Seedha Sign Up:*\n{SIGNUP_LINK}\n\n"
            f"Demo mein aapko dikhayenge ki Paytm specifically aapke {lead.get('business_type', 'business')} ke liye "
            f"kaise kaam karta hai! Koi bhi sawaal ho toh bataiye 😊"
        )
        send_whatsapp(phone, wa_message)

        # Email
        subject = f"🎉 Your Paytm Demo is Ready — Book in 1 Click! | {lead.get('business')}"
        email_body = f"""
        <h2 style="color:#002970;">Demo Book Karein — FREE!</h2>
        <p>{name} ji, bahut khushi hui ki aap Paytm ke baare mein jaanna chahte hain!</p>
        <div style="text-align:center;margin:24px 0;">
          <a href="{DEMO_LINK}" style="background:#00BAF2;color:white;padding:14px 32px;border-radius:6px;text-decoration:none;font-size:16px;font-weight:bold;">
            📅 Book FREE Demo Now
          </a>
        </div>
        <p>Demo mein aap dekhenge:</p>
        <ul>
          <li>✅ FREE QR Code setup (5 minutes)</li>
          <li>🔊 Soundbox demo live</li>
          <li>💳 POS Machine features</li>
          <li>💰 Business Loan eligibility</li>
        </ul>
        <p>Sirf 15 minutes — aur aapka business zyada smart ho jayega! 🚀</p>
        """
        full_body = f"""
        <!DOCTYPE html><html><body style="font-family:Arial;background:#f4f4f4;padding:20px;">
        <div style="background:white;max-width:600px;margin:0 auto;padding:32px;border-radius:8px;">
          <div style="background:#002970;padding:16px;border-radius:6px;text-align:center;margin-bottom:24px;">
            <h1 style="color:white;margin:0;"><span style="color:#00BAF2;">Pay</span>tm for Business</h1>
          </div>
          {email_body}
          <p style="color:#888;font-size:12px;margin-top:24px;">Paytm AI Sales Teammate | Paytm Business</p>
        </div></body></html>
        """
        send_email(email, subject, full_body)

        # Update lead
        self._add_to_conversation(lead, "agent", wa_message)
        lead["status"] = "demo_scheduled"
        lead["qualification"] = "hot"
        lead["last_contacted"] = _now()
        lead["notes"] = lead.get("notes", "") + f"\n[{_now()}] Demo link sent via WhatsApp + Email"

        # Notify manager
        send_manager_notification(lead, "hot_lead", "Demo link sent to merchant")

        return lead

    def send_product_info(self, lead: dict, ai_response: str = None) -> dict:
        """Send WhatsApp reply + product info email."""
        phone = lead.get("phone", "")
        email = lead.get("email", "")
        name = lead.get("name", "").split()[0]

        # Send AI response via WhatsApp
        if ai_response:
            send_whatsapp(phone, ai_response)
            self._add_to_conversation(lead, "agent", ai_response)

        # Send product info email
        subject = f"Paytm Business Solutions — Sirf {lead.get('business_type', 'Aapke Business')} Ke Liye! 📱"
        email_body = f"""
        <!DOCTYPE html><html><body style="font-family:Arial;background:#f4f4f4;padding:20px;">
        <div style="background:white;max-width:600px;margin:0 auto;padding:32px;border-radius:8px;">
          <div style="background:#002970;padding:16px;border-radius:6px;text-align:center;margin-bottom:24px;">
            <h1 style="color:white;margin:0;"><span style="color:#00BAF2;">Pay</span>tm for Business</h1>
          </div>
          <h2 style="color:#002970;">Namaste {name} ji! 🙏</h2>
          <p>Maine aapke {lead.get('business_type', 'business')} ke baare mein soch ke yeh information taiyaar ki hai:</p>

          <div style="border:2px solid #00BAF2;border-radius:8px;padding:16px;margin:16px 0;">
            <h3 style="color:#002970;margin:0 0 12px;">🔊 Paytm Soundbox</h3>
            <ul style="color:#333;margin:0;padding-left:20px;">
              <li>₹0 monthly rental (just refundable deposit)</li>
              <li>Works with ALL UPI apps</li>
              <li>Loud voice confirmation in Hindi/English</li>
              <li>Prevents fraud & employee theft</li>
            </ul>
          </div>

          <div style="border:2px solid #002970;border-radius:8px;padding:16px;margin:16px 0;">
            <h3 style="color:#002970;margin:0 0 12px;">📱 Free QR Code</h3>
            <ul style="color:#333;margin:0;padding-left:20px;">
              <li>100% FREE — no hidden charges</li>
              <li>Accept GPay, PhonePe, BHIM, all UPI apps</li>
              <li>Instant settlement to bank account</li>
              <li>Transaction history in Paytm Business app</li>
            </ul>
          </div>

          <div style="border:2px solid #002970;border-radius:8px;padding:16px;margin:16px 0;">
            <h3 style="color:#002970;margin:0 0 12px;">💳 POS Machine</h3>
            <ul style="color:#333;margin:0;padding-left:20px;">
              <li>Accept credit card, debit card, UPI, contactless</li>
              <li>MDR as low as 0.4% (best in industry)</li>
              <li>EMI options for your customers</li>
              <li>Next-day settlement</li>
            </ul>
          </div>

          <div style="border:2px solid #002970;border-radius:8px;padding:16px;margin:16px 0;">
            <h3 style="color:#002970;margin:0 0 12px;">💰 Business Loan</h3>
            <ul style="color:#333;margin:0;padding-left:20px;">
              <li>₹10,000 to ₹50 Lakhs</li>
              <li>No collateral required</li>
              <li>24-hour approval</li>
              <li>Auto-repayment from daily settlements</li>
            </ul>
          </div>

          <div style="text-align:center;margin:24px 0;">
            <a href="{DEMO_LINK}" style="background:#00BAF2;color:white;padding:14px 32px;border-radius:6px;text-decoration:none;font-size:16px;font-weight:bold;display:inline-block;">
              📅 Book FREE Demo →
            </a>
          </div>
          <p style="color:#888;font-size:12px;margin-top:24px;">Paytm AI Sales Teammate | Paytm Business</p>
        </div></body></html>
        """
        send_email(email, subject, email_body)

        lead["status"] = "in_conversation"
        lead["last_contacted"] = _now()

        return lead

    def escalate_to_human(self, lead: dict) -> dict:
        """
        Escalate a hot lead to a human sales rep.
        Updates lead status and notifies manager.
        """
        phone = lead.get("phone", "")
        name = lead.get("name", "").split()[0]

        # Notify merchant
        escalation_msg = (
            f"🎉 {name} ji, yeh sun ke bahut khushi hui!\n\n"
            f"Main abhi aapke liye hamare *Paytm Business Expert* se connect kar rahi hun. "
            f"Woh 30 minutes mein aapko personally call karenge aur har sawaal ka jawab denge! 🚀\n\n"
            f"Tab tak agar koi sawaal ho toh main yahan hun 😊"
        )
        send_whatsapp(phone, escalation_msg)

        # Email to merchant
        subject = "🎉 Paytm Expert Will Call You Shortly!"
        email_body = f"""
        <!DOCTYPE html><html><body style="font-family:Arial;background:#f4f4f4;padding:20px;">
        <div style="background:white;max-width:600px;margin:0 auto;padding:32px;border-radius:8px;">
          <div style="background:#002970;padding:16px;border-radius:6px;text-align:center;margin-bottom:24px;">
            <h1 style="color:white;margin:0;"><span style="color:#00BAF2;">Pay</span>tm for Business</h1>
          </div>
          <h2 style="color:#002970;">Namaste {name} ji! 🎉</h2>
          <p style="font-size:16px;color:#333;">Hamara Paytm Business Expert aapko call karega — ek personalized solution design karne ke liye!</p>
          <div style="background:#e8f4fd;border-radius:8px;padding:16px;margin:16px 0;">
            <p style="margin:0;color:#002970;font-weight:bold;">📞 Expected Call: Within 30 minutes</p>
          </div>
          <p>Yeh call mein aap discuss kar sakte hain:</p>
          <ul>
            <li>Custom pricing for your business scale</li>
            <li>Enterprise solutions if needed</li>
            <li>Quick onboarding & setup support</li>
            <li>Any specific requirements</li>
          </ul>
          <p style="color:#888;font-size:12px;margin-top:24px;">Paytm AI Sales Teammate | Paytm Business</p>
        </div></body></html>
        """
        send_email(lead.get("email", ""), subject, email_body)

        # Update lead
        self._add_to_conversation(lead, "agent", escalation_msg)
        lead["status"] = "escalated"
        lead["qualification"] = "hot"
        lead["assigned_human_rep"] = "Available Rep"
        lead["last_contacted"] = _now()
        lead["notes"] = lead.get("notes", "") + f"\n[{_now()}] Escalated to human rep"

        # Notify manager
        send_manager_notification(
            lead, "escalation",
            f"Lead is very interested and needs human follow-up. Phone: {lead.get('phone')}"
        )

        return lead

    def schedule_follow_up(self, lead: dict, days: int = 2) -> dict:
        """
        Schedule a follow-up for the lead.
        
        Args:
            lead: Lead data dict
            days: Days until follow-up (default 2)
        """
        follow_up_time = datetime.now() + timedelta(days=days)
        lead["follow_up_scheduled_at"] = follow_up_time.isoformat()
        lead["status"] = "follow_up_scheduled"
        lead["last_contacted"] = _now()

        logger.info(f"Follow-up scheduled for {lead.get('name')} at {follow_up_time.isoformat()}")
        return lead

    def close_lead(self, lead: dict, outcome: str) -> dict:
        """
        Close a lead as won or lost.
        
        Args:
            lead: Lead data dict
            outcome: "won" | "lost"
        """
        phone = lead.get("phone", "")
        name = lead.get("name", "").split()[0]

        if outcome == "won":
            msg = (
                f"🎉 {name} ji, Paytm Business family mein aapka swagat hai!\n\n"
                f"Aapka account setup ho raha hai. Setup complete hone pe ek confirmation message aayega.\n\n"
                f"Koi bhi sawaal ho toh humari support team hamesha available hai! 😊🚀"
            )
            send_whatsapp(phone, msg)
            self._add_to_conversation(lead, "agent", msg)
            lead["status"] = "converted"
            lead["qualification"] = "hot"
            send_manager_notification(lead, "conversion", "Merchant signed up!")

        else:  # lost
            msg = (
                f"Bilkul theek hai {name} ji! 😊 Koi problem nahi.\n\n"
                f"Kabhi bhi zarorat ho toh Paytm Business hamesha yahan hai — {SIGNUP_LINK}\n\n"
                f"Aapke business ko meri shubhkamnayein! 🙏"
            )
            send_whatsapp(phone, msg)
            self._add_to_conversation(lead, "agent", msg)
            lead["status"] = "closed_lost"
            lead["qualification"] = "cold"
            send_manager_notification(lead, "close_lost", "Merchant not interested")

        lead["last_contacted"] = _now()
        return lead

    def _add_to_conversation(self, lead: dict, role: str, message: str):
        """Helper to append a message to conversation history."""
        if "conversation_history" not in lead:
            lead["conversation_history"] = []

        lead["conversation_history"].append({
            "role": role,
            "message": message,
            "timestamp": _now(),
        })


def _now() -> str:
    """Return current UTC timestamp as ISO string."""
    return datetime.utcnow().isoformat() + "Z"

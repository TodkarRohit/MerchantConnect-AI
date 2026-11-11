"""
agent/decision_engine.py
Lead qualification and next-action decision logic.
"""
import logging

logger = logging.getLogger(__name__)


class DecisionEngine:
    """
    Decides how to qualify leads and what action to take next
    based on AI analysis and lead history.
    """

    # Qualification thresholds
    HOT_THRESHOLD = 2    # Positive exchanges needed for HOT
    ESCALATE_EXCHANGES = 3  # Positive exchanges needed before escalating

    def qualify_lead(self, lead: dict, ai_analysis: dict) -> str:
        """
        Qualify a lead as hot, warm, or cold.

        Args:
            lead: Lead data dict
            ai_analysis: Analysis from GeminiAI.analyze_lead_response()

        Returns:
            "hot" | "warm" | "cold"
        """
        ai_qualification = ai_analysis.get("qualification", "warm")
        sentiment = ai_analysis.get("sentiment", "neutral")
        intent = ai_analysis.get("intent", "needs_info")
        conversation_history = lead.get("conversation_history", [])
        follow_up_count = lead.get("follow_up_count", 0)

        # Count positive merchant messages
        merchant_messages = [
            m for m in conversation_history
            if m.get("role") == "merchant"
        ]
        positive_signals = sum(
            1 for m in merchant_messages
            if any(
                kw in m.get("message", "").lower()
                for kw in ["haan", "yes", "interested", "demo", "batao", "good", "accha", "chahiye"]
            )
        )

        # Hard rules override AI analysis
        if intent == "not_interested" and follow_up_count >= 2:
            return "cold"

        if sentiment == "negative" and intent == "not_interested":
            return "cold"

        if intent == "wants_demo" or (sentiment == "positive" and positive_signals >= self.HOT_THRESHOLD):
            return "hot"

        if sentiment == "positive" or intent == "interested":
            return "warm"

        if sentiment == "negative":
            return "cold"

        # Fall back to AI's assessment
        return ai_qualification

    def decide_next_action(self, lead: dict, ai_analysis: dict) -> str:
        """
        Determine the next action to take for a lead.

        Args:
            lead: Lead data dict
            ai_analysis: Analysis from GeminiAI.analyze_lead_response()

        Returns:
            One of:
            - "send_demo_link"      — Merchant wants a demo
            - "send_product_info"   — Merchant needs more info
            - "escalate_to_human"   — High-value lead needing human touch
            - "schedule_follow_up"  — Merchant said "baad mein" or no response
            - "close_won"           — Merchant signed up
            - "close_lost"          — Merchant clearly not interested
        """
        suggested = ai_analysis.get("suggested_action", "send_product_info")
        intent = ai_analysis.get("intent", "needs_info")
        qualification = self.qualify_lead(lead, ai_analysis)
        follow_up_count = lead.get("follow_up_count", 0)

        # Override: escalate hot leads with enough positive exchanges
        if self.should_escalate(lead, ai_analysis):
            return "escalate_to_human"

        # Map AI suggestion to our action space
        action_map = {
            "send_demo_link": "send_demo_link",
            "send_product_info": "send_product_info",
            "escalate_to_human": "escalate_to_human",
            "follow_up_later": "schedule_follow_up",
            "close_lost": "close_lost",
            "close_won": "close_won",
        }

        action = action_map.get(suggested, "send_product_info")

        # Cold leads with many follow-ups → close lost
        if qualification == "cold" and follow_up_count >= 3:
            return "close_lost"

        # Hot lead who wants demo → send demo link
        if qualification == "hot" and intent in ("wants_demo", "interested"):
            return "send_demo_link"

        return action

    def should_escalate(self, lead: dict, ai_analysis: dict = None) -> bool:
        """
        Determine if this lead should be escalated to a human rep.

        Returns True if:
        - AI suggests escalation, OR
        - Lead is HOT with 3+ positive exchanges and asking for pricing/contract
        """
        if ai_analysis:
            if ai_analysis.get("suggested_action") == "escalate_to_human":
                return True
            if ai_analysis.get("intent") == "wants_demo" and ai_analysis.get("qualification") == "hot":
                # Count positive merchant exchanges
                history = lead.get("conversation_history", [])
                merchant_msgs = [m for m in history if m.get("role") == "merchant"]
                if len(merchant_msgs) >= self.ESCALATE_EXCHANGES:
                    return True

        # Already escalated — don't do it again
        if lead.get("status") == "escalated":
            return False

        return False

    def get_follow_up_message(self, lead: dict) -> str:
        """Generate an appropriate follow-up message based on lead state."""
        follow_up_count = lead.get("follow_up_count", 0)
        name = lead.get("name", "").split()[0]
        business_type = lead.get("business_type", "business")

        messages = [
            f"Namaste {name} ji! 🙏 Paytm Business Team se follow-up message hai. Kuch din pehle aapko message kiya tha — bas check kar rahe the ki koi sawaal tha? Paytm QR Code FREE hai, koi bhi doubt ho toh bataiye! 😊",
            f"{name} ji, ek khaas baat share karna chahti thi — aap jaise {business_type} owners ke liye Paytm Soundbox FREE rental par mil raha hai! Kya ek baar dekhna chahenge? 🔊",
            f"Namaste {name} ji! Yeh mera aakhri message hai. 😊 Agar kabhi Paytm ke baare mein jaanna ho toh main hamesha yahan hun. Paytm Business mein aapka swagat hai! 🙏",
        ]

        idx = min(follow_up_count, len(messages) - 1)
        return messages[idx]

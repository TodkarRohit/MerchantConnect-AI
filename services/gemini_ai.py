"""
services/gemini_ai.py
Wrapper around Google Gemini API with mock mode support.
"""
import os
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Mock responses for demo without API keys
MOCK_RESPONSES = {
    "opening": [
        "Namaste {name} ji! 😊 Paytm Business Team se connect kar rahe hain. Aapki {business} ke baare mein suna — bohot accha business hai! Kya aap abhi customers se UPI payments accept kar pa rahe hain? 🤔",
        "Namaste {name} ji! Paytm Business Team se message hai. {business_type} owners ke liye hamare paas kuch amazing solutions hain — especially jo aaj kal {pain_point} se deal karte hain. Aapka abhi kya setup hai payments ke liye?",
    ],
    "reply": [
        "Bilkul samajh sakti hun! Yeh problem bahut common hai. Paytm Soundbox se yeh issue solve ho jata hai — har payment pe awaaz aati hai, chahe koi bhi app use kare. ₹0 rental hai! Kya aap ek free demo dekhna chahenge? 😊",
        "Main samajhti hun aapki baat! Paytm QR Code bilkul free hai — ek baar set karo, sab UPI apps ka payment aane lagega. Koi monthly charges nahi. Aapki shop kitni badi hai — employees kitne hain?",
        "Arey wah! Yeh toh bahut achhi baat hai. Paytm se aap business loan bhi le sakte hain — ₹10,000 se ₹50 lakh tak, koi collateral nahi chahiye. Aapko kab zarorat hai funds ki?",
    ],
    "analysis": {
        "sentiment": "positive",
        "intent": "interested",
        "qualification": "warm",
        "suggested_action": "send_product_info",
    }
}

MOCK_ANALYSIS_VARIANTS = [
    {
        "sentiment": "positive",
        "intent": "interested",
        "qualification": "warm",
        "suggested_action": "send_product_info",
    },
    {
        "sentiment": "positive",
        "intent": "wants_demo",
        "qualification": "hot",
        "suggested_action": "send_demo_link",
    },
    {
        "sentiment": "neutral",
        "intent": "needs_info",
        "qualification": "warm",
        "suggested_action": "follow_up_later",
    },
    {
        "sentiment": "negative",
        "intent": "not_interested",
        "qualification": "cold",
        "suggested_action": "follow_up_later",
    },
]


class GeminiAI:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.mock_mode = not self.api_key or self.api_key == "mock"
        self.model = None
        self._mock_counter = 0

        if not self.mock_mode:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel("gemini-1.5-flash")
                logger.info("Gemini AI initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini: {e}")
                self.mock_mode = True
                logger.warning("Falling back to mock mode")
        else:
            logger.info("Running in MOCK MODE — no Gemini API key set")

    def chat(self, system_prompt: str, conversation_history: list, user_message: str, lead: dict = None) -> str:
        """
        Generate AI response for a merchant conversation.
        
        Args:
            system_prompt: The sales agent system prompt
            conversation_history: List of {"role": "agent"|"merchant", "message": "..."} dicts
            user_message: The latest message from the merchant
            lead: Lead data dict for personalization
            
        Returns:
            AI response string
        """
        if self.mock_mode:
            return self._mock_chat(lead, user_message, len(conversation_history))

        try:
            # Build the full prompt
            history_text = ""
            for msg in conversation_history[-10:]:  # Last 10 messages for context
                role = "Paytm AI Sales Teammate" if msg["role"] == "agent" else "Merchant"
                history_text += f"\n{role}: {msg['message']}"

            lead_context = ""
            if lead:
                lead_context = f"""
Merchant Information:
- Name: {lead.get('name', 'Unknown')}
- Business: {lead.get('business', 'Unknown')}
- Type: {lead.get('business_type', 'Unknown')}
- City: {lead.get('city', 'Unknown')}
- Monthly Revenue: {lead.get('monthly_revenue_estimate', 'Unknown')}
- Current Payment: {lead.get('current_payment_method', 'Unknown')}
- Pain Points: {', '.join(lead.get('pain_points', []))}
- Follow-up Count: {lead.get('follow_up_count', 0)}
"""

            full_prompt = f"""{system_prompt}

{lead_context}

Conversation so far:{history_text}

Merchant's latest message: {user_message}

Your response as Paytm AI Sales Teammate (keep it SHORT, 2-3 lines max, end with ONE question):"""

            response = self.model.generate_content(full_prompt)
            return response.text.strip()

        except Exception as e:
            logger.error(f"Gemini chat error: {e}")
            return self._mock_chat(lead, user_message, len(conversation_history))

    def analyze_lead_response(self, merchant_message: str, lead_data: dict) -> dict:
        """
        Analyze merchant's reply to determine sentiment, intent, and suggested action.
        
        Returns:
            {
                "sentiment": "positive/negative/neutral",
                "intent": "interested/not_interested/needs_info/wants_demo",
                "qualification": "hot/warm/cold",
                "suggested_action": "send_demo_link/send_product_info/escalate_to_human/follow_up_later/close_lost"
            }
        """
        if self.mock_mode:
            return self._mock_analyze(merchant_message, lead_data)

        try:
            analysis_prompt = f"""Analyze this WhatsApp message from a merchant and return a JSON response.

Merchant's message: "{merchant_message}"

Merchant context:
- Business: {lead_data.get('business_type', 'Unknown')}
- Follow-ups sent: {lead_data.get('follow_up_count', 0)}
- Current status: {lead_data.get('status', 'unknown')}

Return ONLY valid JSON (no markdown, no explanation):
{{
  "sentiment": "positive" | "negative" | "neutral",
  "intent": "interested" | "not_interested" | "needs_info" | "wants_demo",
  "qualification": "hot" | "warm" | "cold",
  "suggested_action": "send_demo_link" | "send_product_info" | "escalate_to_human" | "follow_up_later" | "close_lost"
}}

Rules:
- "hot" = Very interested, wants to proceed soon, asking specific questions
- "warm" = Somewhat interested, asking general questions, open to learning more  
- "cold" = Not interested, says no, busy, doesn't reply
- "escalate_to_human" = when merchant asks for specific pricing/contracts or is very eager
- "send_demo_link" = when merchant explicitly asks for demo or says "yes, interested"
- "close_lost" = when merchant explicitly says not interested, using competitor, no need"""

            response = self.model.generate_content(analysis_prompt)
            text = response.text.strip()

            # Clean up response if it has markdown code blocks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            return json.loads(text)

        except Exception as e:
            logger.error(f"Gemini analysis error: {e}")
            return self._mock_analyze(merchant_message, lead_data)

    def generate_opening_message(self, lead: dict, system_prompt: str) -> str:
        """Generate the first outreach message for a lead."""
        if self.mock_mode:
            name = lead.get("name", "").split()[0]
            business_type = lead.get("business_type", "business")
            pain = lead.get("pain_points", ["digital payments"])[0]
            return f"Namaste {name} ji! 😊 Paytm Business Team se message hai. Aapka {business_type} dekhke laga ki Paytm aapke liye bahut helpful ho sakta hai! Kya aap abhi customers se digital payments accept kar pa rahe hain? 🤔"

        try:
            prompt = f"""{system_prompt}

Merchant Information:
- Name: {lead.get('name')}
- Business: {lead.get('business')}
- Type: {lead.get('business_type')}
- City: {lead.get('city')}
- Current Payment: {lead.get('current_payment_method')}
- Pain Points: {', '.join(lead.get('pain_points', []))}

Write the FIRST WhatsApp outreach message to this merchant as Paytm AI Sales Teammate.
- Address them by first name + "ji"
- Mention their business type to show you know them
- Ask about ONE specific pain point
- Keep it to 2-3 lines MAX
- End with ONE question
- Be warm and friendly, not salesy"""

            response = self.model.generate_content(prompt)
            return response.text.strip()

        except Exception as e:
            logger.error(f"Gemini opening message error: {e}")
            name = lead.get("name", "").split()[0]
            return f"Namaste {name} ji! 😊 Paytm Business Team se message hai. Aapka {lead.get('business_type', 'business')} dekhke laga ki Paytm aapke liye helpful ho sakta hai! Kya aap abhi digital payments accept karte hain? 🤔"

    def _mock_chat(self, lead: dict, user_message: str, history_len: int) -> str:
        """Return mock response for demo purposes."""
        import random
        self._mock_counter += 1

        if lead:
            name = lead.get("name", "").split()[0]
        else:
            name = "ji"

        responses = [
            f"Bilkul samajh sakti hun {name} ji! Paytm Soundbox se yeh problem solve ho jati hai — har payment pe awaaz aati hai chahe PhonePe ho ya GPay. ₹0 rental hai! Ek free demo dekhna chahenge? 😊",
            f"Main samajhti hun! Paytm QR Code FREE hai aur sab UPI apps ka payment accept karta hai. Setup mein sirf 5 minute lagte hain. Aapke paas Android phone hai? 📱",
            f"Wah {name} ji! Yeh bahut acchi baat hai. Paytm se aap business loan bhi le sakte hain — koi collateral nahi chahiye. Apna business grow karna chahte hain? 🚀",
            f"Bilkul sahi! MDR charges ko lekar Paytm mein industry ki best rates hain — debit card pe sirf 0.4%. Kya main aapke liye ek demo book karun? 📅",
            f"Arey {name} ji, yeh toh bahut common problem hai! Paytm ka ek QR code sabka payment accept karta hai — GPay, PhonePe, BHIM sab. Kab try karein? 😊",
        ]
        return random.choice(responses)

    def _mock_analyze(self, message: str, lead_data: dict) -> dict:
        """Return mock analysis based on simple keyword matching."""
        message_lower = message.lower()

        # Positive signals
        positive_keywords = ["haan", "yes", "interested", "chahiye", "batao", "demo", "kaise", "how", "good", "accha", "theek"]
        negative_keywords = ["nahi", "no", "not interested", "busy", "baad mein", "later", "mat karo", "band karo"]
        demo_keywords = ["demo", "dikhaao", "show", "book", "schedule", "milna", "meet"]
        escalate_keywords = ["price", "contract", "rate", "kitna", "cost", "charges", "pricing"]

        pos_count = sum(1 for kw in positive_keywords if kw in message_lower)
        neg_count = sum(1 for kw in negative_keywords if kw in message_lower)
        demo_count = sum(1 for kw in demo_keywords if kw in message_lower)
        escalate_count = sum(1 for kw in escalate_keywords if kw in message_lower)

        follow_up_count = lead_data.get("follow_up_count", 0)

        if neg_count > pos_count:
            return {
                "sentiment": "negative",
                "intent": "not_interested",
                "qualification": "cold",
                "suggested_action": "close_lost" if follow_up_count >= 2 else "follow_up_later",
            }
        elif escalate_count > 0 and pos_count > 0:
            return {
                "sentiment": "positive",
                "intent": "wants_demo",
                "qualification": "hot",
                "suggested_action": "escalate_to_human",
            }
        elif demo_count > 0:
            return {
                "sentiment": "positive",
                "intent": "wants_demo",
                "qualification": "hot",
                "suggested_action": "send_demo_link",
            }
        elif pos_count > 0:
            return {
                "sentiment": "positive",
                "intent": "interested",
                "qualification": "warm",
                "suggested_action": "send_product_info",
            }
        else:
            return {
                "sentiment": "neutral",
                "intent": "needs_info",
                "qualification": "warm",
                "suggested_action": "send_product_info",
            }

"""
services/whatsapp.py
Twilio WhatsApp integration — send messages and parse webhooks.
"""
import os
import logging

logger = logging.getLogger(__name__)


def send_whatsapp(to: str, message: str) -> bool:
    """
    Send a WhatsApp message via Twilio.
    
    Args:
        to: Recipient phone number (e.g., "+919876543210" or "whatsapp:+919876543210")
        message: Message text to send
        
    Returns:
        True if successful, False otherwise
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
    from_number = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")

    # Normalize 'to' number format
    if not to.startswith("whatsapp:"):
        to = f"whatsapp:{to}"

    # Mock mode — no Twilio credentials
    if not account_sid or account_sid == "mock" or not auth_token or auth_token == "mock":
        logger.info(f"[MOCK WhatsApp] To: {to} | Message: {message[:80]}...")
        return True

    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)

        msg = client.messages.create(
            from_=from_number,
            to=to,
            body=message,
        )
        logger.info(f"WhatsApp sent! SID: {msg.sid} | To: {to}")
        return True

    except Exception as e:
        logger.error(f"WhatsApp send failed to {to}: {e}")
        return False


def parse_webhook(form_data: dict) -> dict:
    """
    Parse incoming Twilio WhatsApp webhook POST data.
    
    Args:
        form_data: The form data dict from Twilio's webhook POST
        
    Returns:
        {
            "from": "whatsapp:+91...",
            "body": "message text",
            "phone": "+91..."   # cleaned phone number
        }
    """
    try:
        from_number = form_data.get("From", "")
        body = form_data.get("Body", "").strip()

        # Extract clean phone number (remove "whatsapp:" prefix)
        phone = from_number.replace("whatsapp:", "").strip()

        return {
            "from": from_number,
            "body": body,
            "phone": phone,
            "num_media": int(form_data.get("NumMedia", "0")),
            "profile_name": form_data.get("ProfileName", ""),
        }

    except Exception as e:
        logger.error(f"WhatsApp webhook parse error: {e}")
        return {"from": "", "body": "", "phone": ""}


def send_whatsapp_template(to: str, template_vars: dict, template_type: str = "demo_link") -> bool:
    """
    Send a structured WhatsApp message with link/template.
    
    Args:
        to: Recipient phone
        template_vars: Variables to fill in template
        template_type: "demo_link" | "product_info" | "follow_up"
    """
    templates = {
        "demo_link": (
            "🎉 {name} ji, bahut accha! Main aapke liye demo book kar rahi hun!\n\n"
            "👉 *Demo Book Karein:* https://paytm.com/business/demo\n"
            "👉 *Seedha Sign Up:* https://paytm.com/business\n\n"
            "Demo FREE hai, sirf 15 minutes! Aaj ya kal kab acha rahega? 📅"
        ),
        "product_info": (
            "📱 *Paytm Business Solutions — Sirf Aapke Liye!*\n\n"
            "✅ QR Code — FREE\n"
            "🔊 Soundbox — ₹0 rental\n"
            "💳 POS Machine — Best MDR rates\n"
            "💰 Business Loan — ₹10K-50L, no collateral\n\n"
            "Jaanna chahte hain kaunsa aapke liye best hai? Bas reply karein! 😊"
        ),
        "follow_up": (
            "Namaste {name} ji! 🙏 Paytm Business Team se message hai.\n\n"
            "Kuch din pehle aapko message kiya tha — bas check kar rahi thi ki koi sawaal tha?\n\n"
            "Paytm QR Code aaj bhi FREE hai! Koi bhi sawaal ho toh bataiye 😊"
        ),
        "escalation": (
            "🎉 {name} ji, bahut khushi hui!\n\n"
            "Main abhi aapke liye hamare *Paytm Business Expert* se connect kar rahi hun.\n"
            "Woh 30 minutes mein aapko call karenge aur sab setup kar denge! 🚀\n\n"
            "Koi bhi sawaal ho toh main yahan hun! 😊"
        ),
    }

    template = templates.get(template_type, templates["product_info"])
    message = template.format(**template_vars)
    return send_whatsapp(to, message)

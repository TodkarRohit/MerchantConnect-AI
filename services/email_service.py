"""
services/email_service.py
SMTP email service with Paytm branding.
"""
import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr

# Import templates from prompts package
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from prompts.email_templates import get_outreach_email_content, get_follow_up_email_content

logger = logging.getLogger(__name__)


def send_email(to_email: str, subject: str, body: str) -> bool:
    """
    Send an HTML email via Gmail SMTP.
    
    Args:
        to_email: Recipient email address
        subject: Email subject line
        body: HTML email body
        
    Returns:
        True if successful, False otherwise
    """
    gmail_user = os.getenv("GMAIL_USER", "")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD", "")

    # Mock mode — no credentials
    if not gmail_user or not gmail_password or gmail_password == "mock":
        logger.info(f"[MOCK Email] To: {to_email} | Subject: {subject}")
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = formataddr(("Paytm AI Business Partner", gmail_user))
        msg["To"] = to_email

        # Attach HTML body
        html_part = MIMEText(body, "html", "utf-8")
        msg.attach(html_part)

        # Send via Gmail SMTP
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, to_email, msg.as_string())

        logger.info(f"Email sent successfully to {to_email}")
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error("Gmail SMTP authentication failed — check GMAIL_APP_PASSWORD in .env")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error sending to {to_email}: {e}")
        return False
    except Exception as e:
        logger.error(f"Email send failed to {to_email}: {e}")
        return False


def build_outreach_email(lead: dict) -> tuple:
    """
    Build personalized initial outreach email for a lead.
    
    Args:
        lead: Lead data dict
        
    Returns:
        (subject, html_body) tuple
    """
    try:
        return get_outreach_email_content(lead)
    except Exception as e:
        logger.error(f"Error building outreach email: {e}")
        name = lead.get("name", "").split()[0]
        subject = "Grow Your Business with Paytm — Free Setup!"
        body = f"<p>Namaste {name} ji! Paytm Business Team se message hai. Paytm se aap apna business grow kar sakte hain! <a href='https://paytm.com/business'>paytm.com/business</a></p>"
        return subject, body


def build_follow_up_email(lead: dict, follow_up_number: int) -> tuple:
    """
    Build follow-up email for a lead.
    
    Args:
        lead: Lead data dict
        follow_up_number: Which follow-up this is (1, 2, 3)
        
    Returns:
        (subject, html_body) tuple
    """
    try:
        return get_follow_up_email_content(lead, follow_up_number)
    except Exception as e:
        logger.error(f"Error building follow-up email: {e}")
        name = lead.get("name", "").split()[0]
        subject = f"Follow-up: Paytm ke baare mein kuch sawaal? 🤔"
        body = f"<p>Namaste {name} ji! Bas ek quick follow-up — Paytm join karna chahenge? <a href='https://paytm.com/business'>paytm.com/business</a></p>"
        return subject, body


def send_manager_notification(lead: dict, event_type: str, details: str = "") -> bool:
    """
    Send notification email to the manager.
    
    Args:
        lead: Lead data dict
        event_type: Type of event (e.g., "escalation", "conversion", "hot_lead")
        details: Additional details
        
    Returns:
        True if sent successfully
    """
    manager_email = os.getenv("MANAGER_EMAIL", "")
    if not manager_email:
        logger.info(f"[MOCK Manager Email] Event: {event_type} | Lead: {lead.get('name')}")
        return True

    event_labels = {
        "escalation": "🚨 Lead Escalated to Human Rep",
        "conversion": "🎉 Lead Converted!",
        "hot_lead": "🔥 Hot Lead Identified",
        "close_lost": "❌ Lead Closed (Lost)",
    }

    subject = f"[Paytm AI Agent] {event_labels.get(event_type, event_type)}: {lead.get('name')} — {lead.get('business')}"

    body = f"""
    <html><body style="font-family:Arial;padding:20px;background:#f4f4f4;">
    <div style="background:white;padding:24px;border-radius:8px;max-width:600px;margin:0 auto;">
      <h2 style="color:#002970;">{event_labels.get(event_type, event_type)}</h2>
      <table style="width:100%;border-collapse:collapse;">
        <tr><td style="padding:8px;color:#555;font-weight:bold;">Lead Name</td><td style="padding:8px;">{lead.get('name')}</td></tr>
        <tr style="background:#f8f9fa;"><td style="padding:8px;color:#555;font-weight:bold;">Business</td><td style="padding:8px;">{lead.get('business')}</td></tr>
        <tr><td style="padding:8px;color:#555;font-weight:bold;">City</td><td style="padding:8px;">{lead.get('city')}</td></tr>
        <tr style="background:#f8f9fa;"><td style="padding:8px;color:#555;font-weight:bold;">Phone</td><td style="padding:8px;">{lead.get('phone')}</td></tr>
        <tr><td style="padding:8px;color:#555;font-weight:bold;">Email</td><td style="padding:8px;">{lead.get('email')}</td></tr>
        <tr style="background:#f8f9fa;"><td style="padding:8px;color:#555;font-weight:bold;">Status</td><td style="padding:8px;">{lead.get('status')}</td></tr>
        <tr><td style="padding:8px;color:#555;font-weight:bold;">Qualification</td><td style="padding:8px;">{lead.get('qualification', 'N/A')}</td></tr>
      </table>
      {f'<p style="margin-top:16px;color:#333;"><strong>Details:</strong> {details}</p>' if details else ''}
      <p style="color:#888;font-size:12px;margin-top:24px;">Sent by Paytm AI Sales Teammate</p>
    </div>
    </body></html>
    """

    return send_email(manager_email, subject, body)

"""
main.py
FastAPI application — Paytm AI Sales Teammate
All routes: leads CRUD, WhatsApp webhook, dashboard stats, follow-ups
"""
import os
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Data files
DATA_DIR = Path(__file__).parent / "data"
LEADS_FILE = DATA_DIR / "leads.json"
CONVERSATIONS_FILE = DATA_DIR / "conversations.json"
OUTCOMES_FILE = DATA_DIR / "outcomes.json"
DASHBOARD_FILE = Path(__file__).parent / "dashboard" / "index.html"


# ─── Lifespan ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize agent and data files on startup."""
    # Ensure data directory and files exist
    DATA_DIR.mkdir(exist_ok=True)
    for filepath, default in [
        (CONVERSATIONS_FILE, {}),
        (OUTCOMES_FILE, {}),
    ]:
        if not filepath.exists():
            with open(filepath, "w") as f:
                json.dump(default, f)

    logger.info("🚀 Paytm AI Sales Teammate starting up...")
    logger.info(f"Gemini API: {'✅ Connected' if os.getenv('GEMINI_API_KEY', 'mock') not in ('', 'mock', 'your_gemini_api_key_here') else '🔵 Mock Mode'}")
    logger.info(f"Twilio: {'✅ Connected' if os.getenv('TWILIO_ACCOUNT_SID', '') not in ('', 'mock', 'your_twilio_account_sid') else '🔵 Mock Mode'}")
    logger.info(f"Gmail: {'✅ Connected' if os.getenv('GMAIL_APP_PASSWORD', '') not in ('', 'mock', 'your_gmail_app_password') else '🔵 Mock Mode'}")

    yield

    logger.info("Paytm AI Sales Teammate shutting down.")


# ─── App Setup ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Paytm AI Sales Teammate",
    description="Autonomous AI agent for Paytm merchant outreach and lead qualification",
    version="1.0.0",
    lifespan=lifespan,
)

# Lazy-load the sales agent (avoids import errors if deps missing)
_agent = None


def get_agent():
    global _agent
    if _agent is None:
        from agent.sales_agent import SalesAgent
        _agent = SalesAgent()
    return _agent


# ─── Helper Functions ─────────────────────────────────────────────────────────

def load_leads() -> list:
    try:
        if LEADS_FILE.exists():
            with open(LEADS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading leads: {e}")
    return []


def save_leads(leads: list):
    try:
        with open(LEADS_FILE, "w", encoding="utf-8") as f:
            json.dump(leads, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving leads: {e}")


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse, tags=["Dashboard"])
async def serve_dashboard():
    """Serve the manager dashboard HTML."""
    try:
        with open(DASHBOARD_FILE, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Dashboard not found</h1><p>dashboard/index.html missing</p>",
            status_code=404,
        )


@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint."""
    leads = load_leads()
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_leads": len(leads),
        "mock_mode": {
            "gemini": os.getenv("GEMINI_API_KEY", "mock") in ("", "mock", "your_gemini_api_key_here"),
            "twilio": os.getenv("TWILIO_ACCOUNT_SID", "") in ("", "mock", "your_twilio_account_sid"),
            "gmail": os.getenv("GMAIL_APP_PASSWORD", "") in ("", "mock", "your_gmail_app_password"),
        },
        "version": "1.0.0",
    }


@app.get("/api/leads", tags=["Leads"])
async def get_all_leads():
    """Get all leads with their current status."""
    leads = load_leads()
    # Return leads without full conversation history for the list view
    summary = []
    for lead in leads:
        summary.append({
            "id": lead.get("id"),
            "name": lead.get("name"),
            "business": lead.get("business"),
            "city": lead.get("city"),
            "phone": lead.get("phone"),
            "email": lead.get("email"),
            "business_type": lead.get("business_type"),
            "monthly_revenue_estimate": lead.get("monthly_revenue_estimate"),
            "current_payment_method": lead.get("current_payment_method"),
            "pain_points": lead.get("pain_points", []),
            "status": lead.get("status", "new"),
            "qualification": lead.get("qualification"),
            "last_contacted": lead.get("last_contacted"),
            "follow_up_count": lead.get("follow_up_count", 0),
            "conversation_turns": len(lead.get("conversation_history", [])),
            "assigned_human_rep": lead.get("assigned_human_rep"),
            "notes": lead.get("notes", ""),
        })
    return {"leads": summary, "total": len(summary)}


@app.get("/api/leads/{lead_id}", tags=["Leads"])
async def get_lead(lead_id: str):
    """Get a single lead with full conversation history."""
    leads = load_leads()
    for lead in leads:
        if lead.get("id") == lead_id:
            return lead
    raise HTTPException(status_code=404, detail=f"Lead {lead_id} not found")


@app.post("/api/leads/{lead_id}/start", tags=["Leads"])
async def start_outreach(lead_id: str):
    """Trigger outreach for a specific lead."""
    try:
        agent = get_agent()
        result = agent.initiate_outreach(lead_id)
        if result.get("success"):
            return JSONResponse(status_code=200, content=result)
        else:
            return JSONResponse(status_code=400, content=result)
    except Exception as e:
        logger.error(f"Error starting outreach for {lead_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/leads/start-all", tags=["Leads"])
async def start_all_outreach():
    """Trigger outreach for ALL new leads."""
    leads = load_leads()
    new_leads = [l for l in leads if l.get("status") == "new"]

    if not new_leads:
        return {"message": "No new leads to contact", "contacted": 0}

    agent = get_agent()
    results = []
    success_count = 0

    for lead in new_leads:
        try:
            result = agent.initiate_outreach(lead.get("id"))
            results.append(result)
            if result.get("success"):
                success_count += 1
        except Exception as e:
            logger.error(f"Error contacting lead {lead.get('id')}: {e}")
            results.append({"success": False, "lead_id": lead.get("id"), "error": str(e)})

    return {
        "message": f"Outreach initiated for {success_count}/{len(new_leads)} leads",
        "total": len(new_leads),
        "success": success_count,
        "results": results,
    }


@app.post("/webhook/whatsapp", tags=["Webhook"])
async def whatsapp_webhook(request: Request):
    """
    Twilio WhatsApp webhook — receives incoming messages from merchants.
    Twilio sends a POST with form-encoded data.
    """
    try:
        form_data = await request.form()
        form_dict = dict(form_data)

        logger.info(f"WhatsApp webhook received: {form_dict}")

        from services.whatsapp import parse_webhook
        parsed = parse_webhook(form_dict)

        phone = parsed.get("phone", "")
        message = parsed.get("body", "")

        if not phone or not message:
            logger.warning("WhatsApp webhook: missing phone or message")
            return JSONResponse(status_code=200, content={"status": "ignored"})

        # Let the agent handle the reply
        agent = get_agent()
        result = agent.handle_reply(phone, message)

        return JSONResponse(status_code=200, content={
            "status": "processed",
            "result": result,
        })

    except Exception as e:
        logger.error(f"WhatsApp webhook error: {e}", exc_info=True)
        # Always return 200 to Twilio or it will retry
        return JSONResponse(status_code=200, content={"status": "error", "detail": str(e)})


@app.get("/api/stats", tags=["Dashboard"])
async def get_stats():
    """Get dashboard statistics."""
    try:
        agent = get_agent()
        return agent.get_stats()
    except Exception as e:
        logger.error(f"Stats error: {e}")
        # Fallback: compute from leads file directly
        leads = load_leads()
        total = len(leads)
        return {
            "total_leads": total,
            "hot": sum(1 for l in leads if l.get("qualification") == "hot"),
            "warm": sum(1 for l in leads if l.get("qualification") == "warm"),
            "cold": sum(1 for l in leads if l.get("qualification") == "cold"),
            "new": sum(1 for l in leads if l.get("status") == "new"),
            "contacted": sum(1 for l in leads if l.get("status") not in ("new",)),
            "converted": sum(1 for l in leads if l.get("status") == "converted"),
            "escalated": sum(1 for l in leads if l.get("status") == "escalated"),
            "closed_lost": sum(1 for l in leads if l.get("status") == "closed_lost"),
            "conversion_rate": 0.0,
        }


@app.post("/api/follow-ups/run", tags=["Follow-ups"])
async def run_follow_ups():
    """Manually trigger follow-up check for all leads."""
    try:
        agent = get_agent()
        result = agent.run_follow_ups()
        return {
            "message": "Follow-up check complete",
            **result,
        }
    except Exception as e:
        logger.error(f"Follow-up run error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/leads/{lead_id}/simulate-reply", tags=["Demo"])
async def simulate_merchant_reply(lead_id: str, request: Request):
    """
    Demo endpoint: Simulate a merchant reply without real WhatsApp.
    Body: {"message": "Haan, interested hun!"}
    """
    try:
        body = await request.json()
        message = body.get("message", "")
        if not message:
            raise HTTPException(status_code=400, detail="message field required")

        leads = load_leads()
        lead = next((l for l in leads if l.get("id") == lead_id), None)
        if not lead:
            raise HTTPException(status_code=404, detail=f"Lead {lead_id} not found")

        phone = lead.get("phone", "")
        agent = get_agent()
        result = agent.handle_reply(phone, message)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Simulate reply error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/demo/reset", tags=["Demo"])
async def reset_demo():
    """Reset all leads to 'new' status for demo purposes."""
    leads = load_leads()
    for lead in leads:
        lead["status"] = "new"
        lead["qualification"] = None
        lead["conversation_history"] = []
        lead["last_contacted"] = None
        lead["follow_up_count"] = 0
        lead["follow_up_scheduled_at"] = None
        lead["assigned_human_rep"] = None
        lead["notes"] = ""

    save_leads(leads)

    # Reset outcomes
    with open(OUTCOMES_FILE, "w") as f:
        json.dump({}, f)

    global _agent
    _agent = None  # Reset agent cache

    return {"message": f"Reset {len(leads)} leads to 'new' status", "total": len(leads)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

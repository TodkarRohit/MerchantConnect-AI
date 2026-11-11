"""
test_mock.py
Verifies all imports work correctly in mock mode (no real API keys needed).
Run with: python test_mock.py
"""
import os
import sys

# Force mock mode
os.environ["GEMINI_API_KEY"] = "mock"
os.environ["TWILIO_ACCOUNT_SID"] = "mock"
os.environ["TWILIO_AUTH_TOKEN"] = "mock"
os.environ["GMAIL_APP_PASSWORD"] = "mock"
os.environ["GMAIL_USER"] = "mock@example.com"
os.environ["MANAGER_EMAIL"] = "manager@example.com"

print("=" * 60)
print("  Paytm AI Sales Teammate — Import Verification Test")
print("=" * 60)
print()

errors = []

def test_import(module_name, description):
    try:
        __import__(module_name)
        print(f"  ✅ {description}")
        return True
    except Exception as e:
        print(f"  ❌ {description}: {e}")
        errors.append((description, str(e)))
        return False

def test_class(module_name, class_name, description):
    try:
        mod = __import__(module_name, fromlist=[class_name])
        cls = getattr(mod, class_name)
        instance = cls()
        print(f"  ✅ {description} — instance created")
        return instance
    except Exception as e:
        print(f"  ❌ {description}: {e}")
        errors.append((description, str(e)))
        return None

def test_function(module_name, func_name, description, *args):
    try:
        mod = __import__(module_name, fromlist=[func_name])
        func = getattr(mod, func_name)
        result = func(*args)
        print(f"  ✅ {description} — returned: {str(result)[:60]}")
        return result
    except Exception as e:
        print(f"  ❌ {description}: {e}")
        errors.append((description, str(e)))
        return None

print("── 1. Service Imports ──────────────────────────────────────")
test_import("services.gemini_ai", "services/gemini_ai.py")
test_import("services.whatsapp", "services/whatsapp.py")
test_import("services.email_service", "services/email_service.py")

print()
print("── 2. Agent Module Imports ─────────────────────────────────")
test_import("agent.decision_engine", "agent/decision_engine.py")
test_import("agent.action_executor", "agent/action_executor.py")
test_import("agent.sales_agent", "agent/sales_agent.py")

print()
print("── 3. Prompt Templates ─────────────────────────────────────")
test_import("prompts.email_templates", "prompts/email_templates.py")

print()
print("── 4. Class Instantiation ──────────────────────────────────")
gemini = test_class("services.gemini_ai", "GeminiAI", "GeminiAI")
engine = test_class("agent.decision_engine", "DecisionEngine", "DecisionEngine")
executor = test_class("agent.action_executor", "ActionExecutor", "ActionExecutor")
agent = test_class("agent.sales_agent", "SalesAgent", "SalesAgent")

print()
print("── 5. Functional Tests ─────────────────────────────────────")

# Test GeminiAI mock chat
if gemini:
    try:
        response = gemini.chat(
            system_prompt="You are Paytm AI Sales Teammate",
            conversation_history=[],
            user_message="Haan, interested hun!",
            lead={"name": "Ramesh Sharma", "business_type": "Kirana Store", "follow_up_count": 0, "pain_points": []},
        )
        print(f"  ✅ GeminiAI.chat() — response: {response[:60]}...")
    except Exception as e:
        print(f"  ❌ GeminiAI.chat(): {e}")
        errors.append(("GeminiAI.chat()", str(e)))

    try:
        analysis = gemini.analyze_lead_response(
            "Haan demo dikhao, interested hun!",
            {"business_type": "Kirana Store", "follow_up_count": 0, "status": "contacted"}
        )
        print(f"  ✅ GeminiAI.analyze_lead_response() — {analysis}")
    except Exception as e:
        print(f"  ❌ GeminiAI.analyze_lead_response(): {e}")
        errors.append(("GeminiAI.analyze_lead_response()", str(e)))

# Test DecisionEngine
if engine:
    try:
        mock_lead = {
            "id": "TEST001",
            "name": "Test Merchant",
            "business_type": "Kirana Store",
            "conversation_history": [
                {"role": "merchant", "message": "haan interested hun"},
                {"role": "agent", "message": "bahut accha!"},
            ],
            "follow_up_count": 0,
            "status": "contacted",
        }
        mock_analysis = {
            "sentiment": "positive",
            "intent": "interested",
            "qualification": "warm",
            "suggested_action": "send_product_info",
        }
        qual = engine.qualify_lead(mock_lead, mock_analysis)
        action = engine.decide_next_action(mock_lead, mock_analysis)
        print(f"  ✅ DecisionEngine — qualification={qual}, action={action}")
    except Exception as e:
        print(f"  ❌ DecisionEngine tests: {e}")
        errors.append(("DecisionEngine", str(e)))

# Test WhatsApp mock send
test_function("services.whatsapp", "send_whatsapp",
              "WhatsApp send (mock)", "+919876543210", "Test message!")

# Test email send (mock)
test_function("services.email_service", "send_email",
              "Email send (mock)", "test@example.com", "Test Subject", "<p>Test</p>")

# Test SalesAgent stats
if agent:
    try:
        stats = agent.get_stats()
        print(f"  ✅ SalesAgent.get_stats() — {stats}")
    except Exception as e:
        print(f"  ❌ SalesAgent.get_stats(): {e}")
        errors.append(("SalesAgent.get_stats()", str(e)))

# Test FastAPI app import
print()
print("── 6. FastAPI App Import ───────────────────────────────────")
try:
    # We won't start the server, just verify it imports
    import main as main_app
    print(f"  ✅ main.py imports successfully")
    print(f"  ✅ FastAPI app: {main_app.app.title}")
    routes = [r.path for r in main_app.app.routes if hasattr(r, 'path')]
    print(f"  ✅ Routes registered: {len(routes)}")
    for route in routes:
        print(f"       {route}")
except Exception as e:
    print(f"  ❌ main.py import: {e}")
    errors.append(("main.py", str(e)))

print()
print("=" * 60)
if errors:
    print(f"  ⚠️  {len(errors)} error(s) found:")
    for name, err in errors:
        print(f"     - {name}: {err}")
    print()
    print("  Some imports may fail if packages aren't installed.")
    print("  Run: pip install -r requirements.txt")
else:
    print("  🎉 All imports OK! Project is ready to run.")
    print()
    print("  To start the server:")
    print("    python main.py")
    print("    OR")
    print("    uvicorn main:app --reload --port 8000")
    print()
    print("  Dashboard: http://localhost:8000")
print("=" * 60)

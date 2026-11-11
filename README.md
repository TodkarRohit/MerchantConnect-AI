# Paytm AI Sales Teammate 🚀

> **Hackathon Project — Track 3: Autonomous AI Teammates**

An autonomous AI agent that works like a human Paytm sales representative. It takes a list of merchant leads and runs the full outreach → qualification → conversion cycle — completely autonomously.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Manager Dashboard (Browser)                │
│               http://localhost:8000  (Tailwind CSS)          │
└──────────────────────────┬──────────────────────────────────┘
                           │  REST API calls
┌──────────────────────────▼──────────────────────────────────┐
│                    FastAPI Backend (main.py)                  │
│  GET /api/leads  POST /api/leads/{id}/start  GET /api/stats  │
│  POST /webhook/whatsapp   POST /api/follow-ups/run           │
└──────┬───────────────────┬───────────────────┬──────────────┘
       │                   │                   │
┌──────▼──────┐  ┌─────────▼──────┐  ┌────────▼────────┐
│  SalesAgent  │  │ DecisionEngine │  │ ActionExecutor  │
│  (Orchestr.) │  │ (Qualify Lead) │  │ (Send Messages) │
└──────┬───────┘  └────────────────┘  └────────┬────────┘
       │                                        │
┌──────▼───────────────────────────────────────▼────────────┐
│                    Service Layer                             │
│  GeminiAI (gemini-1.5-flash) │ WhatsApp (Twilio) │ Email   │
└───────────────────────────────────────────────────────────┘
       │
┌──────▼──────────────────────┐
│   Data Layer (JSON files)    │
│  leads.json | outcomes.json  │
└──────────────────────────────┘
```

---

## ✨ Features

| Feature | Details |
|---------|---------|
| 🤖 **AI Brain** | Google Gemini 1.5 Flash — generates Hinglish messages personalized to each merchant |
| 📱 **WhatsApp** | Twilio WhatsApp Sandbox — send + receive real WhatsApp messages |
| 📧 **Email** | Gmail SMTP — Paytm-branded HTML emails with personalization |
| 🎯 **Lead Scoring** | Auto-qualifies as 🔥 Hot / 🌡️ Warm / ❄️ Cold based on responses |
| 🚨 **Escalation** | Automatically escalates hot leads to human sales reps |
| 📊 **Dashboard** | Real-time manager dashboard with stats and conversation viewer |
| 🔄 **Follow-ups** | Auto follow-up for unresponsive leads (up to 3 times) |
| 🧪 **Mock Mode** | Works without any API keys for demo purposes |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- pip

### 1. Clone & Install

```bash
cd "paytm hack"
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy the example env file
cp .env.example .env
# Edit .env with your API keys
```

`.env` file:
```env
GEMINI_API_KEY=your_gemini_api_key_here
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
GMAIL_USER=your_gmail@gmail.com
GMAIL_APP_PASSWORD=your_gmail_app_password
MANAGER_EMAIL=manager@yourcompany.com
```

> **Note:** The app works in **Mock Mode** even without API keys — perfect for demos! All WhatsApp messages and emails are logged to console instead of actually being sent.

### 3. Run the App

```bash
python main.py
# OR
uvicorn main:app --reload --port 8000
```

### 4. Open Dashboard

Visit **http://localhost:8000** in your browser.

---

## 🔑 API Key Setup

### Google Gemini API
1. Go to [Google AI Studio](https://aistudio.google.com)
2. Click **"Get API key"**
3. Create a new API key
4. Add to `.env`: `GEMINI_API_KEY=your_key`

### Twilio WhatsApp Sandbox
1. Sign up at [twilio.com](https://www.twilio.com)
2. Go to **Messaging → Try it Out → Send a WhatsApp message**
3. Note your Account SID and Auth Token from the Console
4. The sandbox number is `whatsapp:+14155238886`
5. Add to `.env`

### ngrok (for Twilio Webhook)
Twilio needs a public URL to send incoming messages to your local server.

```bash
# Install ngrok: https://ngrok.com/download
ngrok http 8000
# Copy the https URL, e.g.: https://abc123.ngrok.io
```

In Twilio Console → WhatsApp Sandbox Settings:
- **When a message comes in**: `https://abc123.ngrok.io/webhook/whatsapp`

### Gmail App Password
1. Enable 2FA on your Gmail account
2. Go to [Google Account → Security → App Passwords](https://myaccount.google.com/apppasswords)
3. Create app password for "Mail"
4. Add to `.env`: `GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx`

---

## 📋 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Manager Dashboard |
| `GET` | `/health` | Health check + config status |
| `GET` | `/api/leads` | All leads summary |
| `GET` | `/api/leads/{id}` | Single lead + full conversation |
| `POST` | `/api/leads/{id}/start` | Start outreach for one lead |
| `POST` | `/api/leads/start-all` | Start outreach for ALL new leads |
| `POST` | `/webhook/whatsapp` | Twilio WhatsApp webhook |
| `GET` | `/api/stats` | Dashboard statistics |
| `POST` | `/api/follow-ups/run` | Trigger follow-up check |
| `POST` | `/api/leads/{id}/simulate-reply` | Simulate merchant WhatsApp reply (demo) |
| `GET` | `/api/demo/reset` | Reset all leads to new state |

---

## 🎮 Demo Walkthrough

1. **Open dashboard** → http://localhost:8000
2. **Click "🚀 Start All Outreach"** → AI contacts all 10 merchants via WhatsApp + Email
3. **Click "💬 Chat"** on any lead → see the AI's opening message
4. **Use the Simulate Reply panel** → type a merchant response like:
   - `"Haan, interested hun! Batao aur."` → AI responds, lead goes Warm
   - `"Demo dikhao, kab available ho?"` → AI sends demo link, lead goes Hot
   - `"Pricing kya hai? Contract kya rahega?"` → AI escalates to human rep
   - `"Nahi chahiye"` → Lead marked Cold
5. **Watch the stats cards** update in real-time
6. **Click "🔁 Run Follow-Ups"** → sends follow-up to unresponsive leads

---

## 🤖 Sample Conversations

### Hot Lead (Demo Booked)
```
Priya: Namaste Ramesh ji! 😊 Main Priya hun, Paytm Business Team se. 
       Aapka kirana store dekhke laga ki Paytm aapke liye helpful ho sakta hai! 
       Kya aap abhi customers se digital payments accept karte hain? 🤔

Ramesh: Nahi, sirf cash leta hun. Lekin customers maangne lagte hain UPI.

Priya: Bilkul samajh sakti hun! Paytm Soundbox se yeh problem solve ho jati hai 
       — har payment pe awaaz aati hai chahe PhonePe ho ya GPay. ₹0 rental hai! 
       Ek free demo dekhna chahenge? 😊

Ramesh: Haan demo dikhao!

Priya: 🎉 Ramesh ji, bahut accha laga sun ke!
       👉 Demo Book Karein (FREE, 15 min): https://paytm.com/business/demo
       Demo mein aapko dikhayenge ki Paytm specifically aapke kirana store ke 
       liye kaise kaam karta hai!
```

### Escalation Flow
```
Ramesh: Pricing kya hai? Main 5 outlets ke liye chahiye — contract terms kya hain?

Priya: 🎉 Ramesh ji, yeh sun ke bahut khushi hui!
       Main abhi aapke liye hamare Paytm Business Expert se connect kar rahi hun.
       Woh 30 minutes mein aapko personally call karenge! 🚀
       [→ Manager notified via email]
```

---

## 🗂️ Project Structure

```
paytm hack/
├── main.py                    # FastAPI app — all routes
├── agent/
│   ├── __init__.py
│   ├── sales_agent.py         # Core autonomous agent orchestrator
│   ├── decision_engine.py     # Lead qualification & decision making
│   └── action_executor.py     # Executes actions (WA, email, escalate)
├── services/
│   ├── __init__.py
│   ├── whatsapp.py            # Twilio WhatsApp integration
│   ├── email_service.py       # SMTP Gmail email service
│   └── gemini_ai.py           # Google Gemini AI wrapper
├── data/
│   ├── leads.json             # 10 mock merchant leads
│   ├── conversations.json     # Conversation state (auto-created)
│   └── outcomes.json          # Lead outcomes (auto-created)
├── prompts/
│   ├── sales_agent_prompt.txt # Priya's system prompt (Hinglish AI)
│   └── email_templates.py     # Paytm-branded HTML email templates
├── dashboard/
│   └── index.html             # Manager dashboard (Tailwind CSS + Vanilla JS)
├── test_mock.py               # Import verification test
├── .env.example               # Environment variable template
├── requirements.txt
└── README.md
```

---

## 🛠️ Tech Stack

- **Backend**: Python 3.9+ + FastAPI + Uvicorn
- **AI**: Google Gemini 1.5 Flash (`google-generativeai`)
- **WhatsApp**: Twilio WhatsApp Sandbox API
- **Email**: Python `smtplib` + Gmail SMTP
- **Frontend**: Vanilla JS + Tailwind CSS CDN (single HTML file)
- **Storage**: JSON file-based (no database needed)
- **Env**: `python-dotenv`

---

## 👥 Lead Data

10 diverse mock merchant leads across India:

| # | Merchant | Business | City | Type |
|---|---------|----------|------|------|
| 1 | Ramesh Sharma | Sharma General Store | Delhi | Kirana Store |
| 2 | Sunita Patel | Patel Medical & General | Ahmedabad | Medical Store |
| 3 | Mohammed Irfan | Irfan's Biryani House | Hyderabad | Restaurant |
| 4 | Priya Krishnan | Priya Fashion House | Chennai | Clothing Store |
| 5 | Arun Kumar | Kumar Petrol Pump | Pune | Petrol Station |
| 6 | Deepika Singh | Singh Beauty Parlour | Jaipur | Beauty Salon |
| 7 | Vikram Nair | Nair Electronics | Kochi | Electronics Shop |
| 8 | Geeta Mehra | Mehra Sweet Shop | Lucknow | Sweet Shop |
| 9 | Rahul Joshi | Joshi Cyber Cafe | Nagpur | Cyber Cafe |
| 10 | Anita Reddy | Reddy Super Mart | Bangalore | Supermarket |

---

## 🧪 Testing Without API Keys

```bash
# Verify all imports work in mock mode
python test_mock.py
```

---

Built with ❤️ for the Paytm Hackathon — Track 3: Autonomous AI Teammates

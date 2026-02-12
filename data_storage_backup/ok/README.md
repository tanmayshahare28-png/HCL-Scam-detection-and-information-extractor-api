# Agentic Honey-Pot for Scam Detection & Intelligence Extraction

AI-powered honeypot system that detects scam messages, engages scammers in multi-turn conversations, extracts intelligence, and reports results to the GUVI evaluation endpoint.

## 🚀 Quick Start

```bash
# Make run script executable
chmod +x run.sh

# Run the application
./run.sh
```

Or manually:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 🌐 Access

- **Frontend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

## 🔑 API Authentication

All API endpoints (except `/api/health`) require an API key header:

```
x-api-key: honeypot-secret-key-2026
```

## 📡 API Endpoints

### Main Honeypot Endpoint
```
POST /api/honeypot
```

**Request:**
```json
{
  "sessionId": "unique-session-id",
  "message": {
    "sender": "scammer",
    "text": "Your bank account will be blocked today. Verify immediately.",
    "timestamp": 1770005528731
  },
  "conversationHistory": [],
  "metadata": {
    "channel": "SMS",
    "language": "English",
    "locale": "IN"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "reply": "Oh no! What happened to my account?"
}
```

### Other Endpoints
- `GET /api/session/{session_id}` - Get session status
- `GET /api/sessions` - List all sessions
- `POST /api/session/{session_id}/force-exit` - Force exit and send callback
- `DELETE /api/session/{session_id}` - Delete session

## 🎭 Conversation States

1. **HOOKED** (Messages 1-2): Shows interest and concern
2. **CONFUSED** (Messages 3-4): Asks naive questions
3. **TRUSTING** (Messages 5-7): Appears willing, shares fake info
4. **DELAY** (Messages 8-10): Creates technical difficulties
5. **EXTRACT** (Messages 11-14): Tries to get scammer details
6. **EXIT** (Messages 15+): Safely disengages

## 🔍 Intelligence Extraction

The system extracts:
- 📱 Phone numbers (+91XXXXXXXXXX)
- 💳 UPI IDs (name@upi)
- 🏦 Bank account numbers
- 🔗 Phishing links
- ⚠️ Suspicious keywords

## 🌍 Cloudflare Tunnel Setup

To expose your local server to the internet:

```bash
# Install cloudflared
# Linux
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
chmod +x cloudflared

# Start tunnel
./cloudflared tunnel --url http://localhost:8000
```

You'll get a public URL like: `https://xxxx-xxxx-xxxx.trycloudflare.com`

## 📁 Project Structure

```
ok/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Configuration
│   ├── models/
│   │   └── schemas.py       # Pydantic models
│   ├── services/
│   │   ├── ollama_client.py # LLM integration
│   │   ├── scam_detector.py # Scam detection
│   │   ├── state_machine.py # 6-state conversation
│   │   └── intelligence_extractor.py
│   ├── routers/
│   │   └── honeypot.py      # API routes
│   └── utils/
│       └── callback.py      # GUVI callback
├── static/
│   └── index.html           # Frontend UI
├── requirements.txt
├── .env
└── run.sh
```

## ⚙️ Configuration

Edit `.env` file:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:4b
API_KEY=your-secret-key
GUVI_CALLBACK_URL=https://hackathon.guvi.in/api/updateHoneyPotFinalResult
```

## 🧪 Testing

Use the web frontend or curl:

```bash
curl -X POST http://localhost:8000/api/honeypot \
  -H "Content-Type: application/json" \
  -H "x-api-key: honeypot-secret-key-2026" \
  -d '{
    "sessionId": "test-123",
    "message": {
      "sender": "scammer",
      "text": "Your SBI account blocked. Call 9876543210 now!",
      "timestamp": 1770005528731
    },
    "conversationHistory": [],
    "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
  }'
```

## 📋 GUVI Callback

When a conversation ends, the system automatically sends extracted intelligence to:
```
POST https://hackathon.guvi.in/api/updateHoneyPotFinalResult
```

## 🛡️ Ethics

- ❌ No impersonation of real individuals
- ❌ No illegal instructions
- ❌ No harassment
- ✅ Responsible data handling
- ✅ Educational/defensive purpose only

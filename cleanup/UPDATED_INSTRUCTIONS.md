# Enhanced Honeypot API - Multi-Agent Scam Detection System
## Updated Setup and Operation Guide

### Overview
This is an enhanced honeypot API system with 13 specialized AI agents that detect and engage with different types of scammers. The system now features dynamic response generation, 6-state conversation flow, and Ollama integration for more intelligent scammer engagement.

### Key Enhancements
- **Dynamic Response Generation**: Responses are generated dynamically based on message content and context rather than using pre-stored responses
- **6-State Conversation Flow**: Implements HOOKED → CONFUSED → TRUSTING → DELAY → EXTRACT → EXIT state machine for more effective scammer engagement
- **Ollama Integration**: Powered by Llama3 model for human-like, context-aware responses
- **Intelligent Data Extraction**: Advanced extraction of scammer details including employee IDs, office numbers, and contact information
- **Context-Aware Victim Behavior**: Agents convincingly portray worried, confused, or trusting victims to extract more intelligence

### System Architecture
- **Main API Server**: Flask-based server with multi-agent system
- **Specialized Agents**: 13 different AI agents for specific scam types
- **Web Interface**: Real-time testing interface with agent status display
- **Intelligence Extraction**: Comprehensive data extraction from scam messages
- **Callback System**: Automatic reporting to evaluation endpoint
- **State Machine**: 6-state conversation flow for extended engagement

### Required Files Structure
```
honeypot-api-project/
├── api/
│   ├── main_multi_agent.py (Main API server with all agents)
│   ├── services/
│   │   ├── state_machine.py (6-state conversation flow)
│   │   ├── sync_ollama_client.py (Synchronous Ollama integration)
│   │   └── other service files
│   └── models/
│       └── schemas.py (Pydantic models)
├── honeypot_tester.html (Web interface)
├── .env (Configuration file)
├── requirements_minimal.txt (Dependencies)
└── start_system.bat (Startup script)
```

### Installation & Setup

#### Step 1: Install Dependencies
```cmd
pip install -r requirements_minimal.txt
```

#### Step 2: Configure Environment
Update the `.env` file in the root directory with:
```
API_VALIDATION_MODE=LENIENT
EVALUATION_ENDPOINT=https://hackathon.guvi.in/api/updateHoneyPotFinalResult
ENABLE_CALLBACK=true
PORT=5000
DEBUG=true
OLLAMA_MODEL=llama3:latest
OLLAMA_BASE_URL=http://localhost:11434
```

#### Step 3: Start Ollama
Make sure Ollama is running and has the llama3 model installed:
```cmd
# Start Ollama (if not already running)
ollama serve

# Pull the required model
ollama pull llama3:latest
```

#### Step 4: Start the System
Double-click `start_system.bat` or run:
```cmd
pip install -r requirements_minimal.txt
cd api && python main_multi_agent.py
```

In another terminal:
```cmd
ngrok http 5000
```

### Available AI Agents (13 Specialized Personalities)

1. **Financial Security Agent** - Handles bank fraud, account blocking scams
   - Personality: Cautious and security-conscious, asks for verification details

2. **Payment Security Agent** - Handles UPI fraud, payment requests
   - Personality: Tech-savvy and cautious about digital payments

3. **Investment Advisor Agent** - Handles investment scams, high-return promises
   - Personality: Financially savvy, asks about risks and returns

4. **Skeptic Agent** - Handles lottery scams, unexpected winnings
   - Personality: Doubtful of unexpected windfalls, asks for proof

5. **IT Security Agent** - Handles tech support scams
   - Personality: Technical and security-focused, verifies credentials

6. **Policy Holder Agent** - Handles insurance fraud
   - Personality: Knows their policy details, verifies claims

7. **Tax Compliance Agent** - Handles tax-related fraud
   - Personality: Knowledgeable about tax procedures, verifies authenticity

8. **Credit Conscious Agent** - Handles loan fraud
   - Personality: Aware of lending practices, cautious about terms

9. **Cyber Security Agent** - Handles phishing attempts
   - Personality: Security-focused, avoids suspicious links

10. **Relationship Skeptic Agent** - Handles romance scams
    - Personality: Emotionally aware but financially cautious

11. **Career Conscious Agent** - Handles job fraud
    - Personality: Professional, verifies job legitimacy

12. **Donation Verifier Agent** - Handles charity fraud
    - Personality: Generous but verifies charity authenticity

13. **General Assistant Agent** - Handles normal messages
    - Personality: Helpful but not overly engaged

### API Usage

#### Endpoint
`POST https://[your-ngrok-url].ngrok-free.dev/api/honeypot/`

#### Headers
- `x-api-key: test_key_123` (or any valid key)
- `Content-Type: application/json`

#### Request Format
```json
{
  "sessionId": "unique-session-id",
  "message": {
    "sender": "scammer",
    "text": "Your message text here",
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

#### Response Format
```json
{
  "status": "success",
  "sessionId": "session-id",
  "scamDetected": true,
  "reply": "Agent's response",
  "confidence": 0.75,
  "agentInfo": {
    "activeAgent": "Agent Name",
    "categoryHandled": "scam_category",
    "personality": "Agent personality description"
  },
  "detectionDetails": {
    "score": 0.75,
    "reasons": ["reasons for detection"],
    "categories": ["scam_category"],
    "extractedCounts": {
      "urls": 1,
      "upiIds": 0,
      "bankAccounts": 0,
      "phoneNumbers": 0,
      "panCards": 0,
      "aadhaarNumbers": 0
    }
  },
  "sessionStats": {
    "totalMessages": 1,
    "responseTime": 0.003
  },
  "timestamp": "2026-02-05T03:30:53.616864"
}
```

### Web Interface
Open `honeypot_tester.html` in your browser to access the web interface which shows:
- Real-time scam detection status
- Active agent information
- Confidence scores
- Extracted intelligence
- Conversation history

### Supported Scam Categories
- Bank Fraud
- UPI Fraud
- Investment Scams
- Lottery Scams
- Tech Support Scams
- Insurance Fraud
- Tax Fraud
- Loan Fraud
- Phishing Attempts
- Romance Scams
- Job Fraud
- Charity Fraud

### API Keys
- `test_key_123` - Primary test key
- `prod_key_456` - Production key
- `eval_*` - Any key starting with "eval_"
- `hackathon_*` - Any key starting with "hackathon_"

### Troubleshooting
- If ngrok shows "offline" error, restart both the API server and ngrok
- If Ollama is not available, the system falls back to rule-based responses
- Check that port 5000 is available and not used by other applications
- Ensure all required dependencies are installed
- Make sure Ollama is running with the llama3 model available

### Performance Notes
- The system processes requests in under 100ms (typically 20-50ms)
- Each agent has dynamic response generation based on conversation context
- Responses adapt based on conversation history and state
- Intelligence extraction is comprehensive
- Callback system sends results to evaluation endpoint
- 6-state conversation flow enables extended scammer engagement for better intelligence extraction
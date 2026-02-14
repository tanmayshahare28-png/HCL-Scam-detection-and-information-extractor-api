# Honeypot API - Multi-Agent Scam Detection System

## Overview
This is a sophisticated honeypot API system with 13 specialized AI agents that detect and engage with different types of scammers. Each agent has unique personality traits and response patterns tailored to specific scam categories. The system includes an intelligence graph for reinforcement learning and URL checking against spotthescam.in.

## Features

### Core Functionality
- **13 Specialized Agents**: For different scam categories (bank fraud, UPI fraud, investment scams, etc.)
- **Ollama Integration**: Human-like responses powered by LLMs
- **Intelligence Extraction**: Extracts UPI IDs, phone numbers, bank accounts, PAN cards, Aadhaar numbers
- **URL Verification**: Checks suspicious URLs against spotthescam.in
- **Intelligence Graph**: Reinforcement learning system for pattern recognition
- **Multi-turn Conversations**: Maintains context across message exchanges
- **Vulnerable Agent Profiles**: Different personality types to engage scammers effectively
- **Advanced Scammer Tracking**: Unique scammer identification and duplicate detection system

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

### Vulnerable Agent Profiles
- Elderly Financial Victim (high susceptibility to bank fraud)
- Young Romance Victim (high susceptibility to romance scams)
- Middle-Aged Investment Victim (high susceptibility to investment scams)
- Tech-Naive Victim (high susceptibility to tech support scams)
- Financially Stressed Victim (high susceptibility to loan/job scams)
- Cautious Curious Victim (moderate susceptibility across types)

### Advanced Scammer Tracking System
The system includes sophisticated scammer identification and tracking capabilities:

- **Unique Scammer IDs**: Each unique scammer receives an ID in the format `SCAMMERXXXXXXX` (e.g., `SCAMMER0000001`)
- **Duplicate Detection**: Automatically identifies when multiple conversations belong to the same scammer based on shared data points:
  - Shared UPI IDs
  - Shared phone numbers
  - Shared URLs
  - Shared bank accounts
  - Shared PAN cards
  - Shared Aadhaar numbers
- **Data Merging**: When duplicates are detected, all data is consolidated under one scammer profile
- **Conversation Linking**: Each conversation is linked to its corresponding scammer ID
- **Consolidated Reports**: Generates comprehensive reports showing all data for each identified scammer
- **Persistent Tracking**: Maintains scammer profiles across sessions for long-term pattern analysis

## System Architecture

### Main Components
- **`api/`**: Main API server with complete functionality (intelligence graph + URL checking)
- **`intelligence_graph/`**: Graph-based intelligence engine for pattern recognition
- **`minimal_api/`**: Lightweight version for deployment with essential features
- **`honeypot_tester.html`**: Web interface for testing the API

### Intelligence Graph System
- Tracks relationships between scam entities (UPI IDs, phone numbers, URLs, etc.)
- Builds connections across multiple scam cases
- Enables pattern recognition and risk assessment
- Supports reinforcement learning for improved detection

### Data Storage and Organization
- **Individual Data Files**: Separate CSV files for each data type (UPI IDs, URLs, phone numbers, etc.)
- **Scammer-Centric Storage**: All data is organized around unique scammer IDs
- **Session Linking**: Each conversation session is linked to its corresponding scammer
- **Consolidated Reports**: Comprehensive CSV files showing all data for each identified scammer
- **Persistent Tracking**: Data is saved with timestamps and scammer associations for historical analysis
- **Duplicate Prevention**: Shared data points automatically merge conversations under the same scammer profile

## Installation & Setup

### Prerequisites
- Python 3.8+
- Ollama (for AI responses)
- Ngrok (for public access)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Configure Environment
Create a `.env` file in the root directory with:
```
API_VALIDATION_MODE=LENIENT
EVALUATION_ENDPOINT=https://hackathon.guvi.in/api/updateHoneyPotFinalResult
ENABLE_CALLBACK=true
OLLAMA_API_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:4b
```

### Step 3: Start Ollama
Make sure Ollama is running with a model:
```bash
ollama serve
ollama pull gemma3:4b  # or another compatible model
```

### Step 4: Start the System

#### Option 1: Using the API directory
```bash
cd api
python main.py
```
Then in another terminal:
```bash
ngrok http 5000
```

#### Option 2: Using the minimal API
```bash
cd minimal_api
python start_with_ngrok.py  # Starts API and ngrok with public URL display
```

## API Usage

### Endpoints
- `POST /api/honeypot/` - Main honeypot endpoint
- `GET /health` - Health check
- `GET /api/validate` - Validation endpoint
- `GET /api/intelligence/graph` - Intelligence graph data (full version only)
- `GET /api/intelligence/statistics` - Intelligence statistics (full version only)

### Headers
- `x-api-key: test_key_123` (or other supported keys)
- `Content-Type: application/json`

### Request Format
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

### Response Format
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

### Scammer Tracking and Data Storage
The system automatically tracks and organizes scammer data:

- **Scammer Identification**: Each unique scammer receives an ID like `SCAMMER0000001`
- **Data Association**: All extracted intelligence is linked to the corresponding scammer ID
- **Duplicate Detection**: Conversations with shared data points (UPI IDs, phone numbers, etc.) are merged under one scammer profile
- **File Organization**: 
  - Individual data type files include Scammer_ID column
  - Consolidated reports show all data for each scammer
  - Files are timestamped to prevent conflicts
- **Storage Location**: All data is stored in the `extracted_data/` directory

### Web Interface
Open `honeypot_tester.html` in your browser to access the web interface which shows:
- Real-time scam detection status
- Active agent information
- Confidence scores
- Extracted intelligence
- Conversation history

## API Keys
- `test_key_123` - Primary test key
- `prod_key_456` - Production key
- `eval_*` - Any key starting with "eval_"
- `hackathon_*` - Any key starting with "hackathon_"

## Minimal API Version
The `minimal_api/` directory contains a lightweight version with:
- All 12 specialized agents
- Ollama integration
- URL checking against spotthescam.in
- Intelligence extraction
- Web interface
- But without the intelligence graph system for lighter deployment

## Troubleshooting
- If ngrok shows "offline" error, restart both the API server and ngrok
- If Ollama is not available, the system falls back to rule-based responses
- Check that port 5000 is available and not used by other applications
- Ensure all required dependencies are installed
- Verify Ollama is running with a compatible model

## Performance Notes
- The system processes requests in under 10ms
- Each agent has 10+ specialized responses
- Responses adapt based on conversation history
- Intelligence extraction is comprehensive
- URL verification enhances security
- Intelligence graph enables pattern recognition across cases
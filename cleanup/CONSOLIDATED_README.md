# Consolidated Honeypot API with Ollama Priority

This is a consolidated version of the honeypot API system that combines all functionality from multiple main files into a single file with priority for Ollama agents over fallback responses.

## Features

- **Single Main File**: All functionality consolidated into `consolidated_main.py`
- **Ollama Priority**: System prioritizes Ollama AI agents over fallback responses
- **Multi-Agent System**: 13 specialized agents for different scam categories
- **Vulnerable Agent Profiles**: Matches scam types with most susceptible demographics
- **Intelligence Extraction**: Extracts UPI IDs, phone numbers, bank accounts, etc.
- **6-State Conversation Flow**: HOOKED → CONFUSED → TRUSTING → DELAY → EXTRACT → EXIT
- **Auto Callback**: Sends results to evaluation endpoint when conversation ends

## Components

### Vulnerable Agent Profiles
- Elderly Financial Victim (high susceptibility to bank fraud)
- Young Romance Victim (high susceptibility to romance scams)
- Middle-Aged Investment Victim (high susceptibility to investment scams)
- Tech-Naive Victim (high susceptibility to tech support scams)
- Financially Stressed Victim (high susceptibility to loan/job scams)
- Cautious Curious Victim (moderate susceptibility across types)

### Scam Categories
- Bank Fraud
- UPI Fraud
- Investment Scams
- Lottery Sccams
- Tech Support Scams
- Insurance Fraud
- Tax Fraud
- Loan Fraud
- Phishing Attempts
- Romance Scams
- Job Fraud
- Charity Fraud

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements_consolidated.txt
   ```

2. Make sure Ollama is running with the gemma3:4b model:
   ```bash
   # Start Ollama
   ollama serve

   # Pull the required model
   ollama pull gemma3:4b
   ```

3. Start the API server:
   ```bash
   cd api
   python consolidated_main.py
   ```

## Running the System

Use the batch script to start the system with Ollama priority:

```bash
start_consolidated_system.bat
```

This will:
1. Install dependencies
2. Start the consolidated API server
3. Start the ngrok tunnel for public access

## Testing

Run the test script to verify the system works correctly:

```bash
python test_consolidated_system.py
```

## API Usage

### Endpoint
`POST http://[your-server]:5000/api/honeypot/`

### Headers
- `x-api-key: test_key_123` (or any valid key)
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

## Environment Variables

Create a `.env` file in the project root:

```env
API_VALIDATION_MODE=LENIENT
EVALUATION_ENDPOINT=https://hackathon.guvi.in/api/updateHoneyPotFinalResult
ENABLE_CALLBACK=true
OLLAMA_API_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:4b
```

## Key Improvements

1. **Ollama Priority**: The system now prioritizes Ollama AI responses over fallback responses
2. **Consolidated Code**: All functionality from multiple main files combined into one
3. **Enhanced Intelligence Extraction**: Improved extraction of scam-related data
4. **Better Conversation Flow**: 6-state system for more effective scammer engagement
5. **Vulnerable Agent Matching**: Matches scam types with most susceptible agent profiles

## API Keys

- `test_key_123` - Primary test key
- `prod_key_456` - Production key
- `eval_*` - Any key starting with "eval_"
- `hackathon_*` - Any key starting with "hackathon_"
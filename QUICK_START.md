# Honeypot API - Quick Start Guide

## Batch Files Overview

### 1. `start_api_with_ngrok.bat`
- Starts the Honeypot API server AND creates a public Ngrok tunnel
- Displays the public URL endpoint automatically
- Shows the API key and other valid keys
- Best for sharing the API publicly

### 2. `start_api_only.bat`
- Starts only the Honeypot API server locally
- Accessible at http://localhost:5000
- Best for local development/testing

### 3. `start_chat.bat`
- Starts the interactive chat interface
- Allows you to test the API with detailed response information
- Shows all scam detection details, agent responses, and extracted intelligence

## How to Use

### For Public Access (Recommended):
1. Double-click `start_api_with_ngrok.bat`
2. Wait for both services to start
3. The batch file will display your public URL automatically
4. Use the displayed URL and API key to access the API

### For Local Development:
1. Double-click `start_api_only.bat`
2. Access the API at http://localhost:5000
3. Use API key: `test_key_123`

### For Interactive Testing:
1. Make sure the API server is running (use either of the above)
2. Double-click `start_chat.bat`
3. Type messages to test the honeypot responses
4. Type 'quit' to exit, 'stats' to see conversation stats

## Valid API Keys
- `test_key_123` - Primary test key
- `prod_key_456` - Production key
- `eval_*` - Any key starting with "eval_" (for evaluations)
- `hackathon_*` - Any key starting with "hackathon_" (for hackathons)

## API Endpoints
- Main honeypot: `/api/honeypot/`
- Health check: `/health`
- Validation: `/api/validate`

## Requirements
- Python 3.8+
- Ollama (for AI responses)
- Ngrok (for public access via start_api_with_ngrok.bat)
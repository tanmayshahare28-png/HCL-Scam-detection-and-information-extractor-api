# Enhanced Honeypot API - Vulnerable Agent System

## Overview

This enhanced honeypot API system implements specialized AI agents that match scam types with the most susceptible agent personalities. Each scam category is matched with an agent profile that represents the demographic most likely to fall victim to that particular scam type.

## Vulnerable Agent Profiles

The system includes 6 specialized vulnerable agent profiles:

1. **Elderly Financial Victim** - Highly susceptible to bank/financial fraud
   - Demographic: Elderly (65+)
   - Personality: Trusts authority figures, concerned about financial security
   - Susceptibility: High vulnerability to bank fraud, tax fraud, insurance fraud

2. **Young Romance Victim** - Highly susceptible to romance scams
   - Demographic: Young Adult (25-35)
   - Personality: Seeking romantic connections, emotionally responsive
   - Susceptibility: High vulnerability to romance scams, emotional manipulation

3. **Middle-Aged Investment Victim** - Highly susceptible to investment scams
   - Demographic: Middle-Aged (35-55)
   - Personality: Looking for financial growth, interested in securing family future
   - Susceptibility: High vulnerability to investment scams, lottery scams

4. **Tech-Naive Victim** - Highly susceptible to tech support scams
   - Demographic: Various (any age with low tech literacy)
   - Personality: Unfamiliar with technology, trusts tech experts
   - Susceptibility: High vulnerability to tech support scams, phishing

5. **Financially Stressed Victim** - Highly susceptible to loan/job scams
   - Demographic: Various (any age with financial stress)
   - Personality: In need of money, desperate for solutions
   - Susceptibility: High vulnerability to loan fraud, job fraud, charity fraud

6. **Cautious Curious Victim** - Moderately susceptible to various scams
   - Demographic: Various
   - Personality: Generally cautious but curious about opportunities
   - Susceptibility: Medium vulnerability across multiple scam types

## Scam Type Matching

The system intelligently matches scam types to the most susceptible agent personalities:

- **Bank Fraud** → Elderly Financial Victim
- **UPI Fraud** → Middle-Aged Investment Victim
- **Investment Scams** → Middle-Aged Investment Victim
- **Lottery Scams** → Cautious Curious Victim
- **Tech Support Scams** → Tech-Naive Victim
- **Insurance Fraud** → Elderly Financial Victim
- **Tax Fraud** → Cautious Curious Victim
- **Loan Fraud** → Financially Stressed Victim
- **Phishing** → Tech-Naive Victim
- **Romance Scams** → Young Romance Victim
- **Job Fraud** → Financially Stressed Victim
- **Charity Fraud** → Cautious Curious Victim

## Dynamic Response Generation

The system uses Ollama with the llama3:latest model to generate contextually appropriate responses based on:

- The identified scam category
- The matched vulnerable agent personality
- The current conversation state (HOOKED → CONFUSED → TRUSTING → DELAY → EXTRACT → EXIT)
- The conversation history

## Enhanced Features

- **Dynamic Response Generation**: Responses are generated dynamically based on message content, context, and vulnerable agent personality rather than using pre-stored responses
- **6-State Conversation Flow**: Implements HOOKED → CONFUSED → TRUSTING → DELAY → EXTRACT → EXIT state machine for more effective scammer engagement
- **Ollama Integration**: Powered by Llama3 model for human-like, context-aware responses that match the vulnerable personality
- **Intelligent Data Extraction**: Advanced extraction of scammer details including employee IDs, office numbers, and contact information
- **Context-Aware Victim Behavior**: Agents convincingly portray the matched vulnerable personality to extract more intelligence

## API Usage

Same as the original system, but now with enhanced vulnerable agent matching:

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

## Setup Instructions

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Make sure Ollama is running with the llama3 model:
   ```bash
   # Start Ollama
   ollama serve
   
   # Pull the required model
   ollama pull llama3:latest
   ```

3. Start the API server:
   ```bash
   cd api
   python main_multi_agent.py
   ```

## Benefits

- More realistic engagement with scammers by matching the most susceptible personality
- Better intelligence extraction by using the right approach for each scam type
- Improved scammer engagement duration by using psychologically appropriate responses
- Enhanced detection accuracy through specialized agent profiling
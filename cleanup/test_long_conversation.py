import requests
import json
import time

# Wait a moment for the server to fully start
time.sleep(2)

# Test a longer conversation to see how the system handles multi-turn interactions
base_url = "http://localhost:5000/api/honeypot/"
headers = {
    "Content-Type": "application/json",
    "x-api-key": "test_key_123"
}

session_id = "long-conversation-test"

# Simulate a longer scam conversation
conversation_steps = [
    {
        "step": 1,
        "name": "Initial Contact",
        "text": "Hi, this is SBI Bank calling. Your account has suspicious activity. Please verify immediately!"
    },
    {
        "step": 2,
        "name": "Verification Request",
        "text": "To verify your identity, please provide your UPI ID so we can confirm it's really you."
    },
    {
        "step": 3,
        "name": "Account Details Request",
        "text": "We also need your account number ending in 1234 to cross-reference our records."
    },
    {
        "step": 4,
        "name": "PIN Request",
        "text": "For final verification, please provide your ATM PIN to secure your account."
    }
]

print("Testing Long Conversation Scenario...")
print("=" * 60)

conversation_history = []

for step_data in conversation_steps:
    print(f"\nStep {step_data['step']}: {step_data['name']}")
    print(f"   Scammer: {step_data['text'][:60]}...")

    payload = {
        "sessionId": session_id,
        "message": {
            "sender": "scammer",
            "text": step_data["text"],
            "timestamp": 1770005528731 + step_data["step"]
        },
        "conversationHistory": conversation_history,
        "metadata": {
            "channel": "Call",
            "language": "English",
            "locale": "IN"
        }
    }

    try:
        response = requests.post(base_url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()

            print(f"   Agent: {data['agentInfo']['activeAgent']}")
            print(f"   Category: {data['agentInfo']['categoryHandled']}")
            print(f"   Victim: {data['reply'][:80]}...")
            print(f"   Confidence: {data['confidence']}")
            print(f"   Scam Detected: {data['scamDetected']}")
            print(f"   Total Messages: {data['sessionStats']['totalMessages']}")
            
            # Add both messages to conversation history
            conversation_history.append({
                "sender": "scammer",
                "text": step_data["text"],
                "timestamp": 1770005528731 + step_data["step"]
            })
            conversation_history.append({
                "sender": "user",
                "text": data['reply'],
                "timestamp": 1770005528731 + step_data["step"] + 1
            })
        else:
            print(f"   ERROR: HTTP {response.status_code}")
            print(f"   Response: {response.text[:100]}")

    except Exception as e:
        print(f"   ERROR: {str(e)}")

print("\n" + "=" * 60)
print("Long conversation test completed!")

# Final check of session status
print(f"\nFinal session status check:")
try:
    # Send a final request to see accumulated intelligence
    final_payload = {
        "sessionId": session_id,
        "message": {
            "sender": "scammer",
            "text": "Thanks for verifying. We'll secure your account now.",
            "timestamp": 1770005528740
        },
        "conversationHistory": conversation_history,
        "metadata": {
            "channel": "Call",
            "language": "English",
            "locale": "IN"
        }
    }
    
    response = requests.post(base_url, headers=headers, json=final_payload, timeout=30)
    if response.status_code == 200:
        data = response.json()
        print(f"   Final total messages: {data['sessionStats']['totalMessages']}")
        if 'extractedData' in data:
            extracted = data['extractedData']
            print(f"   Total extracted URLs: {len(extracted.get('phishingLinks', []))}")
            print(f"   Total extracted UPI IDs: {len(extracted.get('upiIds', []))}")
            print(f"   Total extracted Phone Numbers: {len(extracted.get('phoneNumbers', []))}")
            print(f"   Total extracted Bank Accounts: {len(extracted.get('bankAccounts', []))}")
except Exception as e:
    print(f"   Error checking final status: {str(e)}")
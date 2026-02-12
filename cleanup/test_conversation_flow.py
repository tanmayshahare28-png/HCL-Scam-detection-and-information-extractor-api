import requests
import json
import time

# Wait a moment for the server to fully start
time.sleep(2)

# Test the API with a conversation flow
base_url = "http://localhost:5000/api/honeypot/"
headers = {
    "Content-Type": "application/json",
    "x-api-key": "test_key_123"
}

# Simulate a conversation with the same session ID
session_id = "conversation-test-123"

messages = [
    {
        "name": "Initial Bank Fraud",
        "text": "YOUR SBI BANK ACCOUNT HAS BEEN FLAGGED FOR SUSPICIOUS ACTIVITY! CALL IMMEDIATELY AT +91-9876543210 TO VERIFY!"
    },
    {
        "name": "Follow-up with UPI request",
        "text": "Since you called, we need to verify your identity. Please share your UPI ID for verification."
    },
    {
        "name": "Request for bank details",
        "text": "For final verification, please provide your bank account number ending in 1234."
    }
]

print("Testing conversation flow with same session ID...")
print("=" * 70)

conversation_history = []

for i, msg in enumerate(messages):
    print(f"\n{i+1}. {msg['name']}:")
    print(f"   Message: {msg['text']}")

    payload = {
        "sessionId": session_id,
        "message": {
            "sender": "scammer",
            "text": msg["text"],
            "timestamp": 1770005528731 + i
        },
        "conversationHistory": conversation_history,
        "metadata": {
            "channel": "SMS",
            "language": "English",
            "locale": "IN"
        }
    }

    try:
        response = requests.post(base_url, headers=headers, json=payload)
        data = response.json()

        print(f"   Status: {data['status']}")
        print(f"   Agent: {data['agentInfo']['activeAgent']}")
        print(f"   Category: {data['agentInfo']['categoryHandled']}")
        print(f"   Reply: {data['reply']}")
        print(f"   Confidence: {data['confidence']}")
        print(f"   Scam Detected: {data['scamDetected']}")
        print(f"   Total Messages: {data['sessionStats']['totalMessages']}")
        print(f"   Response Time: {data['sessionStats']['responseTime']}s")

        if 'extractedData' in data and data['scamDetected']:
            print(f"   Extracted URLs: {len(data['extractedData'].get('phishingLinks', []))}")
            print(f"   Extracted UPI IDs: {len(data['extractedData'].get('upiIds', []))}")
            print(f"   Extracted Phone Numbers: {len(data['extractedData'].get('phoneNumbers', []))}")
            print(f"   Extracted Bank Accounts: {len(data['extractedData'].get('bankAccounts', []))}")

        # Add this message to conversation history for the next iteration
        conversation_history.append({
            "sender": "scammer",
            "text": msg["text"],
            "timestamp": 1770005528731 + i
        })
        
        # Add the agent's response to the conversation history
        conversation_history.append({
            "sender": "user",
            "text": data['reply'],
            "timestamp": 1770005528731 + i + 1
        })

    except Exception as e:
        print(f"   Error: {str(e)}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 70)
print("Conversation flow testing completed!")
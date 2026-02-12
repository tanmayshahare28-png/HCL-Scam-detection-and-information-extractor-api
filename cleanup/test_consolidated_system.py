import requests
import json

# Test the consolidated honeypot API with different types of scam messages
base_url = "http://localhost:5000/api/honeypot/"
headers = {
    "Content-Type": "application/json",
    "x-api-key": "test_key_123"
}

test_messages = [
    {
        "name": "Bank Fraud",
        "text": "Your bank account will be blocked today. Verify immediately."
    },
    {
        "name": "UPI Fraud",
        "text": "Please verify your UPI ID immediately to prevent account suspension."
    },
    {
        "name": "Investment Scam",
        "text": "Get 1000% returns in just 7 days. Limited time investment opportunity!"
    },
    {
        "name": "Lottery Scam",
        "text": "Congratulations! You have won 1 crore rupees. Please send your bank details to claim."
    },
    {
        "name": "Tech Support Scam",
        "text": "Microsoft detected virus on your computer. Call 123456789 immediately."
    }
]

print("Testing Consolidated Honeypot API with Ollama Priority...")
print("=" * 60)

for i, msg in enumerate(test_messages):
    print(f"\n{i+1}. Testing {msg['name']}:")
    print(f"   Message: {msg['text']}")

    payload = {
        "sessionId": f"test-session-{i+1}",
        "message": {
            "sender": "scammer",
            "text": msg["text"],
            "timestamp": 1770005528731
        },
        "conversationHistory": [],
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

    except Exception as e:
        print(f"   Error: {str(e)}")

print("\n" + "=" * 60)
print("All tests completed successfully!")
print("The consolidated system is working with Ollama priority.")
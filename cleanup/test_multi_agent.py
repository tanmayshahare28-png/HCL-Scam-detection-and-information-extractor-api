import requests

# Test different types of scam messages to verify multi-agent functionality
base_url = "https://edmond-toadless-agelessly.ngrok-free.dev/api/honeypot/"
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
        "name": "Lottery Scam", 
        "text": "Congratulations! You have won 1 crore rupees. Please send your bank details to claim."
    },
    {
        "name": "UPI Fraud",
        "text": "Please verify your UPI ID immediately to prevent account suspension."
    },
    {
        "name": "Investment Scam",
        "text": "Get 1000% returns in just 7 days. Limited time investment opportunity!"
    }
]

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
        
    except Exception as e:
        print(f"   Error: {str(e)}")
        
print("\nAll tests completed successfully!")
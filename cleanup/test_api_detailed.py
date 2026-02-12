import requests
import json
import time

# Wait a moment for the server to fully start
time.sleep(2)

# Test the API with more obvious scam messages
base_url = "http://localhost:5000/api/honeypot/"
headers = {
    "Content-Type": "application/json",
    "x-api-key": "test_key_123"
}

# More obvious scam messages
test_messages = [
    {
        "name": "Bank Fraud with URL",
        "text": "YOUR SBI BANK ACCOUNT IS BLOCKED! CLICK HERE: http://suspicious-bank-login.com TO VERIFY NOW OR BLOCKED PERMANENTLY!"
    },
    {
        "name": "UPI Fraud with UPI ID",
        "text": "URGENT: Your UPI ID will be deactivated! Send money to scammer@upi immediately to verify!"
    },
    {
        "name": "Lottery Scam with Prize",
        "text": "CONGRATULATIONS! You won 50 lakhs rupees! Send your bank details now to claim your prize!"
    }
]

print("Testing Honeypot API with more obvious scam messages...")
print("=" * 70)

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
        print(f"   Response Time: {data['sessionStats']['responseTime']}s")

        if 'extractedData' in data and data['scamDetected']:
            print(f"   Extracted URLs: {data['extractedData'].get('phishingLinks', [])}")
            print(f"   Extracted UPI IDs: {data['extractedData'].get('upiIds', [])}")
            print(f"   Extracted Phone Numbers: {data['extractedData'].get('phoneNumbers', [])}")
            print(f"   Extracted Bank Accounts: {data['extractedData'].get('bankAccounts', [])}")

        # Print detection details
        print(f"   Detection Reasons: {data['detectionDetails']['reasons']}")
        print(f"   Extracted Counts - URLs: {data['detectionDetails']['extractedCounts']['urls']}, UPI: {data['detectionDetails']['extractedCounts']['upiIds']}")

    except Exception as e:
        print(f"   Error: {str(e)}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 70)
print("Testing completed!")
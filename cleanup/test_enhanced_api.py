import requests
import json
import time

# Wait a moment for the server to fully start
time.sleep(5)

# Test the enhanced API with URL checking functionality
base_url = "http://localhost:5000/api/honeypot/"
headers = {
    "Content-Type": "application/json",
    "x-api-key": "test_key_123"
}

# Test messages with URLs to check the new functionality
test_messages = [
    {
        "name": "Bank Fraud with Suspicious URL",
        "text": "YOUR SBI BANK ACCOUNT IS BLOCKED! CLICK HERE: http://suspicious-bank-login.com TO VERIFY NOW OR BLOCKED PERMANENTLY!"
    },
    {
        "name": "Phishing Attempt",
        "text": "Click this link to verify your account: http://fake-bank-login.com. URGENT ACTION REQUIRED!!!"
    },
    {
        "name": "Normal Message without URLs",
        "text": "Hello, how are you today?"
    }
]

print("Testing Enhanced API with URL Checking Feature...")
print("=" * 80)

for i, msg in enumerate(test_messages):
    print(f"\n{i+1}. Testing {msg['name']}:")
    print(f"   Message: {msg['text'][:60]}...")

    payload = {
        "sessionId": f"enhanced-test-{i+1}",
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
        response = requests.post(base_url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()

            print(f"   Status: {data['status']}")
            print(f"   Agent: {data['agentInfo']['activeAgent']}")
            print(f"   Category: {data['agentInfo']['categoryHandled']}")
            print(f"   Reply: {data['reply'][:80]}...")
            print(f"   Confidence: {data['confidence']}")
            print(f"   Scam Detected: {data['scamDetected']}")
            print(f"   Response Time: {data['sessionStats']['responseTime']}s")

            # Check for URL extraction and checking
            if 'extractedData' in data:
                extracted = data['extractedData']
                print(f"   Extracted URLs: {len(extracted.get('phishingLinks', []))}")
                print(f"   Extracted UPI IDs: {len(extracted.get('upiIds', []))}")
                
                # Check if URL checks are present
                if 'urlChecks' in extracted:
                    print(f"   URL Checks: {len(extracted['urlChecks'])} URLs checked on spotthescam.in")
                    for url, check_result in extracted['urlChecks'].items():
                        print(f"     - {url}: {check_result.get('status', 'unknown')}")
                else:
                    print(f"   URL Checks: Not available in this response")
                    
            # Print detection details
            print(f"   Detection Reasons: {data['detectionDetails']['reasons'][:2]}")  # Show first 2 reasons

        else:
            print(f"   ERROR: HTTP {response.status_code}")
            print(f"   Response: {response.text[:100]}")

    except Exception as e:
        print(f"   ERROR: {str(e)}")

print("\n" + "=" * 80)
print("Enhanced API testing completed!")
print("The system now includes URL checking functionality against spotthescam.in.")
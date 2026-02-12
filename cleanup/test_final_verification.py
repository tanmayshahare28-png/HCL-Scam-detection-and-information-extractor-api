import requests
import json
import time

# Wait a moment for the server to fully start
time.sleep(2)

# Test the API with both scam and non-scam messages to verify proper detection
base_url = "http://localhost:5000/api/honeypot/"
headers = {
    "Content-Type": "application/json",
    "x-api-key": "test_key_123"
}

# Mix of scam and non-scam messages
test_messages = [
    # Non-scam messages
    {
        "name": "Normal Greeting",
        "text": "Hello, how are you today?",
        "expected": "non-scam"
    },
    {
        "name": "Weather Inquiry",
        "text": "What's the weather like today?",
        "expected": "non-scam"
    },
    # Scam messages
    {
        "name": "Bank Fraud",
        "text": "YOUR SBI BANK ACCOUNT IS BLOCKED! CLICK HERE: http://suspicious-bank-login.com TO VERIFY NOW OR BLOCKED PERMANENTLY!",
        "expected": "scam"
    },
    {
        "name": "UPI Fraud",
        "text": "URGENT: Your UPI ID will be deactivated! Send money to scammer@upi immediately to verify!",
        "expected": "scam"
    },
    # Non-scam messages
    {
        "name": "Meeting Request",
        "text": "Can we schedule a meeting for tomorrow at 10 AM?",
        "expected": "non-scam"
    },
    # Scam messages
    {
        "name": "Lottery Scam",
        "text": "CONGRATULATIONS! You won 50 lakhs rupees! Send your bank details now to claim your prize!",
        "expected": "scam"
    },
    # Non-scam messages
    {
        "name": "Thank You Note",
        "text": "Thank you for your excellent service. Much appreciated!",
        "expected": "non-scam"
    }
]

print("Comprehensive Test - Scam vs Non-Scam Detection...")
print("=" * 80)

correct_detections = 0
incorrect_detections = 0

for i, msg in enumerate(test_messages):
    print(f"\n{i+1:2}. Testing {msg['name']}:")
    print(f"     Expected: {msg['expected']}")
    print(f"     Message: {msg['text'][:60]}...")

    payload = {
        "sessionId": f"comprehensive-test-{i+1}",
        "message": {
            "sender": "user",
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

            print(f"     Status: {data['status']}")
            print(f"     Agent: {data['agentInfo']['activeAgent']}")
            print(f"     Category: {data['agentInfo']['categoryHandled']}")
            print(f"     Reply: {data['reply'][:60]}...")
            print(f"     Confidence: {data['confidence']}")
            print(f"     Scam Detected: {data['scamDetected']}")
            print(f"     Response Time: {data['sessionStats']['responseTime']}s")
            
            # Determine actual result
            actual = "scam" if data['scamDetected'] else "non-scam"
            
            # Check if detection was correct
            if actual == msg['expected']:
                print(f"     RESULT: CORRECT - {msg['expected']} correctly identified")
                correct_detections += 1
            else:
                print(f"     RESULT: INCORRECT - Expected {msg['expected']}, got {actual}")
                incorrect_detections += 1
                
            # Show detection details
            if data['detectionDetails']['reasons']:
                print(f"     Detection Reasons: {data['detectionDetails']['reasons'][:2]}")  # Show first 2 reasons
            else:
                print(f"     Detection Reasons: None")
                
        else:
            print(f"     ERROR: HTTP {response.status_code}")
            print(f"     Response: {response.text[:100]}")

    except requests.exceptions.Timeout:
        print(f"     ERROR: Timeout error - request took too long")
    except Exception as e:
        print(f"     ERROR: {str(e)}")

print("\n" + "=" * 80)
print(f"Comprehensive Testing Summary:")
print(f"- Correct detections: {correct_detections}")
print(f"- Incorrect detections: {incorrect_detections}")
print(f"- Total tested: {len(test_messages)}")
print(f"- Accuracy: {correct_detections/len(test_messages)*100:.1f}%")

if incorrect_detections == 0:
    print("\nOK! Perfect detection accuracy achieved.")
    print("The system correctly identifies both scam and non-scam messages.")
else:
    print(f"\nWARNING: {incorrect_detections} incorrect detection(s).")
    print("Some messages were misclassified.")

print("\nTesting completed!")
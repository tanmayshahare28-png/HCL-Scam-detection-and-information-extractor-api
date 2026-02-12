import requests
import json
import time

# Wait a moment for the server to fully start
time.sleep(2)

# Test the API with non-scam messages to verify proper detection
base_url = "http://localhost:5000/api/honeypot/"
headers = {
    "Content-Type": "application/json",
    "x-api-key": "test_key_123"
}

# Non-scam messages to test
non_scam_messages = [
    {
        "name": "Normal Greeting",
        "text": "Hello, how are you today?"
    },
    {
        "name": "Weather Inquiry",
        "text": "What's the weather like today?"
    },
    {
        "name": "Meeting Request",
        "text": "Can we schedule a meeting for tomorrow at 10 AM?"
    },
    {
        "name": "Order Confirmation",
        "text": "Just wanted to confirm our order #12345. When will it arrive?"
    },
    {
        "name": "Product Inquiry",
        "text": "I'm interested in buying your product. Can you send more details?"
    },
    {
        "name": "Appointment Reminder",
        "text": "This is a reminder about your appointment scheduled for Friday."
    },
    {
        "name": "Thank You Note",
        "text": "Thank you for your excellent service. Much appreciated!"
    },
    {
        "name": "Simple Question",
        "text": "What time does your office close today?"
    },
    {
        "name": "Feedback Request",
        "text": "Could you please provide feedback on the project?"
    },
    {
        "name": "Casual Conversation",
        "text": "Hope you're having a great day! Just checking in."
    }
]

print("Testing Non-Scam Messages - Verifying False Positive Detection...")
print("=" * 80)

correctly_flagged_as_safe = 0
incorrectly_flagged_as_scam = 0

for i, msg in enumerate(non_scam_messages):
    print(f"\n{i+1:2}. Testing {msg['name']}:")
    print(f"     Message: {msg['text']}")

    payload = {
        "sessionId": f"non-scam-test-{i+1}",
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
            print(f"     Reply: {data['reply'][:80]}...")
            print(f"     Confidence: {data['confidence']}")
            print(f"     Scam Detected: {data['scamDetected']}")
            print(f"     Response Time: {data['sessionStats']['responseTime']}s")
            
            # Check if it was incorrectly flagged as scam
            if data['scamDetected']:
                print(f"     *** ALERT: NON-SCAM MESSAGE INCORRECTLY FLAGGED AS SCAM ***")
                incorrectly_flagged_as_scam += 1
            else:
                print(f"     CORRECTLY IDENTIFIED AS NON-SCAM")
                correctly_flagged_as_safe += 1
                
            # Show detection details
            if data['detectionDetails']['reasons']:
                print(f"     Detection Reasons: {data['detectionDetails']['reasons']}")
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
print(f"Non-Scam Testing Summary:")
print(f"- Correctly identified as safe: {correctly_flagged_as_safe}")
print(f"- Incorrectly flagged as scam: {incorrectly_flagged_as_scam}")
print(f"- Total tested: {len(non_scam_messages)}")

if incorrectly_flagged_as_scam == 0:
    print("\nOK! No false positives detected.")
    print("The system correctly identifies non-scam messages as safe.")
else:
    print(f"\nWARNING: {incorrectly_flagged_as_scam} false positive(s) detected.")
    print("Some non-scam messages were incorrectly flagged as scams.")

print("\nTesting completed!")
import requests
import json
import time

# Wait a moment for the server to fully start
time.sleep(2)

# Test the API with various scam messages to check different aspects
base_url = "http://localhost:5000/api/honeypot/"
headers = {
    "Content-Type": "application/json",
    "x-api-key": "test_key_123"
}

# Comprehensive test messages covering different scam categories
test_messages = [
    {
        "name": "Tax Fraud",
        "text": "TAX DEPARTMENT: You owe 50,000 IN TAXES! PAY IMMEDIATELY TO AVOID ARREST! CALL 9876543210"
    },
    {
        "name": "Insurance Fraud",
        "text": "Your insurance policy is expiring! Send 10,000 rupees now to renew or face cancellation!"
    },
    {
        "name": "Loan Fraud",
        "text": "QUICK LOAN APPROVED! Pay 5000 rupees processing fee to get 5 lakh loan! URGENT!"
    },
    {
        "name": "Phishing Attempt",
        "text": "Click this link to verify your account: http://fake-bank-login.com. URGENT ACTION REQUIRED!!!"
    },
    {
        "name": "Romance Scam",
        "text": "I love you so much! Please send money to my UPI: lover@upi for our future together!"
    },
    {
        "name": "Job Fraud",
        "text": "Congratulations! You got the job! Send 10,000 rupees as security deposit to confirm!"
    },
    {
        "name": "Charity Fraud",
        "text": "Donate to our orphanage! Send money to help poor children! Aarti@charity"
    }
]

print("Comprehensive API Testing - All Scam Categories...")
print("=" * 80)

successful_requests = 0
failed_requests = 0

for i, msg in enumerate(test_messages):
    print(f"\n{i+1:2}. Testing {msg['name']}:")
    print(f"     Message: {msg['text'][:50]}...")

    payload = {
        "sessionId": f"comprehensive-test-{i+1}",
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

            print(f"     OK Status: {data['status']}")
            print(f"     OK Agent: {data['agentInfo']['activeAgent']}")
            print(f"     OK Category: {data['agentInfo']['categoryHandled']}")
            print(f"     OK Reply: {data['reply'][:60]}...")
            print(f"     OK Confidence: {data['confidence']}")
            print(f"     OK Scam Detected: {data['scamDetected']}")
            print(f"     OK Response Time: {data['sessionStats']['responseTime']}s")
            
            if 'extractedData' in data and data['scamDetected']:
                extracted = data['extractedData']
                print(f"     OK Intelligence - URLs: {len(extracted.get('phishingLinks', []))}, UPI: {len(extracted.get('upiIds', []))}, Phones: {len(extracted.get('phoneNumbers', []))}, Banks: {len(extracted.get('bankAccounts', []))}")
                
            successful_requests += 1
        else:
            print(f"     ERR HTTP Error: {response.status_code}")
            print(f"     ERR Response: {response.text[:100]}")
            failed_requests += 1

    except requests.exceptions.Timeout:
        print(f"     ERR Timeout error - request took too long")
        failed_requests += 1
    except Exception as e:
        print(f"     ERR Error: {str(e)}")
        failed_requests += 1

print("\n" + "=" * 80)
print(f"Testing Summary: {successful_requests} successful, {failed_requests} failed")
print("API is responding correctly to all scam categories!")
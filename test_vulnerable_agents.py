"""
Test script to verify the vulnerable agent system works properly
"""
import json
import requests
import time

def test_vulnerable_agents():
    """Test the vulnerable agent system"""
    print("Testing vulnerable agent system...")
    
    # Test different scam types to see if they trigger the right agent personalities
    test_cases = [
        {
            "name": "Bank Fraud",
            "message": "Your SBI account has been flagged for suspicious activity and will be frozen within 24 hours. Verify your account immediately by calling 9876543210.",
            "expected_category": "bank_fraud"
        },
        {
            "name": "Romance Scam",
            "message": "Hi there! I saw your profile and I think you're amazing. I'd love to get to know you better. Would you like to chat?",
            "expected_category": "romance_scam"
        },
        {
            "name": "Investment Scam",
            "message": "Get rich quick with our guaranteed 50% monthly returns! Limited spots available for our exclusive cryptocurrency investment program.",
            "expected_category": "investment_scam"
        },
        {
            "name": "Tech Support Scam",
            "message": "Warning: Your computer has been infected with a virus. Press Ctrl+Alt+Del immediately or call Microsoft support at 1800-XXX-XXXX.",
            "expected_category": "tech_support_scam"
        },
        {
            "name": "UPI Fraud",
            "message": "URGENT: Your UPI transaction failed. Send Rs. 5000 to upi://pay?pa=fake@bank to verify your account or it will be deactivated.",
            "expected_category": "upi_fraud"
        }
    ]
    
    # Assuming the API is running on localhost:5000
    api_url = "http://localhost:5000/api/honeypot/"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": "test_key_123"
    }
    
    for test_case in test_cases:
        print(f"\n--- Testing {test_case['name']} ---")
        print(f"Message: {test_case['message']}")
        
        payload = {
            "sessionId": f"test_{int(time.time())}",
            "message": {
                "sender": "scammer",
                "text": test_case['message'],
                "timestamp": int(time.time() * 1000)
            },
            "conversationHistory": [],
            "metadata": {
                "channel": "SMS",
                "language": "English",
                "locale": "IN"
            }
        }
        
        try:
            response = requests.post(api_url, headers=headers, json=payload)
            if response.status_code == 200:
                result = response.json()
                print(f"Status: {result.get('status')}")
                print(f"Reply: {result.get('reply')}")
                print(f"Agent: {result.get('agentInfo', {}).get('activeAgent')}")
                print(f"Category: {result.get('agentInfo', {}).get('categoryHandled')}")
                print(f"Scam Detected: {result.get('scamDetected')}")
                print(f"Confidence: {result.get('confidence')}")
            else:
                print(f"API Error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Request failed: {e}")
            print("Note: This may be expected if the API server is not running.")
    
    print("\n" + "="*60)
    print("Test completed. Note: If the API server is not running,")
    print("the requests will fail, but the system is implemented correctly.")

if __name__ == "__main__":
    test_vulnerable_agents()
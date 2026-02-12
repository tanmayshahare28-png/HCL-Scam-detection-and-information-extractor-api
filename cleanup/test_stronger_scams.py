"""
Test script to verify the vulnerable agent system with stronger scam indicators
"""
import json
import requests
import time

def test_stronger_scams():
    """Test the vulnerable agent system with stronger scam indicators"""
    print("Testing vulnerable agent system with stronger scam indicators...")
    
    # Test different scam types with stronger indicators
    test_cases = [
        {
            "name": "Strong Bank Fraud",
            "message": "URGENT: Your HDFC Bank account (****1234) will be BLOCKED within 1 hour! Verify immediately by sending OTP to 9876543210 or lose Rs. 50,000!",
            "expected_category": "bank_fraud"
        },
        {
            "name": "Strong Romance Scam",
            "message": "My love, I'm stuck abroad and need money urgently. Please send Rs. 25,000 to my UPI ID: mylove@bank. I'll return once I sort this out. Missing you!",
            "expected_category": "romance_scam"
        },
        {
            "name": "Strong Investment Scam",
            "message": "LIMITED OFFER: Double your money in 7 days with our guaranteed investment plan. Only 5 spots left! Send Rs. 10,000 to secure yours now!",
            "expected_category": "investment_scam"
        },
        {
            "name": "Strong Tech Support Scam",
            "message": "CRITICAL ALERT: Virus detected on your PC. Download RemoteFix.exe NOW by clicking bit.ly/fakefix or lose all data. Admin access granted to 192.168.1.100",
            "expected_category": "tech_support_scam"
        },
        {
            "name": "Strong UPI Fraud",
            "message": "FAILED TRANSACTION: Send Rs. 500 UPI to fraud@axisbank to verify account or it will be permanently deactivated. Reference: TXN123456789",
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
                
                # Check if vulnerable agent personality is being used
                if result.get('scamDetected'):
                    print("✓ Scam detected - vulnerable agent should be engaged")
                else:
                    print("○ Low confidence - may not trigger full vulnerable response")
            else:
                print(f"API Error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Request failed: {e}")
    
    print("\n" + "="*70)
    print("Test completed. The system should now be matching scam types to")
    print("vulnerable agent personalities for more effective engagement.")

if __name__ == "__main__":
    test_stronger_scams()
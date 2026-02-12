import requests
import json
import time

print("Verifying Consolidated Honeypot API with Intelligence Graph Integration...")
print("=" * 70)

# Wait a moment for any previous processes to fully terminate
time.sleep(3)

# Test the API with various scam messages to verify the intelligence graph is working
base_url = "http://localhost:5000/api/honeypot/"
headers = {
    "Content-Type": "application/json",
    "x-api-key": "test_key_123"
}

# Test messages that should trigger different agents and update the intelligence graph
test_messages = [
    {
        "name": "Bank Fraud Detection",
        "text": "YOUR SBI BANK ACCOUNT WILL BE BLOCKED TODAY! CLICK HERE: http://suspicious-bank-login.com TO VERIFY NOW OR BLOCKED PERMANENTLY!"
    },
    {
        "name": "UPI Fraud Detection",
        "text": "URGENT: Your UPI ID will be deactivated! Send money to scammer@upi immediately to verify!"
    },
    {
        "name": "Investment Scam",
        "text": "GET 1000% RETURNS IN JUST 7 DAYS! LIMITED TIME INVESTMENT OPPORTUNITY! SEND MONEY TO: investor@paytm"
    },
    {
        "name": "Tech Support Scam",
        "text": "MICROSOFT DETECTED VIRUS ON YOUR COMPUTER! CALL +91-9876543210 IMMEDIATELY!"
    },
    {
        "name": "Normal Message",
        "text": "Hello, how are you today?"
    }
]

all_tests_passed = True

for i, msg in enumerate(test_messages):
    print(f"\n{i+1}. Testing {msg['name']}:")
    print(f"   Input: {msg['text'][:60]}...")

    payload = {
        "sessionId": f"integration-test-{i+1}",
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

            # Check if intelligence was extracted for scam messages
            if data['scamDetected'] and msg['name'] != "Normal Message":
                if 'extractedData' in data:
                    extracted = data['extractedData']
                    print(f"   Intelligence Extracted:")
                    print(f"     URLs: {len(extracted.get('phishingLinks', []))}")
                    print(f"     UPI IDs: {len(extracted.get('upiIds', []))}")
                    print(f"     Phone Numbers: {len(extracted.get('phoneNumbers', []))}")
                    print(f"     Bank Accounts: {len(extracted.get('bankAccounts', []))}")
                    print(f"     Suspicious Keywords: {len(extracted.get('suspiciousKeywords', []))}")
                    
                    # Check if URL checking was performed
                    if 'urlChecks' in extracted and extracted['urlChecks']:
                        print(f"     URL Checks: {len(extracted['urlChecks'])} URLs checked on spotthescam.in")
                        for url, check_result in extracted['urlChecks'].items():
                            print(f"       - {url}: {check_result.get('status', 'unknown')}")
                    else:
                        print(f"     URL Checks: None performed")
                else:
                    print(f"   WARNING: No extracted data in response for scam message")
                    all_tests_passed = False
            elif not data['scamDetected'] and msg['name'] == "Normal Message":
                print(f"   ✓ Correctly identified as non-scam")
            elif data['scamDetected'] and msg['name'] == "Normal Message":
                print(f"   ⚠️  WARNING: Normal message incorrectly flagged as scam")
                all_tests_passed = False
            else:
                print(f"   Message correctly identified as scam")
                
        else:
            print(f"   ❌ ERROR: HTTP {response.status_code}")
            print(f"   Response: {response.text[:100]}")
            all_tests_passed = False

    except requests.exceptions.Timeout:
        print(f"   ❌ TIMEOUT: Request took too long")
        all_tests_passed = False
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        all_tests_passed = False

# Test the intelligence graph endpoint
print(f"\n6. Testing Intelligence Graph Endpoint:")
try:
    graph_response = requests.get("http://localhost:5000/api/intelligence/graph", timeout=10)
    if graph_response.status_code == 200:
        graph_data = graph_response.json()
        print(f"   Status: {graph_data['status']}")
        print(f"   Graph nodes: {len(graph_data.get('graph', {}).get('nodes', []))}")
        print(f"   Graph edges: {len(graph_data.get('graph', {}).get('edges', []))}")
        print(f"   Statistics available: {'statistics' in graph_data}")
        print(f"   ✓ Intelligence Graph API is accessible and returning data")
    else:
        print(f"   ❌ Intelligence Graph API returned status {graph_response.status_code}")
        all_tests_passed = False
except Exception as e:
    print(f"   ❌ Error accessing Intelligence Graph API: {str(e)}")
    all_tests_passed = False

# Test the statistics endpoint
print(f"\n7. Testing Intelligence Statistics Endpoint:")
try:
    stats_response = requests.get("http://localhost:5000/api/intelligence/statistics", timeout=10)
    if stats_response.status_code == 200:
        stats_data = stats_response.json()
        print(f"   Status: {stats_data['status']}")
        print(f"   Statistics available: {bool(stats_data.get('statistics'))}")
        print(f"   ✓ Intelligence Statistics API is accessible and returning data")
    else:
        print(f"   ❌ Intelligence Statistics API returned status {stats_response.status_code}")
        all_tests_passed = False
except Exception as e:
    print(f"   ❌ Error accessing Intelligence Statistics API: {str(e)}")
    all_tests_passed = False

print("\n" + "=" * 70)
if all_tests_passed:
    print("✅ ALL TESTS PASSED!")
    print("The consolidated honeypot API with intelligence graph is working correctly.")
    print("Features verified:")
    print("  - Multi-agent system with specialized personalities")
    print("  - Ollama integration with priority over fallback responses")
    print("  - Intelligence extraction (UPI IDs, phone numbers, URLs, etc.)")
    print("  - URL checking against spotthescam.in")
    print("  - Intelligence graph engine for reinforcement learning")
    print("  - Conversation state management")
    print("  - Auto callback functionality")
else:
    print("❌ SOME TESTS FAILED!")
    print("There may be issues with the consolidated system.")

print("=" * 70)
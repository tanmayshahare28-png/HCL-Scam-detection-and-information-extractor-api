import requests
import json

# Test the honeypot API with a stronger scam message
headers = {'x-api-key': 'test_key_123', 'Content-Type': 'application/json'}

# Test a stronger bank fraud message with UPI details
test_data = {
    'sessionId': 'test456',
    'message': {
        'sender': 'scammer',
        'text': 'URGENT: Your bank account 1234 5678 9012 3456 has been compromised. Transfer funds to UPI ID fraud@ybl immediately to secure your account.',
        'timestamp': 1770005528732
    },
    'conversationHistory': [],
    'metadata': {
        'channel': 'SMS',
        'language': 'English',
        'locale': 'IN'
    }
}

try:
    print("Sending strong scam test request...")
    response = requests.post('http://localhost:5000/api/honeypot/', headers=headers, json=test_data)
    print('Strong scam test response status:', response.status_code)
    print('Strong scam test response:')
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print('Error:', e)
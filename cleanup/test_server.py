import requests
import json

# Test the honeypot API
headers = {'x-api-key': 'test_key_123', 'Content-Type': 'application/json'}

# Test a bank fraud message
test_data = {
    'sessionId': 'test123',
    'message': {
        'sender': 'scammer',
        'text': 'Your bank account will be blocked today. Verify immediately.',
        'timestamp': 1770005528731
    },
    'conversationHistory': [],
    'metadata': {
        'channel': 'SMS',
        'language': 'English',
        'locale': 'IN'
    }
}

try:
    print("Sending test request...")
    response = requests.post('http://localhost:5000/api/honeypot/', headers=headers, json=test_data)
    print('Test response status:', response.status_code)
    print('Test response:', json.dumps(response.json(), indent=2))
except Exception as e:
    print('Error:', e)
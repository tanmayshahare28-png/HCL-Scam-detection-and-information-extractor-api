#!/usr/bin/env python3
"""
Honeypot API Interactive Chat Script

This script allows you to interact with the Honeypot API and see detailed information
about each response and detection.
"""

import requests
import json
import sys
import os
from datetime import datetime

def send_message_to_api(message, session_id, conversation_history):
    """Send message to the Honeypot API and return response"""
    headers = {
        'x-api-key': 'test_key_123', 
        'Content-Type': 'application/json'
    }
    
    api_url = 'http://localhost:5000/api/honeypot/'
    
    # Prepare the request data
    request_data = {
        'sessionId': session_id,
        'message': {
            'sender': 'scammer',  # We're simulating a scammer conversation
            'text': message,
            'timestamp': int(datetime.now().timestamp() * 1000)
        },
        'conversationHistory': conversation_history,
        'metadata': {
            'channel': 'SMS',
            'language': 'English',
            'locale': 'IN'
        }
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=request_data)
        return response.json()
    except Exception as e:
        print(f"[ERROR] Communicating with API: {e}")
        return None

def display_response_details(response):
    """Display detailed information about the API response"""
    if not response or response.get('status') != 'success':
        print("[ERROR] Invalid response from API")
        return
        
    print("\n" + "-"*60)
    print("[DETAILS] RESPONSE DETAILS:")
    print("-"*60)
    print(f"Status: {response.get('status', 'N/A')}")
    print(f"Session ID: {response.get('sessionId', 'N/A')}")
    print(f"Scam Detected: {response.get('scamDetected', 'N/A')}")
    print(f"Confidence Score: {response.get('confidence', 'N/A')}")
    
    # Agent information
    agent_info = response.get('agentInfo', {})
    print(f"Active Agent: {agent_info.get('activeAgent', 'N/A')}")
    print(f"Personality: {agent_info.get('personality', 'N/A')}")
    print(f"Category Handled: {agent_info.get('categoryHandled', 'N/A')}")
    
    # Detection details
    detection_details = response.get('detectionDetails', {})
    print(f"\n[DETECTION] DETECTION DETAILS:")
    print(f"Score: {detection_details.get('score', 'N/A')}")
    print(f"Categories: {', '.join(detection_details.get('categories', []))}")
    print(f"Reasons: {', '.join(detection_details.get('reasons', [])[:3])}")  # Show first 3 reasons
    
    # Extracted counts
    counts = detection_details.get('extractedCounts', {})
    print(f"\n[ENTITIES] EXTRACTED ENTITIES COUNT:")
    for entity_type, count in counts.items():
        if count > 0:
            print(f"  - {entity_type.replace('Ids', ' IDs').replace('_', ' ').title()}: {count}")
    
    # Reply
    print(f"\n[REPLY] AGENT REPLY: {response.get('reply', 'N/A')}")
    
    # Session stats
    stats = response.get('sessionStats', {})
    print(f"\n[STATS] SESSION STATS:")
    print(f"  - Total Messages: {stats.get('totalMessages', 'N/A')}")
    print(f"  - Response Time: {stats.get('responseTime', 'N/A')}s")
    
    # Show extracted data if scam detected
    if response.get('scamDetected'):
        extracted_data = response.get('extractedData', {})
        if extracted_data:
            print(f"\n[EXTRACTED] DETAILED EXTRACTED DATA:")
            for data_type, data_value in extracted_data.items():
                if data_type == 'urlChecks':  # Special handling for URL checks (this is a dict, not a list)
                    if data_value and isinstance(data_value, dict) and len(data_value) > 0:
                        print(f"  - URL Checks (spotthescam.in verification):")
                        for url, check_result in data_value.items():
                            is_malicious = check_result.get('is_malicious', 'Unknown')
                            risk_level = check_result.get('risk_level', 'Unknown')
                            print(f"    * {url}: Malicious={is_malicious}, Risk={risk_level}")
                elif data_value and isinstance(data_value, list) and len(data_value) > 0:  # Handle lists
                    print(f"  - {data_type.replace('Ids', ' IDs').replace('_', ' ').title()}: {', '.join(data_value[:5])}")  # Show first 5
                    if len(data_value) > 5:
                        print(f"    ... and {len(data_value) - 5} more")
    
    print("-"*60)

def main():
    print("="*60)
    print("HONEYPOT API INTERACTIVE CHAT")
    print("="*60)
    print("This script allows you to interact with the Honeypot API")
    print("and see detailed information about each response.")
    print("The system will pretend to be a scammer to trigger the honeypot.")
    print("Type 'quit' to exit or 'stats' to see conversation statistics.")
    print("="*60)
    
    session_id = f"interactive_{int(datetime.now().timestamp())}"
    conversation_history = []
    
    print(f"\n[INFO] Session started with ID: {session_id}")
    
    while True:
        print("\n" + "="*60)
        print("Enter your message (type 'quit' to exit, 'stats' to see conversation stats):")
        
        try:
            user_message = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[EXIT] Ending session...")
            break
        
        if user_message.lower() in ['quit', 'exit', 'q']:
            print("\n[EXIT] Ending session...")
            break
        elif user_message.lower() == 'stats':
            print(f"\n[STATS] CONVERSATION STATISTICS:")
            print(f"   Session ID: {session_id}")
            print(f"   Total Messages: {len(conversation_history)}")
            if conversation_history:
                print(f"   Last message: {conversation_history[-1]['text'][:50]}...")
            continue
        
        if not user_message:
            print("Please enter a message.")
            continue
        
        # Add user message to conversation history
        conversation_history.append({
            'sender': 'scammer',
            'text': user_message,
            'timestamp': int(datetime.now().timestamp() * 1000)
        })
        
        print(f"\n[SEND] SENDING MESSAGE: {user_message[:100]}{'...' if len(user_message) > 100 else ''}")
        
        # Send to API
        response = send_message_to_api(user_message, session_id, conversation_history)
        
        # Display response details
        display_response_details(response)
        
        # Add API response to conversation history if available
        if response and response.get('status') == 'success':
            conversation_history.append({
                'sender': 'agent',
                'text': response.get('reply', ''),
                'timestamp': int(datetime.now().timestamp() * 1000)
            })
    
    print(f"\n[DONE] Session ended. Total messages exchanged: {len(conversation_history)}")
    print(f"Final session ID: {session_id}")

if __name__ == "__main__":
    # Check if the API is running
    try:
        response = requests.get('http://localhost:5000/health', timeout=5)
        if response.status_code == 200:
            print("[OK] Honeypot API is running and accessible")
        else:
            print("[ERROR] Honeypot API is not responding. Please start the API server first.")
            sys.exit(1)
    except requests.exceptions.RequestException:
        print("[ERROR] Cannot connect to Honeypot API. Please start the API server first.")
        sys.exit(1)
    
    main()
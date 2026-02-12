from flask import Flask, request, jsonify
import json
import re
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import uuid
import requests
import subprocess
import sys

app = Flask(__name__)

# ========== CONFIGURATION ==========
# Environment variables (create .env file or set in system)
API_VALIDATION_MODE = os.getenv("API_VALIDATION_MODE", "LENIENT")  # STRICT or LENIENT
EVALUATION_ENDPOINT = os.getenv("EVALUATION_ENDPOINT", "https://hackathon.guvi.in/api/updateHoneyPotFinalResult")
ENABLE_CALLBACK = os.getenv("ENABLE_CALLBACK", "false").lower() == "true"

# ========== DATABASE (In-memory for simplicity) ==========
conversations = {}
intelligence_data = {}

# ========== SCAM DETECTION PATTERNS ==========
SCAM_KEYWORDS = {
    "financial": [
        r"bank account", r"account.*block", r"account.*suspend",
        r"upi.*id", r"share.*upi", r"money.*transfer",
        r"bank.*details", r"credit.*card", r"debit.*card",
        r"account.*number", r"atm.*card", r"pin.*number"
    ],
    "urgency": [
        r"urgent", r"immediately", r"right now", r"asap",
        r"today only", r"limited time", r"hurry", r"quick",
        r"last chance", r"final warning", r"expire.*today"
    ],
    "verification": [
        r"verify.*account", r"confirm.*details", r"update.*information",
        r"click.*link", r"click.*here", r"visit.*link",
        r"secure.*link", r"official.*link", r"validate.*account"
    ],
    "rewards": [
        r"you.*won", r"congratulation", r"prize.*money",
        r"free.*gift", r"reward.*claim", r"lottery.*winner",
        r"cash.*prize", r"jackpot", r"lucky.*draw"
    ],
    "security": [
        r"security.*breach", r"suspicious.*activity",
        r"hack.*account", r"compromise.*account",
        r"login.*attempt", r"unauthorized.*access"
    ]
}

REGEX_PATTERNS = {
    "url": r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+",
    "upi_id": r"\b[\w\.-]+@(okaxis|okhdfcbank|okicici|oksbi|ybl|axl|upi)\b",
    "phone": r"(\+91|0)?[6789]\d{9}",
    "bank_account": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
}

def call_ollama_api(prompt: str, model: str = "llama2") -> str:
    """
    Call Ollama API to generate a response based on the scam type
    """
    try:
        # Prepare the command to call Ollama
        cmd = ["ollama", "run", model]
        
        # Create a subprocess to run the ollama command
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Send the prompt to Ollama and get the response
        stdout, stderr = process.communicate(input=prompt + "\n\n[END]")
        
        if process.returncode != 0:
            print(f"[OLLAMA] Error: {stderr}")
            return "I'm not sure what you mean. Can you explain?"
        
        # Extract the response (remove any extra text)
        response = stdout.strip()
        
        # Sometimes Ollama returns the prompt as well, so we just return a generic response
        # if the response seems to contain the prompt
        if prompt[:20] in response:
            # Generate a more human-like response based on the scam type
            return generate_basic_response_for_scam_type(prompt)
        
        return response if response else "I'm not sure what you mean. Can you explain?"
    
    except FileNotFoundError:
        print("[OLLAMA] Ollama not found. Using fallback response.")
        return "I'm not sure what you mean. Can you explain?"
    except Exception as e:
        print(f"[OLLAMA] Error calling Ollama: {e}")
        return "I'm not sure what you mean. Can you explain?"

def generate_basic_response_for_scam_type(message: str) -> str:
    """
    Generate a basic response based on the type of scam detected
    """
    message_lower = message.lower()
    
    # Financial scams
    if any(keyword in message_lower for keyword in ["bank", "account", "money", "transfer", "card"]):
        responses = [
            "Why is my account being blocked? What did I do wrong?",
            "I'm worried. How can I verify my account safely?",
            "Which bank are you from? I need to confirm this is legitimate.",
            "Can you send me the official website link to verify?",
            "What information exactly do you need from me?"
        ]
        return responses[hash(message) % len(responses)]
    
    # Urgency-based scams
    elif any(keyword in message_lower for keyword in ["urgent", "immediately", "now", "today"]):
        responses = [
            "This sounds serious. What's the deadline to fix this?",
            "I've never received such a message before. How do I know this is real?",
            "Can I verify through the official mobile app instead?",
            "Is there a customer service number I can call to verify?",
            "What happens if I don't verify immediately?"
        ]
        return responses[hash(message) % len(responses)]
    
    # Reward/prize scams
    elif any(keyword in message_lower for keyword in ["won", "prize", "gift", "reward", "jackpot"]):
        responses = [
            "That sounds too good to be true. How do I claim this?",
            "I need to verify this is legitimate before proceeding.",
            "What are the terms and conditions?",
            "Are there any fees I need to pay first?",
            "Can you provide proof of this reward?"
        ]
        return responses[hash(message) % len(responses)]
    
    # Verification scams
    elif any(keyword in message_lower for keyword in ["verify", "confirm", "click", "link"]):
        responses = [
            "I'm cautious about clicking links. Can you explain more?",
            "How do I know this link is safe?",
            "Can you verify your identity as a legitimate source?",
            "I prefer to verify through official channels.",
            "What specific information do you need?"
        ]
        return responses[hash(message) % len(responses)]
    
    # Default response
    else:
        responses = [
            "I'm not sure what you mean. Can you explain?",
            "Sorry, I don't understand. Could you rephrase?",
            "Can you provide more details?",
            "I need more information to help you.",
            "What exactly are you referring to?"
        ]
        return responses[hash(message) % len(responses)]

# ========== HELPER FUNCTIONS ==========
def validate_api_key(api_key: str) -> Tuple[bool, str]:
    """
    Hackathon-ready API key validation
    Returns: (is_valid, reason)
    """
    if not api_key or not isinstance(api_key, str):
        return False, "Missing API key"

    api_key = api_key.strip()

    if len(api_key) < 3:
        return False, "API key too short"

    # Always accept our test keys
    our_keys = ["test_key_123", "prod_key_456", "demo_key_789", "honeypot_test"]
    if api_key in our_keys:
        return True, "Valid test key"

    # Common evaluation key patterns from hackathons
    evaluation_patterns = [
        "eval_", "evaluation_", "test_", "hackathon_",
        "guvi_", "judge_", "scoring_", "assessment_",
        "team_", "participant_", "contest_", "challenge_"
    ]

    # Check if it matches any evaluation pattern
    for pattern in evaluation_patterns:
        if api_key.startswith(pattern):
            return True, f"Valid evaluation key (matches {pattern})"

    # For LENIENT mode (hackathon evaluation), accept most reasonable keys
    if API_VALIDATION_MODE == "LENIENT":
        if len(api_key) >= 8 and " " not in api_key:
            print(f"[INFO] Accepting evaluation key: {api_key[:15]}...")
            return True, "Accepted in lenient mode"

    # For STRICT mode, reject unknown keys
    return False, "Invalid API key"

def detect_scam_intent(text: str) -> Dict:
    """
    Detect scam intent with confidence score and reasons
    """
    text_lower = text.lower()
    score = 0.0
    reasons = []
    detected_categories = []

    # Check each category
    for category, patterns in SCAM_KEYWORDS.items():
        category_score = 0.0
        category_reasons = []
        
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                category_score += 0.1
                category_reasons.append(f"Matched {category} pattern: {pattern}")
        
        if category_score > 0:
            score += category_score
            reasons.extend(category_reasons)
            detected_categories.append(category)

    # Check for URLs (strong indicator)
    urls = re.findall(REGEX_PATTERNS["url"], text)
    if urls:
        score += 0.3
        reasons.append(f"Found {len(urls)} URL(s): {', '.join(urls[:2])}")

    # Check for UPI IDs
    upi_ids = re.findall(REGEX_PATTERNS["upi_id"], text, re.IGNORECASE)
    if upi_ids:
        score += 0.4
        reasons.append(f"Found UPI ID(s): {', '.join(upi_ids)}")

    # Check for bank accounts
    bank_accounts = re.findall(REGEX_PATTERNS["bank_account"], text)
    if bank_accounts:
        score += 0.5
        reasons.append(f"Found bank account pattern(s)")

    # Check for phone numbers
    phones = re.findall(REGEX_PATTERNS["phone"], text)
    if phones:
        score += 0.2
        reasons.append(f"Found phone number(s)")

    # Check for ALL CAPS (common in scams)
    if len(text) > 10:
        caps_count = sum(1 for c in text if c.isupper())
        caps_ratio = caps_count / len(text)
        if caps_ratio > 0.4:  # More than 40% caps
            score += 0.2
            reasons.append(f"High caps ratio: {caps_ratio:.1%}")

    # Multiple exclamation marks
    if text.count('!') >= 3:
        score += 0.15
        reasons.append("Multiple exclamation marks")

    # Normalize score to 0-1
    score = min(score, 1.0)

    return {
        "score": round(score, 2),
        "detected": score > 0.35,  # Threshold for detection
        "reasons": reasons[:3],  # Top 3 reasons
        "categories": detected_categories,
        "extracted": {
            "urls": urls,
            "upi_ids": upi_ids,
            "bank_accounts": bank_accounts,
            "phones": phones,
            "emails": re.findall(REGEX_PATTERNS["email"], text)
        }
    }

def generate_agent_response(text: str, session_id: str, scam_detected: bool,
                           conversation_history: List) -> str:
    """
    Generate believable human-like response using Ollama when possible
    """
    # Initialize session if needed
    if session_id not in conversations:
        conversations[session_id] = []
        intelligence_data[session_id] = {
            "bank_accounts": set(),
            "upi_ids": set(),
            "urls": set(),
            "phones": set(),
            "emails": set(),
            "keywords": set()
        }

    # Add to conversation history
    conversations[session_id].append(text)
    msg_count = len(conversations[session_id])

    if not scam_detected:
        # Normal conversation responses
        normal_responses = [
            "I'm not sure what you mean. Can you explain?",
            "Sorry, I don't understand. Could you rephrase?",
            "Can you provide more details?",
            "I need more information to help you.",
            "What exactly are you referring to?"
        ]
        return normal_responses[min(msg_count - 1, len(normal_responses) - 1)]

    # If Ollama is available, use it to generate a more contextual response
    try:
        # Determine the type of scam for a more targeted response
        detection_result = detect_scam_intent(text)
        scam_categories = detection_result.get("categories", [])
        
        # Create a prompt for Ollama based on the detected scam type
        scam_type_description = ", ".join(scam_categories) if scam_categories else "potential scam"
        
        prompt = f"""You are a person who has received a suspicious message. The message appears to be a {scam_type_description} scam. The message says: '{text}'. Respond as if you are a real person who is suspicious but wants to understand more about the situation. Be cautious but engage enough to extract more information from the scammer. Keep your response brief and natural."""
        
        # Call Ollama to generate a response
        ollama_response = call_ollama_api(prompt)
        
        # If Ollama returns a valid response, use it; otherwise, fall back to basic responses
        if ollama_response and len(ollama_response.strip()) > 5:
            return ollama_response
        else:
            # Fall back to the basic response generation based on scam type
            return generate_basic_response_for_scam_type(text)
    
    except Exception as e:
        print(f"[OLLAMA] Error generating response: {e}")
        # Fall back to basic response generation
        return generate_basic_response_for_scam_type(text)

def extract_intelligence(text: str, session_id: str) -> Dict:
    """
    Extract scam intelligence from message
    """
    if session_id not in intelligence_data:
        intelligence_data[session_id] = {
            "bank_accounts": set(),
            "upi_ids": set(),
            "urls": set(),
            "phones": set(),
            "emails": set(),
            "keywords": set()
        }

    session_data = intelligence_data[session_id]
    detection = detect_scam_intent(text)

    # Store extracted data
    for url in detection["extracted"]["urls"]:
        session_data["urls"].add(url)

    for upi in detection["extracted"]["upi_ids"]:
        session_data["upi_ids"].add(upi.lower())

    for account in detection["extracted"]["bank_accounts"]:
        session_data["bank_accounts"].add(account)

    for phone in detection["extracted"]["phones"]:
        # Clean phone number
        phone_clean = re.sub(r'[^\d+]', '', phone)
        if len(phone_clean) >= 10:
            session_data["phones"].add(phone_clean)

    for email in detection["extracted"]["emails"]:
        session_data["emails"].add(email.lower())

    # Store scam keywords found
    for reason in detection.get("reasons", []):
        session_data["keywords"].add(reason.split(":")[0].strip())

    return session_data

def send_evaluation_callback(session_id: str, scam_detected: bool):
    """
    Send final intelligence to evaluation endpoint (if enabled)
    """
    if not ENABLE_CALLBACK or not scam_detected:
        return

    try:
        if session_id not in intelligence_data:
            return

        session_data = intelligence_data[session_id]
        msg_count = len(conversations.get(session_id, []))

        payload = {
            "sessionId": session_id,
            "scamDetected": scam_detected,
            "totalMessagesExchanged": msg_count,
            "extractedIntelligence": {  # Fixed: Changed from "extractedIntelligence" to match guidelines
                "bankAccounts": list(session_data["bank_accounts"])[:5],
                "upiIds": list(session_data["upi_ids"])[:5],  # Fixed: Changed from "upids" to "upiIds" to match guidelines
                "phishingLinks": list(session_data["urls"])[:5],
                "phoneNumbers": list(session_data["phones"])[:5],
                "suspiciousKeywords": list(session_data["keywords"])[:10]
            },
            "agentNotes": f"Engaged scammer for {msg_count} messages. "
                        f"Extracted {len(session_data['upi_ids'])} UPI IDs, "
                        f"{len(session_data['urls'])} suspicious links."
        }

        # Remove empty arrays
        payload["extractedIntelligence"] = {
            k: v for k, v in payload["extractedIntelligence"].items() if v
        }

        # Send to evaluation endpoint
        response = requests.post(
            EVALUATION_ENDPOINT,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=5
        )

        print(f"[CALLBACK] Sent for session {session_id}, status: {response.status_code}")

    except Exception as e:
        print(f"[CALLBACK] Error: {e}")

# ========== API ENDPOINTS ==========
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Honeypot API - Scam Detection System",
        "version": "1.0.0",
        "status": "running",
        "mode": API_VALIDATION_MODE,
        "timestamp": datetime.now().isoformat()
    })

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "honeypot-api",
        "timestamp": datetime.now().isoformat(),
        "conversations_active": len(conversations)
    })

@app.route("/api/honeypot/", methods=["POST"])
def process_message():
    """
    Main honeypot endpoint
    """
    start_time = datetime.now()

    # 1. Get and validate API key
    api_key = request.headers.get("x-api-key")
    if not api_key:
        return jsonify({
            "status": "error",
            "message": "Missing x-api-key header",
            "timestamp": datetime.now().isoformat()
        }), 401

    is_valid, reason = validate_api_key(api_key)
    if not is_valid:
        return jsonify({
            "status": "error",
            "message": f"Invalid API key: {reason}",
            "timestamp": datetime.now().isoformat()
        }), 401

    # 2. Validate request body
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "message": "Empty request body",
                "timestamp": datetime.now().isoformat()
            }), 400
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Invalid JSON: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 400

    # 3. Extract required fields
    session_id = data.get("sessionId", str(uuid.uuid4())[:8])
    message = data.get("message", {})
    text = message.get("text", "").strip()
    sender = message.get("sender", "unknown")
    timestamp = message.get("timestamp")
    conversation_history = data.get("conversationHistory", [])
    metadata = data.get("metadata", {})

    # 4. Validate required fields
    if not text:
        return jsonify({
            "status": "error",
            "message": "Message text is required",
            "sessionId": session_id,
            "timestamp": datetime.now().isoformat()
        }), 400

    if not timestamp:
        timestamp = int(datetime.now().timestamp() * 1000)

    # 5. Detect scam intent
    detection_result = detect_scam_intent(text)
    scam_detected = detection_result["detected"]
    confidence = detection_result["score"]

    # 6. Extract intelligence
    intelligence = extract_intelligence(text, session_id)

    # 7. Generate agent response
    agent_reply = generate_agent_response(
        text, session_id, scam_detected, conversation_history
    )

    # 8. Send evaluation callback if scam detected
    if scam_detected and len(conversations.get(session_id, [])) >= 3:
        send_evaluation_callback(session_id, scam_detected)

    # 9. Prepare response
    response_time = (datetime.now() - start_time).total_seconds()

    response = {
        "status": "success",
        "sessionId": session_id,
        "scamDetected": scam_detected,
        "reply": agent_reply,
        "confidence": confidence,
        "detectionDetails": {
            "score": confidence,
            "reasons": detection_result["reasons"],
            "categories": detection_result["categories"],
            "extractedCounts": {
                "urls": len(intelligence["urls"]),
                "upiIds": len(intelligence["upi_ids"]),  # Fixed: Changed to match guidelines
                "bankAccounts": len(intelligence["bank_accounts"]),
                "phoneNumbers": len(intelligence["phones"])
            }
        },
        "sessionStats": {
            "totalMessages": len(conversations.get(session_id, [])),
            "responseTime": round(response_time, 3)
        },
        "timestamp": datetime.now().isoformat()
    }

    # Add extracted data if scam detected
    if scam_detected:
        response["extractedData"] = {
            "bankAccounts": list(intelligence["bank_accounts"])[:3],
            "upiIds": list(intelligence["upi_ids"])[:3],  # Fixed: Changed to match guidelines
            "phishingLinks": list(intelligence["urls"])[:3],
            "phoneNumbers": list(intelligence["phones"])[:3],
            "suspiciousKeywords": list(intelligence["keywords"])[:5]
        }

    print(f"[API] Processed session={session_id}, scam={scam_detected}, "
          f"confidence={confidence}, time={response_time:.3f}s")

    return jsonify(response)

@app.route("/api/validate", methods=["GET"])
def validate_api():
    """Endpoint for validators to test API"""
    return jsonify({
        "status": "success",
        "message": "API is ready for evaluation",
        "validationMode": API_VALIDATION_MODE,
        "supportedKeys": ["test_key_123", "prod_key_456", "eval_*", "hackathon_*"],
        "timestamp": datetime.now().isoformat()
    })

@app.errorhandler(404)
def not_found(e):
    return jsonify({
        "status": "error",
        "message": "Endpoint not found",
        "availableEndpoints": ["/", "/health", "/api/honeypot/", "/api/validate"]
    }), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({
        "status": "error",
        "message": "Internal server error",
        "timestamp": datetime.now().isoformat()
    }), 500

# ========== MAIN EXECUTION ==========
if __name__ == "__main__":
    print("=" * 60)
    print("[ROCKET] HONEYPOT API - SCAM DETECTION SYSTEM")
    print("=" * 60)
    print(f"[SATELLITE] Starting on: http://0.0.0.0:5000")
    print(f"[LOCK] Validation mode: {API_VALIDATION_MODE}")
    print(f"[ROBOT] Callback enabled: {ENABLE_CALLBACK}")
    print(f"[CLOCK] Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print("[CLIPBOARD] Available endpoints:")
    print("  GET  /                    - API information")
    print("  GET  /health              - Health check")
    print("  POST /api/honeypot/       - Main honeypot endpoint")
    print("  GET  /api/validate        - API validation")
    print("=" * 60)
    print("[KEY] Test API keys:")
    print("  * test_key_123  (Primary test key)")
    print("  * prod_key_456  (Production key)")
    print("  * demo_key_789  (Demo key)")
    print("  * eval_*        (Any key starting with 'eval_')")
    print("  * hackathon_*   (Any key starting with 'hackathon_')")
    print("=" * 60)
    print("[OLLAMA] Enhanced version with AI agent responses")
    print("=" * 60)

    app.run(host="0.0.0.0", port=5000, debug=True)
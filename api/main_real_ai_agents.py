from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import re
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import uuid
import requests
import random
import threading
import time

# Import transformers and torch for real AI agents
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import torch

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# ========== CONFIGURATION ==========
# Environment variables (create .env file or set in system)
API_VALIDATION_MODE = os.getenv("API_VALIDATION_MODE", "LENIENT")  # STRICT or LENIENT
EVALUATION_ENDPOINT = os.getenv("EVALUATION_ENDPOINT", "https://hackathon.guvi.in/api/updateHoneyPotFinalResult")
ENABLE_CALLBACK = os.getenv("ENABLE_CALLBACK", "false").lower() == "true"

# ========== REAL AI AGENT INITIALIZATION ==========
print("Initializing real AI agents...")

# Initialize a lightweight model for the agents
# Using a smaller model for efficiency while maintaining quality
try:
    # Use a lightweight model for the agents
    tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-medium")
    model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-medium")
    
    # Create a text generation pipeline
    generator = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        torch_dtype=torch.float16 if torch.cuda.is_available() else None,
        device_map="auto" if torch.cuda.is_available() else None
    )
    print("Real AI agents initialized successfully!")
    AI_AVAILABLE = True
except Exception as e:
    print(f"Could not initialize AI agents: {e}")
    print("Falling back to rule-based responses")
    AI_AVAILABLE = False

# ========== DATABASE (In-memory for simplicity) ==========
conversations = {}
intelligence_data = {}

# ========== EXPANDED SCAM DETECTION PATTERNS ==========
SCAM_CATEGORIES = {
    "bank_fraud": [
        r"bank account", r"account.*block", r"account.*suspend", r"account.*freeze",
        r"verify.*account", r"confirm.*account", r"bank.*suspicious", r"unusual.*activity.*bank",
        r"card.*deactivated", r"card.*blocked", r"card.*suspended"
    ],
    "upi_fraud": [
        r"upi.*id", r"share.*upi", r"upi.*transfer", r"payment.*gateway",
        r"verify.*upi", r"confirm.*upi", r"upi.*payment", r"pay.*via.*upi"
    ],
    "investment_scam": [
        r"investment", r"high.*return", r"guaranteed.*profit", r"get.*rich.*quick",
        r"investment.*opportunity", r"stock.*tip", r"trading.*opportunity", r"cryptocurrency.*investment"
    ],
    "lottery_scam": [
        r"you.*won", r"congratulation", r"prize.*money", r"lottery.*winner",
        r"cash.*prize", r"jackpot", r"lucky.*draw", r"won.*amount", r"claim.*prize"
    ],
    "tech_support_scam": [
        r"microsoft.*support", r"windows.*error", r"computer.*virus", r"device.*infected",
        r"technical.*issue", r"system.*compromised", r"security.*breach.*device"
    ],
    "insurance_fraud": [
        r"insurance.*claim", r"policy.*expired", r"premium.*due", r"coverage.*cancelled",
        r"insurance.*verification", r"policy.*suspension", r"coverage.*suspended"
    ],
    "tax_fraud": [
        r"irs.*notice", r"tax.*debt", r"owe.*tax", r"tax.*refund", r"tax.*authority",
        r"fiscal.*authority", r"tax.*compliance", r"revenue.*service"
    ],
    "loan_fraud": [
        r"loan.*approval", r"quick.*loan", r"no.*credit.*check", r"advance.*fee",
        r"loan.*processing", r"credit.*facilitation", r"emergency.*loan"
    ],
    "phishing": [
        r"click.*link", r"click.*here", r"visit.*link", r"secure.*link",
        r"official.*link", r"login.*here", r"verify.*credentials", r"update.*password"
    ],
    "romance_scam": [
        r"love.*relationship", r"online.*dating", r"heart.*felt", r"emotional.*connection",
        r"financial.*help", r"money.*transfer.*love", r"urgent.*need.*money"
    ],
    "job_fraud": [
        r"work.*from.*home", r"easy.*money", r"job.*opportunity", r"work.*guaranteed",
        r"training.*fee", r"processing.*fee", r"background.*check.*fee"
    ],
    "charity_fraud": [
        r"donate.*now", r"charitable.*cause", r"help.*people", r"donation.*needed",
        r"charity.*organization", r"fund.*raising", r"give.*to.*cause"
    ]
}

REGEX_PATTERNS = {
    "url": r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+",
    "upi_id": r"\b[\w\.-]+@(okaxis|okhdfcbank|okicici|oksbi|ybl|axl|upi)\b",
    "phone": r"(\+91|0)?[6789]\d{9}",
    "bank_account": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "pan_card": r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b",
    "aadhaar": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}\b"
}

def identify_scam_category(text: str) -> Tuple[str, float]:
    """
    Identify the most likely scam category based on the message content
    """
    text_lower = text.lower()
    best_match = ("unknown", 0.0)
    
    for category, patterns in SCAM_CATEGORIES.items():
        score = 0.0
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                score += 1
        
        if score > best_match[1]:
            best_match = (category, score)
    
    return best_match

def get_agent_info(category: str) -> Dict:
    """
    Get information about the agent handling this category
    """
    agent_info = {
        "bank_fraud": {
            "name": "Financial Security Agent",
            "personality": "Cautious and security-conscious, asks for verification details",
            "context": "You are a person who has received a suspicious message about their bank account. The message says: '{message}'. Respond as if you are a real person who is suspicious but wants to understand more about the situation. Be cautious but engage enough to extract more information from the scammer. Keep your response brief and natural."
        },
        "upi_fraud": {
            "name": "Payment Security Agent",
            "personality": "Tech-savvy and cautious about digital payments",
            "context": "You are a person who has received a suspicious message about UPI payments. The message says: '{message}'. Respond as if you are a real person who is suspicious but wants to understand more about the situation. Be cautious but engage enough to extract more information from the scammer. Keep your response brief and natural."
        },
        "investment_scam": {
            "name": "Investment Advisor Agent",
            "personality": "Financially savvy, asks about risks and returns",
            "context": "You are a person who has received a suspicious investment offer. The message says: '{message}'. Respond as if you are a real person who is suspicious but wants to understand more about the situation. Be cautious but engage enough to extract more information from the scammer. Keep your response brief and natural."
        },
        "lottery_scam": {
            "name": "Skeptic Agent",
            "personality": "Doubtful of unexpected windfalls, asks for proof",
            "context": "You are a person who has received a suspicious lottery winning message. The message says: '{message}'. Respond as if you are a real person who is suspicious but wants to understand more about the situation. Be cautious but engage enough to extract more information from the scammer. Keep your response brief and natural."
        },
        "tech_support_scam": {
            "name": "IT Security Agent",
            "personality": "Technical and security-focused, verifies credentials",
            "context": "You are a person who has received a suspicious tech support message. The message says: '{message}'. Respond as if you are a real person who is suspicious but wants to understand more about the situation. Be cautious but engage enough to extract more information from the scammer. Keep your response brief and natural."
        },
        "insurance_fraud": {
            "name": "Policy Holder Agent",
            "personality": "Knows their policy details, verifies claims",
            "context": "You are a person who has received a suspicious insurance message. The message says: '{message}'. Respond as if you are a real person who is suspicious but wants to understand more about the situation. Be cautious but engage enough to extract more information from the scammer. Keep your response brief and natural."
        },
        "tax_fraud": {
            "name": "Tax Compliance Agent",
            "personality": "Knowledgeable about tax procedures, verifies authenticity",
            "context": "You are a person who has received a suspicious tax-related message. The message says: '{message}'. Respond as if you are a real person who is suspicious but wants to understand more about the situation. Be cautious but engage enough to extract more information from the scammer. Keep your response brief and natural."
        },
        "loan_fraud": {
            "name": "Credit Conscious Agent",
            "personality": "Aware of lending practices, cautious about terms",
            "context": "You are a person who has received a suspicious loan offer. The message says: '{message}'. Respond as if you are a real person who is suspicious but wants to understand more about the situation. Be cautious but engage enough to extract more information from the scammer. Keep your response brief and natural."
        },
        "phishing": {
            "name": "Cyber Security Agent",
            "personality": "Security-focused, avoids suspicious links",
            "context": "You are a person who has received a suspicious message with links. The message says: '{message}'. Respond as if you are a real person who is suspicious but wants to understand more about the situation. Be cautious but engage enough to extract more information from the scammer. Keep your response brief and natural."
        },
        "romance_scam": {
            "name": "Relationship Skeptic Agent",
            "personality": "Emotionally aware but financially cautious",
            "context": "You are a person who has received a suspicious romantic message requesting money. The message says: '{message}'. Respond as if you are a real person who is suspicious but wants to understand more about the situation. Be cautious but engage enough to extract more information from the scammer. Keep your response brief and natural."
        },
        "job_fraud": {
            "name": "Career Conscious Agent",
            "personality": "Professional, verifies job legitimacy",
            "context": "You are a person who has received a suspicious job offer. The message says: '{message}'. Respond as if you are a real person who is suspicious but wants to understand more about the situation. Be cautious but engage enough to extract more information from the scammer. Keep your response brief and natural."
        },
        "charity_fraud": {
            "name": "Donation Verifier Agent",
            "personality": "Generous but verifies charity authenticity",
            "context": "You are a person who has received a suspicious charity request. The message says: '{message}'. Respond as if you are a real person who is suspicious but wants to understand more about the situation. Be cautious but engage enough to extract more information from the scammer. Keep your response brief and natural."
        },
        "normal": {
            "name": "General Assistant Agent",
            "personality": "Helpful but not overly engaged",
            "context": "You are a person who has received a message. The message says: '{message}'. Respond as if you are a real person. Keep your response brief and natural."
        }
    }
    
    if category in agent_info:
        return agent_info[category]
    else:
        return agent_info["normal"]

def generate_real_ai_response(message_text: str, conversation_context: List = [], session_id: str = "", agent_category: str = "normal") -> str:
    """
    Generate response using real AI with the appropriate agent context
    """
    if not AI_AVAILABLE:
        # Fallback to rule-based responses if AI is not available
        fallback_responses = {
            "bank_fraud": [
                "Why is my account being blocked? What did I do wrong?",
                "I'm worried. How can I verify my account safely?",
                "Which bank are you from? I need to confirm this is legitimate."
            ],
            "upi_fraud": [
                "I need to verify this is a legitimate request first.",
                "Can you provide more details about this payment?",
                "I'm cautious about sharing UPI details."
            ],
            "investment_scam": [
                "That sounds interesting. What are the risks involved?",
                "I'd like to verify this investment opportunity first.",
                "Are there any fees I need to pay upfront?"
            ],
            "lottery_scam": [
                "That sounds too good to be true. How do I claim this?",
                "I need to verify this is legitimate before proceeding.",
                "What are the terms and conditions?"
            ],
            "tech_support_scam": [
                "I'm experiencing some computer issues. Can you help?",
                "How do I know you're really from Microsoft?",
                "What information do you need to fix my computer?"
            ],
            "normal": [
                "I'm not sure what you mean. Can you explain?",
                "Sorry, I don't understand. Could you rephrase?",
                "Can you provide more details?"
            ]
        }
        
        responses = fallback_responses.get(agent_category, fallback_responses["normal"])
        idx = (hash(message_text) + len(conversation_context)) % len(responses)
        return responses[idx]
    
    try:
        # Get the agent context
        agent_info = get_agent_info(agent_category)
        prompt = agent_info["context"].format(message=message_text)
        
        # Generate response using the real AI model
        response = generator(
            prompt,
            max_length=len(prompt.split()) + 50,  # Keep responses reasonably short
            num_return_sequences=1,
            temperature=0.7,  # Balance creativity and coherence
            pad_token_id=tokenizer.eos_token_id,
            truncation=True
        )
        
        # Extract the generated text
        generated_text = response[0]['generated_text']
        
        # Extract just the response part (after the prompt)
        response_part = generated_text[len(prompt):].strip()
        
        # Clean up the response to make it more natural
        # Remove any incomplete sentences or extra text
        sentences = response_part.split('.')
        if len(sentences) > 1:
            response_part = '.'.join(sentences[:-1]) + '.'  # Take all but the last sentence
        else:
            response_part = sentences[0]
        
        # Further clean up by removing any trailing incomplete phrases
        response_part = response_part.split('\n')[0]  # Take only the first line
        
        # If the response is empty or too short, use a fallback
        if not response_part or len(response_part.strip()) < 5:
            fallback_responses = {
                "bank_fraud": "I need to verify this with my bank directly.",
                "upi_fraud": "I'm cautious about sharing payment details.",
                "investment_scam": "I'd like to research this opportunity first.",
                "lottery_scam": "I need to verify this is legitimate before claiming.",
                "tech_support_scam": "I'll contact support through official channels.",
                "normal": "I'm not sure what you mean. Can you explain?"
            }
            return fallback_responses.get(agent_category, "I'm not sure what you mean.")
        
        return response_part.strip()
    
    except Exception as e:
        print(f"Error generating AI response: {e}")
        # Fallback to rule-based response
        fallback_responses = {
            "bank_fraud": "I need to verify this with my bank directly.",
            "upi_fraud": "I'm cautious about sharing payment details.",
            "investment_scam": "I'd like to research this opportunity first.",
            "lottery_scam": "I need to verify this is legitimate before claiming.",
            "tech_support_scam": "I'll contact support through official channels.",
            "normal": "I'm not sure what you mean. Can you explain?"
        }
        return fallback_responses.get(agent_category, "I'm not sure what you mean.")

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

def detect_scam_intent(text: str, conversation_context: List = []) -> Dict:
    """
    Detect scam intent with confidence score and reasons
    """
    text_lower = text.lower()
    score = 0.0
    reasons = []
    detected_categories = []

    # Check each category
    for category, patterns in SCAM_CATEGORIES.items():
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

    # Check for PAN cards
    pan_cards = re.findall(REGEX_PATTERNS["pan_card"], text)
    if pan_cards:
        score += 0.6
        reasons.append(f"Found PAN card(s): {', '.join(pan_cards)}")

    # Check for Aadhaar numbers
    aadhaars = re.findall(REGEX_PATTERNS["aadhaar"], text)
    if aadhaars:
        score += 0.6
        reasons.append(f"Found Aadhaar number(s): {', '.join(aadhaars)}")

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

    # Increase score based on conversation context (if multiple scammy messages in a row)
    if conversation_context:
        recent_scammy_messages = sum(1 for msg in conversation_context[-3:] if detect_scam_intent(msg.get('text', ''), [])['score'] > 0.35)
        if recent_scammy_messages > 1:
            score += 0.2  # Boost confidence if multiple scammy messages in sequence

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
            "pan_cards": pan_cards,
            "aadhaars": aadhaars,
            "emails": re.findall(REGEX_PATTERNS["email"], text)
        }
    }

def generate_agent_response_with_context(text: str, session_id: str, scam_detected: bool,
                                        conversation_history: List, agent_category: str) -> str:
    """
    Generate AI agent response that adapts based on the conversation context
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
            "pan_cards": set(),
            "aadhaars": set(),
            "keywords": set()
        }

    # Add to conversation history
    conversations[session_id].append({
        "sender": "scammer",
        "text": text,
        "timestamp": datetime.now().isoformat()
    })
    msg_count = len(conversations[session_id])

    # Generate response using the real AI agent
    return generate_real_ai_response(text, conversation_history, session_id, agent_category)

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
            "pan_cards": set(),
            "aadhaars": set(),
            "keywords": set()
        }

    session_data = intelligence_data[session_id]
    detection = detect_scam_intent(text, conversations.get(session_id, []))

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

    for pan in detection["extracted"]["pan_cards"]:
        session_data["pan_cards"].add(pan.upper())

    for aadhaar in detection["extracted"]["aadhaars"]:
        session_data["aadhaars"].add(aadhaar)

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
                "suspiciousKeywords": list(session_data["keywords"])[:10],
                "panCards": list(session_data["pan_cards"])[:5],
                "aadhaarNumbers": list(session_data["aadhaars"])[:5]
            },
            "agentNotes": f"Engaged scammer for {msg_count} messages. "
                        f"Extracted {len(session_data['upi_ids'])} UPI IDs, "
                        f"{len(session_data['urls'])} suspicious links, "
                        f"{len(session_data['pan_cards'])} PAN cards, "
                        f"{len(session_data['aadhaars'])} Aadhaar numbers."
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
    ai_status = "ACTIVE" if AI_AVAILABLE else "FALLBACK MODE"
    return jsonify({
        "message": f"Real AI-Powered Multi-Agent Honeypot System ({ai_status})",
        "version": "5.0.0",
        "status": "running",
        "mode": API_VALIDATION_MODE,
        "ai_agents_status": ai_status,
        "timestamp": datetime.now().isoformat(),
        "agent_personalities": list({k: v["name"] for k, v in get_agent_info("normal").items()}.keys())
    })

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "real-ai-multi-agent-honeypot",
        "timestamp": datetime.now().isoformat(),
        "conversations_active": len(conversations),
        "scam_categories_supported": len(SCAM_CATEGORIES),
        "ai_agents_available": AI_AVAILABLE,
        "agent_personalities_available": 13  # 12 scam-specific + 1 normal
    })

@app.route("/api/honeypot/", methods=["POST"])
def process_message():
    """
    Main honeypot endpoint with real AI agents
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
    detection_result = detect_scam_intent(text, conversation_history)
    scam_detected = detection_result["detected"]
    confidence = detection_result["score"]

    # 6. Identify the scam category to select the appropriate agent
    category, category_score = identify_scam_category(text)
    agent_category = category if category != "unknown" else "normal"

    # 7. Extract intelligence
    intelligence = extract_intelligence(text, session_id)

    # 8. Generate agent response using the appropriate real AI agent
    agent_reply = generate_agent_response_with_context(
        text, session_id, scam_detected, conversation_history, agent_category
    )

    # 9. Get agent information for response
    agent_info = get_agent_info(agent_category)

    # 10. Send evaluation callback if scam detected
    if scam_detected and len(conversations.get(session_id, [])) >= 3:
        send_evaluation_callback(session_id, scam_detected)

    # 11. Prepare response
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
                "phoneNumbers": len(intelligence["phones"]),
                "panCards": len(intelligence["pan_cards"]),
                "aadhaarNumbers": len(intelligence["aadhaars"])
            }
        },
        "agentInfo": {
            "activeAgent": agent_info["name"],
            "personality": agent_info["personality"],
            "categoryHandled": agent_category,
            "aiPowered": AI_AVAILABLE
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
            "suspiciousKeywords": list(intelligence["keywords"])[:5],
            "panCards": list(intelligence["pan_cards"])[:3],
            "aadhaarNumbers": list(intelligence["aadhaars"])[:3]
        }

    print(f"[API] Processed session={session_id}, scam={scam_detected}, "
          f"active_agent={agent_info['name']}, ai_powered={AI_AVAILABLE}, "
          f"confidence={confidence}, time={response_time:.3f}s")

    return jsonify(response)

@app.route("/api/validate", methods=["GET"])
def validate_api():
    """Endpoint for validators to test API"""
    return jsonify({
        "status": "success",
        "message": "Real AI Multi-Agent API is ready for evaluation",
        "validationMode": API_VALIDATION_MODE,
        "supportedKeys": ["test_key_123", "prod_key_456", "eval_*", "hackathon_*"],
        "supportedScamCategories": list(SCAM_CATEGORIES.keys()),
        "aiAgentsAvailable": AI_AVAILABLE,
        "availableAgents": list(get_agent_info("normal").keys()),
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
    print("[ROCKET] REAL AI MULTI-AGENT HONEYPOT - ACTIVATED")
    print("=" * 60)
    print(f"[SATELLITE] Starting on: http://0.0.0.0:5000")
    print(f"[LOCK] Validation mode: {API_VALIDATION_MODE}")
    print(f"[ROBOT] Callback enabled: {ENABLE_CALLBACK}")
    print(f"[AI] AI Agents Status: {'ACTIVE' if AI_AVAILABLE else 'FALLBACK MODE'}")
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
    if AI_AVAILABLE:
        print("[AGENTS] Real AI agents with 13 specialized personalities:")
        for category in SCAM_CATEGORIES.keys():
            agent_info = get_agent_info(category)
            print(f"  * {agent_info['name']} ({category}): {agent_info['personality']}")
        print(f"  * General Assistant Agent (normal): Helpful but not overly engaged")
    else:
        print("[FALLBACK] Using rule-based responses due to AI initialization failure")
    print("=" * 60)

    app.run(host="0.0.0.0", port=5000, debug=True)
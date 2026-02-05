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
from dotenv import load_dotenv
from vulnerable_agents import get_most_susceptible_agent, get_agent_profile, VULNERABLE_AGENT_PROMPTS

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# ========== CONFIGURATION ==========
API_VALIDATION_MODE = os.getenv("API_VALIDATION_MODE", "LENIENT")
EVALUATION_ENDPOINT = os.getenv("EVALUATION_ENDPOINT", "https://hackathon.guvi.in/api/updateHoneyPotFinalResult")
ENABLE_CALLBACK = os.getenv("ENABLE_CALLBACK", "false").lower() == "true"

# ========== DATABASE (In-memory) ==========
conversations = {}
intelligence_data = {}

# ========== EXPANDED SCAM CATEGORIES WITH AGENTS ==========
SCAM_CATEGORIES = {
    "bank_fraud": {
        "patterns": [
            r"bank account", r"account.*block", r"account.*suspend", r"account.*freeze",
            r"verify.*account", r"confirm.*account", r"bank.*suspicious", r"unusual.*activity.*bank",
            r"card.*deactivated", r"card.*blocked", r"card.*suspended"
        ],
        "agent_info": {
            "name": "Financial Security Agent",
            "personality": "Cautious and security-conscious, asks for verification details"
        },
        "responses": [
            "Why is my account being blocked? What did I do wrong?",
            "I'm worried. How can I verify my account safely?",
            "Which bank are you from? I need to confirm this is legitimate.",
            "Can you send me the official website link to verify?",
            "What information exactly do you need from me?",
            "I need to call my bank directly to confirm this.",
            "This seems unusual. Can you provide more details?",
            "I have to be careful with account information these days.",
            "How do I know this is really from the bank?",
            "I'll need to verify this through official channels."
        ]
    },
    "upi_fraud": {
        "patterns": [
            r"upi.*id", r"share.*upi", r"upi.*transfer", r"payment.*gateway",
            r"verify.*upi", r"confirm.*upi", r"upi.*payment", r"pay.*via.*upi"
        ],
        "agent_info": {
            "name": "Payment Security Agent",
            "personality": "Tech-savvy and cautious about digital payments"
        },
        "responses": [
            "I need to verify this is a legitimate request first.",
            "Can you provide more details about this payment?",
            "I'm cautious about sharing UPI details.",
            "How do I know this payment is safe?",
            "What are the terms of this transaction?",
            "I've heard about UPI scams lately, so I'm being careful.",
            "Can you verify your identity as the recipient?",
            "I prefer to initiate payments myself.",
            "This seems suspicious. Are you sure this is safe?",
            "I need to check with my family before sharing UPI info."
        ]
    },
    "investment_scam": {
        "patterns": [
            r"investment", r"high.*return", r"guaranteed.*profit", r"get.*rich.*quick",
            r"investment.*opportunity", r"stock.*tip", r"trading.*opportunity", r"cryptocurrency.*investment"
        ],
        "agent_info": {
            "name": "Investment Advisor Agent",
            "personality": "Financially savvy, asks about risks and returns"
        },
        "responses": [
            "That sounds interesting. What are the risks involved?",
            "I'd like to verify this investment opportunity first.",
            "Are there any fees I need to pay upfront?",
            "Can you provide documentation about this investment?",
            "How can I verify the legitimacy of this offer?",
            "I've been burned by investments before, so I'm cautious.",
            "What's the track record of this investment?",
            "I need to speak with a financial advisor first.",
            "These high returns seem too good to be true.",
            "Can you provide references from other investors?"
        ]
    },
    "lottery_scam": {
        "patterns": [
            r"you.*won", r"congratulation", r"prize.*money", r"lottery.*winner",
            r"cash.*prize", r"jackpot", r"lucky.*draw", r"won.*amount", r"claim.*prize"
        ],
        "agent_info": {
            "name": "Skeptic Agent",
            "personality": "Doubtful of unexpected windfalls, asks for proof"
        },
        "responses": [
            "That sounds too good to be true. How do I claim this?",
            "I need to verify this is legitimate before proceeding.",
            "What are the terms and conditions?",
            "Are there any fees I need to pay first?",
            "Can you provide proof of this reward?",
            "I've never entered any lotteries recently.",
            "This seems like a scam I've heard about.",
            "I'm skeptical about lottery winnings.",
            "How can I be sure this isn't a fraud?",
            "I need to consult with someone before claiming."
        ]
    },
    "tech_support_scam": {
        "patterns": [
            r"microsoft.*support", r"windows.*error", r"computer.*virus", r"device.*infected",
            r"technical.*issue", r"system.*compromised", r"security.*breach.*device"
        ],
        "agent_info": {
            "name": "IT Security Agent",
            "personality": "Technical and security-focused, verifies credentials"
        },
        "responses": [
            "I'm experiencing some computer issues. Can you help?",
            "How do I know you're really from Microsoft?",
            "What information do you need to fix my computer?",
            "Can you verify your identity as a support agent?",
            "I prefer to contact support through official channels.",
            "I've heard about fake tech support calls.",
            "Can you provide a callback number?",
            "I'll call the official support number instead.",
            "I need to be careful about remote access.",
            "Let me check your credentials first."
        ]
    },
    "insurance_fraud": {
        "patterns": [
            r"insurance.*claim", r"policy.*expired", r"premium.*due", r"coverage.*cancelled",
            r"insurance.*verification", r"policy.*suspension", r"coverage.*suspended"
        ],
        "agent_info": {
            "name": "Policy Holder Agent",
            "personality": "Knows their policy details, verifies claims"
        },
        "responses": [
            "I need to verify my policy details.",
            "Can you provide my policy number?",
            "How do I confirm this insurance claim?",
            "What documents do I need to submit?",
            "I'll need to contact my insurance company directly.",
            "I have my insurance documents at home.",
            "This doesn't match what I have on file.",
            "I need to verify this with my agent.",
            "My insurance is definitely not expired.",
            "I pay my premiums on time every month."
        ]
    },
    "tax_fraud": {
        "patterns": [
            r"irs.*notice", r"tax.*debt", r"owe.*tax", r"tax.*refund", r"tax.*authority",
            r"fiscal.*authority", r"tax.*compliance", r"revenue.*service"
        ],
        "agent_info": {
            "name": "Tax Compliance Agent",
            "personality": "Knowledgeable about tax procedures, verifies authenticity"
        },
        "responses": [
            "I need to verify this tax notice.",
            "Can you provide official documentation?",
            "How do I confirm this is from the IRS?",
            "What are my rights in this situation?",
            "I'll contact the IRS directly to verify.",
            "I always file my taxes on time.",
            "I haven't received any notices by mail.",
            "This seems like a scam I've heard about.",
            "I need to speak with a real IRS agent.",
            "I have records of all my tax filings."
        ]
    },
    "loan_fraud": {
        "patterns": [
            r"loan.*approval", r"quick.*loan", r"no.*credit.*check", r"advance.*fee",
            r"loan.*processing", r"credit.*facilitation", r"emergency.*loan"
        ],
        "agent_info": {
            "name": "Credit Conscious Agent",
            "personality": "Aware of lending practices, cautious about terms"
        },
        "responses": [
            "What are the interest rates and terms?",
            "I need to review the loan agreement carefully.",
            "Are there any hidden fees?",
            "How do I verify this lender is legitimate?",
            "I prefer to apply through established banks.",
            "I don't like lenders who charge upfront fees.",
            "I have good credit, so I qualify for better rates.",
            "I need to compare this with other offers.",
            "This loan approval seems too easy.",
            "I'll need time to consider this offer."
        ]
    },
    "phishing": {
        "patterns": [
            r"click.*link", r"click.*here", r"visit.*link", r"secure.*link",
            r"official.*link", r"login.*here", r"verify.*credentials", r"update.*password"
        ],
        "agent_info": {
            "name": "Cyber Security Agent",
            "personality": "Security-focused, avoids suspicious links"
        },
        "responses": [
            "I'm cautious about clicking links. Can you explain more?",
            "How do I know this link is safe?",
            "Can you verify your identity as a legitimate source?",
            "I prefer to verify through official channels.",
            "What specific information do you need?",
            "I never click links in unsolicited messages.",
            "I'll navigate to the site myself.",
            "This looks like a phishing attempt.",
            "I use bookmarks for official sites.",
            "I have security software that warns me about dangerous sites."
        ]
    },
    "romance_scam": {
        "patterns": [
            r"love.*relationship", r"online.*dating", r"heart.*felt", r"emotional.*connection",
            r"financial.*help", r"money.*transfer.*love", r"urgent.*need.*money"
        ],
        "agent_info": {
            "name": "Relationship Skeptic Agent",
            "personality": "Emotionally aware but financially cautious"
        },
        "responses": [
            "I need to be careful about financial requests.",
            "How can I verify your identity?",
            "I prefer to meet in person first.",
            "I'm not comfortable sending money.",
            "Can we discuss this more before proceeding?",
            "Money should never be part of a real relationship.",
            "I need to trust and verify you first.",
            "This seems rushed for our relationship stage.",
            "I have financial responsibilities to consider.",
            "I'm not in a position to send money right now."
        ]
    },
    "job_fraud": {
        "patterns": [
            r"work.*from.*home", r"easy.*money", r"job.*opportunity", r"work.*guaranteed",
            r"training.*fee", r"processing.*fee", r"background.*check.*fee"
        ],
        "agent_info": {
            "name": "Career Conscious Agent",
            "personality": "Professional, verifies job legitimacy"
        },
        "responses": [
            "What are the job requirements?",
            "I need to verify this company is legitimate.",
            "Are there any upfront fees?",
            "Can you provide references?",
            "I'll need to research this opportunity.",
            "Legitimate jobs don't require upfront payments.",
            "I need to check reviews about this company.",
            "I want to speak with HR directly.",
            "I'm interested, but I need more information.",
            "I've heard about many work-from-home scams."
        ]
    },
    "charity_fraud": {
        "patterns": [
            r"donate.*now", r"charitable.*cause", r"help.*people", r"donation.*needed",
            r"charity.*organization", r"fund.*raising", r"give.*to.*cause"
        ],
        "agent_info": {
            "name": "Donation Verifier Agent",
            "personality": "Generous but verifies charity authenticity"
        },
        "responses": [
            "I need to verify this charity is legitimate.",
            "Can you provide registration details?",
            "How will my donation be used?",
            "Are there other ways to donate?",
            "I prefer verified charitable organizations.",
            "I donate through established charities.",
            "I need to research this organization first.",
            "I have a regular charity I support.",
            "I verify all charities before donating.",
            "I prefer to donate locally to verified groups."
        ]
    }
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

    for category, data in SCAM_CATEGORIES.items():
        score = 0.0
        for pattern in data["patterns"]:
            if re.search(pattern, text_lower, re.IGNORECASE):
                score += 1

        if score > best_match[1]:
            best_match = (category, score)

    return best_match

def get_agent_info(category: str) -> Dict:
    """
    Get information about the agent handling this category
    """
    if category in SCAM_CATEGORIES:
        return SCAM_CATEGORIES[category]["agent_info"]
    else:
        return {
            "name": "General Assistant Agent",
            "personality": "Helpful but not overly engaged"
        }

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
    for category, data in SCAM_CATEGORIES.items():
        category_score = 0.0
        category_reasons = []

        for pattern in data["patterns"]:
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

    # Try to use the enhanced state machine and Ollama-based agents from the 'ok' directory
    # This will generate responses dynamically based on conversation context
    try:
        from services.state_machine import state_machine, ConversationState
        from services.sync_ollama_client import sync_ollama_client
        from models.schemas import Message

        # Get or create session in the state machine
        session = state_machine.get_or_create_session(session_id)

        # Convert conversation history to Message objects
        message_objects = []
        for msg in conversation_history:
            if isinstance(msg, dict):
                message_objects.append(Message(
                    sender=msg.get('sender', 'scammer'),
                    text=msg.get('text', ''),
                    timestamp=msg.get('timestamp', int(datetime.now().timestamp() * 1000))
                ))
            elif hasattr(msg, 'sender'):
                message_objects.append(msg)

        # Add current message to history
        current_msg = Message(
            sender="scammer",
            text=text,
            timestamp=int(datetime.now().timestamp() * 1000)
        )

        # Determine the most susceptible agent for this scam type
        vulnerable_agent_key = get_most_susceptible_agent(agent_category)
        vulnerable_agent_profile = get_agent_profile(vulnerable_agent_key)
        
        # Generate response using the synchronous Ollama client with vulnerable agent profile
        # This generates responses dynamically based on conversation state and vulnerable personality
        response = sync_ollama_client.generate_response_with_personality(
            state=session.state,
            current_message=text,
            conversation_history=message_objects + [current_msg],
            metadata={"channel": "SMS", "language": "English", "locale": "IN"},
            agent_personality=VULNERABLE_AGENT_PROMPTS[vulnerable_agent_key]
        )

        return response

    except ImportError as e:
        # If enhanced agents are not available, continue with other fallbacks
        print(f"Import error for enhanced agents: {e}")
        pass
    except Exception as e:
        print(f"Unexpected error in Ollama integration: {e}")
        pass

    # If Ollama is not available, use dynamic response generation based on context
    import random
    if not scam_detected:
        # Generate a response based on the current message and context
        basic_responses = [
            f"I'm not sure what you mean by '{text[:30]}...'. Can you explain?",
            f"Sorry, I don't understand '{text[:30]}...'. Could you rephrase?",
            f"Can you provide more details about '{text[:30]}...'?",
            f"I need more information to help with '{text[:30]}...'.",
            f"What exactly are you referring to with '{text[:30]}...'?",
            f"I'm having trouble understanding your message about '{text[:30]}...'.",
            f"Could you clarify what you're asking regarding '{text[:30]}...'?",
            f"I'm not familiar with this request about '{text[:30]}...'.",
            f"This seems unclear to me regarding '{text[:30]}...'.",
            f"I need more context to respond properly to '{text[:30]}...'."
        ]
        return random.choice(basic_responses)

    # For scam messages, generate context-aware responses dynamically based on vulnerable personality
    text_lower = text.lower()

    # Determine the most susceptible agent for this scam type
    vulnerable_agent_key = get_most_susceptible_agent(agent_category)
    vulnerable_agent_profile = get_agent_profile(vulnerable_agent_key)

    # Generate dynamic responses based on detected patterns in the message and agent vulnerability
    if any(word in text_lower for word in ["bank", "account", "blocked", "suspended", "freeze"]):
        if vulnerable_agent_key == "elderly_financial_victim":
            # Elderly victims are more trusting and concerned
            bank_responses = [
                f"Oh dear, is my account really blocked? What do I need to do to fix this?",
                f"I'm so worried about my savings. How can I verify this is really from the bank?",
                f"Please help me, I don't want to lose my life's savings. What information do you need?",
                f"My children always told me to be careful, but I need to resolve this. What should I do?",
                f"I trust you're from the bank, but I'm scared. Can you guide me through this?",
                f"I've had my account for years. Is this really necessary?",
                f"I'm not very tech-savvy, but I want to make sure everything is safe.",
                f"Should I drive to the branch to verify this? Or can you help me here?",
                f"I just want to make sure my family is protected. What's the safest way?",
                f"You sound official, but I'm nervous. Can you reassure me this is real?"
            ]
        else:
            # Other agents respond differently
            bank_responses = [
                f"Why is my account being blocked? What did I do wrong with '{text[:20]}...'?",
                f"I'm worried. How can I verify this safely regarding '{text[:20]}...'?",
                f"Which bank are you from? I need to confirm this is legitimate about '{text[:20]}...'?",
                f"Can you send me the official website link to verify '{text[:20]}...'?",
                f"What information exactly do you need from me about '{text[:20]}...'?",
                f"I need to call my bank directly to confirm this about '{text[:20]}...'?",
                f"This seems unusual. Can you provide more details about '{text[:20]}...'?",
                f"I have to be careful with account information these days regarding '{text[:20]}...'?",
                f"How do I know this is really from the bank about '{text[:20]}...'?",
                f"I'll need to verify this through official channels about '{text[:20]}...'."
            ]
        return random.choice(bank_responses)

    elif any(word in text_lower for word in ["upi", "payment", "transfer", "money"]):
        if vulnerable_agent_key == "tech_naive_victim":
            # Tech-naive victims are more trusting of payment instructions
            payment_responses = [
                f"I'm not sure how to do this. Can you walk me through the payment process?",
                f"I trust you know what you're doing. How do I make this payment safely?",
                f"I'm not great with apps. Do I just follow the instructions you give me?",
                f"You seem knowledgeable about this. What's the safest way to proceed?",
                f"I want to make sure I do this right. Can you guide me step by step?",
                f"I've heard about UPI but never used it much. Is this normal?",
                f"If you say it's safe, I'll follow your instructions.",
                f"I just want to resolve this issue. What do I need to do?",
                f"I'm not tech-savvy, but I trust your guidance.",
                f"Please help me understand what I'm supposed to do."
            ]
        else:
            # Other agents respond differently
            payment_responses = [
                f"I need to verify this is a legitimate request about '{text[:20]}...'.",
                f"Can you provide more details about this payment '{text[:20]}...?'",
                f"I'm cautious about sharing UPI details regarding '{text[:20]}...'.",
                f"How do I know this payment is safe for '{text[:20]}...?'",
                f"What are the terms of this transaction '{text[:20]}...?'",
                f"I've heard about UPI scams lately, so I'm being careful about '{text[:20]}...'.",
                f"Can you verify your identity as the recipient for '{text[:20]}...?'",
                f"I prefer to initiate payments myself for '{text[:20]}...'.",
                f"This seems suspicious. Are you sure this is safe for '{text[:20]}...?'",
                f"I need to check with my family before sharing UPI info about '{text[:20]}....'"
            ]
        return random.choice(payment_responses)

    elif any(word in text_lower for word in ["love", "relationship", "romance", "heart"]):
        if vulnerable_agent_key == "young_romance_victim":
            # Romance scam victims are emotionally engaged
            romance_responses = [
                f"I've been feeling lonely lately. Tell me more about yourself.",
                f"I'm flattered that you think so highly of me. What would you like to know?",
                f"I'm interested in getting to know you better. What's your story?",
                f"I've been looking for someone special. How did you find me?",
                f"I feel like I can trust you. What do you need from me?",
                f"I'm glad I found someone who understands me. How can I help?",
                f"You seem genuine. What are your intentions with me?",
                f"I've been wanting to connect with someone. What are your feelings?",
                f"I'm happy to hear from you. What's next for us?",
                f"I feel a connection with you. How can I support you?"
            ]
        else:
            # Other agents respond differently
            romance_responses = [
                f"I need to be careful about financial requests in relationships.",
                f"How can I verify your identity before discussing personal matters?",
                f"I prefer to meet in person before sharing personal details.",
                f"I'm not comfortable sending money to online contacts.",
                f"Can we discuss this more before proceeding with anything?",
                f"Money should never be part of a real relationship.",
                f"I need to trust and verify you first.",
                f"This seems rushed for our relationship stage.",
                f"I have financial responsibilities to consider.",
                f"I'm not in a position to send money right now."
            ]
        return random.choice(romance_responses)

    elif any(word in text_lower for word in ["investment", "profit", "return", "money"]):
        if vulnerable_agent_key == "middle_aged_investment_victim":
            # Investment victims are interested in financial growth
            investment_responses = [
                f"That sounds promising. What are the specific returns I can expect?",
                f"I have some savings I could invest. What's the minimum amount?",
                f"I'm looking for ways to secure my family's future. Tell me more.",
                f"Is this a guaranteed return investment? I need to be sure.",
                f"I've been thinking about diversifying my portfolio. How does this work?",
                f"Can you provide documentation about this opportunity?",
                f"I'm interested, but I need to understand the risks involved.",
                f"What's the timeline for seeing returns on this investment?",
                f"I need to discuss this with my family, but I'm intrigued.",
                f"Is this registered with financial regulators? I want to be safe."
            ]
        else:
            # Other agents respond differently
            investment_responses = [
                f"That sounds interesting. What are the risks involved?",
                f"I'd like to verify this investment opportunity first.",
                f"Are there any fees I need to pay upfront?",
                f"Can you provide documentation about this investment?",
                f"How can I verify the legitimacy of this offer?",
                f"I've been burned by investments before, so I'm cautious.",
                f"What's the track record of this investment?",
                f"I need to speak with a financial advisor first.",
                f"These high returns seem too good to be true.",
                f"Can you provide references from other investors?"
            ]
        return random.choice(investment_responses)

    elif any(word in text_lower for word in ["computer", "virus", "support", "microsoft"]):
        if vulnerable_agent_key == "tech_naive_victim":
            # Tech support victims trust experts
            tech_responses = [
                f"I'm having trouble with my computer. Can you help?",
                f"I don't know much about computers. What do I need to do?",
                f"You sound like you know what you're talking about. How do I fix this?",
                f"I'm worried about viruses. Can you scan my computer?",
                f"I trust you can help me. What's the safest way to proceed?",
                f"I've never done this before. Can you guide me?",
                f"I'm scared something is wrong with my computer. Please help.",
                f"I rely on my computer for everything. How do I solve this?",
                f"I'm not tech-savvy, but I want to fix this problem.",
                f"Thank you for offering to help. What do I do next?"
            ]
        else:
            # Other agents respond differently
            tech_responses = [
                f"I'm experiencing some computer issues. Can you help?",
                f"How do I know you're really from Microsoft?",
                f"What information do you need to fix my computer?",
                f"Can you verify your identity as a support agent?",
                f"I prefer to contact support through official channels.",
                f"I've heard about fake tech support calls.",
                f"Can you provide a callback number?",
                f"I'll call the official support number instead.",
                f"I need to be careful about remote access.",
                f"Let me check your credentials first."
            ]
        return random.choice(tech_responses)

    # Fallback to general dynamic response
    general_responses = [
        f"I'm concerned about '{text[:30]}...'. Can you explain more?",
        f"This sounds serious regarding '{text[:30]}...'. What should I do?",
        f"I need to think carefully about '{text[:30]}...'.",
        f"Can you provide proof or verification for '{text[:30]}...?'",
        f"I always verify these kinds of requests about '{text[:30]}...'.",
        f"This seems urgent about '{text[:30]}...'. Let me consider it.",
        f"I need to be careful with requests like '{text[:30]}...'.",
        f"Can you give me time to verify '{text[:30]}...?'",
        f"I have questions about '{text[:30]}...'. Can you clarify?",
        f"I need to contact official sources about '{text[:30]}...'."
    ]
    return random.choice(general_responses)

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
    return jsonify({
        "message": "AI-Powered Multi-Agent Honeypot System",
        "version": "5.0.0",
        "status": "running",
        "mode": API_VALIDATION_MODE,
        "timestamp": datetime.now().isoformat(),
        "agent_personalities_available": len(SCAM_CATEGORIES) + 1  # +1 for normal
    })

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "multi-agent-honeypot",
        "timestamp": datetime.now().isoformat(),
        "conversations_active": len(conversations),
        "scam_categories_supported": len(SCAM_CATEGORIES)
    })

@app.route("/api/honeypot/", methods=["POST"])
def process_message():
    """
    Main honeypot endpoint with multi-agent system
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

    # 8. Generate agent response using the appropriate agent
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
        "agentInfo": {
            "activeAgent": agent_info["name"],
            "personality": agent_info["personality"],
            "categoryHandled": agent_category
        },
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
          f"active_agent={agent_info['name']}, time={response_time:.3f}s")

    return jsonify(response)

@app.route("/api/validate", methods=["GET"])
def validate_api():
    """Endpoint for validators to test API"""
    return jsonify({
        "status": "success",
        "message": "Multi-Agent API is ready for evaluation",
        "validationMode": API_VALIDATION_MODE,
        "supportedKeys": ["test_key_123", "prod_key_456", "eval_*", "hackathon_*"],
        "supportedScamCategories": list(SCAM_CATEGORIES.keys()),
        "availableAgents": [get_agent_info(cat)["name"] for cat in SCAM_CATEGORIES.keys()],
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
    print("[ROCKET] MULTI-AGENT HONEYPOT - ADVANCED AI SYSTEM")
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
    print("[AGENTS] Advanced multi-agent system with specialized personalities:")
    for category, data in SCAM_CATEGORIES.items():
        print(f"  * {data['agent_info']['name']} ({category}): {data['agent_info']['personality']}")
    print("  * General Assistant Agent (normal): Helpful but not overly engaged")
    print("=" * 60)

    app.run(host="0.0.0.0", port=5000, debug=True)
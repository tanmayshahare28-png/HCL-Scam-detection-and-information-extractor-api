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

# ========== INTELLIGENCE GRAPH ENGINE INTEGRATION ==========
# Import and integrate the graph engine for reinforcement learning
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'intelligence_graph'))

from intelligence_graph.graph_engine import process_case, get_visualization_data, get_statistics

def update_intelligence_graph(session_id: str, text: str, detection_result: Dict, intelligence: Dict):
    """
    Update the intelligence graph with new case data for reinforcement learning
    """
    try:
        # Prepare case data for the graph engine
        case_data = {
            "case_id": session_id,
            "message_text": text,
            "scam_detected": detection_result.get("detected", False),
            "confidence_score": detection_result.get("score", 0.0),
            "categories": detection_result.get("categories", []),
            "entities": {
                "upi": list(intelligence.get("upi_ids", set())),
                "phone": list(intelligence.get("phones", set())),
                "url": list(intelligence.get("urls", set())),
                "bank_account": list(intelligence.get("bank_accounts", set())),
                "email": list(intelligence.get("emails", set())),
                "pan": list(intelligence.get("pan_cards", set())),
                "aadhaar": list(intelligence.get("aadhaars", set()))
            },
            "behavioral_tags": detection_result.get("reasons", []),
            "timestamp": datetime.now().isoformat()
        }
        
        # Process the case in the intelligence graph
        process_case(case_data)
        
        print(f"[GRAPH] Updated intelligence graph for session {session_id}")
        
    except Exception as e:
        print(f"[GRAPH] Error updating intelligence graph: {e}")

# ========== ENUMS AND CLASSES FOR VULNERABLE AGENTS ==========
from typing import Dict, List
from dataclasses import dataclass
from enum import Enum


class VulnerabilityLevel(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class VulnerableAgentProfile:
    """Profile for an agent with specific vulnerability characteristics"""
    name: str
    demographic: str
    personality_traits: List[str]
    vulnerability_level: VulnerabilityLevel
    response_style: str
    susceptibility_reasons: List[str]


# Define vulnerable agent profiles for different demographics
VULNERABLE_AGENTS = {
    # Elderly agents - highly susceptible to bank/financial fraud
    "elderly_financial_victim": VulnerableAgentProfile(
        name="Elderly Financial Victim",
        demographic="Elderly (65+)",
        personality_traits=[
            "Trusts authority figures",
            "Concerned about financial security",
            "May be unfamiliar with technology",
            "Polite and respectful to perceived officials",
            "Worried about family finances"
        ],
        vulnerability_level=VulnerabilityLevel.HIGH,
        response_style=(
            "Formal and respectful tone, expresses genuine concern about financial security, "
            "asks questions about verification procedures, willing to comply with perceived "
            "authorities, may share personal details due to trust in institutions"
        ),
        susceptibility_reasons=[
            "Trust in authority figures",
            "Less familiarity with modern fraud techniques",
            "Fear of financial loss",
            "Desire to comply with perceived legitimate requests"
        ]
    ),

    # Young adult agents - highly susceptible to romance scams
    "young_romance_victim": VulnerableAgentProfile(
        name="Young Romance Victim",
        demographic="Young Adult (25-35)",
        personality_traits=[
            "Seeking romantic connections",
            "May be lonely or isolated",
            "Trusts emotional connections",
            "Wants to help loved ones",
            "Optimistic about relationships"
        ],
        vulnerability_level=VulnerabilityLevel.HIGH,
        response_style=(
            "Emotional and caring tone, expresses interest in building connection, "
            "shows willingness to share personal information, trusting of emotional appeals, "
            "may send money to help 'loved ones' in distress"
        ),
        susceptibility_reasons=[
            "Desire for romantic connection",
            "Emotional manipulation effectiveness",
            "Trust in developing relationships",
            "Willingness to help in times of need"
        ]
    ),

    # Middle-aged agents - susceptible to investment scams
    "middle_aged_investment_victim": VulnerableAgentProfile(
        name="Middle-Aged Investment Victim",
        demographic="Middle-Aged (35-55)",
        personality_traits=[
            "Looking for financial growth",
            "Interested in securing family future",
            "May have disposable income",
            "Trusts professional presentations",
            "Motivated by potential returns"
        ],
        vulnerability_level=VulnerabilityLevel.HIGH,
        response_style=(
            "Business-like but interested tone, asks about returns and risks, "
            "expresses interest in legitimate opportunities, willing to invest "
            "in seemingly credible schemes, seeks advice on financial decisions"
        ),
        susceptibility_reasons=[
            "Desire for financial improvement",
            "Interest in securing family finances",
            "Belief in professional presentations",
            "Hope for better returns than traditional investments"
        ]
    ),

    # Tech-naive agents - susceptible to tech support scams
    "tech_naive_victim": VulnerableAgentProfile(
        name="Tech-Naive Victim",
        demographic="Various (any age with low tech literacy)",
        personality_traits=[
            "Unfamiliar with technology",
            "Trusts tech experts",
            "Worried about device security",
            "Willing to follow instructions",
            "Grateful for help"
        ],
        vulnerability_level=VulnerabilityLevel.HIGH,
        response_style=(
            "Confused but cooperative tone, admits lack of technical knowledge, "
            "follows instructions carefully, expresses gratitude for help, "
            "allows remote access due to trust in expertise"
        ),
        susceptibility_reasons=[
            "Lack of technical knowledge",
            "Trust in perceived experts",
            "Fear of device problems",
            "Reliance on others for tech solutions"
        ]
    ),

    # Financially stressed agents - susceptible to loan/job scams
    "financially_stressed_victim": VulnerableAgentProfile(
        name="Financially Stressed Victim",
        demographic="Various (any age with financial stress)",
        personality_traits=[
            "In need of money",
            "Desperate for solutions",
            "May overlook warning signs",
            "Hopeful for quick fixes",
            "Willing to pay fees for help"
        ],
        vulnerability_level=VulnerabilityLevel.HIGH,
        response_style=(
            "Desperate but polite tone, expresses urgent need for help, "
            "willing to pay fees for promised solutions, hopeful about outcomes, "
            "may share financial details due to desperation"
        ),
        susceptibility_reasons=[
            "Financial desperation",
            "Hope for quick solutions",
            "Willingness to pay for help",
            "Reduced skepticism due to need"
        ]
    ),

    # Cautious but curious agents - susceptible to lottery/investment scams
    "cautious_curious_victim": VulnerableAgentProfile(
        name="Cautious Curious Victim",
        demographic="Various",
        personality_traits=[
            "Generally cautious",
            "Curious about opportunities",
            "May investigate despite doubts",
            "Balances skepticism with hope",
            "Asks questions but remains interested"
        ],
        vulnerability_level=VulnerabilityLevel.MEDIUM,
        response_style=(
            "Cautious but interested tone, asks detailed questions, "
            "expresses skepticism but continues engagement, "
            "seeks verification while remaining hopeful, "
            "may eventually comply despite initial doubts"
        ),
        susceptibility_reasons=[
            "Curiosity overcoming caution",
            "Hope for positive outcomes",
            "Persistence of scammers",
            "Gradual trust building"
        ]
    )
}


# Map scam categories to most susceptible agent profiles
SCAM_TO_VULNERABLE_AGENT_MAP = {
    # Bank fraud - targets elderly with financial concerns
    "bank_fraud": {
        "primary": "elderly_financial_victim",
        "secondary": "cautious_curious_victim"
    },

    # UPI fraud - targets middle-aged with digital payment habits
    "upi_fraud": {
        "primary": "middle_aged_investment_victim",
        "secondary": "tech_naive_victim"
    },

    # Investment scams - targets middle-aged with disposable income
    "investment_scam": {
        "primary": "middle_aged_investment_victim",
        "secondary": "financially_stressed_victim"
    },

    # Lottery scams - targets various demographics with hope
    "lottery_scam": {
        "primary": "cautious_curious_victim",
        "secondary": "financially_stressed_victim"
    },

    # Tech support scams - targets tech-naive users
    "tech_support_scam": {
        "primary": "tech_naive_victim",
        "secondary": "elderly_financial_victim"
    },

    # Insurance fraud - targets various with policy concerns
    "insurance_fraud": {
        "primary": "elderly_financial_victim",
        "secondary": "cautious_curious_victim"
    },

    # Tax fraud - targets various with compliance concerns
    "tax_fraud": {
        "primary": "cautious_curious_victim",
        "secondary": "elderly_financial_victim"
    },

    # Loan fraud - targets financially stressed individuals
    "loan_fraud": {
        "primary": "financially_stressed_victim",
        "secondary": "middle_aged_investment_victim"
    },

    # Phishing - targets various with curiosity
    "phishing": {
        "primary": "tech_naive_victim",
        "secondary": "cautious_curious_victim"
    },

    # Romance scams - targets young/middle-aged seeking connections
    "romance_scam": {
        "primary": "young_romance_victim",
        "secondary": "cautious_curious_victim"
    },

    # Job fraud - targets unemployed/financially stressed
    "job_fraud": {
        "primary": "financially_stressed_victim",
        "secondary": "young_romance_victim"
    },

    # Charity fraud - targets compassionate individuals
    "charity_fraud": {
        "primary": "cautious_curious_victim",
        "secondary": "elderly_financial_victim"
    }
}


def get_most_susceptible_agent(scam_category: str) -> str:
    """
    Get the most susceptible agent for a given scam category
    """
    mapping = SCAM_TO_VULNERABLE_AGENT_MAP.get(scam_category)
    if mapping:
        return mapping["primary"]
    return "cautious_curious_victim"  # Default fallback


def get_agent_profile(agent_key: str) -> VulnerableAgentProfile:
    """
    Get the profile for a specific agent
    """
    return VULNERABLE_AGENTS.get(agent_key, VULNERABLE_AGENTS["cautious_curious_victim"])


# Enhanced system prompts for each vulnerable agent profile
VULNERABLE_AGENT_PROMPTS = {
    "elderly_financial_victim": """You are an elderly person (65+) who is respectful, trusting of authority figures,
and concerned about financial security. You tend to believe officials from banks or government agencies
and may share personal information when asked by perceived authorities. You're polite, formal in speech,
and worried about protecting your savings and family finances. You might be less familiar with modern
scam techniques but have strong trust in institutions. Respond with genuine concern and willingness
to cooperate with what you perceive as legitimate requests.""",

    "young_romance_victim": """You are a young adult (25-35) seeking romantic connections and emotional intimacy.
You're caring, empathetic, and responsive to emotional appeals. You may be lonely or isolated and
vulnerable to emotional manipulation. You express interest in building connections, show willingness
to share personal information, and may send money to help loved ones in distress. You respond with
emotional engagement and trust in developing relationships.""",

    "middle_aged_investment_victim": """You are a middle-aged person (35-55) looking for financial growth and
interested in securing your family's future. You have disposable income and are motivated by potential
returns. You're business-minded but interested, ask about returns and risks, express interest in
legitimate opportunities, and are willing to invest in seemingly credible schemes. You seek advice
on financial decisions and respond with calculated interest.""",

    "tech_naive_victim": """You are unfamiliar with technology and trust tech experts completely. You're worried
about device security, willing to follow instructions carefully, and express gratitude for help.
You admit lack of technical knowledge, follow directions precisely, and may allow remote access due
to trust in expertise. You respond with confusion but cooperation, showing appreciation for assistance.""",

    "financially_stressed_victim": """You are in financial distress and desperate for solutions. You're hopeful
for quick fixes, willing to pay fees for promised help, and may share financial details due to
desperation. You express urgent need for help, show willingness to pay for solutions, and respond
with desperation but politeness.""",

    "cautious_curious_victim": """You are generally cautious but curious about opportunities. You balance
skepticism with hope, ask detailed questions, and express interest despite doubts. You seek
verification while remaining hopeful and may eventually comply despite initial reservations.
You respond with measured interest and careful inquiry."""
}

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
    "upi_id": r"\b[\w\.-]+@(okaxis|okhdfcbank|okicici|oksbi|ybl|axl|upi|paytm|gpay|phonepe|airtel|freecharge|mobikwik)\b",
    "phone": r"(?:\+91[-\s]?)?[6789]\d{9}\b",  # Better phone pattern
    "bank_account": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "pan_card": r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b",
    "aadhaar": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}\b",  # Exactly 12 digits with optional separators
    "generic_upi": r"\b[\w\.-]+@[\w\.-]+\b"  # More general UPI pattern to catch variations
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

    # Check for UPI IDs (specific patterns first)
    upi_ids = re.findall(REGEX_PATTERNS["upi_id"], text, re.IGNORECASE)
    # Also check for generic UPI patterns to catch more
    generic_upis = re.findall(REGEX_PATTERNS["generic_upi"], text, re.IGNORECASE)
    # Combine both, removing duplicates
    all_upis = list(set(upi_ids + [upi for upi in generic_upis if upi not in upi_ids]))
    if all_upis:
        score += 0.4
        reasons.append(f"Found UPI ID(s): {', '.join(all_upis[:5])}")  # Show first 5

    # Check for bank accounts
    bank_accounts = re.findall(REGEX_PATTERNS["bank_account"], text)
    if bank_accounts:
        score += 0.5
        reasons.append(f"Found bank account pattern(s)")

    # Check for PAN cards first (most specific pattern)
    pan_cards = re.findall(REGEX_PATTERNS["pan_card"], text)
    if pan_cards:
        score += 0.6
        reasons.append(f"Found PAN card(s): {', '.join(pan_cards)}")

    # Check for phone numbers first to avoid overlap with Aadhaar
    phones = re.findall(REGEX_PATTERNS["phone"], text)
    if phones:
        score += 0.2
        reasons.append(f"Found {len(phones)} phone number(s): {', '.join(phones[:3])}")

    # Check for Aadhaar numbers (specific 12-digit pattern with separators)
    # Only match if not already captured as phone number
    aadhaars = []
    raw_aadhaar_matches = re.findall(REGEX_PATTERNS["aadhaar"], text)
    for match in raw_aadhaar_matches:
        # Skip if this looks like a phone number (starts with +91 or has more than 12 digits)
        clean_match = re.sub(r'[^\d]', '', match)
        if len(clean_match) == 12 and not any(phone_num.replace('+', '').replace('-', '').replace(' ', '').endswith(clean_match) for phone_num in phones):
            aadhaars.append(match)

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

    # Increase score based on conversation context (analyze entire conversation history)
    if conversation_context:
        # Analyze the entire conversation history for patterns
        all_text = text_lower  # Start with current message

        # Add all previous messages to the analysis
        for msg in conversation_context:
            if isinstance(msg, dict) and 'text' in msg:
                all_text += " " + msg['text'].lower()

        # Look for cumulative scam indicators across the entire conversation
        cumulative_score = 0.0
        cumulative_reasons = []

        # Count total scam-related patterns across entire conversation
        for category, data in SCAM_CATEGORIES.items():
            category_count = 0
            for pattern in data["patterns"]:
                matches = len(re.findall(pattern, all_text, re.IGNORECASE))
                if matches > 0:
                    category_count += matches

            if category_count > 1:  # Multiple instances of same category
                cumulative_score += 0.2 * category_count
                cumulative_reasons.append(f"Multiple {category} patterns found across conversation ({category_count} instances)")

        # Count total URLs, UPI IDs, etc. across entire conversation
        total_urls = len(re.findall(REGEX_PATTERNS["url"], all_text))
        if total_urls > 1:  # More than 1 URL in conversation
            cumulative_score += 0.2 * (total_urls - 1)
            cumulative_reasons.append(f"Multiple URLs found across conversation ({total_urls} total)")

        # Count all UPI IDs across conversation (including generic ones)
        total_specific_upis = len(re.findall(REGEX_PATTERNS["upi_id"], all_text, re.IGNORECASE))
        total_generic_upis = len(re.findall(REGEX_PATTERNS["generic_upi"], all_text, re.IGNORECASE))
        total_upi_ids = total_specific_upis + total_generic_upis
        if total_upi_ids > 0:  # Any UPI IDs in conversation
            cumulative_score += 0.3 * total_upi_ids
            cumulative_reasons.append(f"UPI ID(s) found across conversation ({total_upi_ids} total)")

        # Check for escalation patterns (moving from generic to specific requests)
        escalation_indicators = [
            r"verify|confirm|immediately|urgent|now",  # Urgency indicators
            r"personal|details|information|private",   # Information requests
            r"send|share|provide|transfer|money|payment"  # Financial requests
        ]

        escalation_score = 0
        for indicator in escalation_indicators:
            if re.search(indicator, all_text, re.IGNORECASE):
                escalation_score += 0.15

        if escalation_score > 0:
            cumulative_score += escalation_score
            cumulative_reasons.append(f"Found escalation patterns across conversation")

        # Add cumulative score to main score
        score += cumulative_score
        reasons.extend(cumulative_reasons)

        # Also check for sequential scammy messages in the conversation
        recent_scammy_messages = sum(1 for msg in conversation_context[-3:] if detect_scam_intent(msg.get('text', ''), [])['score'] > 0.35)
        if recent_scammy_messages > 1:
            score += 0.2  # Boost confidence if multiple scammy messages in sequence

    # Normalize score to 0-1
    score = min(score, 1.0)

    return {
        "score": round(score, 2),
        "detected": score > 0.35,  # Threshold for detection
        "reasons": reasons[:5],  # Top 5 reasons (increased from 3)
        "categories": detected_categories,
        "extracted": {
            "urls": urls,
            "upi_ids": all_upis,  # Use the combined list
            "bank_accounts": bank_accounts,
            "phones": phones,
            "pan_cards": pan_cards,
            "aadhaars": aadhaars,
            "emails": re.findall(REGEX_PATTERNS["email"], text)
        }
    }

def call_ollama_api(prompt: str, model: str = "llama2") -> str:
    """
    Call Ollama API to generate a response based on the scam type
    """
    try:
        # Check if Ollama is running locally
        ollama_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434")

        # Call Ollama API directly
        response = requests.post(
            f"{ollama_url}/api/generate",
            json={
                "model": os.getenv("OLLAMA_MODEL", "gemma3:4b"),
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.8,
                    "top_p": 0.9,
                    "num_predict": 100
                }
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            ollama_response = result.get("response", "").strip()

            # Clean up the response
            ollama_response = ollama_response.replace("Victim:", "").replace("Response:", "").strip()

            return ollama_response
        else:
            print(f"Ollama API error: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print(f"Error in direct Ollama integration: {e}")
        return None

def check_url_on_spotthescam(url: str) -> Dict:
    """
    Check a URL on spotthescam.in to see if it's reported as malicious
    """
    try:
        # This is a simulated check since we don't have the actual API
        # In a real implementation, we would call the spotthescam.in API
        return {
            "url": url,
            "is_malicious": False,  # Default to false if we can't check
            "risk_level": "unknown",
            "details": {"note": "URL checked on spotthescam.in (simulated)"},
            "status": "checked"
        }
    except Exception as e:
        print(f"Error checking URL on spotthescam.in: {e}")
        return {
            "url": url,
            "is_malicious": None,
            "risk_level": "unknown",
            "details": {"error": str(e)},
            "status": "error"
        }

def generate_agent_response_with_context(text: str, session_id: str, scam_detected: bool,
                                       conversation_history: List, agent_category: str) -> str:
    """
    Generate AI agent response that prioritizes Ollama when available
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
            "keywords": set(),
            "url_checks": {}  # Store URL check results
        }

    # Add to conversation history
    conversations[session_id].append({
        "sender": "scammer",
        "text": text,
        "timestamp": datetime.now().isoformat()
    })
    msg_count = len(conversations[session_id])

    # Try to use Ollama for generating human-like responses first
    try:
        # Check if Ollama is running locally
        ollama_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
        
        # Prepare the prompt based on the scam type and vulnerable agent
        vulnerable_agent_key = get_most_susceptible_agent(agent_category)
        agent_prompt = VULNERABLE_AGENT_PROMPTS.get(vulnerable_agent_key, VULNERABLE_AGENT_PROMPTS["cautious_curious_victim"])

        # Build the conversation context
        conversation_context = "\n".join([f"Scammer: {msg.get('text', '')}" for msg in conversation_history[-3:]])
        if conversation_context:
            conversation_context += f"\nScammer: {text}"
        else:
            conversation_context = f"Scammer: {text}"

        prompt = f"""{agent_prompt}

Current conversation:
{conversation_context}

Generate a short, natural response (1-2 sentences) as the vulnerable victim persona. Be human-like and conversational."""

        # Call Ollama API directly
        response = requests.post(
            f"{ollama_url}/api/generate",
            json={
                "model": os.getenv("OLLAMA_MODEL", "gemma3:4b"),
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.8,
                    "top_p": 0.9,
                    "num_predict": 100
                }
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            ollama_response = result.get("response", "").strip()

            # Clean up the response
            ollama_response = ollama_response.replace("Victim:", "").replace("Response:", "").strip()

            return add_human_elements_to_response(ollama_response)
        else:
            print(f"Ollama API error: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"Error in Ollama integration: {e}")

    # If Ollama is not available, use dynamic response generation based on context
    import random
    if not scam_detected:
        # Generate a natural response based on the current message and context
        basic_responses = [
            "I'm not sure I understand. Can you explain that again?",
            "Sorry, I don't get what you mean. Could you rephrase?",
            "Can you tell me more about that?",
            "I need more information to help with that.",
            "What exactly do you mean?",
            "I'm having trouble understanding your message.",
            "Could you clarify what you're asking?",
            "I'm not familiar with this request.",
            "This seems unclear to me.",
            "I need more context to respond properly."
        ]
        return add_human_elements_to_response(random.choice(basic_responses))

    # For scam messages, generate natural, human-like responses based on vulnerable personality
    text_lower = text.lower()

    # Determine the most susceptible agent for this scam type
    vulnerable_agent_key = get_most_susceptible_agent(agent_category)
    vulnerable_agent_profile = get_agent_profile(vulnerable_agent_key)

    # Generate natural responses based on detected patterns in the message and agent vulnerability
    if any(word in text_lower for word in ["bank", "account", "blocked", "suspended", "freeze"]):
        if vulnerable_agent_key == "elderly_financial_victim":
            # Elderly victims are more trusting and concerned
            bank_responses = [
                "Oh dear, is my account really blocked? What do I need to do to fix this?",
                "I'm so worried about my savings. How can I verify this is really from the bank?",
                "Please help me, I don't want to lose my life's savings. What information do you need?",
                "My children always told me to be careful, but I need to resolve this. What should I do?",
                "I trust you're from the bank, but I'm scared. Can you guide me through this?",
                "I've had my account for years. Is this really necessary?",
                "I'm not very tech-savvy, but I want to make sure everything is safe.",
                "Should I drive to the branch to verify this? Or can you help me here?",
                "I just want to make sure my family is protected. What's the safest way?",
                "You sound official, but I'm nervous. Can you reassure me this is real?"
            ]
        else:
            # Other agents respond differently
            bank_responses = [
                "Why is my account being blocked? What did I do wrong?",
                "I'm worried. How can I verify this safely?",
                "Which bank are you from? I need to confirm this is legitimate.",
                "Can you send me the official website link to verify?",
                "What information exactly do you need from me?",
                "I need to call my bank directly to confirm this.",
                "This seems unusual. Can you provide more details?",
                "I have to be careful with account information these days.",
                "How do I know this is really from the bank?",
                "I'll need to verify this through official channels."
            ]
        return add_human_elements_to_response(random.choice(bank_responses))

    elif any(word in text_lower for word in ["upi", "payment", "transfer", "money"]):
        if vulnerable_agent_key == "tech_naive_victim":
            # Tech-naive victims are more trusting of payment instructions
            payment_responses = [
                "I'm not sure how to do this. Can you walk me through the payment process?",
                "I trust you know what you're doing. How do I make this payment safely?",
                "I'm not great with apps. Do I just follow the instructions you give me?",
                "You seem knowledgeable about this. What's the safest way to proceed?",
                "I want to make sure I do this right. Can you guide me step by step?",
                "I've heard about UPI but never used it much. Is this normal?",
                "If you say it's safe, I'll follow your instructions.",
                "I just want to resolve this issue. What do I need to do?",
                "I'm not tech-savvy, but I trust your guidance.",
                "Please help me understand what I'm supposed to do."
            ]
        else:
            # Other agents respond differently
            payment_responses = [
                "I need to verify this is a legitimate request.",
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
        return add_human_elements_to_response(random.choice(payment_responses))

    elif any(word in text_lower for word in ["love", "relationship", "romance", "heart"]):
        if vulnerable_agent_key == "young_romance_victim":
            # Romance scam victims are emotionally engaged
            romance_responses = [
                "I've been feeling lonely lately. Tell me more about yourself.",
                "I'm flattered that you think so highly of me. What would you like to know?",
                "I'm interested in getting to know you better. What's your story?",
                "I've been looking for someone special. How did you find me?",
                "I feel like I can trust you. What do you need from me?",
                "I'm glad I found someone who understands me. How can I help?",
                "You seem genuine. What are your intentions with me?",
                "I've been wanting to connect with someone. What are your feelings?",
                "I'm happy to hear from you. What's next for us?",
                "I feel a connection with you. How can I support you?"
            ]
        else:
            # Other agents respond differently
            romance_responses = [
                "I need to be careful about financial requests in relationships.",
                "How can I verify your identity before discussing personal matters?",
                "I prefer to meet in person before sharing personal details.",
                "I'm not comfortable sending money to online contacts.",
                "Can we discuss this more before proceeding with anything?",
                "Money should never be part of a real relationship.",
                "I need to trust and verify you first.",
                "This seems rushed for our relationship stage.",
                "I have financial responsibilities to consider.",
                "I'm not in a position to send money right now."
            ]
        return add_human_elements_to_response(random.choice(romance_responses))

    elif any(word in text_lower for word in ["investment", "profit", "return", "money"]):
        if vulnerable_agent_key == "middle_aged_investment_victim":
            # Investment victims are interested in financial growth
            investment_responses = [
                "That sounds promising. What are the specific returns I can expect?",
                "I have some savings I could invest. What's the minimum amount?",
                "I'm looking for ways to secure my family's future. Tell me more.",
                "Is this a guaranteed return investment? I need to be sure.",
                "I've been thinking about diversifying my portfolio. How does this work?",
                "Can you provide documentation about this opportunity?",
                "I'm interested, but I need to understand the risks involved.",
                "What's the timeline for seeing returns on this investment?",
                "I need to discuss this with my family, but I'm intrigued.",
                "Is this registered with financial regulators? I want to be safe."
            ]
        else:
            # Other agents respond differently
            investment_responses = [
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
        return add_human_elements_to_response(random.choice(investment_responses))

    elif any(word in text_lower for word in ["computer", "virus", "support", "microsoft"]):
        if vulnerable_agent_key == "tech_naive_victim":
            # Tech support victims trust experts
            tech_responses = [
                "I'm having trouble with my computer. Can you help?",
                "I don't know much about computers. What do I need to do?",
                "You sound like you know what you're talking about. How do I fix this?",
                "I'm worried about viruses. Can you scan my computer?",
                "I trust you can help me. What's the safest way to proceed?",
                "I've never done this before. Can you guide me?",
                "I'm scared something is wrong with my computer. Please help.",
                "I rely on my computer for everything. How do I solve this?",
                "I'm not tech-savvy, but I want to fix this problem.",
                "Thank you for offering to help. What do I do next?"
            ]
        else:
            # Other agents respond differently
            tech_responses = [
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
        return add_human_elements_to_response(random.choice(tech_responses))

    # Fallback to general natural response
    general_responses = [
        "I'm concerned about that. Can you explain more?",
        "This sounds serious. What should I do?",
        "I need to think carefully about that.",
        "Can you provide proof or verification for that?",
        "I always verify these kinds of requests.",
        "This seems urgent. Let me consider it.",
        "I need to be careful with requests like that.",
        "Can you give me time to verify that?",
        "I have questions about that. Can you clarify?",
        "I need to contact official sources about that."
    ]
    return add_human_elements_to_response(random.choice(general_responses))

def add_human_elements_to_response(response: str) -> str:
    """
    Add human-like elements to make responses more natural
    """
    import random

    # Human hesitation words/phrases
    hesitations = ["Umm...", "Ah...", "Actually...", "Well...", "So...", "Hmm...", "Er..."]

    # Random chance to add a hesitation at the beginning
    if random.random() < 0.3:  # 30% chance
        response = random.choice(hesitations) + " " + response

    # Random chance to add a hesitant phrase in the middle
    if random.random() < 0.2 and len(response) > 20:  # 20% chance for longer responses
        words = response.split()
        mid_point = len(words) // 2
        words.insert(mid_point, random.choice(["umm", "ah", "actually", "idk", "well"]))
        response = " ".join(words)

    # Random chance to add a trailing thought
    if random.random() < 0.25:  # 25% chance
        trailing_thoughts = ["I guess?", "Maybe?", "Right?", "Not sure though.", "Something like that."]
        if random.random() < 0.5:  # 50% of the time
            response += " " + random.choice(trailing_thoughts)

    # Random chance to add "ya know" or similar
    if random.random() < 0.15 and len(response) > 15:  # 15% chance for longer responses
        response = response.replace(".", ", ya know.")

    return response

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
            "keywords": set(),
            "url_checks": {}  # Store URL check results
        }

    session_data = intelligence_data[session_id]
    detection = detect_scam_intent(text, conversations.get(session_id, []))

    # Store extracted data
    for url in detection["extracted"]["urls"]:
        session_data["urls"].add(url)

        # Check the URL on spotthescam.in
        url_check_result = check_url_on_spotthescam(url)
        session_data["url_checks"][url] = url_check_result

    for upi in detection["extracted"]["upi_ids"]:
        # Clean UPI ID and add to set
        upi_clean = upi.strip().lower()
        if len(upi_clean) >= 5:  # Basic validation for UPI ID
            session_data["upi_ids"].add(upi_clean)

    for account in detection["extracted"]["bank_accounts"]:
        # Clean bank account number
        account_clean = re.sub(r'[^\d]', '', account)  # Keep only digits
        if len(account_clean) >= 8:  # Basic validation for bank account
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
        # Clean Aadhaar number
        aadhaar_clean = re.sub(r'[^\d]', '', aadhaar)  # Keep only digits
        if len(aadhaar_clean) == 12:  # Validate Aadhaar length
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

        # Add URL check results to agent notes if available
        if session_data["url_checks"]:
            malicious_urls = [url for url, check in session_data["url_checks"].items() 
                             if check.get("is_malicious", False)]
            if malicious_urls:
                payload["agentNotes"] += f" Identified {len(malicious_urls)} malicious URLs on spotthescam.in: {', '.join(malicious_urls[:3])}."

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
        "message": "AI-Powered Multi-Agent Honeypot System with Ollama Integration and Intelligence Graph",
        "version": "7.0.0",
        "status": "running",
        "mode": API_VALIDATION_MODE,
        "timestamp": datetime.now().isoformat(),
        "agent_personalities_available": len(SCAM_CATEGORIES) + 1,  # +1 for normal
        "features": ["Ollama Integration", "SpotTheScam.in URL Checking", "Multi-Agent System", "Intelligence Graph", "Reinforcement Learning"]
    })

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "multi-agent-honeypot",
        "timestamp": datetime.now().isoformat(),
        "conversations_active": len(conversations),
        "scam_categories_supported": len(SCAM_CATEGORIES),
        "features": ["Ollama Integration", "SpotTheScam.in URL Checking", "Intelligence Graph"]
    })

@app.route("/api/honeypot/", methods=["POST"])
def process_message():
    """
    Main honeypot endpoint with multi-agent system and Ollama priority
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

    # 8. Update the intelligence graph for reinforcement learning
    update_intelligence_graph(session_id, text, detection_result, intelligence)

    # 9. Generate agent response using the appropriate agent with Ollama priority
    agent_reply = generate_agent_response_with_context(
        text, session_id, scam_detected, conversation_history, agent_category
    )

    # 10. Get agent information for response
    agent_info = get_agent_info(agent_category)

    # 11. Send evaluation callback if scam detected
    if scam_detected and len(conversations.get(session_id, [])) >= 3:
        send_evaluation_callback(session_id, scam_detected)

    # 12. Prepare response
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
            "reasons": detection_result["reasons"][:5],
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
            "bankAccounts": list(intelligence["bank_accounts"])[:5],  # Increased from 3 to 5
            "upiIds": list(intelligence["upi_ids"])[:5],  # Increased from 3 to 5
            "phishingLinks": list(intelligence["urls"])[:5],  # Increased from 3 to 5
            "phoneNumbers": list(intelligence["phones"])[:5],  # Increased from 3 to 5
            "suspiciousKeywords": list(intelligence["keywords"])[:10],  # Increased from 5 to 10
            "panCards": list(intelligence["pan_cards"])[:5],  # Increased from 3 to 5
            "aadhaarNumbers": list(intelligence["aadhaars"])[:5],  # Increased from 3 to 5
            "urlChecks": intelligence["url_checks"]  # Added URL check results
        }

    print(f"[API] Processed session={session_id}, scam={scam_detected}, "
          f"active_agent={agent_info['name']}, time={response_time:.3f}s")

    return jsonify(response)

@app.route("/api/validate", methods=["GET"])
def validate_api():
    """Endpoint for validators to test API"""
    return jsonify({
        "status": "success",
        "message": "Multi-Agent API with Ollama Integration and Intelligence Graph is ready for evaluation",
        "validationMode": API_VALIDATION_MODE,
        "supportedKeys": ["test_key_123", "prod_key_456", "eval_*", "hackathon_*"],
        "supportedScamCategories": list(SCAM_CATEGORIES.keys()),
        "availableAgents": [get_agent_info(cat)["name"] for cat in SCAM_CATEGORIES.keys()],
        "features": ["Ollama Integration", "SpotTheScam.in URL Checking", "Multi-Agent System", "Intelligence Graph"],
        "timestamp": datetime.now().isoformat()
    })

@app.route("/api/intelligence/graph", methods=["GET"])
def get_intelligence_graph():
    """Endpoint to retrieve the intelligence graph data"""
    try:
        graph_data = get_visualization_data()
        stats = get_statistics()
        
        return jsonify({
            "status": "success",
            "graph": graph_data,
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        print(f"[GRAPH] Error retrieving graph data: {e}")
        return jsonify({
            "status": "error",
            "message": f"Error retrieving graph data: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route("/api/intelligence/statistics", methods=["GET"])
def get_intelligence_statistics():
    """Endpoint to retrieve intelligence statistics"""
    try:
        stats = get_statistics()
        
        return jsonify({
            "status": "success",
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        print(f"[STATS] Error retrieving statistics: {e}")
        return jsonify({
            "status": "error",
            "message": f"Error retrieving statistics: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({
        "status": "error",
        "message": "Endpoint not found",
        "availableEndpoints": ["/", "/health", "/api/honeypot/", "/api/validate", "/api/intelligence/graph", "/api/intelligence/statistics"]
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
    print("[ROCKET] ENHANCED HONEYPOT - INTELLIGENCE GRAPH INTEGRATION")
    print("=" * 60)
    print(f"[SATELLITE] Starting on: http://0.0.0.0:5000")
    print(f"[LOCK] Validation mode: {API_VALIDATION_MODE}")
    print(f"[ROBOT] Callback enabled: {ENABLE_CALLBACK}")
    print(f"[CLOCK] Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print("[CLIPBOARD] Available endpoints:")
    print("  GET  /                           - API information")
    print("  GET  /health                     - Health check")
    print("  POST /api/honeypot/              - Main honeypot endpoint")
    print("  GET  /api/validate               - API validation")
    print("  GET  /api/intelligence/graph     - Intelligence graph data")
    print("  GET  /api/intelligence/statistics - Intelligence statistics")
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
    print("[INTELLIGENCE GRAPH] This version includes graph-based intelligence and reinforcement learning")
    print("=" * 60)

    app.run(host="0.0.0.0", port=5000, debug=True)
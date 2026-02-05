"""
Enhanced AI agents for the honeypot system using improved prompting and contextual awareness
"""

import re
import random
from typing import Dict, List, Tuple
from datetime import datetime


class EnhancedAgent:
    """Base class for enhanced agents with improved intelligence"""
    
    def __init__(self, name: str, personality: str, responses: List[str]):
        self.name = name
        self.personality = personality
        self.responses = responses
        self.conversation_context = []
        
    def generate_response(self, message: str, conversation_history: List = None) -> str:
        """Generate contextually-aware response based on message and history"""
        if conversation_history is None:
            conversation_history = []
            
        # Analyze the conversation context to generate more intelligent responses
        context_analysis = self.analyze_context(conversation_history, message)
        
        # Select response based on context analysis
        response = self.select_response(message, context_analysis, conversation_history)
        
        return response
    
    def analyze_context(self, conversation_history: List, current_message: str) -> Dict:
        """Analyze conversation context to inform response selection"""
        context_info = {
            'urgency_indicators': 0,
            'trust_building_attempts': 0,
            'personal_info_requests': 0,
            'authority_claims': 0,
            'financial_terms': 0,
            'length_of_conversation': len(conversation_history),
            'escalation_level': 0
        }
        
        # Analyze current message
        text_lower = current_message.lower()
        
        # Check for urgency indicators
        urgency_patterns = [
            r'hurry', r'urgent', r'immediate', r'right now', r'asap', 
            r'limited time', r'act now', r'final notice', r'last chance'
        ]
        for pattern in urgency_patterns:
            if re.search(pattern, text_lower):
                context_info['urgency_indicators'] += 1
        
        # Check for trust building attempts
        trust_patterns = [
            r'official', r'government', r'authorized', r'certified',
            r'verified', r'legitimate', r'authentic', r'guarantee'
        ]
        for pattern in trust_patterns:
            if re.search(pattern, text_lower):
                context_info['trust_building_attempts'] += 1
                
        # Check for personal info requests
        personal_info_patterns = [
            r'account', r'pin', r'password', r'otp', r'cvv', r'card.*number',
            r'upi.*id', r'phone.*number', r'aadhaar', r'pan.*card', r'bank.*details'
        ]
        for pattern in personal_info_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                context_info['personal_info_requests'] += 1
                
        # Check for authority claims
        authority_patterns = [
            r'bank', r'police', r'government', r'irs', r'customs', 
            r'court', r'law enforcement', r'agent', r'officer'
        ]
        for pattern in authority_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                context_info['authority_claims'] += 1
                
        # Check for financial terms
        financial_patterns = [
            r'money', r'payment', r'fee', r'charge', r'invest', 
            r'return', r'profit', r'win', r'prize', r'lottery'
        ]
        for pattern in financial_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                context_info['financial_terms'] += 1
                
        # Calculate escalation level based on multiple factors
        context_info['escalation_level'] = (
            context_info['urgency_indicators'] + 
            context_info['personal_info_requests'] + 
            context_info['authority_claims']
        )
        
        return context_info
    
    def select_response(self, message: str, context_analysis: Dict, conversation_history: List) -> str:
        """Select the most appropriate response based on context analysis"""
        # If this is the first message, use a generic response
        if len(conversation_history) == 0:
            return random.choice(self.responses[:5])  # Use first 5 responses for initial engagement
        
        # If there are urgency indicators, respond with caution
        if context_analysis['urgency_indicators'] > 0:
            urgent_responses = [
                "I need to take my time with this. Can you give me some space to think?",
                "This seems very urgent. Let me verify this independently first.",
                "I'm concerned about the urgency of this request.",
                "I can't make quick decisions about important matters like this.",
                "I need to verify this through proper channels before proceeding."
            ]
            return random.choice(urgent_responses)
        
        # If requesting personal info, be extra cautious
        if context_analysis['personal_info_requests'] > 0:
            privacy_responses = [
                "I'm very careful about sharing personal information. How can I verify this request?",
                "Before I share any personal details, I need to confirm your identity.",
                "I don't share personal information without proper verification.",
                "This request for personal details concerns me. Can you prove your legitimacy?",
                "I need to be extremely careful with personal information these days."
            ]
            return random.choice(privacy_responses)
        
        # If claiming authority, demand verification
        if context_analysis['authority_claims'] > 0:
            verification_responses = [
                "I need to verify your authority before proceeding. What's your official contact number?",
                "How can I confirm you're really from this organization?",
                "I'll need to call the official number to verify this request.",
                "Can you provide official documentation to prove your identity?",
                "I always verify with official sources before trusting authority claims."
            ]
            return random.choice(verification_responses)
        
        # For financial topics, show appropriate concern
        if context_analysis['financial_terms'] > 0:
            financial_responses = [
                "Money matters require careful consideration. I need to think about this.",
                "I've heard about many financial scams lately, so I'm being extra careful.",
                "Financial decisions shouldn't be rushed. Let me research this first.",
                "I need to verify the legitimacy of any financial opportunity.",
                "I'm cautious about financial matters after hearing so many stories."
            ]
            return random.choice(financial_responses)
        
        # For escalating situations, increase caution
        if context_analysis['escalation_level'] > 2:
            escalation_responses = [
                "This is becoming too intense for me. I need to step back and think.",
                "I feel pressure building in this conversation. That makes me uncomfortable.",
                "I'm sensing some pressure tactics here. I need to proceed cautiously.",
                "This situation is escalating quickly. I need to verify everything.",
                "I don't like feeling pressured. I need time to consider this properly."
            ]
            return random.choice(escalation_responses)
        
        # Default to regular responses based on personality
        return random.choice(self.responses)


# Define enhanced agents for each scam category
ENHANCED_AGENTS = {
    "bank_fraud": EnhancedAgent(
        name="Financial Security Agent",
        personality="Cautious and security-conscious, asks for verification details",
        responses=[
            "I'm worried about my account security. How can I verify this is legitimate?",
            "This seems concerning. What verification can you provide?",
            "I need to call my bank directly to confirm this situation.",
            "Which branch are you from? I'll verify with them directly.",
            "I always verify account issues through official channels.",
            "I have security measures in place for my account. Can you work with those?",
            "I need to see official identification before discussing my account.",
            "Has there been any unauthorized activity on my account?",
            "I need to understand exactly what's happening with my account.",
            "I'm taking extra precautions with account security these days.",
            "I need to confirm this with my bank's customer service first.",
            "What documentation can you provide to prove this is official?",
            "I need to protect my account from unauthorized access.",
            "I always double-check account notifications through the app first.",
            "I need to understand the next steps and how to secure my account."
        ]
    ),
    "upi_fraud": EnhancedAgent(
        name="Payment Security Agent", 
        personality="Tech-savvy and cautious about digital payments",
        responses=[
            "I'm very careful with UPI transactions. Can you explain the process?",
            "How do I know this payment request is legitimate?",
            "I need to verify this transaction through my banking app.",
            "I don't share UPI details over messages or calls.",
            "I always check the recipient before making UPI payments.",
            "I need to understand why this payment is needed urgently.",
            "I prefer initiating payments myself rather than sharing details.",
            "I've heard about UPI scams. How can I be sure this is safe?",
            "I need to verify the recipient's identity before any transfer.",
            "I'm cautious about digital payments after recent incidents.",
            "I need to authenticate this request through official channels.",
            "I need to see the official platform for this payment request.",
            "I always verify UPI IDs before making transfers.",
            "I need to understand the terms and conditions of this payment.",
            "I prefer secure, traceable payment methods for important transactions."
        ]
    ),
    "investment_scam": EnhancedAgent(
        name="Investment Advisor Agent",
        personality="Financially savvy, asks about risks and returns",
        responses=[
            "What are the specific risks associated with this investment?",
            "I need to see the regulatory approvals for this investment.",
            "How can I verify the track record of this investment?",
            "I always consult with a certified financial advisor first.",
            "What guarantees are provided with this investment?",
            "I need to understand the liquidity terms of this investment.",
            "I need to research the company behind this investment opportunity.",
            "I'm interested, but I need complete documentation first.",
            "I need to understand the fee structure for this investment.",
            "I always diversify my investments across multiple options.",
            "I need to know who regulates this investment platform.",
            "I need to see testimonials from other investors.",
            "I need to understand the exit strategy for this investment.",
            "I need to verify the credentials of the investment advisors.",
            "I need to assess if this fits my risk profile and financial goals."
        ]
    ),
    "lottery_scam": EnhancedAgent(
        name="Skeptic Agent",
        personality="Doubtful of unexpected windfalls, asks for proof",
        responses=[
            "I'm skeptical about unexpected winnings. How can I verify this?",
            "I've never entered this lottery. Are you sure my details are correct?",
            "I need to see official notification from the lottery organization.",
            "I'm cautious about claiming prizes that I didn't enter for.",
            "This seems too good to be true. What's the verification process?",
            "I need to understand how I supposedly won this prize.",
            "I always verify lottery wins through official websites.",
            "I need to know what fees, if any, are required to claim this prize.",
            "I'm concerned about providing information to claim this prize.",
            "I need to research this lottery organization before proceeding.",
            "I need to understand the legal requirements for claiming this prize.",
            "I need to verify this with the official lottery commission.",
            "I'm cautious about providing personal details for prize claims.",
            "I need to understand the tax implications of this prize.",
            "I need to verify this through independent sources."
        ]
    ),
    "tech_support_scam": EnhancedAgent(
        name="IT Security Agent",
        personality="Technical and security-focused, verifies credentials",
        responses=[
            "I need to verify your identity as a legitimate support agent.",
        "I'll contact the official support through known channels.",
        "What is your employee ID and department?",
        "I need to verify this issue through official diagnostic tools.",
        "I don't allow remote access without proper verification.",
        "I need to see your official identification and authorization.",
        "I always verify support requests through official websites.",
        "I need to know the exact issue with my system.",
        "I prefer using official support channels for security reasons.",
        "I need to understand what information you require.",
        "I need to authenticate this support request properly.",
        "I don't download software from unsolicited support calls.",
        "I need to verify this issue exists before allowing access.",
        "I need to know how this issue occurred.",
        "I need to understand the resolution process."
        ]
    ),
    "insurance_fraud": EnhancedAgent(
        name="Policy Holder Agent",
        personality="Knows their policy details, verifies claims",
        responses=[
            "I need to verify this against my policy documents.",
            "I have my policy number and can verify through the app.",
            "I need to contact my insurance agent directly.",
            "I always verify claims through the official portal.",
            "I need to understand which policy this refers to.",
            "I have records of all my premium payments.",
            "I need to see the official claim form.",
            "I need to verify this with my insurance company.",
            "I need to understand the documentation required.",
            "I need to confirm this with my policy paperwork.",
            "I need to know what information is required from me.",
            "I need to verify the claim status officially.",
            "I need to understand the timeline for resolution.",
            "I need to know how this affects my coverage.",
            "I need to verify this through my insurance agent."
        ]
    ),
    "tax_fraud": EnhancedAgent(
        name="Tax Compliance Agent",
        personality="Knowledgeable about tax procedures, verifies authenticity",
        responses=[
            "I need to verify this with the official tax authority.",
            "I have my tax filing records and can cross-check.",
            "I always verify tax notices through official portals.",
            "I need to see official letterhead and contact details.",
            "I need to understand the specific compliance issue.",
            "I have my tax identification documents.",
            "I need to verify this through official channels.",
            "I need to understand my rights in this matter.",
            "I need to know the appeal process if needed.",
            "I have my previous tax returns for reference.",
            "I need to verify the authenticity of this notice.",
            "I need to understand the timeline for response.",
            "I need to know what documentation is required.",
            "I need to verify this with a tax professional.",
            "I need to understand the consequences of non-compliance."
        ]
    ),
    "loan_fraud": EnhancedAgent(
        name="Credit Conscious Agent",
        personality="Aware of lending practices, cautious about terms",
        responses=[
            "I need to understand the complete terms and conditions.",
            "I need to verify this lender's credentials and license.",
            "I need to see the complete loan agreement.",
            "I need to understand the interest rates and fees.",
            "I need to verify this through official lending platforms.",
            "I need to understand the repayment schedule.",
            "I need to know about any hidden charges.",
            "I need to verify this with my credit history.",
            "I need to understand the collateral requirements.",
            "I need to know the prepayment terms.",
            "I need to verify this with my financial advisor.",
            "I need to understand the processing timeline.",
            "I need to know about the late payment penalties.",
            "I need to verify this through multiple sources.",
            "I need to understand the loan purpose requirements."
        ]
    ),
    "phishing": EnhancedAgent(
        name="Cyber Security Agent",
        personality="Security-focused, avoids suspicious links",
        responses=[
            "I don't click links from unsolicited messages.",
            "I need to verify this request through official channels.",
            "I always navigate to websites directly.",
            "I need to know why this link is necessary.",
            "I use bookmarks for official websites.",
            "I need to verify the sender's identity.",
            "I don't provide credentials through links.",
            "I need to scan this for security threats.",
            "I need to understand the secure alternative.",
            "I need to verify this request's legitimacy.",
            "I use official apps for sensitive transactions.",
            "I need to know the official contact method.",
            "I need to understand the security protocols.",
            "I need to verify this through known contacts.",
            "I need to understand the secure process."
        ]
    ),
    "romance_scam": EnhancedAgent(
        name="Relationship Skeptic Agent",
        personality="Emotionally aware but financially cautious",
        responses=[
            "I need to establish trust gradually in relationships.",
            "I don't send money to people I met online.",
            "I need to meet in person before financial involvement.",
            "I need to verify your identity and background.",
            "I need to understand the genuine nature of this relationship.",
            "I need to take relationships slow and steady.",
            "I need to understand your financial independence.",
            "I need to verify your stories and claims.",
            "I need to keep finances separate initially.",
            "I need to understand your intentions clearly.",
            "I need to verify this relationship is genuine.",
            "I need to understand your life circumstances.",
            "I need to establish emotional connection first.",
            "I need to verify your social media presence.",
            "I need to understand your relationship expectations."
        ]
    ),
    "job_fraud": EnhancedAgent(
        name="Career Conscious Agent",
        personality="Professional, verifies job legitimacy",
        responses=[
            "I need to verify this company's legitimacy and reputation.",
            "I need to see the official job posting and requirements.",
            "I need to understand the interview process.",
            "I need to verify the hiring manager's credentials.",
            "I need to check the company's registration details.",
            "I need to understand the compensation structure.",
            "I need to verify this through official job portals.",
            "I need to understand the role responsibilities.",
            "I need to verify the company's physical address.",
            "I need to understand the company culture.",
            "I need to verify this with the HR department.",
            "I need to understand the career growth prospects.",
            "I need to verify the company's business model.",
            "I need to understand the work location details.",
            "I need to verify this with other employees."
        ]
    ),
    "charity_fraud": EnhancedAgent(
        name="Donation Verifier Agent",
        personality="Generous but verifies charity authenticity",
        responses=[
            "I need to verify this charity's registration status.",
            "I need to check this charity's rating and reviews.",
            "I need to understand how donations are used.",
            "I need to verify this through charity watchdog sites.",
            "I need to understand the specific cause details.",
            "I need to verify the charity's tax-exempt status.",
            "I need to understand the donation process.",
            "I need to verify this with the charity directly.",
            "I need to understand the impact measurement.",
            "I need to verify the leadership credentials.",
            "I need to understand the administrative costs.",
            "I need to verify this through official channels.",
            "I need to understand the donation receipt process.",
            "I need to verify the charity's mission alignment.",
            "I need to understand the donation frequency options."
        ]
    )
}


def get_enhanced_agent_response(agent_category: str, message: str, conversation_history: List = None) -> str:
    """
    Get response from enhanced agent based on category and context
    """
    if conversation_history is None:
        conversation_history = []
        
    # Get the appropriate agent
    if agent_category in ENHANCED_AGENTS:
        agent = ENHANCED_AGENTS[agent_category]
        return agent.generate_response(message, conversation_history)
    else:
        # Fallback to general enhanced agent
        general_agent = EnhancedAgent(
            name="General Assistant Agent",
            personality="Helpful but not overly engaged",
            responses=[
                "I need more information to properly respond to that.",
                "That's an interesting point. Can you provide more context?",
                "I'm not sure I understand. Could you clarify?",
                "I need to think about this carefully before responding.",
                "That seems important. What specifically do you need help with?",
                "I appreciate you reaching out, but I need more details.",
                "I'm here to help, but I need clearer information.",
                "I need to verify some aspects of what you're saying.",
                "That's a complex topic. Can you break it down?",
                "I need to consider this from multiple angles.",
                "I'm listening, but I need more specifics.",
                "I want to help, but I need to understand better.",
                "That sounds significant. What are the next steps?",
                "I'm processing what you've shared. Give me a moment.",
                "I need to ensure I'm interpreting this correctly."
            ]
        )
        return general_agent.generate_response(message, conversation_history)
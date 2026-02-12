"""
Scam Detection Service
Analyzes messages to detect scam intent using keyword matching and patterns
"""
import re
from typing import Tuple, List
from loguru import logger


class ScamDetector:
    """
    Detects scam intent in messages using multi-layered analysis:
    1. Keyword matching (urgency, threats, payment requests)
    2. Pattern matching (UPI requests, OTP requests, link sharing)
    3. Behavioral indicators (pressure tactics, impersonation)
    """
    
    # Urgency keywords
    URGENCY_KEYWORDS = [
        "urgent", "immediately", "right now", "today only", "last chance",
        "expire", "deadline", "hurry", "quick", "fast", "asap",
        "तुरंत", "जल्दी", "अभी", "फौरन",  # Hindi urgency words
        "turant", "jaldi", "abhi"  # Hinglish
    ]
    
    # Threat keywords
    THREAT_KEYWORDS = [
        "blocked", "suspended", "deactivated", "frozen", "closed",
        "legal action", "police", "arrest", "fine", "penalty",
        "court", "jail", "case filed", "fir", "cybercrime",
        "बंद", "ब्लॉक", "गिरफ्तार", "जुर्माना",  # Hindi
        "band", "block", "arrest"  # Hinglish
    ]
    
    # Payment/financial keywords
    PAYMENT_KEYWORDS = [
        "upi", "upi id", "gpay", "phonepe", "paytm", "bhim",
        "bank account", "account number", "ifsc", "transfer",
        "payment", "pay now", "send money", "deposit",
        "otp", "pin", "cvv", "card number", "expiry",
        "refund", "cashback", "reward", "prize", "lottery", "winner",
        "kyc", "verify", "verification", "update details",
        "पैसे", "भुगतान", "खाता", "ट्रांसफर"  # Hindi
    ]
    
    # Impersonation indicators
    IMPERSONATION_KEYWORDS = [
        "bank", "rbi", "sbi", "hdfc", "icici", "axis", "pnb",
        "customer care", "support", "helpdesk", "service center",
        "government", "income tax", "gst", "aadhaar", "pan",
        "amazon", "flipkart", "delivery", "courier",
        "telecom", "jio", "airtel", "vi", "bsnl",
        "executive", "officer", "manager", "representative"
    ]
    
    # Suspicious patterns (regex)
    SUSPICIOUS_PATTERNS = [
        r"share\s*(your)?\s*(upi|otp|pin|cvv|password)",
        r"click\s*(on|here|this)\s*link",
        r"verify\s*(your)?\s*(account|identity|kyc)",
        r"(account|card)\s*(will be|is being)\s*(blocked|suspended)",
        r"(win|won|winner|prize|reward)\s*of?\s*₹?\s*\d+",
        r"refund\s*of?\s*₹?\s*\d+",
        r"call\s*(this|on)\s*number",
        r"whatsapp\s*(on|at)?\s*\+?\d+",
        r"(dear|respected)\s*(customer|user|sir|madam)",
    ]
    
    # Scam type indicators
    SCAM_TYPES = {
        "bank_fraud": ["bank", "account", "blocked", "suspended", "upi", "otp"],
        "upi_fraud": ["upi", "gpay", "phonepe", "paytm", "payment", "transfer"],
        "lottery_scam": ["winner", "prize", "lottery", "reward", "cashback", "congratulations"],
        "kyc_scam": ["kyc", "verify", "aadhaar", "pan", "update", "expire"],
        "delivery_scam": ["delivery", "courier", "package", "customs", "tracking"],
        "job_scam": ["job", "offer", "salary", "work from home", "hiring", "recruitment"],
        "tech_support": ["virus", "hacked", "compromised", "antivirus", "security alert"],
    }
    
    def __init__(self):
        # Compile regex patterns for efficiency
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in self.SUSPICIOUS_PATTERNS
        ]
    
    def detect(self, message: str, conversation_history: List[dict] = None) -> Tuple[bool, float, List[str], str]:
        """
        Analyze message for scam intent
        
        Args:
            message: The message text to analyze
            conversation_history: Previous messages for context
            
        Returns:
            Tuple of (is_scam, confidence_score, detected_keywords, scam_type)
        """
        message_lower = message.lower()
        detected_keywords = []
        scores = []
        
        # 1. Check urgency keywords
        urgency_matches = self._match_keywords(message_lower, self.URGENCY_KEYWORDS)
        if urgency_matches:
            detected_keywords.extend(urgency_matches)
            scores.append(0.3)
        
        # 2. Check threat keywords
        threat_matches = self._match_keywords(message_lower, self.THREAT_KEYWORDS)
        if threat_matches:
            detected_keywords.extend(threat_matches)
            scores.append(0.4)
        
        # 3. Check payment keywords
        payment_matches = self._match_keywords(message_lower, self.PAYMENT_KEYWORDS)
        if payment_matches:
            detected_keywords.extend(payment_matches)
            scores.append(0.3)
        
        # 4. Check impersonation keywords
        impersonation_matches = self._match_keywords(message_lower, self.IMPERSONATION_KEYWORDS)
        if impersonation_matches:
            detected_keywords.extend(impersonation_matches)
            scores.append(0.2)
        
        # 5. Check suspicious patterns
        pattern_matches = self._match_patterns(message)
        if pattern_matches:
            detected_keywords.extend(pattern_matches)
            scores.append(0.4)
        
        # Calculate confidence score (capped at 1.0)
        confidence = min(sum(scores), 1.0)
        
        # Determine scam type
        scam_type = self._determine_scam_type(detected_keywords)
        
        # Is it a scam? (threshold: 0.3)
        is_scam = confidence >= 0.3
        
        # Boost confidence if conversation history shows escalation
        if conversation_history and is_scam:
            confidence = min(confidence + 0.1, 1.0)
        
        logger.info(f"Scam detection: is_scam={is_scam}, confidence={confidence:.2f}, type={scam_type}")
        logger.debug(f"Detected keywords: {detected_keywords}")
        
        return is_scam, confidence, list(set(detected_keywords)), scam_type
    
    def _match_keywords(self, text: str, keywords: List[str]) -> List[str]:
        """Find matching keywords in text"""
        matches = []
        for keyword in keywords:
            if keyword.lower() in text:
                matches.append(keyword)
        return matches
    
    def _match_patterns(self, text: str) -> List[str]:
        """Find matching regex patterns"""
        matches = []
        for pattern in self.compiled_patterns:
            if pattern.search(text):
                matches.append(pattern.pattern[:30] + "...")  # Truncate for readability
        return matches
    
    def _determine_scam_type(self, keywords: List[str]) -> str:
        """Determine the type of scam based on detected keywords"""
        keywords_lower = [k.lower() for k in keywords]
        
        type_scores = {}
        for scam_type, indicators in self.SCAM_TYPES.items():
            score = sum(1 for ind in indicators if ind in keywords_lower)
            if score > 0:
                type_scores[scam_type] = score
        
        if type_scores:
            return max(type_scores, key=type_scores.get)
        return "unknown"
    
    def get_risk_level(self, confidence: float) -> str:
        """Convert confidence score to risk level"""
        if confidence >= 0.7:
            return "HIGH"
        elif confidence >= 0.4:
            return "MEDIUM"
        elif confidence >= 0.3:
            return "LOW"
        return "NONE"


# Singleton instance
scam_detector = ScamDetector()

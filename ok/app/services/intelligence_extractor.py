"""
Intelligence Extractor Service
Extracts actionable intelligence from scammer messages:
- Bank account numbers
- UPI IDs
- Phone numbers
- Phishing links
- Suspicious keywords
"""
import re
from typing import List
from loguru import logger

from app.models.schemas import ExtractedIntelligence


class IntelligenceExtractor:
    """
    Extracts structured intelligence from conversation messages
    using regex patterns optimized for Indian financial data
    """
    
    # UPI ID patterns (name@bank format)
    UPI_PATTERNS = [
        r'[a-zA-Z0-9._-]+@[a-zA-Z]{2,}',  # Standard UPI
        r'[a-zA-Z0-9._-]+@ybl',  # PhonePe
        r'[a-zA-Z0-9._-]+@paytm',  # Paytm
        r'[a-zA-Z0-9._-]+@okaxis',  # GPay
        r'[a-zA-Z0-9._-]+@oksbi',  # GPay SBI
        r'[a-zA-Z0-9._-]+@okicici',  # GPay ICICI
        r'[a-zA-Z0-9._-]+@okhdfcbank',  # GPay HDFC
        r'[a-zA-Z0-9._-]+@apl',  # Amazon Pay
        r'[a-zA-Z0-9._-]+@ibl',  # Various banks
        r'[a-zA-Z0-9._-]+@upi',  # Generic UPI
    ]
    
    # Indian phone number patterns
    PHONE_PATTERNS = [
        r'\+91[\s-]?[6-9]\d{9}',  # +91 format
        r'91[\s-]?[6-9]\d{9}',  # 91 format
        r'\b[6-9]\d{9}\b',  # 10 digit Indian mobile
        r'\b0[1-9]\d{9,10}\b',  # Landline with STD
    ]
    
    # Bank account patterns
    BANK_ACCOUNT_PATTERNS = [
        r'\b\d{9,18}\b',  # 9-18 digit account numbers
        r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',  # Card format
        r'[A-Z]{4}0[A-Z0-9]{6}',  # IFSC code
    ]
    
    # URL/Link patterns
    URL_PATTERNS = [
        r'https?://[^\s<>"{}|\\^`\[\]]+',  # Standard URLs
        r'www\.[^\s<>"{}|\\^`\[\]]+',  # www URLs
        r'bit\.ly/[a-zA-Z0-9]+',  # Bitly
        r't\.me/[a-zA-Z0-9_]+',  # Telegram
        r'wa\.me/\d+',  # WhatsApp
    ]
    
    # Suspicious keywords for Indian context
    SUSPICIOUS_KEYWORDS = [
        # Urgency
        "urgent", "immediately", "today", "now", "asap", "deadline",
        # Threats
        "blocked", "suspended", "deactivated", "legal action", "police", "arrest",
        "fine", "penalty", "court", "fir", "cybercrime",
        # Requests
        "verify", "update", "confirm", "share", "send", "transfer",
        # Financial
        "otp", "pin", "cvv", "password", "upi", "kyc", "aadhaar", "pan",
        # Promises
        "reward", "prize", "winner", "cashback", "refund", "lottery",
        # Impersonation
        "bank", "rbi", "government", "customer care", "support",
    ]
    
    # Known safe UPI domains to filter out
    SAFE_UPI_DOMAINS = [
        "@example", "@test", "@demo", "@sample"
    ]
    
    # Known safe phone prefixes
    SAFE_PHONE_PREFIXES = [
        "1800", "1860",  # Toll-free
    ]
    
    def __init__(self):
        # Compile patterns
        self.upi_regex = re.compile('|'.join(self.UPI_PATTERNS), re.IGNORECASE)
        self.phone_regex = re.compile('|'.join(self.PHONE_PATTERNS))
        self.bank_regex = re.compile('|'.join(self.BANK_ACCOUNT_PATTERNS))
        self.url_regex = re.compile('|'.join(self.URL_PATTERNS), re.IGNORECASE)
    
    def extract(self, text: str) -> ExtractedIntelligence:
        """
        Extract all intelligence from a text message
        
        Args:
            text: Message text to analyze
            
        Returns:
            ExtractedIntelligence object with all extracted data
        """
        intel = ExtractedIntelligence()
        
        # Extract UPI IDs
        intel.upiIds = self._extract_upi_ids(text)
        
        # Extract phone numbers
        intel.phoneNumbers = self._extract_phone_numbers(text)
        
        # Extract bank accounts
        intel.bankAccounts = self._extract_bank_accounts(text)
        
        # Extract phishing links
        intel.phishingLinks = self._extract_urls(text)
        
        # Extract suspicious keywords
        intel.suspiciousKeywords = self._extract_keywords(text)
        
        logger.debug(f"Extracted intelligence: UPI={len(intel.upiIds)}, Phones={len(intel.phoneNumbers)}, URLs={len(intel.phishingLinks)}")
        
        return intel
    
    def extract_from_conversation(self, messages: List[dict]) -> ExtractedIntelligence:
        """
        Extract intelligence from entire conversation history
        
        Args:
            messages: List of message dicts with 'text' field
            
        Returns:
            ExtractedIntelligence with all extracted data
        """
        combined_intel = ExtractedIntelligence()
        
        for msg in messages:
            text = msg.get('text', '') if isinstance(msg, dict) else msg.text
            msg_intel = self.extract(text)
            
            # Merge intelligences
            for upi in msg_intel.upiIds:
                if upi not in combined_intel.upiIds:
                    combined_intel.upiIds.append(upi)
            
            for phone in msg_intel.phoneNumbers:
                if phone not in combined_intel.phoneNumbers:
                    combined_intel.phoneNumbers.append(phone)
            
            for account in msg_intel.bankAccounts:
                if account not in combined_intel.bankAccounts:
                    combined_intel.bankAccounts.append(account)
            
            for url in msg_intel.phishingLinks:
                if url not in combined_intel.phishingLinks:
                    combined_intel.phishingLinks.append(url)
            
            for keyword in msg_intel.suspiciousKeywords:
                if keyword not in combined_intel.suspiciousKeywords:
                    combined_intel.suspiciousKeywords.append(keyword)
        
        return combined_intel
    
    def _extract_upi_ids(self, text: str) -> List[str]:
        """Extract UPI IDs from text"""
        matches = self.upi_regex.findall(text)
        
        # Filter out safe/test UPIs and emails
        filtered = []
        for match in matches:
            match = match.lower()
            # Skip if it's a known safe domain
            if any(safe in match for safe in self.SAFE_UPI_DOMAINS):
                continue
            # Skip if it looks like an email domain
            if any(domain in match for domain in ['@gmail', '@yahoo', '@outlook', '@hotmail']):
                continue
            # Skip if too short
            if len(match) < 5:
                continue
            filtered.append(match)
        
        return list(set(filtered))
    
    def _extract_phone_numbers(self, text: str) -> List[str]:
        """Extract phone numbers from text"""
        matches = self.phone_regex.findall(text)
        
        # Clean and filter
        filtered = []
        for match in matches:
            # Remove spaces and dashes
            cleaned = re.sub(r'[\s-]', '', match)
            
            # Skip toll-free numbers
            if any(cleaned.startswith(prefix) for prefix in self.SAFE_PHONE_PREFIXES):
                continue
            
            # Format consistently
            if len(cleaned) == 10:
                cleaned = '+91' + cleaned
            elif len(cleaned) == 12 and cleaned.startswith('91'):
                cleaned = '+' + cleaned
            
            if cleaned not in filtered:
                filtered.append(cleaned)
        
        return filtered
    
    def _extract_bank_accounts(self, text: str) -> List[str]:
        """Extract bank account numbers and IFSC codes"""
        matches = self.bank_regex.findall(text)
        
        # Filter out likely non-account numbers
        filtered = []
        for match in matches:
            # Remove spaces and dashes
            cleaned = re.sub(r'[\s-]', '', match)
            
            # IFSC codes (4 letters + 0 + 6 alphanumeric)
            if re.match(r'^[A-Z]{4}0[A-Z0-9]{6}$', cleaned):
                filtered.append(cleaned)
                continue
            
            # Account numbers (9-18 digits, not starting with 0)
            if cleaned.isdigit():
                if 9 <= len(cleaned) <= 18 and not cleaned.startswith('0'):
                    # Skip if it looks like a phone number
                    if len(cleaned) == 10 and cleaned[0] in '6789':
                        continue
                    # Skip if it looks like a timestamp
                    if len(cleaned) > 12:
                        continue
                    filtered.append(cleaned)
        
        return list(set(filtered))
    
    def _extract_urls(self, text: str) -> List[str]:
        """Extract URLs/links from text"""
        matches = self.url_regex.findall(text)
        
        # Filter out safe URLs
        safe_domains = ['google.com', 'facebook.com', 'twitter.com', 'instagram.com', 
                        'youtube.com', 'linkedin.com', 'microsoft.com', 'apple.com']
        
        filtered = []
        for url in matches:
            # Skip safe domains
            if any(domain in url.lower() for domain in safe_domains):
                continue
            
            # Add http if missing
            if not url.startswith('http'):
                url = 'http://' + url
            
            filtered.append(url)
        
        return list(set(filtered))
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract suspicious keywords from text"""
        text_lower = text.lower()
        found = []
        
        for keyword in self.SUSPICIOUS_KEYWORDS:
            if keyword in text_lower:
                found.append(keyword)
        
        return list(set(found))
    
    def get_intelligence_summary(self, intel: ExtractedIntelligence) -> str:
        """Generate human-readable summary of extracted intelligence"""
        parts = []
        
        if intel.upiIds:
            parts.append(f"UPI IDs: {', '.join(intel.upiIds)}")
        if intel.phoneNumbers:
            parts.append(f"Phone numbers: {', '.join(intel.phoneNumbers)}")
        if intel.bankAccounts:
            parts.append(f"Bank accounts/IFSC: {', '.join(intel.bankAccounts)}")
        if intel.phishingLinks:
            parts.append(f"Suspicious links: {', '.join(intel.phishingLinks[:3])}")
        if intel.suspiciousKeywords:
            parts.append(f"Keywords: {', '.join(intel.suspiciousKeywords[:5])}")
        
        return "; ".join(parts) if parts else "No intelligence extracted"


# Singleton instance
intelligence_extractor = IntelligenceExtractor()

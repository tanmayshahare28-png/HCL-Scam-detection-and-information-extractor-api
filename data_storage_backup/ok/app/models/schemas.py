"""
Pydantic schemas for API request/response validation
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class ConversationState(str, Enum):
    """6-state conversation machine states"""
    HOOKED = "hooked"
    CONFUSED = "confused"
    TRUSTING = "trusting"
    DELAY = "delay"
    EXTRACT = "extract"
    EXIT = "exit"


class MessageSender(str, Enum):
    """Message sender types"""
    SCAMMER = "scammer"
    USER = "user"


class Message(BaseModel):
    """Individual message in conversation"""
    sender: str
    text: str
    timestamp: int


class Metadata(BaseModel):
    """Request metadata"""
    channel: Optional[str] = "SMS"
    language: Optional[str] = "English"
    locale: Optional[str] = "IN"


class HoneypotRequest(BaseModel):
    """
    Incoming API request format from evaluation platform
    """
    sessionId: str = Field(..., description="Unique session ID for the conversation")
    message: Message = Field(..., description="Current incoming message")
    conversationHistory: List[Message] = Field(default=[], description="Previous messages")
    metadata: Optional[Metadata] = Field(default=None, description="Channel and locale info")

    class Config:
        json_schema_extra = {
            "example": {
                "sessionId": "wertyu-dfghj-ertyui",
                "message": {
                    "sender": "scammer",
                    "text": "Your bank account will be blocked today. Verify immediately.",
                    "timestamp": 1770005528731
                },
                "conversationHistory": [],
                "metadata": {
                    "channel": "SMS",
                    "language": "English",
                    "locale": "IN"
                }
            }
        }


class HoneypotResponse(BaseModel):
    """
    API response format
    """
    status: str = Field(..., description="success or error")
    reply: str = Field(..., description="Agent's response to scammer")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "reply": "Why is my account being suspended?"
            }
        }


class ExtractedIntelligence(BaseModel):
    """Intelligence extracted from scammer"""
    bankAccounts: List[str] = Field(default_factory=list)
    upiIds: List[str] = Field(default_factory=list)
    phishingLinks: List[str] = Field(default_factory=list)
    phoneNumbers: List[str] = Field(default_factory=list)
    suspiciousKeywords: List[str] = Field(default_factory=list)


class GUVICallbackPayload(BaseModel):
    """
    Final result payload to send to GUVI evaluation endpoint
    """
    sessionId: str
    scamDetected: bool
    totalMessagesExchanged: int
    extractedIntelligence: ExtractedIntelligence
    agentNotes: str

    class Config:
        json_schema_extra = {
            "example": {
                "sessionId": "abc123-session-id",
                "scamDetected": True,
                "totalMessagesExchanged": 18,
                "extractedIntelligence": {
                    "bankAccounts": ["XXXX-XXXX-XXXX"],
                    "upiIds": ["scammer@upi"],
                    "phishingLinks": ["http://malicious-link.example"],
                    "phoneNumbers": ["+91XXXXXXXXXX"],
                    "suspiciousKeywords": ["urgent", "verify now", "account blocked"]
                },
                "agentNotes": "Scammer used urgency tactics and payment redirection"
            }
        }


class SessionData(BaseModel):
    """Session state stored in memory"""
    session_id: str
    state: ConversationState = ConversationState.HOOKED
    conversation_history: List[Message] = Field(default_factory=list)
    intelligence: ExtractedIntelligence = Field(default_factory=ExtractedIntelligence)
    scam_detected: bool = False
    message_count: int = 0
    agent_notes: List[str] = Field(default_factory=list)
    metadata: Optional[Metadata] = None

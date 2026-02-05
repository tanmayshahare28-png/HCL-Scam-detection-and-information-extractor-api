"""
GUVI Callback Service
Sends final results to the GUVI evaluation endpoint
"""
import httpx
from loguru import logger

from app.config import get_settings
from app.models.schemas import GUVICallbackPayload, SessionData


async def send_guvi_callback(session: SessionData, agent_notes: str) -> bool:
    """
    Send final extracted intelligence to GUVI evaluation endpoint
    
    Args:
        session: Session data with all conversation info
        agent_notes: Summary notes about the scam engagement
        
    Returns:
        True if callback was successful, False otherwise
    """
    settings = get_settings()
    
    # Build payload
    payload = GUVICallbackPayload(
        sessionId=session.session_id,
        scamDetected=session.scam_detected,
        totalMessagesExchanged=session.message_count,
        extractedIntelligence=session.intelligence,
        agentNotes=agent_notes
    )
    
    logger.info(f"Sending GUVI callback for session {session.session_id}")
    logger.debug(f"Payload: {payload.model_dump_json()}")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                settings.guvi_callback_url,
                json=payload.model_dump(),
                headers={
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code == 200:
                logger.info(f"GUVI callback successful for session {session.session_id}")
                return True
            else:
                logger.error(f"GUVI callback failed: {response.status_code} - {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"GUVI callback error: {e}")
        return False


def build_callback_payload(session: SessionData, agent_notes: str) -> dict:
    """
    Build the callback payload as a dictionary (for testing/debugging)
    """
    return {
        "sessionId": session.session_id,
        "scamDetected": session.scam_detected,
        "totalMessagesExchanged": session.message_count,
        "extractedIntelligence": {
            "bankAccounts": session.intelligence.bankAccounts,
            "upiIds": session.intelligence.upiIds,
            "phishingLinks": session.intelligence.phishingLinks,
            "phoneNumbers": session.intelligence.phoneNumbers,
            "suspiciousKeywords": session.intelligence.suspiciousKeywords
        },
        "agentNotes": agent_notes
    }

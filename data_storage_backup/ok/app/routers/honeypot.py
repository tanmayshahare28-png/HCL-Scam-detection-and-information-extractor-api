"""
Honeypot API Router
Main API endpoints for the scam detection and engagement system
"""
from fastapi import APIRouter, HTTPException, Header, Depends
from loguru import logger
from typing import Optional

from app.config import get_settings
from app.models.schemas import (
    HoneypotRequest, 
    HoneypotResponse, 
    ConversationState,
    Message,
    SessionData
)
from app.services.ollama_client import ollama_client
from app.services.scam_detector import scam_detector
from app.services.state_machine import state_machine
from app.services.intelligence_extractor import intelligence_extractor
from app.utils.callback import send_guvi_callback


router = APIRouter(prefix="/api", tags=["honeypot"])


async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    """Verify API key from header"""
    settings = get_settings()
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


@router.post("/honeypot", response_model=HoneypotResponse)
async def process_message(
    request: HoneypotRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Main honeypot endpoint - processes incoming scam messages
    
    Flow:
    1. Get or create session
    2. Detect scam intent
    3. Extract intelligence from message
    4. Generate contextual response based on state
    5. Update session state
    6. Send GUVI callback if conversation ends
    
    Returns:
        HoneypotResponse with status and reply
    """
    logger.info(f"Received message for session {request.sessionId}")
    logger.debug(f"Message: {request.message.text[:100]}...")
    
    try:
        # 1. Get or create session
        session = state_machine.get_or_create_session(
            request.sessionId,
            request.metadata
        )
        
        # Sync conversation history from request if provided
        if request.conversationHistory:
            session.conversation_history = request.conversationHistory.copy()
        
        # 2. Detect scam intent
        is_scam, confidence, keywords, scam_type = scam_detector.detect(
            request.message.text,
            [msg.model_dump() for msg in session.conversation_history]
        )
        
        # 3. Extract intelligence from current message
        message_intel = intelligence_extractor.extract(request.message.text)
        message_intel.suspiciousKeywords = list(set(
            message_intel.suspiciousKeywords + keywords
        ))
        
        # 4. Generate response based on current state
        metadata_dict = request.metadata.model_dump() if request.metadata else {}
        
        response_text = await ollama_client.generate_response(
            state=session.state,
            current_message=request.message.text,
            conversation_history=session.conversation_history,
            metadata=metadata_dict
        )
        
        # 5. Update session with new message and intelligence
        session = state_machine.update_session(
            session_id=request.sessionId,
            scammer_message=request.message,
            agent_response=response_text,
            intelligence=message_intel,
            scam_detected=is_scam
        )
        
        # Add agent note about this interaction
        if is_scam and scam_type != "unknown":
            session.agent_notes.append(f"Detected {scam_type} scam (confidence: {confidence:.2f})")
        
        logger.info(f"Session {request.sessionId}: State={session.state.value}, Messages={session.message_count}")
        
        # 6. Check if we should send GUVI callback (conversation ending)
        if state_machine.should_send_callback(session):
            agent_notes = state_machine.get_agent_notes_summary(session)
            callback_success = await send_guvi_callback(session, agent_notes)
            
            if callback_success:
                logger.info(f"GUVI callback sent for session {request.sessionId}")
            else:
                logger.warning(f"GUVI callback failed for session {request.sessionId}")
        
        return HoneypotResponse(
            status="success",
            reply=response_text
        )
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}")
async def get_session_status(
    session_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Get current session status and intelligence
    """
    session = state_machine.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    intel_summary = intelligence_extractor.get_intelligence_summary(session.intelligence)
    
    return {
        "sessionId": session.session_id,
        "state": session.state.value,
        "messageCount": session.message_count,
        "scamDetected": session.scam_detected,
        "intelligenceSummary": intel_summary,
        "agentNotes": session.agent_notes
    }


@router.get("/sessions")
async def list_sessions(api_key: str = Depends(verify_api_key)):
    """
    List all active sessions (admin endpoint)
    """
    sessions = state_machine.get_all_sessions()
    
    return {
        "count": len(sessions),
        "sessions": [
            {
                "sessionId": s.session_id,
                "state": s.state.value,
                "messageCount": s.message_count,
                "scamDetected": s.scam_detected
            }
            for s in sessions.values()
        ]
    }


@router.post("/session/{session_id}/force-exit")
async def force_exit_session(
    session_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Force a session to exit state and send GUVI callback
    """
    session = state_machine.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Force transition to EXIT
    session = state_machine.force_transition(session_id, ConversationState.EXIT)
    
    # Send callback
    agent_notes = state_machine.get_agent_notes_summary(session)
    callback_success = await send_guvi_callback(session, agent_notes)
    
    return {
        "status": "success" if callback_success else "callback_failed",
        "sessionId": session_id,
        "callbackSent": callback_success,
        "intelligence": session.intelligence.model_dump()
    }


@router.delete("/session/{session_id}")
async def delete_session(
    session_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Delete a session (cleanup)
    """
    session = state_machine.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    state_machine.delete_session(session_id)
    
    return {"status": "deleted", "sessionId": session_id}


@router.get("/health")
async def health_check():
    """Health check endpoint (no auth required)"""
    # Check Ollama connection
    ollama_ok = await ollama_client.check_connection()
    
    return {
        "status": "healthy" if ollama_ok else "degraded",
        "ollama": "connected" if ollama_ok else "disconnected",
        "activeSessions": len(state_machine.get_all_sessions())
    }

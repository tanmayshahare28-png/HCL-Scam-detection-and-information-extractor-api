"""
6-State Conversation State Machine
States: HOOKED → CONFUSED → TRUSTING → DELAY → EXTRACT → EXIT
"""
from typing import Dict, Optional
from loguru import logger

from app.models.schemas import (
    ConversationState, 
    SessionData, 
    Message, 
    ExtractedIntelligence,
    Metadata
)


class ConversationStateMachine:
    """
    Manages conversation state transitions for the honeypot agent.
    
    State Flow:
    1. HOOKED (1-2 messages) - Show interest, appear worried
    2. CONFUSED (2-3 messages) - Ask naive questions
    3. TRUSTING (2-3 messages) - Appear willing, share fake info
    4. DELAY (2-3 messages) - Create technical difficulties
    5. EXTRACT (2-4 messages) - Try to get scammer details
    6. EXIT (1 message) - Safely disengage
    """
    
    # Message thresholds for state transitions
    STATE_THRESHOLDS = {
        ConversationState.HOOKED: 2,
        ConversationState.CONFUSED: 4,
        ConversationState.TRUSTING: 7,
        ConversationState.DELAY: 10,
        ConversationState.EXTRACT: 14,
        ConversationState.EXIT: 18
    }
    
    # State transition order
    STATE_ORDER = [
        ConversationState.HOOKED,
        ConversationState.CONFUSED,
        ConversationState.TRUSTING,
        ConversationState.DELAY,
        ConversationState.EXTRACT,
        ConversationState.EXIT
    ]
    
    def __init__(self):
        # In-memory session storage
        self.sessions: Dict[str, SessionData] = {}
    
    def get_or_create_session(
        self, 
        session_id: str, 
        metadata: Optional[Metadata] = None
    ) -> SessionData:
        """Get existing session or create new one"""
        if session_id not in self.sessions:
            self.sessions[session_id] = SessionData(
                session_id=session_id,
                state=ConversationState.HOOKED,
                metadata=metadata
            )
            logger.info(f"Created new session: {session_id}")
        return self.sessions[session_id]
    
    def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get session by ID"""
        return self.sessions.get(session_id)
    
    def update_session(
        self,
        session_id: str,
        scammer_message: Message,
        agent_response: str,
        intelligence: ExtractedIntelligence,
        scam_detected: bool = False
    ) -> SessionData:
        """
        Update session with new message and potentially transition state
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Add scammer message to history
        session.conversation_history.append(scammer_message)
        
        # Add agent response to history
        agent_msg = Message(
            sender="user",
            text=agent_response,
            timestamp=scammer_message.timestamp + 1000  # 1 second later
        )
        session.conversation_history.append(agent_msg)
        
        # Update message count (count both sides)
        session.message_count = len(session.conversation_history)
        
        # Merge intelligence
        self._merge_intelligence(session.intelligence, intelligence)
        
        # Update scam detection
        if scam_detected:
            session.scam_detected = True
        
        # Check for state transition
        new_state = self._check_transition(session)
        if new_state != session.state:
            logger.info(f"Session {session_id}: State transition {session.state.value} → {new_state.value}")
            session.agent_notes.append(f"Transitioned to {new_state.value} at message {session.message_count}")
            session.state = new_state
        
        return session
    
    def _check_transition(self, session: SessionData) -> ConversationState:
        """
        Determine if state should transition based on message count and conditions
        """
        current_idx = self.STATE_ORDER.index(session.state)
        
        # Check if we should move to next state
        for i, state in enumerate(self.STATE_ORDER):
            if i > current_idx:
                threshold = self.STATE_THRESHOLDS.get(self.STATE_ORDER[i-1], 999)
                if session.message_count >= threshold:
                    # Check if we've extracted enough intelligence to skip to exit
                    if self._should_exit_early(session):
                        return ConversationState.EXIT
                    return state
        
        return session.state
    
    def _should_exit_early(self, session: SessionData) -> bool:
        """
        Check if we should exit early (got enough intelligence or scammer disengaging)
        """
        intel = session.intelligence
        
        # Exit if we have substantial intelligence
        intel_count = (
            len(intel.bankAccounts) +
            len(intel.upiIds) +
            len(intel.phoneNumbers) +
            len(intel.phishingLinks)
        )
        
        # If we're past EXTRACT state and have good intelligence
        if session.state == ConversationState.EXTRACT and intel_count >= 2:
            return True
        
        # If too many messages exchanged
        if session.message_count >= 20:
            return True
        
        return False
    
    def _merge_intelligence(
        self, 
        existing: ExtractedIntelligence, 
        new: ExtractedIntelligence
    ):
        """Merge new intelligence into existing, avoiding duplicates"""
        for account in new.bankAccounts:
            if account not in existing.bankAccounts:
                existing.bankAccounts.append(account)
        
        for upi in new.upiIds:
            if upi not in existing.upiIds:
                existing.upiIds.append(upi)
        
        for link in new.phishingLinks:
            if link not in existing.phishingLinks:
                existing.phishingLinks.append(link)
        
        for phone in new.phoneNumbers:
            if phone not in existing.phoneNumbers:
                existing.phoneNumbers.append(phone)
        
        for keyword in new.suspiciousKeywords:
            if keyword not in existing.suspiciousKeywords:
                existing.suspiciousKeywords.append(keyword)
    
    def force_transition(self, session_id: str, new_state: ConversationState) -> SessionData:
        """Force a state transition (for testing or manual override)"""
        session = self.sessions.get(session_id)
        if session:
            logger.info(f"Force transition {session_id}: {session.state.value} → {new_state.value}")
            session.state = new_state
        return session
    
    def should_send_callback(self, session: SessionData) -> bool:
        """Check if we should send final callback to GUVI"""
        return (
            session.state == ConversationState.EXIT and
            session.scam_detected and
            session.message_count >= 4  # At least 4 messages exchanged
        )
    
    def get_agent_notes_summary(self, session: SessionData) -> str:
        """Generate summary of agent notes for callback"""
        notes = session.agent_notes.copy()
        
        # Add intelligence summary
        intel = session.intelligence
        if intel.suspiciousKeywords:
            notes.append(f"Suspicious keywords detected: {', '.join(intel.suspiciousKeywords[:5])}")
        
        if intel.upiIds:
            notes.append("Scammer requested UPI payment")
        
        if intel.phoneNumbers:
            notes.append("Extracted scammer phone number(s)")
        
        if intel.phishingLinks:
            notes.append("Phishing links detected")
        
        return ". ".join(notes) if notes else "Scam engagement completed"
    
    def delete_session(self, session_id: str):
        """Delete a session after callback is sent"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Deleted session: {session_id}")
    
    def get_all_sessions(self) -> Dict[str, SessionData]:
        """Get all active sessions (for debugging/admin)"""
        return self.sessions


# Singleton instance
state_machine = ConversationStateMachine()

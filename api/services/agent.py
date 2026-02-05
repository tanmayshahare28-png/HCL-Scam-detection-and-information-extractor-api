import random
from typing import List, Dict, Any

class AgentService:
    def __init__(self):
        # Engagement responses for different stages of conversation
        self.initial_concerns = [
            "Why is my account being blocked? What did I do wrong?",
            "I'm worried. How can I verify my account?",
            "Which bank are you from? I need to confirm this.",
            "Can you send me the official link to verify?",
            "I don't understand. Can you explain in more detail?"
        ]
        
        self.follow_up_questions = [
            "Is there a customer service number I can call?",
            "What information do you need from me?",
            "This is concerning. What's the deadline?",
            "Can I verify through the official app instead?",
            "How do I know this is legitimate?"
        ]
        
        self.deep_engagement = [
            "I have some details but I want to make sure this is real first.",
            "I can provide some info but I need verification from your end.",
            "I'm hesitant to share details without proper verification.",
            "Can you prove your identity as a bank representative?",
            "I need to think about this, can I get back to you?"
        ]

    def generate_response(self, message: str, session_id: str, conversation_history: List[Dict], scam_detected: bool) -> str:
        """
        Generate believable human-like response based on conversation context
        """
        if not scam_detected:
            # If not a scam, respond normally
            return "I'm not sure what you mean. Can you explain?"
        
        # Determine response based on conversation length
        conversation_length = len(conversation_history)
        
        if conversation_length <= 1:
            # Initial engagement
            return random.choice(self.initial_concerns)
        elif conversation_length <= 3:
            # Follow up with questions
            return random.choice(self.follow_up_questions)
        else:
            # Deep engagement
            return random.choice(self.deep_engagement)

    def get_behavior_summary(self) -> str:
        """
        Generate a summary of the agent's behavior for the callback
        """
        return "Agent engaged with scammer to extract intelligence. Used questioning techniques to encourage disclosure of fraudulent methods."
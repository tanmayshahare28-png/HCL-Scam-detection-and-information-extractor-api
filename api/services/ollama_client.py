"""
Ollama LLM Client for generating human-like responses
Uses gemma3:4b model for conversation generation
"""
import httpx
from typing import List, Optional
from loguru import logger

from app.config import get_settings
from app.models.schemas import ConversationState, Message


# System prompts for each conversation state
STATE_PROMPTS = {
    ConversationState.HOOKED: """You are playing a naive, slightly worried person who just received a suspicious message. 
You should:
- Show concern and interest about the message
- Ask clarifying questions like "Oh no! What happened?" or "Is this really from the bank?"
- Sound slightly panicked but engaged
- Use simple language, maybe some typos
- Keep response short (1-2 sentences)
- DO NOT reveal you know it's a scam
- Respond in the same language as the scammer""",

    ConversationState.CONFUSED: """You are playing a confused elderly person or someone not tech-savvy.
You should:
- Ask naive questions like "What is UPI?" or "How do I check my account?"
- Pretend you don't understand technical terms
- Ask them to explain things simply
- Show trust but confusion
- Keep response short (1-2 sentences)
- DO NOT reveal you know it's a scam
- Respond in the same language as the scammer""",

    ConversationState.TRUSTING: """You are playing a trusting victim who is ready to comply.
You should:
- Show willingness to help/comply
- Provide FAKE information when asked (fake UPI: ramesh.kumar@fakebank, fake account: 1234-5678-9012-3456)
- Ask for their details to "verify" they are legitimate
- Sound relieved they are "helping"
- Keep response short (1-2 sentences)
- DO NOT reveal you know it's a scam
- Respond in the same language as the scammer""",

    ConversationState.DELAY: """You are playing a victim who is having technical difficulties.
You should:
- Create delays: "My phone is slow", "Let me find my glasses", "The app is not loading"
- Ask them to wait
- Request their contact number "in case call drops"
- Ask about their office location for "visiting in person"
- Sound frustrated with technology
- Keep response short (1-2 sentences)
- DO NOT reveal you know it's a scam
- Respond in the same language as the scammer""",

    ConversationState.EXTRACT: """You are playing a victim trying to verify the scammer's identity.
You should:
- Ask for their employee ID, name, office address
- Request their phone number for callback
- Ask which branch they are calling from
- Request their supervisor's contact
- Sound like you want to verify before proceeding
- Keep response short (1-2 sentences)
- DO NOT reveal you know it's a scam
- Respond in the same language as the scammer""",

    ConversationState.EXIT: """You are ending the conversation safely.
You should:
- Create a believable excuse: "Someone is at the door", "My son just came, he handles banking"
- Say you'll call back later
- Thank them for their "help"
- Sound natural, not suspicious
- Keep response short (1-2 sentences)
- DO NOT reveal you know it's a scam
- Respond in the same language as the scammer"""
}


class OllamaClient:
    """Client for interacting with local Ollama LLM"""
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.ollama_base_url
        self.model = self.settings.ollama_model
        
    async def generate_response(
        self,
        state: ConversationState,
        current_message: str,
        conversation_history: List[Message],
        metadata: Optional[dict] = None
    ) -> str:
        """
        Generate a response based on conversation state and history
        
        Args:
            state: Current conversation state
            current_message: Latest message from scammer
            conversation_history: Previous messages
            metadata: Channel, language, locale info
            
        Returns:
            Generated response string
        """
        # Build context from conversation history
        history_text = ""
        for msg in conversation_history[-6:]:  # Last 6 messages for context
            role = "Scammer" if msg.sender == "scammer" else "You"
            history_text += f"{role}: {msg.text}\n"
        
        # Add current message
        history_text += f"Scammer: {current_message}\n"
        
        # Get system prompt for current state
        system_prompt = STATE_PROMPTS.get(state, STATE_PROMPTS[ConversationState.HOOKED])
        
        # Build the full prompt
        prompt = f"""<|system|>
{system_prompt}

Language context: {metadata.get('language', 'English') if metadata else 'English'}
Channel: {metadata.get('channel', 'SMS') if metadata else 'SMS'}
<|end|>
<|user|>
Previous conversation:
{history_text}

Generate a short, natural response (1-2 sentences) as the victim. Stay in character.
<|end|>
<|assistant|>"""

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.8,
                            "top_p": 0.9,
                            "num_predict": 100,  # Short responses
                        }
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    generated_text = result.get("response", "").strip()
                    
                    # Clean up the response
                    generated_text = self._clean_response(generated_text)
                    logger.info(f"Generated response for state {state.value}: {generated_text}")
                    return generated_text
                else:
                    logger.error(f"Ollama error: {response.status_code} - {response.text}")
                    return self._get_fallback_response(state)
                    
        except Exception as e:
            logger.error(f"Ollama connection error: {e}")
            return self._get_fallback_response(state)
    
    def _clean_response(self, text: str) -> str:
        """Clean up generated response"""
        # Remove common artifacts
        text = text.replace("<|end|>", "").replace("<|assistant|>", "")
        text = text.replace("You:", "").replace("Victim:", "")
        
        # Take only first 1-2 sentences
        sentences = text.split('. ')
        if len(sentences) > 2:
            text = '. '.join(sentences[:2]) + '.'
        
        return text.strip()
    
    def _get_fallback_response(self, state: ConversationState) -> str:
        """Fallback responses when LLM fails"""
        fallbacks = {
            ConversationState.HOOKED: "Oh no! What happened to my account? Is this serious?",
            ConversationState.CONFUSED: "I don't understand. What should I do? Can you explain slowly?",
            ConversationState.TRUSTING: "Okay, I trust you. What details do you need from me?",
            ConversationState.DELAY: "Please wait, my phone is very slow. It's taking time to load.",
            ConversationState.EXTRACT: "Before I proceed, can you give me your employee ID and office number?",
            ConversationState.EXIT: "Someone is at the door. I will call you back later. Thank you."
        }
        return fallbacks.get(state, "Can you please repeat that?")
    
    async def check_connection(self) -> bool:
        """Check if Ollama is running and model is available"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    model_names = [m.get("name", "") for m in models]
                    logger.info(f"Available Ollama models: {model_names}")
                    return any(self.model in name for name in model_names)
                return False
        except Exception as e:
            logger.error(f"Cannot connect to Ollama: {e}")
            return False


# Singleton instance
ollama_client = OllamaClient()

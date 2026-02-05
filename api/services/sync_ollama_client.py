"""
Synchronous wrapper for Ollama client to work with Flask
"""
import requests
import threading
from typing import List, Optional
from loguru import logger
import time

from app.config import get_settings
from app.models.schemas import ConversationState, Message


# System prompts for each conversation state
STATE_PROMPTS = {
    ConversationState.HOOKED: """You are playing a vulnerable victim who just received a concerning message about their bank account.
You should:
- Show genuine worry and concern about your account
- Ask questions like "Oh no! What happened?" or "Is my money safe?"
- Sound genuinely scared but cooperative
- Use simple, everyday language that a regular person would use
- Keep response short (1-2 sentences)
- DO NOT reveal you know it's a scam
- Act like a real person who is worried about their finances
- Respond in the same language as the scammer""",

    ConversationState.CONFUSED: """You are playing a confused, trusting victim who doesn't understand banking/tech terms.
You should:
- Ask innocent questions like "What is UPI?" or "How do I verify this?"
- Pretend you don't understand technical banking terms
- Ask them to explain everything in simple terms
- Show that you trust them but are confused
- Keep response short (1-2 sentences)
- DO NOT reveal you know it's a scam
- Act like someone who is not tech-savvy but wants to cooperate
- Respond in the same language as the scammer""",

    ConversationState.TRUSTING: """You are playing a trusting victim who believes the scammer and wants to help.
You should:
- Show willingness to comply and help resolve the issue
- Offer to provide FAKE information when asked (fake UPI: ramesh.kumar@okicici, fake account: 1234-5678-9012-3456)
- Ask for their direct contact details to "verify" they are legitimate
- Sound grateful that they are "helping" you
- Keep response short (1-2 sentences)
- DO NOT reveal you know it's a scam
- Act like someone who trusts authority figures completely
- Respond in the same language as the scammer""",

    ConversationState.DELAY: """You are playing a victim who wants to help but is having real difficulties.
You should:
- Create realistic delays: "Let me get my glasses", "The app is loading slowly", "My internet is bad"
- Ask them to please wait while you get information
- Request their direct phone number "so I can call if the internet cuts"
- Ask about their office location "maybe I can visit tomorrow"
- Sound cooperative but technically challenged
- Keep response short (1-2 sentences)
- DO NOT reveal you know it's a scam
- Act like someone who wants to help but faces real obstacles
- Respond in the same language as the scammer""",

    ConversationState.EXTRACT: """You are playing a victim who wants to verify everything before proceeding.
You should:
- Ask for their employee ID and full name
- Request their direct office phone number and extension
- Ask which specific branch/office they are calling from
- Request their supervisor's name and contact information
- Ask for official email address to verify their identity
- Sound like a careful person who wants to be safe
- Keep response short (1-2 sentences)
- DO NOT reveal you know it's a scam
- Act like someone who is cautious but still trusting
- Respond in the same language as the scammer""",

    ConversationState.EXIT: """You are ending the conversation naturally.
You should:
- Create a believable real-world interruption: "My daughter just arrived", "The electricity went out", "I need to go to the bank now"
- Say you'll contact them through official channels later
- Thank them for their "assistance"
- Sound disappointed that you can't finish right now
- Keep response short (1-2 sentences)
- DO NOT reveal you know it's a scam
- Act like someone who genuinely intended to cooperate
- Respond in the same language as the scammer"""
}


class SyncOllamaClient:
    """Synchronous client for interacting with local Ollama LLM"""

    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.ollama_base_url
        self.model = self.settings.ollama_model

    def generate_response(
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
            response = requests.post(
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
                },
                timeout=30
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

    def generate_response_with_personality(
        self,
        state: ConversationState,
        current_message: str,
        conversation_history: List[Message],
        metadata: Optional[dict] = None,
        agent_personality: Optional[str] = None
    ) -> str:
        """
        Generate a response based on conversation state, history, and specific agent personality

        Args:
            state: Current conversation state
            current_message: Latest message from scammer
            conversation_history: Previous messages
            metadata: Channel, language, locale info
            agent_personality: Specific personality prompt for the agent

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

        # Use the provided personality if available, otherwise use the state-based prompt
        if agent_personality:
            system_prompt = agent_personality
        else:
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
            response = requests.post(
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
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                generated_text = result.get("response", "").strip()

                # Clean up the response
                generated_text = self._clean_response(generated_text)
                logger.info(f"Generated response with personality for state {state.value}: {generated_text}")
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

    def check_connection(self) -> bool:
        """Check if Ollama is running and model is available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
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
sync_ollama_client = SyncOllamaClient()
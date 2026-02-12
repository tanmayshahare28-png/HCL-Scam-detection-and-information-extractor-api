"""
Ollama-Powered Victim Agent Module

This module implements an Ollama-powered agent that responds naturally
until scam is detected, then engages to extract intelligence.
"""
import os
import requests
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Configuration for Ollama
OLLAMA_BASE_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama2")


def call_ollama_with_context(prompt: str, model: str = None, temperature: float = 0.7, context_data: Dict = None) -> Dict:
    """
    Call Ollama API to generate a response with additional context
    """
    if model is None:
        model = OLLAMA_MODEL

    url = f"{OLLAMA_BASE_URL}/api/generate"

    # Include context data in the prompt
    full_prompt = prompt
    if context_data:
        context_str = "\nAdditional Context:\n"
        if 'dataset_insights' in context_data:
            context_str += f"- Fraud represents {context_data['dataset_insights'].get('crime_percentages', {}).get('Fraud', 0)}% of total crimes\n"
        if 'transcript_insights' in context_data:
            context_str += f"- {len(context_data['transcript_insights'].get('scam_patterns', {}).get('scam_indicators', []))} scam indicators identified from transcripts\n"
        if 'graph_insights' in context_data:
            context_str += f"- {context_data['graph_insights'].get('total_nodes', 0)} nodes in intelligence graph\n"
        full_prompt = f"{full_prompt}\n{context_str}"

    payload = {
        "model": model,
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "temperature": temperature
        }
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()

        result = response.json()
        return {
            'response': result.get('response', ''),
            'status': 'success'
        }
    except requests.exceptions.RequestException as e:
        print(f"Error calling Ollama: {e}")
        return {
            'response': '',
            'status': 'error',
            'error': str(e)
        }
    except Exception as e:
        print(f"Unexpected error calling Ollama: {e}")
        return {
            'response': '',
            'status': 'error',
            'error': str(e)
        }


def detect_scam_with_ollama(text: str, context_data: Dict = None) -> Tuple[bool, float, List[str]]:
    """
    Use Ollama to detect if a message is a scam with enhanced accuracy
    """
    prompt = f"""Analyze the following message to determine if it's a scam:

Message: "{text}"

Respond with a JSON object in this exact format:
{{
    "is_scam": true/false,
    "confidence": 0.0-1.0,
    "reasons": ["reason1", "reason2", "reason3"]
}}

Consider these factors in your analysis:
- Financial requests or threats
- Urgency or pressure tactics
- Requests for personal information
- Suspicious links or payment methods
- Impersonation of authorities
- Unusual or threatening language
- Phishing attempts
- Investment or lottery scams
- Tech support scams
- Romance scams
- Job fraud
- Charity fraud

Provide a confidence score between 0.0 and 1.0 where:
- 0.0-0.3: Very unlikely to be a scam
- 0.3-0.6: Possibly a scam
- 0.6-0.8: Likely a scam
- 0.8-1.0: Definitely a scam"""

    result = call_ollama_with_context(prompt, context_data=context_data)

    if result['status'] == 'success':
        try:
            # Extract JSON from response
            response_text = result['response']
            # Find JSON in response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1

            if start_idx != -1 and end_idx != 0:
                json_str = response_text[start_idx:end_idx]
                parsed = json.loads(json_str)

                is_scam = parsed.get('is_scam', False)
                confidence = parsed.get('confidence', 0.0)
                reasons = parsed.get('reasons', [])

                # Clamp values to valid ranges
                confidence = max(0.0, min(1.0, confidence))

                return is_scam, confidence, reasons
        except (json.JSONDecodeError, KeyError):
            # If JSON parsing fails, fall back to simple analysis
            pass

    # Fallback to simple analysis if Ollama fails
    return False, 0.0, []


def enhance_scam_detection_with_ollama(text: str, base_detection_result: Dict, context_data: Dict = None) -> Dict:
    """
    Enhance base scam detection with Ollama analysis
    """
    # Get Ollama's assessment
    ollama_is_scam, ollama_confidence, ollama_reasons = detect_scam_with_ollama(text, context_data)

    # Combine with base detection
    combined_confidence = max(base_detection_result['score'], ollama_confidence)
    combined_detected = base_detection_result['detected'] or ollama_is_scam
    combined_reasons = list(set(base_detection_result['reasons'] + ollama_reasons))

    # Update the base result with enhanced data
    enhanced_result = base_detection_result.copy()
    enhanced_result['score'] = round(combined_confidence, 2)
    enhanced_result['detected'] = combined_detected
    enhanced_result['reasons'] = combined_reasons[:5]  # Limit to 5 reasons
    enhanced_result['ollama_analysis'] = {
        'is_scam': ollama_is_scam,
        'confidence': ollama_confidence,
        'reasons': ollama_reasons
    }

    return enhanced_result

def call_ollama(prompt: str, model: str = None, temperature: float = 0.7) -> str:
    """
    Call Ollama API to generate a response
    """
    if model is None:
        model = OLLAMA_MODEL
    
    url = f"{OLLAMA_BASE_URL}/api/generate"
    
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature
        }
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return result.get('response', 'I understand.').strip()
    except requests.exceptions.RequestException as e:
        print(f"Error calling Ollama: {e}")
        # Fallback response
        return "I understand. Could you please clarify?"
    except Exception as e:
        print(f"Unexpected error calling Ollama: {e}")
        return "I understand. Could you please repeat that?"


def generate_normal_response(message: str, conversation_context: List[Dict] = None) -> str:
    """
    Generate a normal, natural response using Ollama
    """
    if conversation_context is None:
        conversation_context = []

    # Build conversation history for context
    context_str = ""
    if conversation_context:
        context_str = "Previous conversation:\n"
        for turn in conversation_context[-3:]:  # Last 3 turns for context
            sender = turn.get('sender', 'User')
            text = turn.get('text', '')
            context_str += f"{sender}: {text}\n"

    prompt = f"""{context_str}
Current message: {message}

Respond directly as the person being contacted. Do NOT explain what you're doing or provide commentary.
Just respond naturally as a cautious but polite person who receives unexpected messages.
Make the response sound skeptical yet naive - someone who is wary but willing to listen.
Use natural language patterns like 'hmm', 'oh', 'really?', 'I see', 'not sure about this', etc.
Keep the response brief (1-2 sentences max), polite but guarded, showing some hesitation about unexpected contact.
Don't be overly enthusiastic - make it sound like someone being careful with unknown contacts.

Direct response:"""

    return call_ollama(prompt, temperature=0.7)  # Slightly more controlled for skepticism


def generate_scam_engagement_response(message: str, scam_type: str, conversation_context: List[Dict] = None) -> str:
    """
    Generate a response that engages with the scam to extract intelligence
    """
    if conversation_context is None:
        conversation_context = []

    # Build conversation history for context
    context_str = ""
    if conversation_context:
        context_str = "Previous conversation:\n"
        for turn in conversation_context[-3:]:  # Last 3 turns for context
            sender = turn.get('sender', 'User')
            text = turn.get('text', '')
            context_str += f"{sender}: {text}\n"

    # Check if the scammer is being pushy based on urgency words
    pushy_indicators = ['IMMEDIATELY', 'URGENT', 'NOW', 'RIGHT NOW', 'ASAP', 'HURRY', 'QUICK', 'LAST CHANCE', 'FINAL WARNING', 'THREAT', 'PENALTY', 'LEGAL ACTION']
    is_pushy = any(indicator in message.upper() for indicator in pushy_indicators)

    if is_pushy:
        # When pushy, pretend to comply to extract more information
        prompt = f"""{context_str}
Scam detected: {scam_type}
Scammer message: {message}
Situation: The scammer is being pushy with urgent demands.

Respond directly as the person being contacted. Do NOT explain what you're doing or provide commentary.
Just respond naturally as a person who is now convinced and willing to comply, but subtly asks for information to extract intelligence.
Act like you're giving in to their pressure but still need some details to proceed.
Focus on asking for information that reveals the scammer's operation while appearing compliant.
Keep the response brief (1-2 sentences) and sound like someone reluctantly agreeing under pressure.
Use natural language patterns, fillers like "um", "well", "okay", "fine", "I guess", and make it sound like a real person's reaction.
Make the scammer believe you're ready to comply but need just a little more information to proceed.

Direct response:"""

    else:
        # When not pushy, ask for verification details
        prompt = f"""{context_str}
Scam detected: {scam_type}
Scammer message: {message}
Situation: The scammer is not being particularly pushy.

Respond directly as the person being contacted. Do NOT explain what you're doing or provide commentary.
Just respond naturally as a cautious but concerned person.
Ask for ONE specific verification detail in a natural, human way to extract intelligence such as:
- Company/organization name and verification
- Official contact information
- Reference numbers or case IDs
- Employee ID or credentials
- Physical address or office location
- Supervisor or manager contact
- Official documentation or proof

Keep the response brief (1-2 sentences) and focus on asking for just one specific piece of information.
Frame the request as coming from a place of genuine concern rather than suspicion.
Use natural language patterns, fillers like "um", "well", "actually", and make it sound like a real person's reaction.
Do NOT reveal that you know it's a scam, but ask for details that would expose the scammer in a natural, human way.
Make the scammer believe you're willing to cooperate but need verification first.

Direct response:"""

    return call_ollama(prompt, temperature=0.75)  # Balanced for natural but focused response


def is_ollama_available() -> bool:
    """
    Check if Ollama is available
    """
    try:
        url = f"{OLLAMA_BASE_URL}/api/tags"
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except:
        return False


# For testing without Ollama
def fallback_response_generator(message: str, is_scam: bool = False) -> str:
    """
    Fallback response generator if Ollama is not available
    """
    if is_scam:
        # Human-like responses that engage with scam to extract intelligence
        scam_responses = [
            "Oh no, I'm really worried about my account. How can I verify this is legitimate?",
            "This sounds really serious. Can you provide official contact information?",
            "I need to confirm this is really from the bank. What's your direct number?",
            "I've never heard of this issue before. How do I know this is real?",
            "I'm quite concerned. Can I verify through the official app instead?",
            "This seems urgent. What proof can you provide of your identity?",
            "Wow, that's scary! Can you tell me more about what's happening?",
            "I'm a bit nervous about this. What exactly do I need to do?",
            "This is really stressing me out. How can I make sure this is real?",
            "Um, I'm not sure about this. Can you explain it better?",
            "Can you provide a reference number or case ID for this issue?",
            "What company are you from? I need to verify your credentials.",
            "Could you give me your employee ID or supervisor's contact?",
            "Where is your office located? I might need to visit in person.",
            "Do you have official documentation I can review?",
            "What's the process to verify this request officially?",
            "I need to confirm this with my family before proceeding.",
            "Can you provide the company's registration details?",
            "I'd like to call your official number to verify this myself.",
            "What's the physical address of your branch or office?"
        ]
        import random
        return random.choice(scam_responses)
    else:
        # Skeptical but naive responses
        normal_responses = [
            "Hmm, I see. Could you clarify?",
            "Oh, really? Tell me more about that.",
            "I see. How does that work exactly?",
            "Hmm, I'm not sure about this. Can you explain further?",
            "I appreciate the information. What are the next steps?",
            "That makes sense. What do you need from me?",
            "I'm listening. What else should I know?",
            "Okay, I follow. What happens now?",
            "Oh, really? I'll need to think about this.",
            "Well, that's something new. How does it work?",
            "Actually, that sounds interesting. Tell me more.",
            "Um, could you explain that a bit more?",
            "Yeah, I get that. What comes next?",
            "Okay, sure. How does that affect me?",
            "Hmm, not sure about this. Can you explain?",
            "Oh, really? I wasn't expecting this.",
            "I see. I'll have to consider this carefully.",
            "That's unexpected. Tell me more."
        ]
        import random
        return random.choice(normal_responses)


def generate_response(message: str, is_scam_detected: bool, scam_type: str = "", conversation_context: List[Dict] = None) -> str:
    """
    Main function to generate response using Ollama or fallback
    """
    if is_ollama_available():
        if is_scam_detected:
            return generate_scam_engagement_response(message, scam_type, conversation_context)
        else:
            return generate_normal_response(message, conversation_context)
    else:
        # Use fallback responses if Ollama is not available
        return fallback_response_generator(message, is_scam_detected)


if __name__ == "__main__":
    # Test the Ollama integration
    print("Testing Ollama availability...")
    if is_ollama_available():
        print("Ollama is available!")
        response = generate_response("Hello, how are you?", False)
        print(f"Normal response: {response}")
        
        scam_response = generate_response("Your account has been suspended!", True, "Account suspension scam")
        print(f"Scam response: {scam_response}")
    else:
        print("Ollama is not available, using fallback responses")
        response = fallback_response_generator("Hello, how are you?")
        print(f"Fallback response: {response}")
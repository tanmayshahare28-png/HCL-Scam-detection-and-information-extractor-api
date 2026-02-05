import requests
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class CallbackService:
    def __init__(self):
        # Using a mock endpoint for demonstration
        # In production, this would be the actual evaluation endpoint
        self.evaluation_endpoint = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

    def send_callback(self, callback_data: Dict[str, Any]) -> bool:
        """
        Send intelligence data to the evaluation endpoint
        """
        try:
            payload = callback_data

            response = requests.post(
                self.evaluation_endpoint,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )

            if response.status_code in [200, 201]:
                logger.info(f"Callback sent successfully for session {callback_data.get('sessionId', 'unknown')}")
                return True
            else:
                logger.error(f"Callback failed for session {callback_data.get('sessionId', 'unknown')}. Status: {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending callback for session {callback_data.get('sessionId', 'unknown')}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending callback for session {callback_data.get('sessionId', 'unknown')}: {e}")
            return False
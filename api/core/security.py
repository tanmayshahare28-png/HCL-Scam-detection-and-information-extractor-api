import logging
from typing import Optional
from api.core.config import settings

async def validate_api_key(api_key: str) -> Optional[dict]:
    """
    Validate API key against stored keys
    """
    if api_key in settings.API_KEYS:
        return settings.API_KEYS[api_key]
    return None

def setup_logging():
    """
    Setup logging configuration
    """
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance
    """
    return logging.getLogger(name)
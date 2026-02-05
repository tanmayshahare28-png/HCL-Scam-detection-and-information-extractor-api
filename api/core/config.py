import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    # App settings
    APP_NAME: str = os.getenv("APP_NAME", "Honeypot API")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    WORKERS: int = int(os.getenv("WORKERS", "1"))
    
    # Security settings
    API_KEYS: dict = {
        "test_key_123": {"name": "Test User", "plan": "free", "rate_limit": "10/minute"},
        "prod_key_456": {"name": "Production", "plan": "pro", "rate_limit": "100/minute"}
    }
    
    ALLOWED_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:8080",
        os.getenv("FRONTEND_URL", "")
    ]
    
    # Evaluation settings
    EVALUATION_CALLBACK_URL: str = os.getenv("EVALUATION_CALLBACK_URL", "https://hackathon.guvi.in/api/updateHoneyPotFinalResult")
    CALLBACK_TIMEOUT: int = int(os.getenv("CALLBACK_TIMEOUT", "5"))
    
    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

settings = Settings()
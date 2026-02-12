"""
Agentic Honey-Pot for Scam Detection & Intelligence Extraction
FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from loguru import logger
import sys
from pathlib import Path

from app.config import get_settings
from app.routers import honeypot

# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="DEBUG"
)
logger.add(
    "logs/honeypot.log",
    rotation="10 MB",
    retention="7 days",
    level="INFO"
)

# Create FastAPI app
app = FastAPI(
    title="Agentic Honey-Pot API",
    description="""
    AI-powered honeypot system that:
    - Detects scam/fraud messages
    - Engages scammers autonomously
    - Maintains believable human-like persona
    - Handles multi-turn conversations
    - Extracts scam-related intelligence
    
    Built for GUVI Hackathon 2026
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for hackathon; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(honeypot.router)

# Serve static files (frontend)
static_path = Path(__file__).parent.parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


@app.get("/")
async def root():
    """Serve frontend or redirect to docs"""
    index_path = static_path / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {
        "message": "Agentic Honey-Pot API",
        "docs": "/docs",
        "health": "/api/health"
    }


@app.on_event("startup")
async def startup_event():
    """Startup tasks"""
    settings = get_settings()
    logger.info("=" * 50)
    logger.info("Agentic Honey-Pot API Starting...")
    logger.info(f"Ollama URL: {settings.ollama_base_url}")
    logger.info(f"Ollama Model: {settings.ollama_model}")
    logger.info(f"GUVI Callback: {settings.guvi_callback_url}")
    logger.info("=" * 50)
    
    # Check Ollama connection
    from app.services.ollama_client import ollama_client
    if await ollama_client.check_connection():
        logger.info("✅ Ollama connection successful")
    else:
        logger.warning("⚠️ Ollama not available - using fallback responses")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup tasks"""
    logger.info("Agentic Honey-Pot API Shutting down...")


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )

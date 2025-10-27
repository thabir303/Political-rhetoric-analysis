"""
Main FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import uvicorn
import warnings
import multiprocessing

# Suppress multiprocessing warnings
warnings.filterwarnings("ignore", category=UserWarning, module="multiprocessing.resource_tracker")

# Set multiprocessing start method
try:
    multiprocessing.set_start_method('spawn', force=True)
except RuntimeError:
    pass  # Already set

from backend.config import settings
# Import from organized routes instead of old api/routes.py
from backend.routes import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="RAG-based Information Retrieval API with ChromaDB vector store",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"ChromaDB persist directory: {settings.chroma_persist_directory}")
    logger.info(f"Embedding model: {settings.embedding_model}")
    
    # Initialize chatbot components
    try:
        logger.info("Initializing chatbot components...")
        from backend.routes.chatbot import initialize_chatbot_components
        initialize_chatbot_components()
        logger.info("✓ Chatbot components initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize chatbot: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down application")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to RAG-IR API",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/api/v1/health"
    }


if __name__ == "__main__":
    # Force single worker for memory optimization (2GB RAM limit)
    # Multiple workers multiply memory usage by worker count
    import os
    os.environ['WEB_CONCURRENCY'] = '1'
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development",
        log_level="info",
        workers=1  # Explicitly set 1 worker for production
    )

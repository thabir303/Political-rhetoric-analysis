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
# Import all routers
from backend.routes.general import router as general_router
from backend.routes.articles import router as articles_router
from backend.routes.scraping import router as scraping_router
from backend.routes.analysis import router as analysis_router
from backend.routes.stored_analysis import router as stored_analysis_router
from backend.routes.parties import router as parties_router
from backend.routes.figures import router as figures_router
from backend.routes.topics import router as topics_router
from backend.routes.keywords import router as keywords_router
from backend.routes.election import router as election_router

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

# Include all routers
app.include_router(general_router, prefix="/api/v1")
app.include_router(articles_router, prefix="/api/v1")
app.include_router(scraping_router, prefix="/api/v1")
app.include_router(analysis_router, prefix="/api/v1")
app.include_router(stored_analysis_router, prefix="/api/v1")
app.include_router(parties_router, prefix="/api/v1")
app.include_router(figures_router, prefix="/api/v1")
app.include_router(topics_router)  # Already has /api/v1 prefix
app.include_router(keywords_router)  # Already has /api/v1 prefix
app.include_router(election_router)  # Already has /api/v1 prefix


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"ChromaDB persist directory: {settings.chroma_persist_directory}")
    logger.info(f"Embedding model: {settings.embedding_model}")


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
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development",
        log_level="info"
    )

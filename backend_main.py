"""
Main FastAPI application entry point with organized backend structure.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import warnings
import multiprocessing

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning, module="multiprocessing.resource_tracker")

# Set multiprocessing start method
try:
    multiprocessing.set_start_method('spawn', force=True)
except RuntimeError:
    pass

from backend.config.settings import settings

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
    description="RAG-based Information Retrieval API with Separated Scraping and LLM Analysis",
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

# Import routers
from backend.routes.general import router as general_router
from backend.routes.articles import router as articles_router
from backend.routes.scraping import router as scraping_router
from backend.routes.analysis import router as analysis_router
from backend.routes.stored_analysis import router as stored_analysis_router
from backend.routes.parties import router as parties_router
from backend.routes.topics import router as topics_router
from backend.routes.keywords import router as keywords_router
from backend.routes.election import router as election_router

# Include routers
app.include_router(general_router, prefix="/api/v1")
app.include_router(articles_router, prefix="/api/v1")
app.include_router(scraping_router, prefix="/api/v1")
app.include_router(analysis_router, prefix="/api/v1")
app.include_router(stored_analysis_router, prefix="/api/v1")
app.include_router(parties_router, prefix="/api/v1")
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
    logger.info("")
    logger.info("=" * 60)
    logger.info("API ENDPOINTS:")
    logger.info("  🔧 General:")
    logger.info("    GET  /api/v1/health")
    logger.info("    GET  /api/v1/stats")
    logger.info("")
    logger.info("  📰 Scraping (NO LLM):")
    logger.info("    POST /api/v1/scraping/newspapers")
    logger.info("    POST /api/v1/scraping/political")
    logger.info("")
    logger.info("  🤖 LLM Analysis (Separate):")
    logger.info("    POST /api/v1/analysis/llm")
    logger.info("    POST /api/v1/analysis/party-report")
    logger.info("    POST /api/v1/analysis/figure-report")
    logger.info("")
    logger.info("  📚 Articles:")
    logger.info("    POST /api/v1/articles")
    logger.info("    POST /api/v1/articles/bulk")
    logger.info("    POST /api/v1/articles/query")
    logger.info("    GET  /api/v1/articles/{id}")
    logger.info("    DELETE /api/v1/articles/{id}")
    logger.info("")
    logger.info("  🏷️  Topics:")
    logger.info("    GET  /api/v1/topics")
    logger.info("    GET  /api/v1/topics/{topic}/articles")
    logger.info("    GET  /api/v1/topics/stats")
    logger.info("")
    logger.info("  🔑 Keywords:")
    logger.info("    GET  /api/v1/keywords")
    logger.info("    GET  /api/v1/keywords/{keyword}/articles")
    logger.info("    GET  /api/v1/keywords/search")
    logger.info("    GET  /api/v1/keywords/stats")
    logger.info("")
    logger.info("  🗳️  2026 Election Impact:")
    logger.info("    GET  /api/v1/election-impact")
    logger.info("    GET  /api/v1/election-impact/stats")
    logger.info("    GET  /api/v1/election-impact/timeline")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down application")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to RAG-IR Backend API",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/api/v1/health",
        "structure": {
            "scraping": "POST /api/v1/scraping/newspapers (NO LLM)",
            "analysis": "POST /api/v1/analysis/llm (Separate LLM Analysis)",
            "articles": "POST /api/v1/articles",
            "query": "POST /api/v1/articles/query"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend_main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development",
        log_level="info"
    )

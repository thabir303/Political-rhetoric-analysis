"""
General Routes - Health, Stats, etc.
"""
from fastapi import APIRouter, HTTPException, status, Depends
import logging

from backend.models.schemas import HealthResponse
from backend.config.settings import settings
from backend.auth import require_auth

logger = logging.getLogger(__name__)

router = APIRouter(tags=["General"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint to verify service status.
    """
    try:
        from backend.core.vector_db import VectorDatabase
        
        db = VectorDatabase(collection_name="political_articles")
        stats = db.get_statistics()
        total_articles = stats.get("total_articles", 0)
        
        # Get ChromaDB path
        chromadb_path = settings.chroma_persist_directory
        
        return HealthResponse(
            status="healthy",
            version=settings.app_version,
            database_connected=True,
            total_articles=total_articles,
            chromadb_path=chromadb_path
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            version=settings.app_version,
            database_connected=False,
            total_articles=0,
            chromadb_path=settings.chroma_persist_directory
        )


@router.get("/stats", dependencies=[Depends(require_auth)])
async def get_statistics():
    """
    Get database statistics.
    """
    try:
        from backend.core.vector_db import VectorDatabase
        
        db = VectorDatabase(collection_name="political_articles")
        stats = db.get_statistics()
        
        return {
            "status": "success",
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )


@router.get("/", dependencies=[Depends(require_auth)])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to RAG-IR Backend API",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/api/v1/health",
        "endpoints": {
            "scraping": "/api/v1/scraping/newspapers",
            "analysis": "/api/v1/analysis/llm",
            "articles": "/api/v1/articles",
            "query": "/api/v1/articles/query"
        }
    }

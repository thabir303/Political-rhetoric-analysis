"""
API route handlers for the RAG-IR application.
"""
from fastapi import APIRouter, HTTPException, status
from typing import List
import time
import logging

from models import (
    ArticleCreate,
    ArticleResponse,
    QueryRequest,
    QueryResponse,
    HealthResponse,
    BulkArticleCreate,
    BulkArticleResponse,
)
from database import vector_store
from config import settings

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint to verify service status.
    """
    try:
        stats = vector_store.get_collection_stats()
        return HealthResponse(
            status="healthy",
            version=settings.app_version,
            database_connected=True,
            total_articles=stats["total_articles"]
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            version=settings.app_version,
            database_connected=False,
            total_articles=0
        )


@router.post(
    "/articles",
    response_model=ArticleResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Articles"]
)
async def create_article(article: ArticleCreate):
    """
    Store a new article in the vector database.
    
    The article content will be embedded and stored along with metadata
    for efficient similarity search.
    """
    try:
        # Convert metadata to dict
        metadata_dict = article.metadata.model_dump(exclude_none=True)
        
        # Add article to vector store
        article_id = vector_store.add_article(
            content=article.content,
            metadata=metadata_dict,
            article_id=article.article_id
        )
        
        return ArticleResponse(
            id=article_id,
            content=article.content,
            metadata=metadata_dict
        )
        
    except Exception as e:
        logger.error(f"Failed to create article: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create article: {str(e)}"
        )


@router.post(
    "/articles/bulk",
    response_model=BulkArticleResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Articles"]
)
async def create_articles_bulk(bulk_request: BulkArticleCreate):
    """
    Store multiple articles in bulk for better performance.
    
    This endpoint is optimized for inserting large batches of articles.
    """
    try:
        contents = []
        metadatas = []
        article_ids = []
        
        for article in bulk_request.articles:
            contents.append(article.content)
            metadatas.append(article.metadata.model_dump(exclude_none=True))
            article_ids.append(article.article_id)
        
        # Filter out None article_ids
        if all(aid is None for aid in article_ids):
            article_ids = None
        
        # Add articles in bulk
        inserted_ids = vector_store.add_articles_bulk(
            contents=contents,
            metadatas=metadatas,
            article_ids=article_ids
        )
        
        return BulkArticleResponse(
            success=True,
            inserted_count=len(inserted_ids),
            failed_count=0,
            article_ids=inserted_ids
        )
        
    except Exception as e:
        logger.error(f"Failed to create articles in bulk: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create articles: {str(e)}"
        )


@router.post(
    "/query",
    response_model=QueryResponse,
    tags=["Query"]
)
async def query_articles(query_request: QueryRequest):
    """
    Query articles based on semantic similarity.
    
    Returns the most similar articles to the query text, with optional
    filtering by category, date, or persons mentioned.
    """
    try:
        start_time = time.time()
        
        # Build filter dictionary
        filter_dict = {}
        if query_request.filter_category:
            filter_dict["category"] = query_request.filter_category
        if query_request.filter_date:
            filter_dict["date"] = query_request.filter_date
        if query_request.filter_persons:
            # For persons, we'll use a contains search
            filter_dict["persons"] = query_request.filter_persons
        
        # Query vector store
        ids, metadatas, documents, distances = vector_store.query_articles(
            query_text=query_request.query,
            top_k=query_request.top_k,
            filter_dict=filter_dict if filter_dict else None
        )
        
        # Build response
        results = []
        for i in range(len(ids)):
            results.append(
                ArticleResponse(
                    id=ids[i],
                    content=documents[i],
                    metadata=metadatas[i],
                    distance=distances[i]
                )
            )
        
        processing_time = time.time() - start_time
        
        return QueryResponse(
            query=query_request.query,
            results=results,
            total_results=len(results),
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {str(e)}"
        )


@router.get(
    "/articles/{article_id}",
    response_model=ArticleResponse,
    tags=["Articles"]
)
async def get_article(article_id: str):
    """
    Retrieve a specific article by its ID.
    """
    try:
        article = vector_store.get_article_by_id(article_id)
        
        if article is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Article with ID {article_id} not found"
            )
        
        return ArticleResponse(
            id=article["id"],
            content=article["content"],
            metadata=article["metadata"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get article: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve article: {str(e)}"
        )


@router.delete(
    "/articles/{article_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Articles"]
)
async def delete_article(article_id: str):
    """
    Delete an article by its ID.
    """
    try:
        vector_store.delete_article(article_id)
        return None
        
    except Exception as e:
        logger.error(f"Failed to delete article: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete article: {str(e)}"
        )


@router.get(
    "/stats",
    tags=["Statistics"]
)
async def get_statistics():
    """
    Get database statistics and information.
    """
    try:
        stats = vector_store.get_collection_stats()
        return {
            "status": "success",
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve statistics: {str(e)}"
        )

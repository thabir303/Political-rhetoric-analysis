"""
Article Management Routes
"""
from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
import time
import logging

from backend.models.schemas import (
    ArticleCreate,
    ArticleResponse,
    QueryRequest,
    QueryResponse,
    BulkArticleCreate,
    BulkArticleResponse,
)
from backend.database.vector_store import vector_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/articles", tags=["Articles"])


@router.post(
    "",
    response_model=ArticleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a single article"
)
async def create_article(article: ArticleCreate):
    """
    Store a new article in the vector database.
    
    The article content will be embedded and stored along with metadata
    for efficient similarity search.
    """
    try:
        metadata_dict = article.metadata.model_dump(exclude_none=True)
        
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
    "/bulk",
    response_model=BulkArticleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create multiple articles in bulk"
)
async def create_articles_bulk(bulk_request: BulkArticleCreate):
    """
    Store multiple articles in bulk for better performance.
    """
    try:
        contents = []
        metadatas = []
        article_ids = []
        
        for article in bulk_request.articles:
            contents.append(article.content)
            metadatas.append(article.metadata.model_dump(exclude_none=True))
            article_ids.append(article.article_id)
        
        if all(aid is None for aid in article_ids):
            article_ids = None
        
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


@router.get(
    "/{article_id}",
    response_model=ArticleResponse,
    summary="Get article by ID"
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
    "/{article_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete article by ID"
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


@router.post(
    "/query",
    response_model=QueryResponse,
    summary="Query articles by semantic similarity"
)
async def query_articles(query_request: QueryRequest):
    """
    Query articles based on semantic similarity.
    
    Returns the most similar articles to the query text, with optional
    filtering by category, date, or persons mentioned.
    """
    try:
        start_time = time.time()
        
        from backend.core.vector_db import VectorDatabase
        
        db = VectorDatabase(collection_name="political_articles")
        
        # Build filter dictionary
        filter_dict = {}
        if query_request.filter_category:
            filter_dict["category"] = query_request.filter_category
        if query_request.filter_date:
            filter_dict["date"] = query_request.filter_date
        if query_request.filter_persons:
            filter_dict["persons"] = query_request.filter_persons
        
        # Query
        result = db.query_articles(
            query_text=query_request.query,
            top_k=query_request.top_k,
            metadata_filter=filter_dict if filter_dict else None
        )
        
        if result.get('success'):
            query_results = result.get('results', [])
            results = []
            for r in query_results:
                results.append(
                    ArticleResponse(
                        id=r.get('id', ''),
                        content=r.get('content', ''),
                        metadata=r.get('metadata', {}),
                        distance=1 - r.get('similarity', 0)
                    )
                )
        else:
            results = []
        
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


@router.post(
    "/{article_id}/summarize",
    summary="Generate article summary using LLM"
)
async def summarize_article(article_id: str):
    """
    Generate a concise summary of an article using LLM.
    
    Args:
        article_id: The ID of the article to summarize
        
    Returns:
        Dict with summary and metadata
    """
    try:
        from backend.core.vector_db import VectorDatabase
        from backend.core.llm_generation import LLMGenerator
        
        logger.info(f"Generating summary for article: {article_id}")
        
        # Get the article from database
        db = VectorDatabase(collection_name="political_articles")
        result = db.collection.get(
            ids=[article_id],
            include=["metadatas", "documents"]
        )
        
        if not result or not result.get('documents') or len(result['documents']) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Article not found: {article_id}"
            )
        
        article_content = result['documents'][0]
        article_metadata = result['metadatas'][0] if result.get('metadatas') else {}
        
        # Generate summary using LLM
        llm = LLMGenerator()
        
        # Check if content is in Bangla or English
        is_bangla = any('\u0980' <= char <= '\u09FF' for char in article_content[:200])
        
        # Simple prompt - only ask for summary, no extra words
        if is_bangla:
            prompt = f"নিচের আর্টিকেলটি ৩-৪টি সংক্ষিপ্ত বাক্যে সংক্ষেপে বলুন (শুধুমাত্র বাংলায় উত্তর দিন):\n\n{article_content}"
        else:
            prompt = f"Summarize the following article in 3-4 concise sentences:\n\n{article_content}"
        
        logger.info(f"Sending summarization request to LLM for article {article_id} (Language: {'Bangla' if is_bangla else 'English'})")
        summary = llm._call_llm(prompt)
        
        logger.info(f"Successfully generated summary for article {article_id}")
        
        # Update the article metadata with the summary (keep original content as document)
        try:
            # Store summary in metadata (NOT replacing the document)
            article_metadata["summary"] = summary
            article_metadata["is_summarized"] = True
            from datetime import datetime
            article_metadata["summarized_at"] = datetime.now().isoformat()
            
            # Update database - keep original content as document, add summary to metadata
            db.collection.update(
                ids=[article_id],
                documents=[article_content],  # Keep original content
                metadatas=[article_metadata]   # Add summary to metadata
            )
            logger.info(f"Stored summary in metadata for article {article_id} (original content preserved)")
        except Exception as update_error:
            logger.error(f"Failed to update article in database: {update_error}")
            # Continue anyway, at least return the summary
        
        return {
            "success": True,
            "article_id": article_id,
            "title": article_metadata.get("title", "No title"),
            "summary": summary,
            "original_length": len(article_content),
            "summary_length": len(summary),
            "stored_in_db": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary: {str(e)}"
        )

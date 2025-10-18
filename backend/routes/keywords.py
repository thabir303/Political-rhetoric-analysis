"""
Keywords API routes for keyword-based article filtering and discovery.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Optional
import logging
from collections import Counter

router = APIRouter(prefix="/api/v1", tags=["keywords"])
logger = logging.getLogger(__name__)


@router.get("/keywords")
async def get_all_keywords(
    min_frequency: int = Query(1, description="Minimum frequency for a keyword to be included"),
    limit: int = Query(100, description="Maximum number of keywords to return")
):
    """
    Get all unique keywords across all articles with frequencies.
    
    Args:
        min_frequency: Minimum number of occurrences for a keyword to be included
        limit: Maximum number of keywords to return
    
    Returns:
        List of keywords with frequencies, sorted by frequency descending
    """
    try:
        from backend.core.vector_db import VectorDatabase
        db = VectorDatabase(collection_name="political_articles")
        
        # Get all articles
        collection = db.collection
        results = collection.get(include=["metadatas"])
        
        if not results or not results['metadatas']:
            return {
                "keywords": [],
                "total_keywords": 0,
                "message": "No articles found"
            }
        
        # Collect all keywords
        keywords_counter = Counter()
        for metadata in results['metadatas']:
            keywords_str = metadata.get('keywords', '')
            if keywords_str:
                # Split comma-separated keywords
                keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]
                keywords_counter.update(keywords)
        
        # Filter by minimum frequency and sort
        keywords_list = [
            {
                "keyword": keyword,
                "frequency": count,
                "percentage": round((count / len(results['metadatas'])) * 100, 1)
            }
            for keyword, count in keywords_counter.items()
            if count >= min_frequency
        ]
        
        # Sort by frequency descending
        keywords_list.sort(key=lambda x: x['frequency'], reverse=True)
        
        # Apply limit
        keywords_list = keywords_list[:limit]
        
        return {
            "keywords": keywords_list,
            "total_keywords": len(keywords_list),
            "total_articles": len(results['metadatas'])
        }
        
    except Exception as e:
        logger.error(f"Error getting keywords: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/keywords/{keyword}/articles")
async def get_articles_by_keyword(
    keyword: str,
    limit: int = Query(50, description="Maximum number of articles to return"),
    offset: int = Query(0, description="Number of articles to skip")
):
    """
    Get all articles containing a specific keyword.
    
    Args:
        keyword: The keyword to filter by
        limit: Maximum number of articles to return
        offset: Number of articles to skip (for pagination)
    
    Returns:
        List of articles containing the specified keyword
    """
    try:
        from backend.core.vector_db import VectorDatabase
        db = VectorDatabase(collection_name="political_articles")
        
        # Get all articles
        collection = db.collection
        results = collection.get(include=["metadatas", "documents"])
        
        if not results or not results['metadatas']:
            return {
                "keyword": keyword,
                "articles": [],
                "total_count": 0
            }
        
        # Filter articles by keyword
        matching_articles = []
        for idx, metadata in enumerate(results['metadatas']):
            keywords_str = metadata.get('keywords', '')
            if keywords_str:
                keywords = [k.strip().lower() for k in keywords_str.split(',')]
                if keyword.lower() in keywords:
                    article = {
                        "id": results['ids'][idx],
                        "title": metadata.get('title', ''),
                        "summary": results['documents'][idx],
                        "date": metadata.get('date', ''),
                        "source": metadata.get('source', ''),
                        "url": metadata.get('url', ''),
                        "keywords": metadata.get('keywords', '').split(',') if metadata.get('keywords') else [],
                        "topics": metadata.get('topics', '').split(',') if metadata.get('topics') else [],
                        "has_election_impact": metadata.get('has_election_impact', False),
                        "election_2026_impact": metadata.get('election_2026_impact', ''),
                        "persons": metadata.get('persons', ''),
                        "language": metadata.get('language', 'Unknown')
                    }
                    matching_articles.append(article)
        
        # Sort by date (newest first)
        matching_articles.sort(
            key=lambda x: x['date'] if x['date'] else '1970-01-01',
            reverse=True
        )
        
        # Apply pagination
        total_count = len(matching_articles)
        paginated_articles = matching_articles[offset:offset + limit]
        
        return {
            "keyword": keyword,
            "articles": paginated_articles,
            "total_count": total_count,
            "returned_count": len(paginated_articles),
            "offset": offset,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error getting articles by keyword: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/keywords/search")
async def search_keywords(
    query: str = Query(..., description="Search query for keywords"),
    limit: int = Query(20, description="Maximum number of keywords to return")
):
    """
    Search for keywords matching a query string.
    
    Args:
        query: Search query
        limit: Maximum number of keywords to return
    
    Returns:
        List of matching keywords with frequencies
    """
    try:
        from backend.core.vector_db import VectorDatabase
        db = VectorDatabase(collection_name="political_articles")
        
        # Get all articles
        collection = db.collection
        results = collection.get(include=["metadatas"])
        
        if not results or not results['metadatas']:
            return {
                "query": query,
                "keywords": [],
                "message": "No articles found"
            }
        
        # Collect all keywords
        keywords_counter = Counter()
        for metadata in results['metadatas']:
            keywords_str = metadata.get('keywords', '')
            if keywords_str:
                keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]
                keywords_counter.update(keywords)
        
        # Filter keywords matching query
        query_lower = query.lower()
        matching_keywords = [
            {
                "keyword": keyword,
                "frequency": count
            }
            for keyword, count in keywords_counter.items()
            if query_lower in keyword.lower()
        ]
        
        # Sort by frequency descending
        matching_keywords.sort(key=lambda x: x['frequency'], reverse=True)
        
        # Apply limit
        matching_keywords = matching_keywords[:limit]
        
        return {
            "query": query,
            "keywords": matching_keywords,
            "total_matches": len(matching_keywords)
        }
        
    except Exception as e:
        logger.error(f"Error searching keywords: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/keywords/stats")
async def get_keyword_statistics():
    """
    Get comprehensive statistics about keywords across all articles.
    
    Returns:
        Statistics about keyword distribution and usage
    """
    try:
        from backend.core.vector_db import VectorDatabase
        db = VectorDatabase(collection_name="political_articles")
        
        # Get all articles
        collection = db.collection
        results = collection.get(include=["metadatas"])
        
        if not results or not results['metadatas']:
            return {
                "total_articles": 0,
                "articles_with_keywords": 0,
                "total_unique_keywords": 0,
                "avg_keywords_per_article": 0,
                "top_keywords": []
            }
        
        keywords_counter = Counter()
        articles_with_keywords = 0
        total_keyword_count = 0
        
        for metadata in results['metadatas']:
            keywords_str = metadata.get('keywords', '')
            if keywords_str:
                keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]
                if keywords:
                    articles_with_keywords += 1
                    total_keyword_count += len(keywords)
                    keywords_counter.update(keywords)
        
        # Get top 20 keywords
        top_keywords = [
            {"keyword": keyword, "count": count}
            for keyword, count in keywords_counter.most_common(20)
        ]
        
        return {
            "total_articles": len(results['metadatas']),
            "articles_with_keywords": articles_with_keywords,
            "total_unique_keywords": len(keywords_counter),
            "avg_keywords_per_article": round(total_keyword_count / articles_with_keywords, 2) if articles_with_keywords > 0 else 0,
            "top_keywords": top_keywords
        }
        
    except Exception as e:
        logger.error(f"Error getting keyword statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

"""
Topics API routes for topic-based article filtering and discovery.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Optional
import logging
from collections import Counter

router = APIRouter(prefix="/api/v1", tags=["topics"])
logger = logging.getLogger(__name__)


@router.get("/topics")
async def get_all_topics(
    min_articles: int = Query(1, description="Minimum number of articles for a topic to be included")
):
    """
    Get all unique topics across all articles with article counts.
    
    Args:
        min_articles: Minimum number of articles required for a topic to be included
    
    Returns:
        List of topics with counts, sorted by article count descending
    """
    try:
        from backend.core.vector_db import VectorDatabase
        db = VectorDatabase(collection_name="political_articles")
        
        # Get all articles
        collection = db.collection
        results = collection.get(include=["metadatas"])
        
        if not results or not results['metadatas']:
            return {
                "topics": [],
                "total_topics": 0,
                "message": "No articles found"
            }
        
        # Collect all topics
        topics_counter = Counter()
        for metadata in results['metadatas']:
            topics_str = metadata.get('topics', '')
            if topics_str:
                # Split comma-separated topics
                topics = [t.strip() for t in topics_str.split(',') if t.strip()]
                topics_counter.update(topics)
        
        # Filter by minimum article count and sort
        topics_list = [
            {
                "topic": topic,
                "article_count": count,
                "percentage": round((count / len(results['metadatas'])) * 100, 1)
            }
            for topic, count in topics_counter.items()
            if count >= min_articles
        ]
        
        # Sort by article count descending
        topics_list.sort(key=lambda x: x['article_count'], reverse=True)
        
        return {
            "topics": topics_list,
            "total_topics": len(topics_list),
            "total_articles": len(results['metadatas'])
        }
        
    except Exception as e:
        logger.error(f"Error getting topics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/topics/{topic}/articles")
async def get_articles_by_topic(
    topic: str,
    limit: int = Query(50, description="Maximum number of articles to return"),
    offset: int = Query(0, description="Number of articles to skip")
):
    """
    Get all articles covering a specific topic.
    
    Args:
        topic: The topic to filter by
        limit: Maximum number of articles to return
        offset: Number of articles to skip (for pagination)
    
    Returns:
        List of articles covering the specified topic
    """
    try:
        from backend.core.vector_db import VectorDatabase
        db = VectorDatabase(collection_name="political_articles")
        
        # Get all articles
        collection = db.collection
        results = collection.get(include=["metadatas", "documents"])
        
        if not results or not results['metadatas']:
            return {
                "topic": topic,
                "articles": [],
                "total_count": 0
            }
        
        # Filter articles by topic
        matching_articles = []
        for idx, metadata in enumerate(results['metadatas']):
            topics_str = metadata.get('topics', '')
            if topics_str:
                topics = [t.strip().lower() for t in topics_str.split(',')]
                if topic.lower() in topics:
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
            "topic": topic,
            "articles": paginated_articles,
            "total_count": total_count,
            "returned_count": len(paginated_articles),
            "offset": offset,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error getting articles by topic: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/topics/stats")
async def get_topic_statistics():
    """
    Get comprehensive statistics about topics across all articles.
    
    Returns:
        Statistics about topic distribution and coverage
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
                "articles_with_topics": 0,
                "total_unique_topics": 0,
                "avg_topics_per_article": 0,
                "top_topics": []
            }
        
        topics_counter = Counter()
        articles_with_topics = 0
        total_topic_count = 0
        
        for metadata in results['metadatas']:
            topics_str = metadata.get('topics', '')
            if topics_str:
                topics = [t.strip() for t in topics_str.split(',') if t.strip()]
                if topics:
                    articles_with_topics += 1
                    total_topic_count += len(topics)
                    topics_counter.update(topics)
        
        # Get top 10 topics
        top_topics = [
            {"topic": topic, "count": count}
            for topic, count in topics_counter.most_common(10)
        ]
        
        return {
            "total_articles": len(results['metadatas']),
            "articles_with_topics": articles_with_topics,
            "total_unique_topics": len(topics_counter),
            "avg_topics_per_article": round(total_topic_count / articles_with_topics, 2) if articles_with_topics > 0 else 0,
            "top_topics": top_topics
        }
        
    except Exception as e:
        logger.error(f"Error getting topic statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

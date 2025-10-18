"""
Election Impact API routes for 2026 Bangladesh election impact analysis.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Optional
import logging

router = APIRouter(prefix="/api/v1", tags=["election"])
logger = logging.getLogger(__name__)


@router.get("/election-impact")
async def get_election_impact_articles(
    limit: int = Query(50, description="Maximum number of articles to return"),
    offset: int = Query(0, description="Number of articles to skip")
):
    """
    Get all articles with potential 2026 Bangladesh election impact.
    
    Args:
        limit: Maximum number of articles to return
        offset: Number of articles to skip (for pagination)
    
    Returns:
        List of articles with election impact analysis
    """
    try:
        from backend.core.vector_db import VectorDatabase
        db = VectorDatabase(collection_name="political_articles")
        
        # Get all articles
        collection = db.collection
        results = collection.get(include=["metadatas", "documents"])
        
        if not results or not results['metadatas']:
            return {
                "articles": [],
                "total_count": 0,
                "message": "No articles found"
            }
        
        # Filter articles with election impact
        impact_articles = []
        for idx, metadata in enumerate(results['metadatas']):
            has_impact = metadata.get('has_election_impact', False)
            
            # Handle both boolean and string representations
            if isinstance(has_impact, str):
                has_impact = has_impact.lower() in ['true', '1', 'yes']
            
            if has_impact:
                article = {
                    "id": results['ids'][idx],
                    "title": metadata.get('title', ''),
                    "summary": results['documents'][idx],
                    "date": metadata.get('date', ''),
                    "source": metadata.get('source', ''),
                    "url": metadata.get('url', ''),
                    "keywords": metadata.get('keywords', '').split(',') if metadata.get('keywords') else [],
                    "topics": metadata.get('topics', '').split(',') if metadata.get('topics') else [],
                    "election_2026_impact": metadata.get('election_2026_impact', ''),
                    "persons": metadata.get('persons', ''),
                    "language": metadata.get('language', 'Unknown'),
                    "analyzed_at": metadata.get('analyzed_at', '')
                }
                impact_articles.append(article)
        
        # Sort by date (newest first)
        impact_articles.sort(
            key=lambda x: x['date'] if x['date'] else '1970-01-01',
            reverse=True
        )
        
        # Apply pagination
        total_count = len(impact_articles)
        paginated_articles = impact_articles[offset:offset + limit]
        
        return {
            "articles": paginated_articles,
            "total_count": total_count,
            "returned_count": len(paginated_articles),
            "offset": offset,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error getting election impact articles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/election-impact/stats")
async def get_election_stats():
    """
    Get statistics about 2026 Bangladesh election impact across articles.
    
    Returns:
        Statistics about election impact analysis
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
                "articles_with_impact": 0,
                "articles_without_impact": 0,
                "impact_percentage": 0,
                "impact_by_source": {},
                "impact_by_party": {}
            }
        
        total_articles = len(results['metadatas'])
        articles_with_impact = 0
        impact_by_source = {}
        impact_by_party = {}
        
        for metadata in results['metadatas']:
            has_impact = metadata.get('has_election_impact', False)
            
            # Handle both boolean and string representations
            if isinstance(has_impact, str):
                has_impact = has_impact.lower() in ['true', '1', 'yes']
            
            source = metadata.get('source', 'Unknown')
            persons = metadata.get('persons', '')
            
            # Count by source
            if source not in impact_by_source:
                impact_by_source[source] = {"total": 0, "with_impact": 0}
            impact_by_source[source]["total"] += 1
            
            if has_impact:
                articles_with_impact += 1
                impact_by_source[source]["with_impact"] += 1
                
                # Count by party (extract from persons if available)
                # This is a simple heuristic - can be improved
                if persons:
                    for party in ["BNP", "JI", "NCP", "AB Party", "GOP", "Gono Songhati", "Interim Government"]:
                        if party.lower() in persons.lower():
                            if party not in impact_by_party:
                                impact_by_party[party] = 0
                            impact_by_party[party] += 1
        
        # Calculate percentages for sources
        for source in impact_by_source:
            total = impact_by_source[source]["total"]
            with_impact = impact_by_source[source]["with_impact"]
            impact_by_source[source]["percentage"] = round((with_impact / total * 100), 1) if total > 0 else 0
        
        return {
            "total_articles": total_articles,
            "articles_with_impact": articles_with_impact,
            "articles_without_impact": total_articles - articles_with_impact,
            "impact_percentage": round((articles_with_impact / total_articles * 100), 1) if total_articles > 0 else 0,
            "impact_by_source": impact_by_source,
            "impact_by_party": impact_by_party
        }
        
    except Exception as e:
        logger.error(f"Error getting election statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/election-impact/timeline")
async def get_election_impact_timeline(
    group_by: str = Query("month", description="Group by: 'day', 'week', or 'month'")
):
    """
    Get timeline of articles with election impact over time.
    
    Args:
        group_by: Time grouping - 'day', 'week', or 'month'
    
    Returns:
        Timeline data showing election impact articles over time
    """
    try:
        from backend.core.vector_db import VectorDatabase
        db = VectorDatabase(collection_name="political_articles")
        from datetime import datetime
        from collections import defaultdict
        
        # Get all articles
        collection = db.collection
        results = collection.get(include=["metadatas"])
        
        if not results or not results['metadatas']:
            return {
                "timeline": [],
                "message": "No articles found"
            }
        
        timeline_data = defaultdict(lambda: {"total": 0, "with_impact": 0})
        
        for metadata in results['metadatas']:
            date_str = metadata.get('date', '')
            has_impact = metadata.get('has_election_impact', False)
            
            # Handle boolean string representations
            if isinstance(has_impact, str):
                has_impact = has_impact.lower() in ['true', '1', 'yes']
            
            if date_str:
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    
                    # Group by specified period
                    if group_by == 'day':
                        key = date_str
                    elif group_by == 'week':
                        # Get ISO week number
                        week_num = date_obj.isocalendar()[1]
                        key = f"{date_obj.year}-W{week_num:02d}"
                    else:  # month
                        key = date_obj.strftime('%Y-%m')
                    
                    timeline_data[key]["total"] += 1
                    if has_impact:
                        timeline_data[key]["with_impact"] += 1
                        
                except ValueError:
                    logger.warning(f"Invalid date format: {date_str}")
                    continue
        
        # Convert to list and calculate percentages
        timeline = []
        for period, counts in sorted(timeline_data.items()):
            percentage = round((counts["with_impact"] / counts["total"] * 100), 1) if counts["total"] > 0 else 0
            timeline.append({
                "period": period,
                "total_articles": counts["total"],
                "articles_with_impact": counts["with_impact"],
                "impact_percentage": percentage
            })
        
        return {
            "timeline": timeline,
            "group_by": group_by,
            "total_periods": len(timeline)
        }
        
    except Exception as e:
        logger.error(f"Error getting election impact timeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))

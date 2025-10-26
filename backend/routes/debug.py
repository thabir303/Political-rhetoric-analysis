"""
Add this route to your backend to view all stored articles
"""

from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional
from backend.core.vector_db import VectorDatabase
from backend.auth import require_auth
import json

router = APIRouter(prefix="/debug", tags=["Debug"], dependencies=[Depends(require_auth)])


@router.get("/articles")
async def get_all_articles(
    limit: int = Query(20, description="Number of articles to return"),
    offset: int = Query(0, description="Offset for pagination"),
    has_people: Optional[bool] = Query(None, description="Filter by articles with people"),
    has_parties: Optional[bool] = Query(None, description="Filter by articles with parties")
):
    """
    Debug endpoint to view all stored articles with their metadata.
    
    Usage:
    - GET /debug/articles?limit=20 - Get first 20 articles
    - GET /debug/articles?has_people=true - Get articles with people data
    - GET /debug/articles?has_parties=false - Get articles without parties
    """
    db = VectorDatabase(collection_name="political_articles")
    
    # Get all articles
    all_results = db.collection.get(include=["metadatas"])
    
    all_ids = all_results.get("ids", [])
    all_metadatas = all_results.get("metadatas", [])
    
    # Build articles list
    articles = []
    for doc_id, metadata in zip(all_ids, all_metadatas):
        # Apply filters
        if has_people is not None:
            people = metadata.get('people', '')
            if has_people and not people:
                continue
            if not has_people and people:
                continue
        
        if has_parties is not None:
            parties = metadata.get('parties', '')
            if has_parties and not parties:
                continue
            if not has_parties and parties:
                continue
        
        # Parse people_affiliations
        affiliations = {}
        if 'people_affiliations' in metadata:
            try:
                affiliations = json.loads(metadata['people_affiliations'])
            except:
                pass
        
        articles.append({
            'id': doc_id,
            'title': metadata.get('title', ''),
            'date': metadata.get('date', ''),
            'source': metadata.get('source', ''),
            'parties': metadata.get('parties', '').split(', ') if metadata.get('parties') else [],
            'people': metadata.get('people', '').split(', ') if metadata.get('people') else [],
            'people_affiliations': affiliations,
            'url': metadata.get('url', ''),
            'is_speech': metadata.get('is_speech', 'False') == 'True'
        })
    
    # Sort by ID (latest first)
    articles.sort(key=lambda x: x['id'], reverse=True)
    
    # Apply pagination
    total = len(articles)
    articles = articles[offset:offset+limit]
    
    return {
        'total': total,
        'offset': offset,
        'limit': limit,
        'count': len(articles),
        'articles': articles,
        'stats': {
            'with_parties': sum(1 for a in articles if a['parties']),
            'with_people': sum(1 for a in articles if a['people']),
            'with_affiliations': sum(1 for a in articles if a['people_affiliations'])
        }
    }


@router.get("/stats")
async def get_database_stats():
    """
    Get comprehensive database statistics.
    """
    db = VectorDatabase(collection_name="political_articles")
    
    # Get all metadata
    all_results = db.collection.get(include=["metadatas"])
    all_metadatas = all_results.get("metadatas", [])
    
    total = len(all_metadatas)
    
    # Count articles with data
    with_parties = sum(1 for m in all_metadatas if m.get('parties'))
    with_people = sum(1 for m in all_metadatas if m.get('people'))
    with_affiliations = sum(1 for m in all_metadatas if m.get('people_affiliations') and m.get('people_affiliations') != '{}')
    
    # Collect unique parties and people
    all_parties = set()
    all_people = set()
    
    for m in all_metadatas:
        if m.get('parties'):
            all_parties.update(p.strip() for p in m['parties'].split(','))
        if m.get('people'):
            all_people.update(p.strip() for p in m['people'].split(','))
    
    return {
        'total_articles': total,
        'articles_with_parties': with_parties,
        'articles_with_people': with_people,
        'articles_with_affiliations': with_affiliations,
        'percentage': {
            'with_parties': round(with_parties / total * 100, 1) if total > 0 else 0,
            'with_people': round(with_people / total * 100, 1) if total > 0 else 0,
            'with_affiliations': round(with_affiliations / total * 100, 1) if total > 0 else 0
        },
        'unique_parties': sorted(list(all_parties)),
        'unique_people': sorted(list(all_people)),
        'counts': {
            'unique_parties': len(all_parties),
            'unique_people': len(all_people)
        }
    }


@router.delete("/clear")
async def clear_database(confirm: str = Query(..., description="Type 'DELETE_ALL' to confirm")):
    """
    ⚠️ DANGER: Clear all articles from the database.
    
    This will permanently delete ALL articles and cannot be undone.
    
    Usage:
    - DELETE /debug/clear?confirm=DELETE_ALL
    """
    if confirm != "DELETE_ALL":
        raise HTTPException(
            status_code=400,
            detail="Confirmation failed. Use confirm=DELETE_ALL to proceed"
        )
    
    db = VectorDatabase(collection_name="political_articles")
    
    # Get count before deletion
    count_before = db.collection.count()
    
    # Reset collection
    db.reset_collection()
    
    # Get count after
    count_after = db.collection.count()
    
    return {
        'status': 'success',
        'message': 'Database cleared successfully',
        'articles_deleted': count_before,
        'articles_remaining': count_after
    }

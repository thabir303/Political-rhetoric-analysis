"""
Category Management Routes
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
import logging
from datetime import datetime, timedelta
from collections import Counter, defaultdict

from backend.models.schemas import CategoryAnalysisRequest, CategoryStatsResponse, CategoryArticlesResponse
from backend.core.category_classifier import CategoryClassifier, get_all_categories, get_category_info
from backend.database.vector_store import vector_store
from backend.core.vector_db import VectorDatabase
from backend.auth import require_auth

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/categories", tags=["Categories"], dependencies=[Depends(require_auth)])


@router.delete(
    "/clear-metadata",
    summary="Clear all category metadata from articles"
)
async def clear_category_metadata():
    """
    Remove all category-related metadata from all articles.
    Use this to clear keyword-based classifications before running LLM-based categorization.
    
    Removes the following fields from article metadata:
    - ai_categories
    - primary_category
    - category_confidence
    - category_reasoning
    - categorized_at
    """
    try:
        logger.info("Starting to clear category metadata from all articles")
        
        db = VectorDatabase(collection_name="political_articles")
        
        # Get all articles
        all_data = db.collection.get(
            include=["metadatas"]
        )
        
        if not all_data or not all_data.get('metadatas'):
            return {
                "success": True,
                "message": "No articles found in database",
                "cleared_count": 0
            }
        
        # Clear category metadata from each article
        updated_count = 0
        
        for i, metadata in enumerate(all_data['metadatas']):
            # Check if has category metadata
            has_categories = any(
                key in metadata 
                for key in ['ai_categories', 'primary_category', 'category_confidence', 
                           'category_reasoning', 'categorized_at']
            )
            
            if has_categories:
                # Check if it's a keyword-based classification
                # Keyword-based will have "fallback" in reasoning or no reasoning at all
                reasoning = metadata.get('category_reasoning', '')
                is_keyword_based = (
                    'fallback' in reasoning.lower() or 
                    'keyword-based' in reasoning.lower() or
                    not reasoning  # No reasoning = old keyword-based
                )
                
                # Clear all keyword-based OR if user wants to clear ALL (for fresh start)
                # For now, we'll clear ALL to give user a fresh start
                should_clear = True  # Change to is_keyword_based if you want to keep LLM ones
                
                if should_clear:
                    # ChromaDB doesn't remove fields on update, so we set them to empty strings
                    # This way stats check will skip them (empty string = not categorized)
                    metadata['ai_categories'] = ''
                    metadata['primary_category'] = ''
                    metadata['category_confidence'] = ''
                    metadata['category_reasoning'] = ''
                    metadata['categorized_at'] = ''
                    
                    # Update in database with cleared metadata
                    db.collection.update(
                        ids=[all_data['ids'][i]],
                        metadatas=[metadata]
                    )
                    
                    updated_count += 1
                    
                    if updated_count % 100 == 0:
                        logger.info(f"Cleared {updated_count} articles...")
        
        logger.info(f"Category metadata cleared from {updated_count} articles (ALL categorized articles)")
        
        return {
            "success": True,
            "message": f"Successfully cleared category metadata from {updated_count} articles",
            "total_articles": len(all_data['metadatas']),
            "cleared_count": updated_count,
            "untouched_count": len(all_data['metadatas']) - updated_count
        }
        
    except Exception as e:
        logger.error(f"Failed to clear category metadata: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear category metadata: {str(e)}"
        )


@router.get(
    "",
    summary="Get all available categories"
)
async def list_categories():
    """
    Get list of all 9 available categories with descriptions.
    """
    try:
        categories = get_all_categories()
        category_data = []
        
        for cat in categories:
            info = get_category_info(cat)
            category_data.append({
                "name": cat,
                "description": info.get("description", ""),
                "keywords": info.get("keywords", [])
            })
        
        return {
            "success": True,
            "total_categories": len(categories),
            "categories": category_data
        }
        
    except Exception as e:
        logger.error(f"Failed to list categories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list categories: {str(e)}"
        )


@router.post(
    "/analyze",
    summary="Analyze articles by date range and assign categories"
)
async def analyze_articles_by_date_range(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    limit: Optional[int] = Query(None, description="Maximum articles to analyze (optional)"),
    force_reclassify: bool = Query(False, description="Force re-classification of already classified articles")
):
    """
    Analyze articles within a date range and assign categories using AI.
    Similar to LLM analysis button, but for categorization.
    """
    try:
        logger.info(f"Starting category analysis for date range: {start_date} to {end_date}")
        
        # Initialize database and classifier
        db = VectorDatabase(collection_name="political_articles")
        classifier = CategoryClassifier()
        
        # Get all articles in date range
        all_data = db.collection.get(
            include=["documents", "metadatas"]
        )
        
        if not all_data or not all_data.get('documents'):
            return {
                "success": True,
                "message": "No articles found in database",
                "analyzed_count": 0,
                "updated_count": 0
            }
        
        # Filter by date range
        articles_to_analyze = []
        article_ids = []
        
        for i, metadata in enumerate(all_data.get('metadatas', [])):
            article_date = metadata.get('date', '')
            
            # Check if already categorized
            has_category = metadata.get('ai_categories') or metadata.get('primary_category')
            
            if force_reclassify or not has_category:
                if start_date <= article_date <= end_date:
                    articles_to_analyze.append({
                        "id": all_data['ids'][i],
                        "title": metadata.get('title', 'No Title'),
                        "content": all_data['documents'][i],
                        "date": article_date,
                        "metadata": metadata
                    })
                    article_ids.append(all_data['ids'][i])
                    
                    if limit and len(articles_to_analyze) >= limit:
                        break
        
        if not articles_to_analyze:
            return {
                "success": True,
                "message": f"No articles found in date range {start_date} to {end_date} that need categorization",
                "analyzed_count": 0,
                "updated_count": 0
            }
        
        logger.info(f"Found {len(articles_to_analyze)} articles to categorize")
        
        # Classify articles
        classifications = []
        updated_count = 0
        
        for article in articles_to_analyze:
            try:
                # Detect language
                content_sample = article['content'][:500]
                is_bangla = any('\u0980' <= char <= '\u09FF' for char in content_sample)
                language = "Bangla" if is_bangla else "English"
                
                # Classify
                result = classifier.classify_article(
                    title=article['title'],
                    content=article['content'],
                    language=language
                )
                
                # Update metadata
                metadata = article['metadata']
                metadata['ai_categories'] = ', '.join(result['categories'])
                metadata['primary_category'] = result['primary_category']
                metadata['category_confidence'] = str(result['confidence_scores'])
                metadata['category_reasoning'] = result['reasoning']
                metadata['categorized_at'] = datetime.now().isoformat()
                
                # Store relevant excerpts as JSON string (for highlighting later)
                if result.get('relevant_excerpts'):
                    import json
                    metadata['category_excerpts'] = json.dumps(result['relevant_excerpts'], ensure_ascii=False)
                
                # Update in database
                db.collection.update(
                    ids=[article['id']],
                    metadatas=[metadata]
                )
                
                classifications.append({
                    "article_id": article['id'],
                    "title": article['title'],
                    "date": article['date'],
                    **result
                })
                
                updated_count += 1
                
                if updated_count % 10 == 0:
                    logger.info(f"Categorized {updated_count}/{len(articles_to_analyze)} articles")
                    
            except Exception as e:
                logger.error(f"Error categorizing article {article['id']}: {e}")
                continue
        
        logger.info(f"Category analysis complete: {updated_count} articles updated")
        
        # Generate statistics
        category_counts = Counter()
        for classification in classifications:
            for cat in classification['categories']:
                category_counts[cat] += 1
        
        return {
            "success": True,
            "message": f"Successfully analyzed {updated_count} articles",
            "analyzed_count": updated_count,
            "date_range": {
                "start": start_date,
                "end": end_date
            },
            "category_distribution": dict(category_counts),
            "sample_classifications": classifications[:10]  # Return first 10 as samples
        }
        
    except Exception as e:
        logger.error(f"Category analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Category analysis failed: {str(e)}"
        )


@router.get(
    "/stats",
    summary="Get category statistics"
)
async def get_category_stats(
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)")
):
    """
    Get comprehensive statistics about article categories.
    Returns article counts per category, party breakdown, etc.
    """
    try:
        db = VectorDatabase(collection_name="political_articles")
        
        # Get all categorized articles
        all_data = db.collection.get(
            include=["metadatas"]
        )
        
        if not all_data or not all_data.get('metadatas'):
            return {
                "success": True,
                "total_articles": 0,
                "categorized_articles": 0,
                "category_stats": {}
            }
        
        # Filter by date if provided
        metadatas = all_data['metadatas']
        
        if start_date or end_date:
            filtered_metadatas = []
            for meta in metadatas:
                article_date = meta.get('date', '')
                if start_date and article_date < start_date:
                    continue
                if end_date and article_date > end_date:
                    continue
                filtered_metadatas.append(meta)
            metadatas = filtered_metadatas
        
        # Calculate statistics
        category_counts = Counter()
        primary_category_counts = Counter()
        category_party_breakdown = defaultdict(lambda: Counter())
        category_date_distribution = defaultdict(lambda: Counter())
        
        categorized_count = 0
        
        logger.info(f"Checking {len(metadatas)} articles for category stats")
        
        for meta in metadatas:
            # Check if categorized
            categories_str = meta.get('ai_categories', '')
            primary_cat = meta.get('primary_category', '')
            
            # Skip if empty or not categorized
            if not categories_str or not primary_cat:
                continue
            
            # Additional check: skip if values are empty strings (cleared)
            if categories_str.strip() == '' and primary_cat.strip() == '':
                continue
            
            categorized_count += 1
            
            # Count categories
            if categories_str:
                categories = [c.strip() for c in categories_str.split(',')]
                for cat in categories:
                    category_counts[cat] += 1
                    
                    # Party breakdown
                    parties_str = meta.get('parties', '')
                    if parties_str:
                        parties = [p.strip() for p in parties_str.split(',')]
                        for party in parties:
                            if party:
                                category_party_breakdown[cat][party] += 1
                    
                    # Date distribution (by month)
                    article_date = meta.get('date', '')
                    if article_date:
                        month = article_date[:7]  # YYYY-MM
                        category_date_distribution[cat][month] += 1
            
            if primary_cat:
                primary_category_counts[primary_cat] += 1
        
        logger.info(f"Found {categorized_count} categorized articles out of {len(metadatas)} total")
        
        # Format response
        category_stats = {}
        for category in get_all_categories():
            category_stats[category] = {
                "total_articles": category_counts.get(category, 0),
                "as_primary": primary_category_counts.get(category, 0),
                "party_breakdown": dict(category_party_breakdown.get(category, {})),
                "monthly_distribution": dict(category_date_distribution.get(category, {}))
            }
        
        return {
            "success": True,
            "total_articles": len(metadatas),
            "categorized_articles": categorized_count,
            "uncategorized_articles": len(metadatas) - categorized_count,
            "date_range": {
                "start": start_date,
                "end": end_date
            } if (start_date or end_date) else None,
            "category_stats": category_stats,
            "top_categories": [
                {"name": cat, "count": count}
                for cat, count in category_counts.most_common(9)
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get category stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get category stats: {str(e)}"
        )


@router.get(
    "/{category_name}/articles",
    summary="Get articles by category"
)
async def get_articles_by_category(
    category_name: str,
    party: Optional[str] = Query(None, description="Filter by political party"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    source: Optional[str] = Query(None, description="Filter by newspaper source"),
    page: int = Query(1, description="Page number", ge=1),
    items_per_page: int = Query(20, description="Items per page (20, 50, 100, 200)")
):
    """
    Get all articles belonging to a specific category with filters.
    """
    try:
        # Validate category
        if category_name not in get_all_categories():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category: {category_name}"
            )
        
        db = VectorDatabase(collection_name="political_articles")
        
        # Get all articles
        all_data = db.collection.get(
            include=["documents", "metadatas"]
        )
        
        if not all_data or not all_data.get('documents'):
            return {
                "success": True,
                "category": category_name,
                "total_articles": 0,
                "articles": []
            }
        
        # Filter articles
        matching_articles = []
        
        for i, meta in enumerate(all_data['metadatas']):
            # Check category
            categories_str = meta.get('ai_categories', '')
            if not categories_str:
                continue
            
            categories = [c.strip() for c in categories_str.split(',')]
            if category_name not in categories:
                continue
            
            # Apply filters
            if party:
                parties_str = meta.get('parties', '')
                parties = [p.strip() for p in parties_str.split(',')]
                if party not in parties:
                    continue
            
            if start_date and meta.get('date', '') < start_date:
                continue
            
            if end_date and meta.get('date', '') > end_date:
                continue
            
            if source and meta.get('source', '').lower() != source.lower():
                continue
            
            # Parse category excerpts if available
            category_excerpts_dict = {}
            if meta.get('category_excerpts'):
                try:
                    import json
                    category_excerpts_dict = json.loads(meta['category_excerpts'])
                except:
                    pass
            
            # Add to results
            matching_articles.append({
                "id": all_data['ids'][i],
                "title": meta.get('title', 'No Title'),
                "content": all_data['documents'][i],  # Full content
                "date": meta.get('date', ''),
                "source": meta.get('source', ''),
                "url": meta.get('url', ''),
                "parties": meta.get('parties', '').split(',') if meta.get('parties') else [],
                "people": meta.get('people', '').split(',') if meta.get('people') else [],
                "primary_category": meta.get('primary_category', ''),
                "all_categories": categories,
                "is_primary": meta.get('primary_category') == category_name,
                "relevant_excerpt": category_excerpts_dict.get(category_name, ''),  # Get excerpt for this category
                "category_reasoning": meta.get('category_reasoning', '')  # Why this was categorized
            })
        
        # Sort by date (newest first)
        matching_articles.sort(key=lambda x: x['date'], reverse=True)
        
        # Calculate pagination
        total = len(matching_articles)
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        paginated_articles = matching_articles[start_idx:end_idx]
        
        return {
            "success": True,
            "category": category_name,
            "total_articles": total,
            "returned_articles": len(paginated_articles),
            "page": page,
            "items_per_page": items_per_page,
            "total_pages": (total + items_per_page - 1) // items_per_page,
            "filters": {
                "party": party,
                "start_date": start_date,
                "end_date": end_date,
                "source": source
            },
            "articles": paginated_articles
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get articles by category: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get articles: {str(e)}"
        )


@router.get(
    "/{category_name}/party-breakdown",
    summary="Get party-wise breakdown for a category"
)
async def get_category_party_breakdown(
    category_name: str,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """
    Get detailed party-wise breakdown for a specific category.
    Used for generating interactive graphs.
    """
    try:
        # Validate category
        if category_name not in get_all_categories():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category: {category_name}"
            )
        
        db = VectorDatabase(collection_name="political_articles")
        
        # Get all articles
        all_data = db.collection.get(
            include=["metadatas"]
        )
        
        if not all_data or not all_data.get('metadatas'):
            return {
                "success": True,
                "category": category_name,
                "party_breakdown": {},
                "time_series": {}
            }
        
        # Collect data
        party_counts = Counter()
        monthly_counts = defaultdict(lambda: Counter())
        
        for meta in all_data['metadatas']:
            # Check category
            categories_str = meta.get('ai_categories', '')
            if not categories_str:
                continue
            
            categories = [c.strip() for c in categories_str.split(',')]
            if category_name not in categories:
                continue
            
            # Apply date filter
            article_date = meta.get('date', '')
            if start_date and article_date < start_date:
                continue
            if end_date and article_date > end_date:
                continue
            
            # Count parties
            parties_str = meta.get('parties', '')
            if parties_str:
                parties = [p.strip() for p in parties_str.split(',')]
                for party in parties:
                    if party:
                        party_counts[party] += 1
                        
                        # Monthly breakdown
                        if article_date:
                            month = article_date[:7]
                            monthly_counts[month][party] += 1
        
        # Format time series data
        time_series = []
        for month in sorted(monthly_counts.keys()):
            month_data = {"month": month}
            for party, count in monthly_counts[month].items():
                month_data[party] = count
            time_series.append(month_data)
        
        return {
            "success": True,
            "category": category_name,
            "total_articles": sum(party_counts.values()),
            "party_breakdown": dict(party_counts),
            "top_parties": [
                {"party": party, "count": count}
                for party, count in party_counts.most_common(10)
            ],
            "time_series": time_series,
            "date_range": {
                "start": start_date,
                "end": end_date
            } if (start_date or end_date) else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get party breakdown: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get party breakdown: {str(e)}"
        )


@router.get(
    "/{category_name}/stats",
    summary="Get detailed statistics for a specific category"
)
async def get_category_detailed_stats(category_name: str):
    """
    Get comprehensive statistics for a single category including:
    - Total articles
    - Party breakdown
    - Time trends
    - Top keywords
    - Related figures
    """
    try:
        # Validate category
        if category_name not in get_all_categories():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category: {category_name}"
            )
        
        db = VectorDatabase(collection_name="political_articles")
        
        # Get all articles in this category
        all_data = db.collection.get(
            include=["documents", "metadatas"]
        )
        
        if not all_data or not all_data.get('metadatas'):
            return {
                "success": True,
                "category": category_name,
                "total_articles": 0
            }
        
        # Collect comprehensive stats
        total_articles = 0
        as_primary = 0
        party_counts = Counter()
        people_counts = Counter()
        source_counts = Counter()
        monthly_counts = Counter()
        keywords_counts = Counter()
        
        for meta in all_data['metadatas']:
            # Check category
            categories_str = meta.get('ai_categories', '')
            if not categories_str:
                continue
            
            categories = [c.strip() for c in categories_str.split(',')]
            if category_name not in categories:
                continue
            
            total_articles += 1
            
            # Check if primary
            if meta.get('primary_category') == category_name:
                as_primary += 1
            
            # Parties
            parties_str = meta.get('parties', '')
            if parties_str:
                for party in parties_str.split(','):
                    party = party.strip()
                    if party:
                        party_counts[party] += 1
            
            # People
            people_str = meta.get('people', '')
            if people_str:
                for person in people_str.split(','):
                    person = person.strip()
                    if person:
                        people_counts[person] += 1
            
            # Sources
            source = meta.get('source', '')
            if source:
                source_counts[source] += 1
            
            # Monthly distribution
            date = meta.get('date', '')
            if date:
                month = date[:7]
                monthly_counts[month] += 1
            
            # Keywords
            keywords_str = meta.get('llm_keywords', '') or meta.get('keywords', '')
            if keywords_str:
                for keyword in keywords_str.split(','):
                    keyword = keyword.strip()
                    if keyword:
                        keywords_counts[keyword] += 1
        
        # Get category info
        cat_info = get_category_info(category_name)
        
        return {
            "success": True,
            "category": category_name,
            "description": cat_info.get('description', ''),
            "total_articles": total_articles,
            "as_primary_category": as_primary,
            "as_secondary_category": total_articles - as_primary,
            "top_parties": [
                {"name": party, "count": count}
                for party, count in party_counts.most_common(10)
            ],
            "top_people": [
                {"name": person, "count": count}
                for person, count in people_counts.most_common(10)
            ],
            "sources": dict(source_counts),
            "monthly_trend": [
                {"month": month, "count": count}
                for month, count in sorted(monthly_counts.items())
            ],
            "top_keywords": [
                {"keyword": keyword, "count": count}
                for keyword, count in keywords_counts.most_common(20)
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get category stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get category stats: {str(e)}"
        )

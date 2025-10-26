"""
Figure Profile Routes - Direct access to political figure pages
Mounted without /parties prefix to match frontend expectations
"""
from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import Optional
import logging

from backend.models.schemas import FigureProfileResponse, ArticleSummary
from backend.core.scraping import POLITICAL_ENTITIES
from backend.auth import require_auth

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Figure Profiles"], dependencies=[Depends(require_auth)])


@router.post(
    "/party/{party_name}/figure/{figure_name}/",
    response_model=FigureProfileResponse,
    summary="Get articles for a specific political figure"
)
async def get_figure_profile(
    party_name: str,
    figure_name: str,
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    top_k: int = Query(None, description="Maximum results (default: all)")
):
    """
    Get articles related to a specific political figure within a party.
    
    This endpoint retrieves all stored articles that mention the specified figure,
    with optional date range filtering.
    
    **Path Parameters:**
    - party_name: Name of the political party (e.g., "BNP")
    - figure_name: Name of the political figure (e.g., "Tareq Rahman")
    
    **Query Parameters:**
    - date_from: Start date in YYYY-MM-DD format (e.g., "2024-08-05")
    - date_to: End date in YYYY-MM-DD format (e.g., "2025-09-30")
    - top_k: Maximum number of results (default: all, max: 100)
    
    Returns:
        FigureProfileResponse with articles mentioning the figure
    """
    try:
        from backend.core.vector_db import VectorDatabase
        from backend.core.ai_summary_store import AISummaryStore
        from datetime import datetime
        import json
        
        # Validate date format if provided
        if date_from:
            try:
                datetime.strptime(date_from, '%Y-%m-%d')
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date_from format. Use YYYY-MM-DD (e.g., '2024-08-05')"
                )
        
        if date_to:
            try:
                datetime.strptime(date_to, '%Y-%m-%d')
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date_to format. Use YYYY-MM-DD (e.g., '2025-09-30')"
                )
        
        # Verify the party exists
        if party_name not in POLITICAL_ENTITIES:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Party '{party_name}' not found. Available parties: {list(POLITICAL_ENTITIES.keys())}"
            )
        
        # Verify the figure belongs to this party
        party_figures = list(POLITICAL_ENTITIES[party_name].get("figures", {}).keys())
        if figure_name not in party_figures:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Figure '{figure_name}' not found in {party_name}. Available figures: {party_figures}"
            )
        
        db = VectorDatabase(collection_name="political_articles")
        
        # Get all articles from the database
        all_results = db.collection.get(include=["metadatas", "documents"])
        
        # Filter articles that mention this figure
        matching_articles = []
        seen_urls = set()  # Track URLs to deduplicate
        
        for i, (metadata, document, doc_id) in enumerate(zip(
            all_results.get("metadatas", []),
            all_results.get("documents", []),
            all_results.get("ids", [])
        )):
            # Parse people_affiliations
            people_affiliations_str = metadata.get("people_affiliations", "{}")
            try:
                people_affiliations = json.loads(people_affiliations_str) if people_affiliations_str else {}
            except:
                people_affiliations = {}
            
            # Check if this figure is mentioned and affiliated with this party
            if figure_name in people_affiliations and people_affiliations[figure_name] == party_name:
                article_url = metadata.get("url", "")
                
                # Skip duplicates based on URL
                if article_url and article_url in seen_urls:
                    continue
                if article_url:
                    seen_urls.add(article_url)
                
                article_date = metadata.get("date", "")
                
                # Apply date filtering if provided
                if date_from or date_to:
                    try:
                        # Parse article date (format: "2025-10-11")
                        article_date_obj = datetime.strptime(article_date, '%Y-%m-%d')
                        
                        if date_from:
                            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                            if article_date_obj < date_from_obj:
                                continue
                        
                        if date_to:
                            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
                            if article_date_obj > date_to_obj:
                                continue
                    except ValueError:
                        # Skip articles with invalid dates
                        continue
                
                # Get keywords - prioritize LLM keywords
                keywords_str = ""
                llm_topics_str = metadata.get("llm_topics", "")
                llm_extra_keywords = metadata.get("llm_extra_keywords", "")
                regular_keywords = metadata.get("keywords", "")
                
                # Use LLM topics first, then LLM extra keywords, then regular keywords
                if llm_topics_str:
                    keywords_str = llm_topics_str
                elif llm_extra_keywords:
                    keywords_str = llm_extra_keywords
                elif regular_keywords:
                    keywords_str = regular_keywords
                
                matching_articles.append({
                    "id": doc_id,
                    "title": metadata.get("title", "No title"),
                    "date": article_date,
                    "source": metadata.get("source", "Unknown"),
                    "content": document if document else "",  # Full content - no truncation
                    "url": article_url,
                    "keywords": keywords_str,
                    "parties": metadata.get("parties", ""),
                    "people": metadata.get("people", ""),
                    "date_ts": int(metadata.get("date_ts", 0))
                })
        
        # Sort by date (newest first)
        matching_articles.sort(key=lambda x: (x["date_ts"], x["id"]), reverse=True)
        
        # Apply limit if specified (otherwise return all)
        if top_k is not None and top_k > 0:
            matching_articles = matching_articles[:min(top_k, 100)]  # Max 100
        
        # Convert to ArticleSummary format
        articles_list = []
        for article in matching_articles:
            # Create preview (first 300 characters for display)
            full_content = article["content"]
            preview = full_content[:300] + "..." if len(full_content) > 300 else full_content
            
            articles_list.append(ArticleSummary(
                id=article["id"],
                title=article["title"],
                date=article["date"],
                source=article["source"],
                similarity=1.0,  # All articles are relevant since they mention the figure
                summary=preview,  # Preview for display
                key_points=[],
                stance_analysis=None,
                keywords=article["keywords"].split(",") if article["keywords"] else [],
                key_phrases=[],
                topics=[],
                url=article.get("url")
            ))
        
        # Organize by date for timeline view
        summaries_by_date = {}
        for article in matching_articles:
            date = article["date"]
            if date not in summaries_by_date:
                summaries_by_date[date] = []
            summaries_by_date[date].append({
                "title": article["title"],
                "source": article["source"],
                "url": article.get("url", "")
            })
        
        # Get AI summary for this figure
        summary_store = AISummaryStore()
        ai_summary_data = summary_store.get_figure_summary(figure_name)
        
        logger.info(f"Retrieved {len(articles_list)} articles for {figure_name} ({party_name})")
        
        return FigureProfileResponse(
            figure_name=figure_name,
            party_name=party_name,
            total_articles=len(articles_list),
            articles=articles_list,
            summaries_by_date=summaries_by_date,
            ai_summary=ai_summary_data.get("summary") if ai_summary_data else None,
            ai_keywords=ai_summary_data.get("keywords", []) if ai_summary_data else [],
            ai_topics=ai_summary_data.get("topics", []) if ai_summary_data else [],
            last_analyzed=ai_summary_data.get("last_updated") if ai_summary_data else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get figure profile: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve figure profile: {str(e)}"
        )


@router.get(
    "/article/{article_id}/full",
    summary="Get full article content by ID"
)
async def get_full_article(article_id: str):
    """
    Get the complete content of an article by its ID.
    
    This endpoint is used when the user clicks "See More" to view
    the full article text instead of just the preview.
    
    **Path Parameters:**
    - article_id: The unique ID of the article
    
    Returns:
        Dictionary with full article content and metadata
    """
    try:
        from backend.core.vector_db import VectorDatabase
        import json
        
        db = VectorDatabase(collection_name="political_articles")
        
        # Get the specific article
        result = db.collection.get(
            ids=[article_id],
            include=["metadatas", "documents"]
        )
        
        if not result or not result.get("ids"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Article with ID '{article_id}' not found"
            )
        
        metadata = result["metadatas"][0]
        document = result["documents"][0]
        
        # Parse people_affiliations
        people_affiliations_str = metadata.get("people_affiliations", "{}")
        try:
            people_affiliations = json.loads(people_affiliations_str) if people_affiliations_str else {}
        except:
            people_affiliations = {}
        
        return {
            "id": article_id,
            "title": metadata.get("title", "No title"),
            "date": metadata.get("date", ""),
            "source": metadata.get("source", "Unknown"),
            "url": metadata.get("url", ""),
            "content": document,  # Full content
            "people": metadata.get("people", ""),
            "parties": metadata.get("parties", ""),
            "people_affiliations": people_affiliations,
            "keywords": metadata.get("keywords", "").split(",") if metadata.get("keywords") else [],
            "categories": metadata.get("categories", "")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get full article: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve article: {str(e)}"
        )

"""
Political Parties Endpoint - Uses strict POLITICAL_ENTITIES mapping
"""
from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import List, Dict, Any, Optional
import logging

from backend.models.schemas import PartiesListResponse, PartyResponse, FigureProfileResponse, ArticleSummary
from backend.core.scraping import POLITICAL_ENTITIES
from backend.auth import require_auth

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/parties", tags=["Political Parties"], dependencies=[Depends(require_auth)])


@router.get(
    "/",
    response_model=PartiesListResponse,
    summary="Get list of political parties with their figures"
)
async def get_parties():
    """
    Get list of political parties with associated figures.
    
    Uses data from categorized articles in the database to show
    which figures were actually detected in stored articles.
    
    Returns:
        PartiesListResponse with parties and their canonical figures
    """
    try:
        from backend.core.vector_db import VectorDatabase
        import json
        
        db = VectorDatabase(collection_name="political_articles")
        
        # Get all articles to analyze actual categorization
        results = db.collection.get(include=["metadatas"])
        
        all_metadatas = results.get("metadatas", [])
        
        # Build party -> figures mapping from actual stored data
        party_figures_found = {}
        party_counts = {}
        
        for metadata in all_metadatas:
            # Get parties from this article
            parties_str = metadata.get('parties', '')
            if parties_str:
                parties = [p.strip() for p in parties_str.split(',') if p.strip()]
                
                # Get people_affiliations if available
                people_affiliations_str = metadata.get('people_affiliations', '{}')
                try:
                    people_affiliations = json.loads(people_affiliations_str) if people_affiliations_str else {}
                except:
                    people_affiliations = {}
                
                # Get people from this article
                people_str = metadata.get('people', '')
                people = [p.strip() for p in people_str.split(',') if p.strip()] if people_str else []
                
                # Count articles per party and track figures
                for party in parties:
                    party_counts[party] = party_counts.get(party, 0) + 1
                    
                    if party not in party_figures_found:
                        party_figures_found[party] = set()
                    
                    # Add figures associated with this party
                    for person in people:
                        if people_affiliations.get(person) == party:
                            party_figures_found[party].add(person)
        
        # Build response using POLITICAL_ENTITIES as the authoritative source
        parties_list = []
        for party_key, party_data in POLITICAL_ENTITIES.items():
            # Get canonical figure names from POLITICAL_ENTITIES
            figures_dict = party_data.get("figures", {})
            canonical_figures = list(figures_dict.keys())
            
            # Get article count for this party
            article_count = party_counts.get(party_key, 0)
            
            # Get full party name (first variant)
            party_names = party_data.get("party_names", [party_key])
            full_name = party_names[0] if party_names else party_key
            
            parties_list.append(PartyResponse(
                name=party_key,
                full_name=full_name,
                figures=canonical_figures,  # Always use canonical figures from POLITICAL_ENTITIES
                total_articles=article_count
            ))
        
        # Sort by article count (most prominent first)
        parties_list.sort(key=lambda x: x.total_articles, reverse=True)
        
        logger.info(f"Retrieved {len(parties_list)} political parties")
        
        return PartiesListResponse(
            parties=parties_list,
            total_parties=len(parties_list)
        )
        
    except Exception as e:
        logger.error(f"Failed to get parties: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve parties: {str(e)}"
        )


@router.get(
    "/categorization-test",
    summary="Test endpoint to view how articles are categorized"
)
async def test_categorization(limit: int = 50):
    """
    Test endpoint to view how articles are categorized in the database.
    
    Shows party-figure associations for debugging and verification.
    
    Args:
        limit: Maximum number of articles to return (default: 50)
        
    Returns:
        Dictionary with articles and their categorization details
    """
    try:
        from backend.core.vector_db import VectorDatabase
        import json
        
        db = VectorDatabase(collection_name="political_articles")
        
        # Get recent articles - ChromaDB returns in insertion order (newest first if that's how they were added)
        results = db.collection.get(
            limit=limit,
            include=["metadatas", "documents"]
        )
        
        # Get IDs and sort by them to ensure newest articles first
        # ChromaDB IDs are typically timestamps or sequential, so reverse order gives newest first
        all_metadatas = results.get("metadatas", [])
        all_documents = results.get("documents", [])
        all_ids = results.get("ids", [])
        
        # Create a list of tuples (id, metadata, document) and sort
        combined = list(zip(all_ids, all_metadatas, all_documents))
        
        # Sort by date_ts (timestamp) if available, otherwise by ID (both descending for newest first)
        combined.sort(
            key=lambda x: (
                int(x[1].get('date_ts', 0)) if x[1].get('date_ts') else 0,
                x[0]
            ),
            reverse=True
        )
        
        articles = []
        for i, (doc_id, metadata, document) in enumerate(combined):
            # Parse people_affiliations if available
            people_affiliations_str = metadata.get("people_affiliations", "{}")
            try:
                people_affiliations = json.loads(people_affiliations_str) if people_affiliations_str else {}
            except:
                people_affiliations = {}
            
            article_data = {
                "index": i + 1,
                "title": metadata.get("title", "No title"),
                "date": metadata.get("date", "No date"),
                "source": metadata.get("source", "Unknown"),
                "parties": metadata.get("parties", ""),
                "people": metadata.get("people", ""),
                "people_affiliations": people_affiliations,  # Show the mapping
                "primary_parties": metadata.get("primary_parties", ""),
                "mentioned_figures": metadata.get("mentioned_figures", ""),
                "political_entities": metadata.get("political_entities", ""),
                "keywords": metadata.get("keywords", "")[:100] if metadata.get("keywords") else "",
                "content_preview": document[:200] if document else "No content"
            }
            articles.append(article_data)
        
        # Get party-figure breakdown from actual data
        party_figure_map = {}
        for metadata in results.get("metadatas", []):
            parties_str = metadata.get("parties", "")
            people_str = metadata.get("people", "")
            
            # Parse people_affiliations
            people_affiliations_str = metadata.get("people_affiliations", "{}")
            try:
                people_affiliations = json.loads(people_affiliations_str) if people_affiliations_str else {}
            except:
                people_affiliations = {}
            
            if parties_str and people_str:
                parties = [p.strip() for p in parties_str.split(',') if p.strip()]
                people = [p.strip() for p in people_str.split(',') if p.strip()]
                
                for party in parties:
                    if party not in party_figure_map:
                        party_figure_map[party] = set()
                    
                    # Add people affiliated with this party
                    for person in people:
                        if people_affiliations.get(person) == party:
                            party_figure_map[party].add(person)
        
        # Convert sets to sorted lists for JSON serialization
        party_figure_breakdown = {
            party: sorted(list(figures))
            for party, figures in party_figure_map.items()
        }
        
        # Get correct mapping from POLITICAL_ENTITIES
        correct_mapping = {
            party: list(data.get("figures", {}).keys())
            for party, data in POLITICAL_ENTITIES.items()
        }
        
        return {
            "total_articles": len(articles),
            "articles": articles,
            "party_figure_breakdown": party_figure_breakdown,
            "correct_mapping_from_db": correct_mapping,
            "note": "party_figure_breakdown shows figures found in stored articles, correct_mapping_from_db shows all possible figures per party"
        }
        
    except Exception as e:
        logger.error(f"Failed to get categorization test data: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve test data: {str(e)}"
        )


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
    top_k: int = Query(10, description="Maximum results", ge=1, le=50)
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
    - top_k: Maximum number of results (default: 10, max: 50)
    
    Returns:
        FigureProfileResponse with articles mentioning the figure
    """
    try:
        from backend.core.vector_db import VectorDatabase
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
                
                matching_articles.append({
                    "id": doc_id,
                    "title": metadata.get("title", "No title"),
                    "date": article_date,
                    "source": metadata.get("source", "Unknown"),
                    "content": document[:500] if document else "",  # Preview
                    "url": metadata.get("url", ""),
                    "keywords": metadata.get("keywords", ""),
                    "parties": metadata.get("parties", ""),
                    "people": metadata.get("people", ""),
                    "date_ts": int(metadata.get("date_ts", 0))
                })
        
        # Sort by date (newest first)
        matching_articles.sort(key=lambda x: (x["date_ts"], x["id"]), reverse=True)
        
        # Limit results
        matching_articles = matching_articles[:top_k]
        
        # Convert to ArticleSummary format
        articles_list = []
        for article in matching_articles:
            articles_list.append(ArticleSummary(
                id=article["id"],
                title=article["title"],
                date=article["date"],
                source=article["source"],
                similarity=1.0,  # All articles are relevant since they mention the figure
                summary=article["content"],
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
        
        logger.info(f"Retrieved {len(articles_list)} articles for {figure_name} ({party_name})")
        
        return FigureProfileResponse(
            figure_name=figure_name,
            party_name=party_name,
            total_articles=len(articles_list),
            articles=articles_list,
            summaries_by_date=summaries_by_date
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get figure profile: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve figure profile: {str(e)}"
        )


@router.post(
    "/{party_name}/profile",
    response_model=FigureProfileResponse,
    summary="Get profile for a specific political party"
)
async def get_party_profile(
    party_name: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    top_k: Optional[int] = Query(None, description="Maximum results (default: all)")
):
    """
    Get profile for a specific political party including all articles, figures, keywords, and topics.
    
    Similar to figure profiles but shows party-level aggregated data.
    
    Args:
        party_name: Name of the party (e.g., "BNP", "NCP")
        date_from: Optional start date for filtering (YYYY-MM-DD)
        date_to: Optional end date for filtering (YYYY-MM-DD)
        top_k: Optional limit on number of articles (default: all)
    
    Returns:
        Party profile with articles, keywords, topics, and figures
    """
    try:
        from backend.core.vector_db import VectorDatabase
        from backend.core.ai_summary_store import AISummaryStore
        from datetime import datetime
        import json
        
        # Validate party exists in POLITICAL_ENTITIES
        if party_name not in POLITICAL_ENTITIES:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Party '{party_name}' not found. Available parties: {list(POLITICAL_ENTITIES.keys())}"
            )
        
        db = VectorDatabase(collection_name="political_articles")
        summary_store = AISummaryStore()
        
        # Get all articles from the database
        all_results = db.collection.get(include=["metadatas", "documents"])
        
        # Filter articles that mention this party
        matching_articles = []
        seen_urls = set()  # Track URLs to deduplicate
        
        for i, (metadata, document, doc_id) in enumerate(zip(
            all_results.get("metadatas", []),
            all_results.get("documents", []),
            all_results.get("ids", [])
        )):
            # Check if party is mentioned
            parties_str = metadata.get("parties", "")
            parties = [p.strip() for p in parties_str.split(',') if p.strip()] if parties_str else []
            
            if party_name in parties:
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
                        continue
                
                # Store full content
                full_content = document if document else ""
                preview = full_content[:300] + "..." if len(full_content) > 300 else full_content
                
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
                    "content": preview,  # Preview for list view
                    "url": article_url,
                    "keywords": keywords_str,
                    "parties": metadata.get("parties", ""),
                    "people": metadata.get("people", ""),
                    "date_ts": int(metadata.get("date_ts", 0))
                })
        
        # Sort by date (newest first)
        matching_articles.sort(key=lambda x: (x["date_ts"], x["id"]), reverse=True)
        
        # Apply limit if specified
        if top_k is not None and top_k > 0:
            matching_articles = matching_articles[:min(top_k, 100)]
        
        # Convert to ArticleSummary format
        articles_list = []
        for article in matching_articles:
            articles_list.append(ArticleSummary(
                id=article["id"],
                title=article["title"],
                date=article["date"],
                source=article["source"],
                similarity=1.0,
                summary=article["content"],
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
        
        # Get party details
        party_data = POLITICAL_ENTITIES[party_name]
        party_names = party_data.get("party_names", [party_name])
        full_name = party_names[0] if party_names else party_name
        
        # Get list of figures for this party
        figures_dict = party_data.get("figures", {})
        figures_list = list(figures_dict.keys())
        
        # Get AI summary for this party
        ai_summary_data = summary_store.get_party_summary(party_name)
        
        logger.info(f"Retrieved {len(articles_list)} articles for party {party_name}")
        
        return FigureProfileResponse(
            figure_name=full_name,  # Using party full name
            party_name=party_name,
            total_articles=len(articles_list),
            articles=articles_list,
            summaries_by_date=summaries_by_date,
            figures=figures_list,  # Add figures list
            ai_summary=ai_summary_data.get("summary") if ai_summary_data else None,
            ai_keywords=ai_summary_data.get("keywords", []) if ai_summary_data else [],
            ai_topics=ai_summary_data.get("topics", []) if ai_summary_data else [],
            last_analyzed=ai_summary_data.get("last_updated") if ai_summary_data else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get party profile: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve party profile: {str(e)}"
        )

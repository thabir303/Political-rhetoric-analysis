"""
Political Parties Endpoint - Uses LLM's POLITICAL_ENTITIES for consistency
"""
from fastapi import APIRouter, HTTPException, status, Query, Response
from typing import List, Dict, Any, Optional
import logging

from backend.models.schemas import PartiesListResponse, PartyResponse, FigureProfileResponse, ArticleSummary

# Import normalization function and POLITICAL_ENTITIES from political_entities_config (LLM config)
try:
    from political_entities_config import normalize_figure_name as normalize_figure_from_llm, POLITICAL_ENTITIES as LLM_POLITICAL_ENTITIES, normalize_party_name
    USE_LLM_CONFIG = True
    POLITICAL_ENTITIES = LLM_POLITICAL_ENTITIES  # Use LLM's config as single source of truth
    logger = logging.getLogger(__name__)
    logger.info("Using LLM's political_entities_config for parties and figures")
except ImportError:
    from backend.core.scraping import POLITICAL_ENTITIES
    USE_LLM_CONFIG = False
    normalize_party_name = lambda x: x  # Fallback: no normalization
    logger = logging.getLogger(__name__)
    logger.warning("Could not import political_entities_config, using backend's POLITICAL_ENTITIES")

USE_LLM_NORMALIZATION = USE_LLM_CONFIG  # Backward compatibility

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/parties", tags=["Political Parties"])


def get_canonical_name(name_variant: str) -> Optional[str]:
    """
    Convert any name variant (Bangla or English) to canonical English name.
    
    Uses political_entities_config's normalize_figure_name if available (for LLM compatibility),
    otherwise falls back to backend's POLITICAL_ENTITIES.
    
    Args:
        name_variant: Any variant of a political figure's name
        
    Returns:
        Canonical English name or None if not found
    """
    # Try LLM's normalization first (if available)
    if USE_LLM_NORMALIZATION:
        try:
            canonical_name, party = normalize_figure_from_llm(name_variant)
            if canonical_name and canonical_name != name_variant:
                return canonical_name
            # If normalization returns same name, it might not be found
            # Fall through to backend's method
        except Exception as e:
            logger.warning(f"LLM normalization failed for '{name_variant}': {e}")
    
    # Fallback to backend's POLITICAL_ENTITIES
    name_lower = name_variant.lower().strip()
    
    # Search through all parties and figures
    for party_key, party_data in POLITICAL_ENTITIES.items():
        figures_dict = party_data.get('figures', {})
        for canonical_name, variants in figures_dict.items():
            # Check if name_variant matches any variant (case-insensitive)
            for variant in variants:
                if variant.lower() == name_lower:
                    return canonical_name
    
    return None


@router.get(
    "/",
    response_model=PartiesListResponse,
    summary="Get list of political parties with their figures",
    responses={
        200: {
            "headers": {
                "Cache-Control": {"description": "no-cache, no-store, must-revalidate"},
                "Pragma": {"description": "no-cache"},
                "Expires": {"description": "0"}
            }
        }
    }
)
async def get_parties(response: Response):
    """
    Get list of political parties with associated figures.
    
    Uses data from categorized articles in the database to show
    which figures were actually detected in stored articles.
    
    Returns:
        PartiesListResponse with parties and their canonical English figures
    """
    # Disable caching to ensure frontend always gets fresh data
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
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
        party_keywords = {}  # NEW: Track keywords per party
        party_topics = {}  # NEW: Track topics per party
        
        for metadata in all_metadatas:
            # Get parties from this article
            parties_str = metadata.get('parties', '')
            if parties_str:
                parties = [p.strip() for p in parties_str.split(',') if p.strip()]
                
                # Get LLM analysis data - check all possible field names
                keywords_str = (metadata.get('keywords', '') or 
                              metadata.get('llm_keywords', '') or 
                              metadata.get('ai_keywords', ''))
                
                topics_str = (metadata.get('topics', '') or 
                            metadata.get('llm_topics', '') or 
                            metadata.get('ai_topics', ''))
                
                # Get people_affiliations if available
                people_affiliations_str = metadata.get('people_affiliations', '{}')
                try:
                    people_affiliations = json.loads(people_affiliations_str) if people_affiliations_str else {}
                except:
                    people_affiliations = {}
                
                # Get people from this article
                people_str = metadata.get('people', '')
                people = [p.strip() for p in people_str.split(',') if p.strip()] if people_str else []
                
                # Count articles per party and track figures, keywords, topics
                for party in parties:
                    # Normalize party name to match POLITICAL_ENTITIES keys
                    # This handles cases like "JI" → "Jamaat-e-Islami"
                    normalized_party = normalize_party_name(party)
                    
                    party_counts[normalized_party] = party_counts.get(normalized_party, 0) + 1
                    
                    if normalized_party not in party_figures_found:
                        party_figures_found[normalized_party] = set()
                        party_keywords[normalized_party] = set()
                        party_topics[normalized_party] = set()
                    
                    # Add keywords for this party
                    if keywords_str:
                        keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]
                        party_keywords[normalized_party].update(keywords)
                    
                    # Add topics for this party
                    if topics_str:
                        topics = [t.strip() for t in topics_str.split(',') if t.strip()]
                        party_topics[normalized_party].update(topics)
                    
                    # Add figures associated with this party (convert to canonical names)
                    for person in people:
                        # Check if person belongs to this party (compare with original party name)
                        if people_affiliations.get(person) == party or people_affiliations.get(person) == normalized_party:
                            # Convert to canonical English name
                            canonical_name = get_canonical_name(person)
                            if canonical_name:
                                party_figures_found[normalized_party].add(canonical_name)
        
        # Build response - show ALL parties found in database, with POLITICAL_ENTITIES details if available
        parties_list = []
        
        # First, add parties from POLITICAL_ENTITIES that have articles
        for party_key, party_data in POLITICAL_ENTITIES.items():
            article_count = party_counts.get(party_key, 0)
            
            # Only include if we found articles
            if article_count > 0:
                # Get canonical figure names (only those found in articles)
                canonical_figures = sorted(list(party_figures_found.get(party_key, set())))
                
                # Get aggregated keywords and topics
                aggregated_keywords = sorted(list(party_keywords.get(party_key, set())))
                aggregated_topics = sorted(list(party_topics.get(party_key, set())))
                
                # Get full party name (from 'full_name' or first name in 'names' list, or key as fallback)
                full_name = party_data.get("full_name") or (party_data.get("names", [party_key])[0] if party_data.get("names") else party_key)
                
                parties_list.append(PartyResponse(
                    name=party_key,
                    full_name=full_name,
                    figures=canonical_figures,  # ONLY canonical English names
                    total_articles=article_count,
                    ai_keywords=aggregated_keywords,  # NEW: Aggregated from all articles
                    ai_topics=aggregated_topics  # NEW: Aggregated from all articles
                ))
        
        # Also check for any parties in DB that aren't in POLITICAL_ENTITIES (shouldn't happen but for robustness)
        for db_party in party_counts.keys():
            if db_party not in [p.name for p in parties_list]:
                logger.warning(f"Found party in DB not in config: {db_party}")
                parties_list.append(PartyResponse(
                    name=db_party,
                    full_name=db_party,  # Use key as full name
                    figures=sorted(list(party_figures_found.get(db_party, set()))),
                    total_articles=party_counts.get(db_party, 0)
                ))
        
        # Sort by article count (most prominent first)
        parties_list.sort(key=lambda x: x.total_articles, reverse=True)
        
        # Filter out any Bangla party names (they should have been normalized)
        # This is a safety check to ensure only English names are returned
        parties_list = [p for p in parties_list if all(ord(c) < 128 for c in p.name)]
        
        logger.info(f"Retrieved {len(parties_list)} political parties with canonical names")
        
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
        
        # Verify the figure belongs to this party (figures is now a dict with canonical names as keys)
        party_figures_dict = POLITICAL_ENTITIES[party_name].get("figures", {})
        party_figures = list(party_figures_dict.keys())
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
        
        # Get all name variants for this figure to match against stored data
        figure_variants = party_figures_dict.get(figure_name, [])
        figure_variants_lower = [v.lower() for v in figure_variants]
        
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
            
            # Check if this figure is mentioned (match against any variant)
            # people_affiliations has format: {detected_name: party}
            # We need to check if any detected_name maps to our figure_name
            figure_found = False
            for detected_name, detected_party in people_affiliations.items():
                # Check if detected_name is a variant of our figure
                detected_canonical = get_canonical_name(detected_name)
                if detected_canonical == figure_name and detected_party == party_name:
                    figure_found = True
                    break
            
            if not figure_found:
                continue
                
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
            
            # Prefer summary over full content
            llm_summary = metadata.get("summary", "")
            content_preview = llm_summary if llm_summary else (document[:500] if document else "")
            
            matching_articles.append({
                "id": doc_id,
                "title": metadata.get("title", "No title"),
                "date": article_date,
                "source": metadata.get("source", "Unknown"),
                "content": content_preview,  # Use LLM summary if available, else preview
                "summary": llm_summary,  # LLM-generated summary
                "topics": metadata.get("topics", ""),  # LLM-generated topics
                "url": metadata.get("url", ""),
                "keywords": metadata.get("keywords", ""),
                "parties": metadata.get("parties", ""),
                "people": metadata.get("people", ""),
                "has_election_impact": metadata.get("has_election_impact", "false"),
                "election_impact_description": metadata.get("election_impact_description", ""),
                "date_ts": int(metadata.get("date_ts", 0))
            })
        
        # Sort by date (newest first)
        matching_articles.sort(key=lambda x: (x["date_ts"], x["id"]), reverse=True)
        
        # Limit results
        matching_articles = matching_articles[:top_k]
        
        # Convert to ArticleSummary format
        articles_list = []
        for article in matching_articles:
            # Always prefer LLM-generated summary over content
            display_summary = article.get("summary", "") or article.get("content", "")
            
            articles_list.append(ArticleSummary(
                id=article["id"],
                title=article["title"],
                date=article["date"],
                source=article["source"],
                similarity=1.0,  # All articles are relevant since they mention the figure
                summary=display_summary,  # Use LLM summary (already set in content field)
                key_points=[],
                stance_analysis=None,
                keywords=article["keywords"].split(",") if article["keywords"] else [],
                key_phrases=[],
                topics=article.get("topics", "").split(",") if article.get("topics") else [],
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
        
        # Generate aggregated analysis using aggregation utilities
        from backend.core.aggregation import create_aggregated_analysis
        
        aggregated = create_aggregated_analysis(
            articles=matching_articles,
            entity_type="figure",
            entity_name=figure_name
        )
        
        logger.info(f"Retrieved {len(articles_list)} articles for {figure_name} ({party_name})")
        logger.info(f"Aggregated keywords: {aggregated['top_keywords']}")
        logger.info(f"Aggregated topics: {aggregated['top_topics']}")
        logger.info(f"Election impact: {aggregated.get('election_impact', {}).get('total_articles_with_impact', 0)} articles")
        
        return FigureProfileResponse(
            figure_name=figure_name,
            party_name=party_name,
            total_articles=len(articles_list),
            articles=articles_list,
            summaries_by_date=summaries_by_date,
            ai_summary=aggregated.get("coverage_summary"),
            ai_keywords=aggregated.get("top_keywords", []),
            ai_topics=aggregated.get("top_topics", []),
            election_impact=aggregated.get("election_impact")
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
                
                # Get LLM analysis data - check all possible field names
                llm_summary = (metadata.get("summary", "") or 
                             metadata.get("llm_summary", "") or 
                             metadata.get("ai_summary", ""))
                
                llm_keywords = (metadata.get("keywords", "") or 
                              metadata.get("llm_keywords", "") or 
                              metadata.get("ai_keywords", ""))
                
                llm_topics = (metadata.get("topics", "") or 
                            metadata.get("llm_topics", "") or 
                            metadata.get("ai_topics", ""))
                
                # Use LLM summary for display
                content_to_store = llm_summary if llm_summary else preview
                
                matching_articles.append({
                    "id": doc_id,
                    "title": metadata.get("title", "No title"),
                    "date": article_date,
                    "source": metadata.get("source", "Unknown"),
                    "content": content_to_store,
                    "summary": llm_summary,  # LLM-generated summary
                    "keywords": llm_keywords,  # LLM-generated keywords
                    "topics": llm_topics,  # LLM-generated topics
                    "url": article_url,
                    "parties": metadata.get("parties", ""),
                    "people": metadata.get("people", ""),
                    "has_election_impact": metadata.get("has_election_impact", "false") == "true",
                    "election_impact_description": metadata.get("election_impact_description", ""),
                    "date_ts": int(metadata.get("date_ts", 0))
                })
        
        # Sort by date (newest first)
        matching_articles.sort(key=lambda x: (x["date_ts"], x["id"]), reverse=True)
        
        # Apply limit if specified
        if top_k is not None and top_k > 0:
            matching_articles = matching_articles[:min(top_k, 100)]
        
        # Convert to ArticleSummary format
        articles_list = []
        all_keywords = set()  # Collect all unique keywords
        all_topics = set()  # Collect all unique topics
        
        for article in matching_articles:
            # Parse keywords and topics
            keywords_list = [k.strip() for k in article["keywords"].split(",") if k.strip()] if article["keywords"] else []
            topics_list = [t.strip() for t in article["topics"].split(",") if t.strip()] if article["topics"] else []
            
            # Collect for aggregation
            all_keywords.update(keywords_list)
            all_topics.update(topics_list)
            
            articles_list.append(ArticleSummary(
                id=article["id"],
                title=article["title"],
                date=article["date"],
                source=article["source"],
                similarity=1.0,
                summary=article.get("summary", "") or article.get("content", ""),
                key_points=[],
                stance_analysis=None,
                keywords=keywords_list,
                key_phrases=[],
                topics=topics_list,
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
        full_name = party_data.get("full_name", party_name)
        
        # Get list of figures for this party (dict keys are canonical English names)
        figures_dict = party_data.get("figures", {})
        figures_list = list(figures_dict.keys())
        
        # Get AI summary for this party
        ai_summary_data = summary_store.get_party_summary(party_name)
        
        # Use aggregated keywords/topics from actual articles if AI summary not available
        ai_keywords = ai_summary_data.get("keywords", []) if ai_summary_data else list(all_keywords)
        ai_topics = ai_summary_data.get("topics", []) if ai_summary_data else list(all_topics)
        
        # If no pre-generated AI summary, create aggregated analysis
        if not ai_summary_data:
            from backend.core.aggregation import create_aggregated_analysis
            
            aggregated = create_aggregated_analysis(
                articles=matching_articles,
                entity_type="party",
                entity_name=full_name
            )
            
            ai_summary_text = aggregated.get("coverage_summary")
            # Use aggregated data from articles
            ai_keywords_list = list(all_keywords) if all_keywords else aggregated.get("top_keywords", [])
            ai_topics_list = list(all_topics) if all_topics else aggregated.get("top_topics", [])
            election_impact_data = aggregated.get("election_impact")
        else:
            ai_summary_text = ai_summary_data.get("summary")
            # Use aggregated data if available, otherwise from articles
            ai_keywords_list = ai_keywords
            ai_topics_list = ai_topics
            # Still calculate election impact from articles
            from backend.core.aggregation import aggregate_election_impact
            election_impact_data = aggregate_election_impact(matching_articles)
        
        return FigureProfileResponse(
            figure_name=full_name,  # Using party full name
            party_name=party_name,
            total_articles=len(articles_list),
            articles=articles_list,
            summaries_by_date=summaries_by_date,
            figures=figures_list,  # Add figures list
            ai_summary=ai_summary_text,
            ai_keywords=ai_keywords_list,
            ai_topics=ai_topics_list,
            election_impact=election_impact_data,
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

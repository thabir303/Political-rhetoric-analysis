"""
API route handlers for the RAG-IR application.
"""
from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional
import time
import logging
from pydantic import BaseModel

from backend.models import (
    ArticleCreate,
    ArticleResponse,
    QueryRequest,
    QueryResponse,
    HealthResponse,
    BulkArticleCreate,
    BulkArticleResponse,
    PartiesListResponse,
    PartyResponse,
    FigureProfileResponse,
    ArticleSummary,
    PartyFigureQueryRequest,
    PoliticalFigure,
    ScrapingRequest,
    ScrapingResponse,
)
from backend.database import vector_store
from backend.config import settings

# Import VectorDatabase for enhanced filtering
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from backend.core.vector_db import VectorDatabase

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Initialize enhanced vector database for political filtering
try:
    enhanced_db = VectorDatabase(collection_name="political_articles")
    logger.info("Enhanced vector database initialized for political filtering")
except Exception as e:
    logger.warning(f"Could not initialize enhanced vector database: {e}")
    enhanced_db = None


def normalize_name_to_canonical(name: str) -> Optional[str]:
    """
    Convert any name variant (English/Bangla) to its canonical English name.
    
    Args:
        name: Name to normalize (can be English or Bangla)
        
    Returns:
        Canonical English name if found, otherwise None
    """
    from backend.core.scraping import POLITICAL_ENTITIES
    
    name_stripped = name.strip()
    
    # Search through all parties and figures
    for party_key, party_data in POLITICAL_ENTITIES.items():
        if isinstance(party_data, dict) and "figures" in party_data:
            for canonical_name, variants in party_data["figures"].items():
                # Check if name matches canonical name or any variant
                if name_stripped == canonical_name or name_stripped in variants:
                    return canonical_name
    
    # If not found, return the original name
    return name_stripped


def get_correct_party_for_figure(figure_canonical: str) -> Optional[str]:
    """
    Get the correct party for a given figure's canonical name.
    
    Args:
        figure_canonical: Canonical English name of the figure
        
    Returns:
        Party key if found, otherwise None
    """
    from backend.core.scraping import POLITICAL_ENTITIES
    
    for party_key, party_data in POLITICAL_ENTITIES.items():
        if isinstance(party_data, dict) and "figures" in party_data:
            if figure_canonical in party_data["figures"]:
                return party_key
    
    return None


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint to verify service status.
    """
    try:
        # Use enhanced_db (same database as scraping) to get accurate stats
        if enhanced_db:
            stats = enhanced_db.get_statistics()
            total_articles = stats.get("total_articles", 0)
            logger.info(f"Health check: enhanced_db reports {total_articles} articles")
        else:
            # Fallback to vector_store
            stats = vector_store.get_collection_stats()
            total_articles = stats["total_articles"]
            logger.info(f"Health check: vector_store reports {total_articles} articles")
        
        return HealthResponse(
            status="healthy",
            version=settings.app_version,
            database_connected=True,
            total_articles=total_articles
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
        
        # Query vector store - use enhanced_db (same as storage)
        if enhanced_db:
            result = enhanced_db.query_articles(
                query_text=query_request.query,
                top_k=query_request.top_k,
                metadata_filter=filter_dict if filter_dict else None
            )
            
            if result.get('success'):
                query_results = result.get('results', [])
                ids = [r.get('id', '') for r in query_results]
                metadatas = [r.get('metadata', {}) for r in query_results]
                documents = [r.get('content', '') for r in query_results]
                distances = [1 - r.get('similarity', 0) for r in query_results]  # Convert similarity to distance
            else:
                ids, metadatas, documents, distances = [], [], [], []
        else:
            # Fallback to vector_store
            ids, metadatas, documents, distances = vector_store.query_articles(
                query_text=query_request.query,
                top_k=query_request.top_k,
                filter_dict=filter_dict if filter_dict else None
            )
        
        # Build response
        results = []
        for i in range(len(ids)):
            metadata = metadatas[i]
            
            # Document content is already the summary if article was summarized
            results.append(
                ArticleResponse(
                    id=ids[i],
                    content=documents[i],
                    metadata=metadata,
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
    If article is summarized, returns summary instead of full content.
    """
    try:
        article = vector_store.get_article_by_id(article_id)
        
        if article is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Article with ID {article_id} not found"
            )
        
        # Document content is already the summary if article was summarized
        metadata = article["metadata"]
        
        return ArticleResponse(
            id=article["id"],
            content=article["content"],
            metadata=metadata
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


# ==================== Political Figure/Party Endpoints ====================

@router.get(
    "/parties/",
    response_model=PartiesListResponse,
    tags=["Political Analysis"]
)
async def get_parties():
    """
    Get list of political parties with associated popular figures.
    
    Returns all political parties found in the database along with
    their most prominent figures based on article frequency.
    """
    try:
        if enhanced_db is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Enhanced vector database not available"
            )
        
        # Get all articles to analyze parties and figures
        # We'll use a broad query to get a representative sample
        all_articles = enhanced_db.collection.get(
            limit=10000,  # Get up to 10k articles for analysis
            include=["metadatas"]
        )
        
        if not all_articles or 'metadatas' not in all_articles:
            return PartiesListResponse(
                parties=[],
                total_parties=0
            )
        
        # Import name normalizer
        from backend.core.name_normalizer import get_canonical_name, deduplicate_names
        
        # Analyze parties and figures
        party_data = {}  # {party_name: {figures: {name: count}, total_articles: int}}
        
        for metadata in all_articles['metadatas']:
            # Extract parties
            parties_str = metadata.get('parties', '')
            people_str = metadata.get('people', '')
            
            if not parties_str:
                continue
            
            # Parse parties (comma-separated)
            parties = [p.strip() for p in parties_str.split(',') if p.strip()]
            people = [p.strip() for p in people_str.split(',') if p.strip()] if people_str else []
            
            # Normalize people names
            people = [get_canonical_name(p) for p in people if p.strip()]
            
            for party in parties:
                if party not in party_data:
                    party_data[party] = {
                        'figures': {},
                        'total_articles': 0
                    }
                
                party_data[party]['total_articles'] += 1
                
                # Associate people with this party (using canonical names)
                for person in people:
                    canonical_person = get_canonical_name(person)
                    if canonical_person not in party_data[party]['figures']:
                        party_data[party]['figures'][canonical_person] = 0
                    party_data[party]['figures'][canonical_person] += 1
        
        # Build response
        parties_list = []
        for party_name, data in party_data.items():
            # Get top 5 most mentioned figures
            sorted_figures = sorted(
                data['figures'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            # Extract figure names and deduplicate
            popular_figures = deduplicate_names([figure[0] for figure in sorted_figures])
            
            parties_list.append(PartyResponse(
                name=party_name,
                figures=popular_figures,
                total_articles=data['total_articles']
            ))
        
        # Sort by total articles (most prominent first)
        parties_list.sort(key=lambda x: x.total_articles, reverse=True)
        
        logger.info(f"Retrieved {len(parties_list)} political parties")
        
        return PartiesListResponse(
            parties=parties_list,
            total_parties=len(parties_list)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get parties: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve parties: {str(e)}"
        )


@router.get(
    "/debug/database/",
    tags=["Debug"]
)
async def debug_database():
    """Debug endpoint to check database contents."""
    try:
        if enhanced_db is None:
            return {"error": "Database not available"}
        
        # Get recent articles (sorted by date)
        all_articles = enhanced_db.collection.get(
            limit=20,  # Get more articles for debug
            include=["metadatas", "documents"]
        )
        
        if not all_articles:
            return {"error": "No articles found"}
        
        # Sort by date to get recent articles first
        metadatas = all_articles.get('metadatas', [])
        # Filter for recent Bangla articles
        bangla_articles = [m for m in metadatas if m.get('language') == 'Bangla']
        recent_articles = sorted(metadatas, key=lambda x: x.get('date_ts', 0), reverse=True)[:10]
        
        debug_info = {
            "total_articles": len(metadatas),
            "bangla_articles_count": len(bangla_articles),
            "recent_articles": recent_articles[:5],  # 5 most recent
            "bangla_sample": bangla_articles[:3],  # 3 Bangla articles
            "database_stats": enhanced_db.get_statistics() if hasattr(enhanced_db, 'get_statistics') else {}
        }
        
        return debug_info
        
    except Exception as e:
        return {"error": str(e)}


@router.post(
    "/party/{party_name}/figure/{figure_name}/",
    response_model=FigureProfileResponse,
    tags=["Political Analysis"]
)
async def get_figure_profile(
    party_name: str,
    figure_name: str,
    query_params: PartyFigureQueryRequest
):
    """
    Get profile, speech summaries, and keywords for a political figure.
    
    This endpoint retrieves articles related to a specific political figure
    within a party, including LLM-generated summaries and keywords.
    
    Supports date range filtering (e.g., 2024-08-05 to 2025-09-30).
    
    **Path Parameters:**
    - party_name: Name of the political party (e.g., "BNP")
    - figure_name: Name of the political figure (e.g., "Tareq Rahman")
    
    **Query Parameters:**
    - query: Search query (default: "recent statements")
    - date_from: Start date in YYYY-MM-DD format (e.g., "2024-08-05")
    - date_to: End date in YYYY-MM-DD format (e.g., "2025-09-30")
    - speeches_only: Filter for speeches only (default: false)
    - top_k: Maximum number of results (default: 10, max: 50)
    """
    try:
        if enhanced_db is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Enhanced vector database not available"
            )
        
        # Validate date format if provided
        if query_params.date_from:
            try:
                from datetime import datetime
                datetime.strptime(query_params.date_from, '%Y-%m-%d')
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date_from format. Use YYYY-MM-DD (e.g., '2024-08-05')"
                )
        
        if query_params.date_to:
            try:
                from datetime import datetime
                datetime.strptime(query_params.date_to, '%Y-%m-%d')
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date_to format. Use YYYY-MM-DD (e.g., '2025-09-30')"
                )
        
        # Use the convenience method for organized results
        logger.info(f"Querying articles for {figure_name} ({party_name})")
        logger.info(f"Query: {query_params.query}, Date range: {query_params.date_from} to {query_params.date_to}")
        
        results = enhanced_db.retrieve_articles_by_figure_or_party(
            query=query_params.query,
            political_figure=figure_name,
            political_party=party_name,
            date_from=query_params.date_from,
            date_to=query_params.date_to,
            speeches_only=query_params.speeches_only,
            top_k=query_params.top_k
        )
        
        # Check if any results found
        if results['total_results'] == 0:
            # Return empty but valid response
            logger.warning(f"No articles found for {figure_name} ({party_name})")
            return FigureProfileResponse(
                figure_name=figure_name,
                party_name=party_name,
                total_articles=0,
                articles=[],
                summaries_by_date={}
            )
        
        # Convert to response model
        articles_list = []
        for article in results['articles']:
            articles_list.append(ArticleSummary(
                id=article['id'],
                title=article['title'],
                date=article['date'],
                source=article['source'],
                similarity=article['similarity'],
                summary=article.get('summary'),
                key_points=article.get('key_points', []),
                stance_analysis=article.get('stance_analysis'),
                keywords=article.get('keywords', []),
                key_phrases=article.get('key_phrases', []),
                topics=article.get('topics', []),
                url=article.get('url')
            ))
        
        logger.info(f"Retrieved {len(articles_list)} articles for {figure_name}")
        
        return FigureProfileResponse(
            figure_name=figure_name,
            party_name=party_name,
            total_articles=results['total_results'],
            articles=articles_list,
            summaries_by_date=results['summaries_by_date']
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
    "/party/{party_name}/",
    response_model=FigureProfileResponse,
    tags=["Political Analysis"]
)
async def get_party_articles(
    party_name: str,
    query: Optional[str] = Query("party statements", description="Search query"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    speeches_only: bool = Query(False, description="Filter for speeches only"),
    top_k: int = Query(10, description="Maximum results", ge=1, le=50)
):
    """
    Get articles related to a political party.
    
    This endpoint retrieves articles about a political party with optional
    date range filtering.
    
    **Path Parameters:**
    - party_name: Name of the political party (e.g., "BNP", "Interim Government")
    
    **Query Parameters:**
    - query: Search query (default: "party statements")
    - date_from: Start date in YYYY-MM-DD format (e.g., "2024-08-05")
    - date_to: End date in YYYY-MM-DD format (e.g., "2025-09-30")
    - speeches_only: Filter for speeches only (default: false)
    - top_k: Maximum number of results (default: 10, max: 50)
    """
    try:
        if enhanced_db is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Enhanced vector database not available"
            )
        
        # Validate date format if provided
        if date_from:
            try:
                from datetime import datetime
                datetime.strptime(date_from, '%Y-%m-%d')
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date_from format. Use YYYY-MM-DD"
                )
        
        if date_to:
            try:
                from datetime import datetime
                datetime.strptime(date_to, '%Y-%m-%d')
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date_to format. Use YYYY-MM-DD"
                )
        
        logger.info(f"Querying articles for party: {party_name}")
        
        results = enhanced_db.retrieve_articles_by_figure_or_party(
            query=query,
            political_party=party_name,
            date_from=date_from,
            date_to=date_to,
            speeches_only=speeches_only,
            top_k=top_k
        )
        
        if results['total_results'] == 0:
            logger.warning(f"No articles found for party {party_name}")
            return FigureProfileResponse(
                figure_name="",
                party_name=party_name,
                total_articles=0,
                articles=[],
                summaries_by_date={}
            )
        
        # Convert to response model
        articles_list = []
        for article in results['articles']:
            articles_list.append(ArticleSummary(
                id=article['id'],
                title=article['title'],
                date=article['date'],
                source=article['source'],
                similarity=article['similarity'],
                summary=article.get('summary'),
                key_points=article.get('key_points', []),
                stance_analysis=article.get('stance_analysis'),
                keywords=article.get('keywords', []),
                key_phrases=article.get('key_phrases', []),
                topics=article.get('topics', []),
                url=article.get('url')
            ))
        
        logger.info(f"Retrieved {len(articles_list)} articles for party {party_name}")
        
        return FigureProfileResponse(
            figure_name="",
            party_name=party_name,
            total_articles=results['total_results'],
            articles=articles_list,
            summaries_by_date=results['summaries_by_date']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get party articles: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve party articles: {str(e)}"
        )


@router.post(
    "/scrape",
    response_model=ScrapingResponse,
    tags=["Scraping"],
    summary="Scrape newspapers and store articles"
)
async def scrape_newspapers(request: ScrapingRequest):
    """
    Scrape articles from newspapers and automatically store in vector database.
    
    This endpoint will:
    1. Scrape articles from specified newspapers (ProthomAlo, Jugantor, DailyStar, DhakaTribune)
    2. Filter only political articles
    3. Categorize and extract metadata
    4. Generate embeddings
    5. Perform LLM analysis (speech summaries, keywords, stance)
    6. Store everything in ChromaDB
    
    Args:
        request: ScrapingRequest with start_date, end_date, and newspapers list
        
    Returns:
        ScrapingResponse with scraping statistics
    """
    import time
    start_time = time.time()
    
    logger.info(f"Starting newspaper scraping: {request.start_date} to {request.end_date}")
    logger.info(f"Newspapers: {', '.join(request.newspapers)}")
    
    try:
        # Import required modules
        from backend.core.scraping import (
            ProthomAloScraper,
            JugantorScraper,
            DailyStarScraper,
            DhakaTribuneScraper
        )
        from backend.core.categorization import ArticleCategorizer
        from backend.core.embeddings import EmbeddingGenerator
        from backend.core.llm_generation import LLMGenerator
        
        # Step 1: Scrape newspapers
        all_articles = []
        articles_by_source = {}
        
        scraper_map = {
            "ProthomAlo": ProthomAloScraper,
            "Jugantor": JugantorScraper,
            "DailyStar": DailyStarScraper,
            "DhakaTribune": DhakaTribuneScraper
        }
        
        for newspaper in request.newspapers:
            if newspaper not in scraper_map:
                logger.warning(f"Unknown newspaper: {newspaper}, skipping")
                continue
            
            try:
                scraper_class = scraper_map[newspaper]
                scraper = scraper_class(request.start_date, request.end_date)
                articles = scraper.scrape_articles()
                
                all_articles.extend(articles)
                articles_by_source[newspaper] = len(articles)
                
                logger.info(f"Scraped {len(articles)} articles from {newspaper}")
                
            except Exception as e:
                logger.error(f"Error scraping {newspaper}: {e}")
                articles_by_source[newspaper] = 0
        
        if not all_articles:
            return ScrapingResponse(
                status="completed",
                total_articles_scraped=0,
                total_articles_stored=0,
                articles_by_source=articles_by_source,
                processing_time=time.time() - start_time,
                message="No articles found in the specified date range"
            )
        
        logger.info(f"Total articles scraped: {len(all_articles)}")
        
        # Step 2: Categorization
        logger.info("Starting categorization...")
        categorizer = ArticleCategorizer()
        categorized_articles = []
        
        for article in all_articles:
            try:
                categorization = categorizer.categorize_article(article)
                # Merge categorization with original article
                categorized = article.copy()
                categorized.update(categorization)
                categorized_articles.append(categorized)
            except Exception as e:
                logger.error(f"Error categorizing article: {e}")
                continue
        
        logger.info(f"Categorized {len(categorized_articles)} articles")
        
        # Step 3: Generate embeddings
        logger.info("Generating embeddings...")
        try:
            embedder = EmbeddingGenerator(model_name='all-MiniLM-L6-v2')
            texts = [f"{a.get('title', '')}\n\n{a.get('content', '')}" for a in categorized_articles]
            embeddings = embedder.generate_embeddings(texts, show_progress=False)
            
            for i, article in enumerate(categorized_articles):
                article['embedding'] = embeddings[i]
            
            logger.info(f"Generated embeddings for {len(embeddings)} articles")
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            # Continue without embeddings - ChromaDB will generate them
        
        # Step 4: LLM Analysis (Default: ON as requested)
        logger.info("Starting LLM analysis...")
        # Force enable LLM analysis as requested by user
        llm_enabled = True
        logger.info(f"LLM Analysis Enabled: {llm_enabled}")
        if hasattr(request, 'enable_llm_analysis'):
            logger.info(f"Request LLM flag: {request.enable_llm_analysis}")
        else:
            logger.info("No LLM flag in request, using default: True")
        
        if llm_enabled:
            try:
                llm = LLMGenerator(model="llama-3.3-70b-versatile", temperature=0.3)
                
                # Process ALL articles (no limitation as requested)
                articles_to_process = len(categorized_articles)
                logger.info(f"Processing LLM analysis for {articles_to_process} articles (processing all)")
                
                for i, article in enumerate(categorized_articles):
                    try:
                        print(f"\n{'='*100}")
                        print(f"📰 PROCESSING ARTICLE {i+1}/{articles_to_process}")
                        print(f"📰 Title: {article.get('title', 'N/A')[:80]}...")
                        print(f"🏛️ Parties: {article.get('parties', [])}")
                        print(f"👤 People: {article.get('people', [])}")
                        print(f"🎤 Is Speech: {article.get('is_speech', False)}")
                        print(f"🌐 Language: {article.get('language', 'English')}")
                        print(f"{'='*100}")
                        
                        # Get content - handle both 'content' and 'text' keys
                        article_content = article.get('content') or article.get('text', '')
                        if not article_content:
                            logger.warning(f"No content found for article {i}")
                            continue
                        
                        # Speech summary for detected speeches
                        if article.get('is_speech'):
                            people = article.get('people', [])
                            parties = article.get('parties', [])
                            figure = people[0] if people else "Political Figure"
                            party = parties[0] if parties else "Political Party"
                            
                            summary_result = llm.generate_speech_summary(
                                article_content=article_content,
                                article_title=article.get('title', ''),
                                political_figure=figure,
                                political_party=party,
                                language="Bangla"  # Force Bangla responses as requested
                            )
                            article['llm_summary'] = summary_result
                        
                        # Extract keywords for all articles - use generate_keywords method
                        keywords_result = llm.generate_keywords(
                            article_content=article_content,
                            article_title=article.get('title', ''),
                            num_keywords=10,
                            language="Bangla"  # Force Bangla responses as requested
                        )
                        article['llm_keywords'] = keywords_result
                        
                        # Print summary of results
                        print(f"\n✅ LLM PROCESSING COMPLETED FOR ARTICLE {i+1}")
                        if article.get('llm_summary'):
                            print(f"📝 Summary Generated: ✅")
                            print(f"🎯 Key Points: {len(article['llm_summary'].get('key_points', []))}")
                        else:
                            print(f"📝 Summary Generated: ❌ (Not a speech)")
                        
                        if article.get('llm_keywords'):
                            print(f"🔑 Keywords: {len(article['llm_keywords'].get('keywords', []))}")
                            print(f"📋 Phrases: {len(article['llm_keywords'].get('phrases', []))}")
                            print(f"📊 Topics: {len(article['llm_keywords'].get('topics', []))}")
                        
                        print(f"⏱️ Waiting 2 seconds to avoid rate limits...")
                        
                        # Longer delay to avoid rate limits
                        time.sleep(2)
                        
                    except Exception as e:
                        logger.error(f"Error in LLM analysis for article {i}: {e}")
                        continue
                
                # Print final LLM analysis summary
                speech_count = sum(1 for article in categorized_articles if article.get('llm_summary'))
                keyword_count = sum(1 for article in categorized_articles if article.get('llm_keywords'))
                
                print(f"\n{'='*100}")
                print(f"🎉 LLM ANALYSIS COMPLETED SUCCESSFULLY!")
                print(f"📊 Total Articles Processed: {len(categorized_articles)}")
                print(f"🎤 Speech Summaries Generated: {speech_count}")
                print(f"🔑 Keyword Analysis Completed: {keyword_count}")
                print(f"⏱️ LLM Processing Time: {time.time() - start_time:.2f} seconds")
                print(f"{'='*100}\n")
                
                logger.info("LLM analysis completed")
            except Exception as e:
                logger.error(f"LLM initialization failed: {e}")
                # Continue without LLM analysis
        else:
            logger.info("LLM analysis skipped (disabled to avoid rate limits)")
        
        # Step 5: Store in Vector Database (THIS IS CRITICAL - DO NOT SKIP)
        logger.info("Storing articles in vector database...")
        stored_count = 0
        
        try:
            # Use enhanced_db if available, otherwise create new instance
            from datetime import datetime as dt
            
            for i, article in enumerate(categorized_articles):
                try:
                    article['id'] = f"article_{int(dt.now().timestamp())}_{i}"
                except:
                    pass
            
            result = enhanced_db.store_embeddings(
                articles=categorized_articles,
                batch_size=50
            )
            
            if result.get('success'):
                stored_count = result.get('stored', 0)
                logger.info(f"Stored {stored_count} articles in vector database")
            else:
                logger.error(f"Storage failed: {result.get('message')}")
        
        except Exception as e:
            logger.error(f"Error storing articles: {e}")
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        return ScrapingResponse(
            status="completed",
            total_articles_scraped=len(all_articles),
            total_articles_stored=stored_count,
            articles_by_source=articles_by_source,
            processing_time=processing_time,
            message=f"Successfully scraped and stored {stored_count} political articles"
        )
    
    except Exception as e:
        logger.error(f"Scraping failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scraping operation failed: {str(e)}"
        )


# ==================== Analysis Endpoints (NEW) ====================

# Request models for analysis endpoints
class PartyAnalysisRequest(BaseModel):
    party: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    max_articles: int = 50

class FigureAnalysisRequest(BaseModel):
    figure: str
    party: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    max_articles: int = 50

@router.post(
    "/analysis/party",
    tags=["LLM Analysis"],
    summary="Analyze stored articles for a political party using Gemini LLM"
)
async def analyze_party_articles(request: PartyAnalysisRequest):
    """
    Generate comprehensive analysis of stored articles for a specific political party.
    
    Uses Gemini LLM to analyze articles mentioning the party and generate insights.
    
    Args:
        request: PartyAnalysisRequest with party name and optional filters
    """
    try:
        from backend.core.llm_generation import LLMGenerator
        
        logger.info(f"Starting LLM analysis for party: {request.party}")
        
        # Get articles from database
        if enhanced_db is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Vector database not available"
            )
        
        # Build where clause for filtering
        where_clause = {"parties": {"$contains": request.party}}
        
        # Query articles
        results = enhanced_db.collection.get(
            where=where_clause,
            limit=request.max_articles * 3,  # Get more to filter by date
            include=["documents", "metadatas"]
        )
        
        if not results or not results.get("documents"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No articles found for party: {request.party}"
            )
        
        # Filter by date if provided
        articles = []
        for i, doc in enumerate(results["documents"]):
            metadata = results["metadatas"][i]
            
            # Date filtering
            if request.start_date or request.end_date:
                article_date = metadata.get("date", "")
                if request.start_date and article_date < request.start_date:
                    continue
                if request.end_date and article_date > request.end_date:
                    continue
            
            # Document content is already the summary if article was summarized
            articles.append({
                "title": metadata.get("title", ""),
                "content": doc,
                "date": metadata.get("date", ""),
                "source": metadata.get("source", ""),
                "parties": metadata.get("parties", ""),
                "people": metadata.get("people", "")
            })
            
            if len(articles) >= request.max_articles:
                break
        
        if not articles:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No articles found for party {request.party} in the specified date range"
            )
        
        logger.info(f"Found {len(articles)} articles for analysis")
        
        # Generate LLM analysis
        llm_generator = LLMGenerator()
        analysis_result = llm_generator.analyze_party_coverage(request.party, articles)
        
        # Get date range
        dates = [a["date"] for a in articles if a.get("date")]
        date_range = {
            "earliest": min(dates) if dates else "",
            "latest": max(dates) if dates else ""
        }
        
        # Get unique sources
        sources = list(set(a["source"] for a in articles if a.get("source")))
        
        return {
            "success": True,
            "party_or_figure": request.party,
            "total_articles_analyzed": len(articles),
            "date_range": date_range,
            "analysis": {
                "raw_analysis": analysis_result,
                "articles_count": len(articles),
                "date_range": date_range,
                "sources": sources,
                "sample_titles": [a["title"] for a in articles[:5]]
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed for party {request.party}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@router.post(
    "/analysis/figure",
    tags=["LLM Analysis"],
    summary="Analyze stored articles for a political figure using Gemini LLM"
)
async def analyze_figure_articles(request: FigureAnalysisRequest):
    """
    Generate comprehensive analysis of stored articles for a specific political figure.
    
    Uses Gemini LLM to analyze articles mentioning the figure and generate insights.
    
    Args:
        request: FigureAnalysisRequest with figure name, party, and optional filters
    """
    try:
        from backend.core.llm_generation import LLMGenerator
        
        logger.info(f"Starting LLM analysis for figure: {request.figure}")
        
        # Get articles from database
        if enhanced_db is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Vector database not available"
            )
        
        # Build where clause for filtering
        where_clause = {"people": {"$contains": request.figure}}
        if request.party:
            where_clause["parties"] = {"$contains": request.party}
        
        # Query articles
        results = enhanced_db.collection.get(
            where=where_clause,
            limit=request.max_articles * 3,  # Get more to filter by date
            include=["documents", "metadatas"]
        )
        
        if not results or not results.get("documents"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No articles found for figure: {request.figure}"
            )
        
        # Filter by date if provided
        articles = []
        for i, doc in enumerate(results["documents"]):
            metadata = results["metadatas"][i]
            
            # Date filtering
            if request.start_date or request.end_date:
                article_date = metadata.get("date", "")
                if request.start_date and article_date < request.start_date:
                    continue
                if request.end_date and article_date > request.end_date:
                    continue
            
            # Document content is already the summary if article was summarized
            articles.append({
                "title": metadata.get("title", ""),
                "content": doc,
                "date": metadata.get("date", ""),
                "source": metadata.get("source", ""),
                "parties": metadata.get("parties", ""),
                "people": metadata.get("people", "")
            })
            
            if len(articles) >= request.max_articles:
                break
        
        if not articles:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No articles found for figure {request.figure} in the specified date range"
            )
        
        logger.info(f"Found {len(articles)} articles for analysis")
        
        # Generate LLM analysis
        llm_generator = LLMGenerator()
        analysis_result = llm_generator.analyze_figure_coverage(request.figure, articles)
        
        # Get date range
        dates = [a["date"] for a in articles if a.get("date")]
        date_range = {
            "earliest": min(dates) if dates else "",
            "latest": max(dates) if dates else ""
        }
        
        # Get unique sources
        sources = list(set(a["source"] for a in articles if a.get("source")))
        
        # Get associated parties
        all_parties = []
        for a in articles:
            if a.get("parties"):
                all_parties.extend([p.strip() for p in a["parties"].split(",")])
        associated_parties = list(set(all_parties))
        
        return {
            "success": True,
            "party_or_figure": request.figure,
            "total_articles_analyzed": len(articles),
            "date_range": date_range,
            "analysis": {
                "raw_analysis": analysis_result,
                "articles_count": len(articles),
                "date_range": date_range,
                "sources": sources,
                "sample_titles": [a["title"] for a in articles[:5]],
                "associated_parties": associated_parties
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed for figure {request.figure}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@router.get(
    "/parties/categorization-test",
    tags=["Testing"],
    summary="Get categorization test data for validation"
)
async def get_categorization_test(limit: int = Query(default=50, le=200)):
    """
    Get articles with categorization details for testing and validation.
    
    Returns articles with their party/figure associations and compares them
    against the correct POLITICAL_ENTITIES mapping.
    
    Args:
        limit: Number of articles to return (max 200)
    """
    try:
        from backend.core.scraping import POLITICAL_ENTITIES
        
        if enhanced_db is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Vector database not available"
            )
        
        # Get articles
        results = enhanced_db.collection.get(
            limit=limit,
            include=["documents", "metadatas"]
        )
        
        if not results or not results.get("documents"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No articles found in database"
            )
        
        # Format articles
        articles = []
        ids = results.get("ids", [])
        for i in range(len(results["documents"])):
            metadata = results["metadatas"][i]
            # Normalize parties and people into arrays
            parties_raw = metadata.get("parties", "") or ""
            people_raw = metadata.get("people", "") or ""
            parties_arr = [p.strip() for p in parties_raw.split(",") if p.strip()]
            people_arr = [p.strip() for p in people_raw.split(",") if p.strip()]

            # Build per-person affiliation mapping using canonical names
            people_affiliations = {}
            for person in people_arr:
                canonical = normalize_name_to_canonical(person)
                affiliated_party = get_correct_party_for_figure(canonical)
                people_affiliations[canonical] = affiliated_party if affiliated_party else ""

            articles.append({
                "index": i + 1,
                "id": ids[i] if i < len(ids) else f"article_{i+1}",
                "title": metadata.get("title", ""),
                "date": metadata.get("date", ""),
                "source": metadata.get("source", ""),
                "parties": parties_arr,
                "people": people_arr,
                "people_affiliations": people_affiliations,
                "primary_parties": metadata.get("primary_parties", ""),
                "mentioned_figures": metadata.get("mentioned_figures", ""),
                "political_entities": metadata.get("political_entities", ""),
                "keywords": metadata.get("keywords", ""),
                "content_preview": results["documents"][i][:200] + "..."
            })
        
        # Build party-figure breakdown from actual data
        # Articles now contain arrays for parties and people, and people_affiliations mapping
        party_figure_breakdown = {}
        for article in articles:
            parties = article.get("parties", []) or []
            people = article.get("people", []) or []

            # For each person, determine canonical name and affiliation
            for person in people:
                canonical_name = normalize_name_to_canonical(person)
                # If person has an explicit affiliation in this article, prefer it
                affiliation = article.get("people_affiliations", {}).get(canonical_name, "")

                # If affiliation is missing, try to infer from article-level parties
                if not affiliation and parties:
                    # If only one party is mentioned, associate person with that party
                    if len(parties) == 1:
                        affiliation = parties[0]
                    else:
                        # ambiguous: skip affiliation assignment
                        affiliation = ""

                for party in parties:
                    if party not in party_figure_breakdown:
                        party_figure_breakdown[party] = set()

                # If we determined affiliation, add to that party's set
                if affiliation:
                    if affiliation not in party_figure_breakdown:
                        party_figure_breakdown[affiliation] = set()
                    party_figure_breakdown[affiliation].add(canonical_name)
                else:
                    # Ambiguous: prefer the canonical party from POLITICAL_ENTITIES if available
                    canonical_party = get_correct_party_for_figure(canonical_name)
                    if canonical_party and canonical_party in parties:
                        if canonical_party not in party_figure_breakdown:
                            party_figure_breakdown[canonical_party] = set()
                        party_figure_breakdown[canonical_party].add(canonical_name)
                    else:
                        # If only one party mentioned in article, associate with it
                        if len(parties) == 1:
                            only_party = parties[0]
                            if only_party not in party_figure_breakdown:
                                party_figure_breakdown[only_party] = set()
                            party_figure_breakdown[only_party].add(canonical_name)
                        else:
                            # Ambiguous and no canonical match — skip adding to avoid cross-contamination
                            pass

        # Convert sets to sorted lists
        party_figure_breakdown = {k: sorted(list(v)) for k, v in party_figure_breakdown.items()}
        
        # Get correct mapping from POLITICAL_ENTITIES
        # Extract canonical figure names from nested structure
        correct_mapping = {}
        for party_key, party_data in POLITICAL_ENTITIES.items():
            if isinstance(party_data, dict) and "figures" in party_data:
                # New structure: {"BNP": {"party_names": [...], "figures": {"Tareq Rahman": [...]}}}
                correct_mapping[party_key] = list(party_data["figures"].keys())
            elif isinstance(party_data, list):
                # Old structure: {"BNP": ["Tareq Rahman", ...]}
                correct_mapping[party_key] = party_data
            else:
                correct_mapping[party_key] = []
        
        return {
            "total_articles": len(articles),
            "articles": articles,
            "party_figure_breakdown": party_figure_breakdown,
            "correct_mapping": correct_mapping
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get categorization test data: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve test data: {str(e)}"
        )


# ==================== Period Summary Endpoints ====================

class PeriodSummaryRequest(BaseModel):
    """Request model for period summary generation."""
    entity_type: str  # "party" or "figure"
    entity_name: str  # Party or figure name
    start_date: str  # YYYY-MM-DD format
    end_date: str    # YYYY-MM-DD format
    max_articles: int = 100


@router.post(
    "/summary/period",
    tags=["LLM Analysis"],
    summary="Generate summary of summaries for a date range"
)
async def generate_period_summary(request: PeriodSummaryRequest):
    """
    Generate comprehensive period summary for a party/figure.
    
    Process:
    1. Find all articles in date range for the entity
    2. Summarize each article (if not already summarized)
    3. Generate meta-summary from all individual summaries
    4. Return period summary with statistics
    
    Args:
        request: PeriodSummaryRequest with entity info and date range
        
    Returns:
        Period summary with individual summaries and meta-summary
    """
    try:
        from backend.core.llm_generation import LLMGenerator
        from backend.routes.articles import summarize_article
        
        logger.info(f"Generating period summary for {request.entity_type}: {request.entity_name}")
        logger.info(f"Date range: {request.start_date} to {request.end_date}")
        
        if enhanced_db is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Vector database not available"
            )
        
        # Build where clause based on entity type
        if request.entity_type == "party":
            where_clause = {"parties": {"$contains": request.entity_name}}
        elif request.entity_type == "figure":
            where_clause = {"people": {"$contains": request.entity_name}}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="entity_type must be 'party' or 'figure'"
            )
        
        # Get articles from database
        results = enhanced_db.collection.get(
            where=where_clause,
            limit=request.max_articles * 2,
            include=["documents", "metadatas", "ids"]
        )
        
        if not results or not results.get("documents"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No articles found for {request.entity_type}: {request.entity_name}"
            )
        
        # Filter by date range and collect articles
        articles_to_summarize = []
        article_summaries = []
        
        for i, doc in enumerate(results["documents"]):
            metadata = results["metadatas"][i]
            article_id = results["ids"][i]
            article_date = metadata.get("date", "")
            
            # Date filtering
            if article_date < request.start_date or article_date > request.end_date:
                continue
            
            # Check if already summarized
            is_summarized = str(metadata.get('is_summarized', 'False')).lower() == 'true'
            
            if is_summarized:
                # Already summarized - use existing summary
                summary_text = doc  # Document is the summary
                article_summaries.append({
                    "article_id": article_id,
                    "title": metadata.get("title", ""),
                    "date": article_date,
                    "summary": summary_text,
                    "already_summarized": True
                })
            else:
                # Not summarized yet - add to list for summarization
                articles_to_summarize.append({
                    "id": article_id,
                    "title": metadata.get("title", ""),
                    "date": article_date,
                    "content": doc
                })
        
        logger.info(f"Found {len(article_summaries)} already summarized, {len(articles_to_summarize)} to summarize")
        
        # Summarize articles that haven't been summarized yet
        llm_generator = LLMGenerator()
        
        for article in articles_to_summarize:
            try:
                logger.info(f"Summarizing: {article['title'][:60]}...")
                
                # Generate summary using LLM
                summary_result = llm_generator.generate_summary(
                    title=article['title'],
                    content=article['content']
                )
                
                # Update article in database with summary
                article_metadata = enhanced_db.collection.get(
                    ids=[article['id']],
                    include=["metadatas"]
                )['metadatas'][0]
                
                # Store LLM results in metadata
                article_metadata["is_summarized"] = "True"
                article_metadata["llm_key_points"] = ", ".join(summary_result.get('key_points', []))
                article_metadata["llm_keywords"] = ", ".join(summary_result.get('keywords', []))
                article_metadata["llm_topics"] = ", ".join(summary_result.get('topics', []))
                article_metadata["llm_stance_analysis"] = summary_result.get('stance_analysis', '')
                article_metadata["original_content"] = article['content']
                
                # Update database - replace document with summary
                enhanced_db.collection.update(
                    ids=[article['id']],
                    documents=[summary_result.get('summary', '')],
                    metadatas=[article_metadata]
                )
                
                # Add to summaries list
                article_summaries.append({
                    "article_id": article['id'],
                    "title": article['title'],
                    "date": article['date'],
                    "summary": summary_result.get('summary', ''),
                    "already_summarized": False
                })
                
                logger.info(f"✓ Summarized and updated: {article['title'][:60]}")
                
                # Small delay to avoid rate limits
                import asyncio
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Failed to summarize article {article['id']}: {e}")
                # Continue with other articles
                continue
        
        if not article_summaries:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No articles found in date range {request.start_date} to {request.end_date}"
            )
        
        # Sort by date
        article_summaries.sort(key=lambda x: x['date'])
        
        # Generate meta-summary from all summaries
        logger.info(f"Generating meta-summary from {len(article_summaries)} summaries...")
        
        combined_summaries = "\n\n".join([
            f"Date: {s['date']}\nTitle: {s['title']}\nSummary: {s['summary']}"
            for s in article_summaries
        ])
        
        # Generate period summary with structured analysis using LLM
        period_summary_prompt = f"""Analyze the following article summaries for {request.entity_name} from {request.start_date} to {request.end_date}.

Article Summaries:
{combined_summaries}

Generate a comprehensive analysis in the following format:

SUMMARY:
[Write a concise 200-300 word summary capturing overall theme, major events, trends, and impacts]

KEY POINTS:
- [Key point 1]
- [Key point 2]
- [Key point 3]
[Add 5-8 most important points]

KEYWORDS:
[List 8-12 most relevant keywords/phrases separated by commas]

TOPICS:
[List 5-8 main topics/themes separated by commas]"""
        
        meta_analysis = llm_generator.generate_text(period_summary_prompt)
        
        # Parse the structured response
        meta_summary = ""
        key_points = []
        keywords = []
        topics = []
        
        try:
            sections = meta_analysis.split('\n\n')
            current_section = None
            
            for section in sections:
                section = section.strip()
                if section.startswith('SUMMARY:'):
                    meta_summary = section.replace('SUMMARY:', '').strip()
                elif section.startswith('KEY POINTS:'):
                    points_text = section.replace('KEY POINTS:', '').strip()
                    key_points = [p.strip('- ').strip() for p in points_text.split('\n') if p.strip().startswith('-')]
                elif section.startswith('KEYWORDS:'):
                    keywords_text = section.replace('KEYWORDS:', '').strip()
                    keywords = [k.strip() for k in keywords_text.split(',') if k.strip()]
                elif section.startswith('TOPICS:'):
                    topics_text = section.replace('TOPICS:', '').strip()
                    topics = [t.strip() for t in topics_text.split(',') if t.strip()]
        except Exception as e:
            logger.warning(f"Failed to parse structured response: {e}")
            meta_summary = meta_analysis
        
        # Calculate statistics
        total_articles = len(article_summaries)
        newly_summarized = len([s for s in article_summaries if not s.get('already_summarized', False)])
        
        return {
            "success": True,
            "entity_type": request.entity_type,
            "entity_name": request.entity_name,
            "date_range": {
                "start": request.start_date,
                "end": request.end_date
            },
            "statistics": {
                "total_articles": total_articles,
                "newly_summarized": newly_summarized,
                "already_summarized": total_articles - newly_summarized
            },
            "period_summary": meta_summary,
            "key_points": key_points,
            "keywords": keywords,
            "topics": topics,
            "individual_summaries": article_summaries,
            "earliest_date": article_summaries[0]['date'] if article_summaries else None,
            "latest_date": article_summaries[-1]['date'] if article_summaries else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Period summary generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate period summary: {str(e)}"
        )



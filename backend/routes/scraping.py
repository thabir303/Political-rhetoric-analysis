"""
Scraping Routes - Separate from LLM Analysis
"""
from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
import logging
from datetime import datetime
import time

from backend.models.schemas import ScrapingRequest, ScrapingResponse
from political_entities_config import normalize_party_name, normalize_figure_name

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scraping", tags=["Scraping"])


@router.post(
    "/newspapers",
    response_model=ScrapingResponse,
    summary="Scrape newspapers and store articles (NO LLM - Only Categorization)"
)
async def scrape_newspapers(request: ScrapingRequest):
    """
    Scrape articles from newspapers and store in vector database.
    
    This endpoint performs:
    1. Scrapes articles from newspapers (ProthomAlo, Jugantor, DailyStar, DhakaTribune)
    2. **Categorizes articles (political figures, parties detection)**
       - Detects political parties mentioned (BNP, Jamaat-e-Islami, NCP, etc.)
       - Detects political figures mentioned (তারেক রহমান, নাহিদ ইসলাম, etc.)
       - Handles Bengali and English name variants
       - Maps figures to their parties
       - Uses canonical names from POLITICAL_ENTITIES
    3. Generates embeddings
    4. Stores in ChromaDB with categorization metadata
    
    **NO LLM ANALYSIS** - This endpoint does NOT call LLM for:
    - Summary generation
    - Keyword extraction  
    - Topic identification
    - Election impact analysis
    
    For LLM analysis, use the separate `/api/v1/analysis/llm` endpoint.
    
    Args:
        request: ScrapingRequest with start_date, end_date, newspapers
        
    Returns:
        ScrapingResponse with scraping and categorization statistics
    """
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
        from backend.core.vector_db import VectorDatabase
        
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
        
        # Step 2: Categorization (detect parties and figures with name normalization)
        logger.info("=" * 80)
        logger.info("Starting categorization (party/figure detection)...")
        logger.info("This will detect political entities and map Bengali/English name variants")
        logger.info("=" * 80)
        categorizer = ArticleCategorizer()
        categorized_articles = []
        
        for i, article in enumerate(all_articles):
            try:
                # Basic categorization - detect parties and figures
                categorization = categorizer.categorize_article(article)
                categorized = article.copy()
                
                # Extract categorization fields
                parties = categorization.get('parties', [])
                people = categorization.get('people', [])  # Already canonical names
                people_affiliations = categorization.get('people_affiliations', {})
                
                # Add categorization fields to article
                # Important: Store as lists, NOT comma-separated strings
                # The vector_db._prepare_metadata will convert to comma-separated strings
                categorized['parties'] = parties if isinstance(parties, list) else [parties] if parties else []
                categorized['people'] = people if isinstance(people, list) else [people] if people else []
                categorized['people_affiliations'] = people_affiliations
                categorized['keywords'] = categorization.get('keywords', [])
                categorized['themes'] = categorization.get('themes', {})
                categorized['is_speech'] = categorization.get('is_speech', False)
                categorized['is_stance'] = categorization.get('is_stance', False)
                
                categorized_articles.append(categorized)
                
                # Log categorization result with details
                logger.info(f"✅ [{i+1}/{len(all_articles)}] {article.get('title', 'Untitled')[:60]}...")
                if parties and len(parties) > 0:
                    logger.info(f"   🏛️  Parties: {', '.join(str(p) for p in parties)}")
                if people and len(people) > 0:
                    logger.info(f"   👤 Figures: {', '.join(str(p) for p in people)}")
                if people_affiliations and len(people_affiliations) > 0:
                    logger.info(f"   🔗 Affiliations: {people_affiliations}")
                
            except Exception as e:
                logger.error(f"Error categorizing article {i}: {e}")
                # Add article without categorization
                categorized = article.copy()
                categorized['parties'] = ''
                categorized['people'] = ''
                categorized['people_affiliations'] = {}
                categorized_articles.append(categorized)
        
        logger.info("=" * 80)
        logger.info(f"Categorization complete: {len(categorized_articles)} articles processed")
        logger.info("=" * 80)
        
        # Step 3: LLM Analysis DISABLED - Skip entirely
        # We now only do categorization (party/figure detection) without LLM
        logger.info("LLM analysis is disabled. Only categorization (party/figure detection) will be performed.")
        logger.info("Articles will be stored with detected parties and figures only.")
        
        # Step 4: Generate embeddings
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
        
        # Step 5: Store in Vector Database
        logger.info("Storing articles in vector database...")
        stored_count = 0
        
        try:
            db = VectorDatabase(collection_name="political_articles")
            
            # Add unique IDs
            for i, article in enumerate(categorized_articles):
                try:
                    article['id'] = f"article_{int(datetime.now().timestamp())}_{i}"
                except:
                    pass
            
            result = db.store_embeddings(
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
        
        processing_time = time.time() - start_time
        
        success_message = f"Successfully scraped, categorized (party/figure detection), and stored {stored_count} articles WITHOUT LLM analysis"
        
        return ScrapingResponse(
            status="completed",
            total_articles_scraped=len(all_articles),
            total_articles_stored=stored_count,
            articles_by_source=articles_by_source,
            processing_time=processing_time,
            message=success_message
        )
    
    except Exception as e:
        logger.error(f"Scraping failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scraping operation failed: {str(e)}"
        )


@router.post(
    "/political",
    summary="Scrape and store in party-wise collections"
)
async def scrape_political_articles(
    start_date: str,
    end_date: str,
    party: Optional[str] = None,
    figure: Optional[str] = None,
    newspapers: List[str] = ["ProthomAlo", "Jugantor", "DailyStar", "DhakaTribune"]
):
    """
    Scrape newspapers and store in party-wise collections.
    
    Uses the political storage system to organize articles by party.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        party: Optional party filter (bnp, ji, ncp, etc.)
        figure: Optional figure filter
        newspapers: List of newspapers to scrape
        
    Returns:
        Scraping statistics
    """
    try:
        from backend.services.political_scraper import PoliticalNewsScraper
        
        scraper = PoliticalNewsScraper(
            start_date=start_date,
            end_date=end_date
        )
        
        if party:
            stats = scraper.scrape_by_party(party)
        elif figure:
            stats = scraper.scrape_by_figure(figure)
        else:
            stats = scraper.scrape_all_newspapers()
        
        return {
            "status": "completed",
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"Political scraping failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Political scraping failed: {str(e)}"
        )

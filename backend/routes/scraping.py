"""
Scraping Routes - Separate from LLM Analysis
"""
from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
import time
import logging
from datetime import datetime

from backend.models.schemas import ScrapingRequest, ScrapingResponse
from political_entities_config import normalize_party_name, normalize_figure_name

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scraping", tags=["Scraping"])


@router.post(
    "/newspapers",
    response_model=ScrapingResponse,
    summary="Scrape newspapers and store articles (NO LLM)"
)
async def scrape_newspapers(request: ScrapingRequest):
    """
    Scrape articles from newspapers and store in vector database WITH LLM ANALYSIS.
    
    This endpoint performs:
    1. Scrapes articles from newspapers
    2. Categorizes articles (political figures, parties)
    3. **LLM Analysis (NEW):**
       - Generates summary (3-4 sentences)
       - Extracts keywords (5-10 keywords)
       - Identifies topics (3-5 topics)
       - Analyzes 2026 Bangladesh election impact
    4. Generates embeddings
    5. Stores in ChromaDB
    
    If LLM is not available, falls back to basic scraping + categorization.
    
    Args:
        request: ScrapingRequest with start_date, end_date, newspapers
        
    Returns:
        ScrapingResponse with scraping statistics
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
        
        # Step 2: Categorization ONLY (NO LLM Analysis)
        logger.info("Starting categorization (NO LLM analysis during scraping)...")
        categorizer = ArticleCategorizer()
        categorized_articles = []
        
        for article in all_articles:
            try:
                # Basic categorization - detect parties and figures
                categorization = categorizer.categorize_article(article)
                categorized = article.copy()
                categorized.update(categorization)
                
                # NO LLM ANALYSIS HERE - only categorization
                # LLM summary will be generated on-demand when user clicks "Generate Summary"
                
                categorized_articles.append(categorized)
                
                # Log categorization result
                parties = categorized.get('parties', '')
                people = categorized.get('people', '')
                logger.info(f"✅ Categorized: {article.get('title', 'Untitled')[:50]}... | Parties: {parties} | Figures: {people}")
                
            except Exception as e:
                logger.error(f"Error categorizing article: {e}")
                continue
        
        logger.info(f"Categorized {len(categorized_articles)} articles (NO LLM analysis)")
        
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
        
        # Step 4: Store in Vector Database
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
        
        success_message = f"Successfully scraped and stored {stored_count} articles (categorized only, LLM summary available on-demand)"
        
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

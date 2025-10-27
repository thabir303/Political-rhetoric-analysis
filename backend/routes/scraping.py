"""
Scraping Routes - Separate from LLM Analysis
"""
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from typing import List, Optional
import time
import logging
from datetime import datetime

from backend.models.schemas import ScrapingRequest, ScrapingResponse
from backend.auth import require_auth
from backend.services.job_manager import job_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scraping", tags=["Scraping"], dependencies=[Depends(require_auth)])


@router.post(
    "/newspapers",
    response_model=ScrapingResponse,
    summary="Scrape newspapers and store articles (NO LLM)"
)
async def scrape_newspapers(request: ScrapingRequest):
    """
    Scrape articles from newspapers and store in vector database.
    
    This endpoint ONLY:
    1. Scrapes articles from newspapers
    2. Categorizes articles
    3. Generates embeddings
    4. Stores in ChromaDB
    
    NO LLM analysis is performed here.
    Use /analysis/llm endpoint for LLM analysis separately.
    
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
        
        # Step 2: Categorization
        logger.info("Starting categorization...")
        categorizer = ArticleCategorizer()
        categorized_articles = []
        
        for article in all_articles:
            try:
                categorization = categorizer.categorize_article(article)
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
        print(f"Scraping process completed in {processing_time:.2f} seconds")
        return ScrapingResponse(
            status="completed",
            total_articles_scraped=len(all_articles),
            total_articles_stored=stored_count,
            articles_by_source=articles_by_source,
            processing_time=processing_time,
            message=f"Successfully scraped and stored {stored_count} articles (NO LLM analysis)"
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


# ==================== Background Job Endpoints ====================

@router.post("/newspapers/start", summary="Start newspaper scraping as background job")
async def start_scraping_job(
    request: ScrapingRequest,
    background_tasks: BackgroundTasks
):
    """
    Start newspaper scraping as a background job.
    Returns immediately with a job ID that can be used to track progress.
    
    This allows scraping to run for any duration without timeout issues.
    """
    # Create job
    job_id = job_manager.create_job(
        job_type="newspaper_scraping",
        metadata={
            "start_date": request.start_date,
            "end_date": request.end_date,
            "newspapers": request.newspapers
        }
    )
    
    # Add to background tasks
    background_tasks.add_task(
        run_scraping_background_job,
        job_id=job_id,
        request=request
    )
    
    logger.info(f"Started scraping job {job_id}")
    
    return {
        "job_id": job_id,
        "status": "started",
        "message": "Scraping job started in background. Use /scraping/jobs/{job_id} to check status."
    }


@router.get("/jobs/{job_id}", summary="Get scraping job status")
async def get_job_status(job_id: str):
    """
    Get the status of a scraping job by ID.
    
    Status can be: pending, running, completed, failed
    """
    job = job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    return job


@router.get("/jobs", summary="List all scraping jobs")
async def list_jobs(job_type: Optional[str] = "newspaper_scraping", limit: int = 50):
    """
    List all scraping jobs with optional filtering.
    """
    jobs = job_manager.get_all_jobs(job_type=job_type, limit=limit)
    return {"jobs": jobs, "total": len(jobs)}


@router.delete("/jobs/{job_id}", summary="Delete a job")
async def delete_job(job_id: str):
    """
    Delete a job by ID (useful for cleanup).
    """
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    job_manager.delete_job(job_id)
    return {"message": "Job deleted successfully"}


# ==================== Background Job Worker Function ====================

def run_scraping_background_job(job_id: str, request: ScrapingRequest):
    """
    Background worker function that performs the actual scraping.
    This runs independently and updates job status as it progresses.
    """
    try:
        # Update job status to running
        job_manager.update_job(
            job_id,
            status="running",
            current_step="Initializing scraping..."
        )
        
        start_time = time.time()
        
        logger.info(f"Job {job_id}: Starting scraping {request.start_date} to {request.end_date}")
        
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
        job_manager.update_job(
            job_id,
            current_step="Scraping articles from newspapers...",
            progress=10
        )
        
        all_articles = []
        articles_by_source = {}
        
        scraper_map = {
            "ProthomAlo": ProthomAloScraper,
            "Jugantor": JugantorScraper,
            "DailyStar": DailyStarScraper,
            "DhakaTribune": DhakaTribuneScraper
        }
        
        total_newspapers = len(request.newspapers)
        for idx, newspaper in enumerate(request.newspapers):
            if newspaper not in scraper_map:
                logger.warning(f"Job {job_id}: Unknown newspaper {newspaper}")
                continue
            
            try:
                job_manager.update_job(
                    job_id,
                    current_step=f"Scraping {newspaper}... ({idx+1}/{total_newspapers})",
                    progress=10 + (idx * 20 // total_newspapers)
                )
                
                scraper_class = scraper_map[newspaper]
                scraper = scraper_class(request.start_date, request.end_date)
                articles = scraper.scrape_articles()
                
                all_articles.extend(articles)
                articles_by_source[newspaper] = len(articles)
                
                logger.info(f"Job {job_id}: Scraped {len(articles)} from {newspaper}")
                
            except Exception as e:
                logger.error(f"Job {job_id}: Error scraping {newspaper}: {e}")
                articles_by_source[newspaper] = 0
        
        if not all_articles:
            job_manager.update_job(
                job_id,
                status="completed",
                progress=100,
                result={
                    "total_articles_scraped": 0,
                    "total_articles_stored": 0,
                    "articles_by_source": articles_by_source,
                    "processing_time": time.time() - start_time,
                    "message": "No articles found"
                }
            )
            return
        
        logger.info(f"Job {job_id}: Scraped {len(all_articles)} total articles")
        
        # Step 2: Categorization
        job_manager.update_job(
            job_id,
            current_step="Categorizing articles...",
            progress=40
        )
        
        categorizer = ArticleCategorizer()
        categorized_articles = []
        
        for article in all_articles:
            try:
                categorization = categorizer.categorize_article(article)
                categorized = article.copy()
                categorized.update(categorization)
                categorized_articles.append(categorized)
            except Exception as e:
                logger.error(f"Job {job_id}: Error categorizing: {e}")
                continue
        
        logger.info(f"Job {job_id}: Categorized {len(categorized_articles)} articles")
        
        # Step 3: Generate embeddings
        job_manager.update_job(
            job_id,
            current_step="Generating embeddings...",
            progress=60
        )
        
        try:
            embedder = EmbeddingGenerator(model_name='all-MiniLM-L6-v2')
            texts = [f"{a.get('title', '')}\n\n{a.get('content', '')}" for a in categorized_articles]
            embeddings = embedder.generate_embeddings(texts, show_progress=False)
            
            for i, article in enumerate(categorized_articles):
                article['embedding'] = embeddings[i]
            
            logger.info(f"Job {job_id}: Generated {len(embeddings)} embeddings")
        except Exception as e:
            logger.error(f"Job {job_id}: Error generating embeddings: {e}")
        
        # Step 4: Store in database
        job_manager.update_job(
            job_id,
            current_step="Storing articles in database...",
            progress=80
        )
        
        stored_count = 0
        try:
            db = VectorDatabase(collection_name="political_articles")
            
            for i, article in enumerate(categorized_articles):
                try:
                    article['id'] = f"article_{int(datetime.now().timestamp())}_{i}"
                except:
                    pass
            
            result = db.store_embeddings(
                articles=categorized_articles,
                batch_size=50
            )
            
            stored_count = result.get('total_stored', 0)
            logger.info(f"Job {job_id}: Stored {stored_count} articles")
            
        except Exception as e:
            logger.error(f"Job {job_id}: Error storing articles: {e}")
        
        # Job completed successfully
        processing_time = time.time() - start_time
        
        job_manager.update_job(
            job_id,
            status="completed",
            progress=100,
            current_step="Completed successfully!",
            result={
                "total_articles_scraped": len(all_articles),
                "total_articles_stored": stored_count,
                "articles_by_source": articles_by_source,
                "processing_time": processing_time,
                "message": f"Successfully scraped and stored {stored_count} articles"
            }
        )
        
        logger.info(f"Job {job_id}: Completed in {processing_time:.2f}s")
        
    except Exception as e:
        # Job failed
        logger.error(f"Job {job_id}: Failed with error: {e}")
        job_manager.update_job(
            job_id,
            status="failed",
            progress=0,
            error=str(e),
            current_step="Failed"
        )

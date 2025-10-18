"""
LLM Analysis Routes - Separate from Scraping
"""
from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional
import time
import logging

from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["LLM Analysis"])


# Request/Response Models
class LLMAnalysisRequest(BaseModel):
    """Request model for LLM analysis"""
    party: Optional[str] = None
    figure: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    limit: int = 10
    language: str = "Bangla"
    include_summary: bool = True
    include_keywords: bool = True
    include_stance: bool = True


class ArticleAnalysis(BaseModel):
    """Individual article analysis"""
    article_id: str
    title: str
    date: Optional[str] = None
    party: Optional[str] = None
    figures: List[str] = []
    summary: Optional[dict] = None
    keywords: Optional[dict] = None
    stance: Optional[str] = None


class LLMAnalysisResponse(BaseModel):
    """Response model for LLM analysis"""
    status: str
    total_analyzed: int
    analyses: List[ArticleAnalysis]
    processing_time: float
    message: str


class PartyReportRequest(BaseModel):
    """Request for party report generation"""
    party: str
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    limit: int = 50
    language: str = "Bangla"


class PartyReportResponse(BaseModel):
    """Response for party report"""
    party_id: str
    party_name: str
    total_articles: int
    articles_analyzed: int
    top_topics: dict
    top_keywords: dict
    political_stands_distribution: dict
    recent_analyses: List[dict]
    generated_at: str


@router.post(
    "/llm",
    response_model=LLMAnalysisResponse,
    summary="Run LLM analysis on stored articles"
)
async def analyze_articles_with_llm(request: LLMAnalysisRequest):
    """
    Run LLM analysis on articles stored in the database.
    
    This endpoint:
    1. Queries articles from ChromaDB based on filters
    2. Runs LLM analysis (summaries, keywords, stance)
    3. Returns analysis results
    
    Filter by:
    - party: Political party (e.g., "BNP", "JI", "NCP")
    - figure: Political figure name
    - date_from/date_to: Date range
    - limit: Maximum articles to analyze
    
    Args:
        request: LLMAnalysisRequest with filters and options
        
    Returns:
        LLMAnalysisResponse with analysis results
    """
    start_time = time.time()
    
    logger.info(f"Starting LLM analysis with filters: {request}")
    
    try:
        from backend.core.vector_db import VectorDatabase
        from backend.core.llm_generation import LLMGenerator
        
        # Initialize database
        db = VectorDatabase(collection_name="political_articles")
        
        # Build query filters
        where_filter = {}
        if request.party:
            where_filter["parties"] = {"$contains": request.party}
        if request.figure:
            where_filter["people"] = {"$contains": request.figure}
        if request.date_from:
            where_filter["date"] = {"$gte": request.date_from}
        if request.date_to:
            if "date" in where_filter:
                where_filter["date"]["$lte"] = request.date_to
            else:
                where_filter["date"] = {"$lte": request.date_to}
        
        # Query articles
        logger.info(f"Querying articles with filters: {where_filter}")
        
        try:
            results = db.collection.get(
                limit=request.limit,
                where=where_filter if where_filter else None
            )
            
            if not results or not results.get('ids'):
                return LLMAnalysisResponse(
                    status="completed",
                    total_analyzed=0,
                    analyses=[],
                    processing_time=time.time() - start_time,
                    message="No articles found matching the filters"
                )
            
            articles = []
            for i in range(len(results['ids'])):
                article = {
                    'id': results['ids'][i],
                    'content': results['documents'][i] if 'documents' in results else '',
                    'metadata': results['metadatas'][i] if 'metadatas' in results else {}
                }
                articles.append(article)
            
            logger.info(f"Found {len(articles)} articles to analyze")
            
        except Exception as e:
            logger.error(f"Error querying articles: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to query articles: {str(e)}"
            )
        
        # Initialize LLM
        try:
            llm = LLMGenerator(
                model="gemini-2.5-flash",
                provider="gemini",
                temperature=0.3
            )
            logger.info("LLM Generator initialized with Gemini")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to initialize LLM: {str(e)}"
            )
        
        # Analyze each article
        analyses = []
        
        for i, article in enumerate(articles):
            try:
                logger.info(f"Analyzing article {i+1}/{len(articles)}: {article['metadata'].get('title', '')[:50]}...")
                
                analysis = ArticleAnalysis(
                    article_id=article['id'],
                    title=article['metadata'].get('title', ''),
                    date=article['metadata'].get('date', ''),
                    party=article['metadata'].get('parties', [''])[0] if article['metadata'].get('parties') else None,
                    figures=article['metadata'].get('people', [])
                )
                
                content = article['content']
                title = article['metadata'].get('title', '')
                is_speech = article['metadata'].get('is_speech', False)
                
                # Generate summary for speeches
                if request.include_summary and is_speech:
                    try:
                        people = article['metadata'].get('people', [])
                        parties = article['metadata'].get('parties', [])
                        figure = people[0] if people else "Political Figure"
                        party = parties[0] if parties else "Political Party"
                        
                        summary = llm.generate_speech_summary(
                            article_content=content,
                            article_title=title,
                            political_figure=figure,
                            political_party=party,
                            language=request.language
                        )
                        analysis.summary = summary
                        logger.info(f"  ✓ Summary generated")
                    except Exception as e:
                        logger.error(f"  ✗ Summary generation failed: {e}")
                
                # Generate keywords
                if request.include_keywords:
                    try:
                        keywords = llm.generate_keywords(
                            article_content=content,
                            article_title=title,
                            num_keywords=10,
                            language=request.language
                        )
                        analysis.keywords = keywords
                        logger.info(f"  ✓ Keywords generated")
                    except Exception as e:
                        logger.error(f"  ✗ Keyword generation failed: {e}")
                
                # Detect stance
                if request.include_stance:
                    try:
                        # Simple stance detection based on keywords
                        stance = "Neutral"
                        if analysis.keywords:
                            kw_list = analysis.keywords.get('keywords', [])
                            if any(word in ['support', 'praise', 'welcome', 'সমর্থন'] for word in kw_list):
                                stance = "Supportive"
                            elif any(word in ['oppose', 'criticize', 'condemn', 'বিরোধিতা'] for word in kw_list):
                                stance = "Critical"
                        analysis.stance = stance
                        logger.info(f"  ✓ Stance: {stance}")
                    except Exception as e:
                        logger.error(f"  ✗ Stance detection failed: {e}")
                
                analyses.append(analysis)
                
                # Rate limiting
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error analyzing article {i}: {e}")
                continue
        
        processing_time = time.time() - start_time
        
        return LLMAnalysisResponse(
            status="completed",
            total_analyzed=len(analyses),
            analyses=analyses,
            processing_time=processing_time,
            message=f"Successfully analyzed {len(analyses)} articles"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"LLM analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM analysis failed: {str(e)}"
        )


@router.post(
    "/party-report",
    response_model=PartyReportResponse,
    summary="Generate comprehensive party report"
)
async def generate_party_report(request: PartyReportRequest):
    """
    Generate a comprehensive analysis report for a political party.
    
    This includes:
    - Article statistics
    - Top topics
    - Top keywords
    - Political stands distribution
    - Recent analyses
    
    Args:
        request: PartyReportRequest with party ID and filters
        
    Returns:
        PartyReportResponse with comprehensive report
    """
    try:
        from backend.services.political_analyzer import PoliticalArticleAnalyzer
        
        analyzer = PoliticalArticleAnalyzer(
            storage_directory="./political_chroma_db",
            llm_model="rule-based"  # Can be changed to "gemini" with API key
        )
        
        report = analyzer.generate_party_report(
            party_id=request.party,
            limit=request.limit
        )
        
        return PartyReportResponse(**report)
        
    except Exception as e:
        logger.error(f"Party report generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Party report generation failed: {str(e)}"
        )


@router.post(
    "/figure-report",
    summary="Generate comprehensive figure report"
)
async def generate_figure_report(
    figure: str,
    party: Optional[str] = None,
    limit: int = 50,
    language: str = "Bangla"
):
    """
    Generate a comprehensive analysis report for a political figure.
    
    Args:
        figure: Political figure name
        party: Optional party filter
        limit: Maximum articles to analyze
        language: Language for analysis
        
    Returns:
        Comprehensive report
    """
    try:
        from backend.services.political_analyzer import PoliticalArticleAnalyzer
        
        analyzer = PoliticalArticleAnalyzer(
            storage_directory="./political_chroma_db",
            llm_model="rule-based"
        )
        
        report = analyzer.generate_figure_report(
            figure_name=figure,
            party_id=party,
            limit=limit
        )
        
        return report
        
    except Exception as e:
        logger.error(f"Figure report generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Figure report generation failed: {str(e)}"
        )


@router.get(
    "/batch-status/{batch_id}",
    summary="Check status of batch analysis"
)
async def check_batch_status(batch_id: str):
    """
    Check the status of a batch LLM analysis job.
    
    For future implementation with background tasks.
    """
    return {
        "batch_id": batch_id,
        "status": "not_implemented",
        "message": "Batch processing will be implemented in future"
    }

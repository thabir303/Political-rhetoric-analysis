"""
LLM Analysis Routes - Separate from Scraping
"""
from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import List, Optional
import time
import logging

from pydantic import BaseModel
from backend.auth import require_auth

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["LLM Analysis"], dependencies=[Depends(require_auth)])


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
                model="gpt-5-nano",
                temperature=0.3
            )
            logger.info("LLM Generator initialized with gpt-5-nano")
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
    summary="Generate summary of summaries for a date range"
)
async def generate_period_summary(request: PeriodSummaryRequest):
    """
    Generate comprehensive period summary for a party/figure.
    
    Process:
    1. Check if period summary already exists in storage
    2. If exists, return cached summary
    3. If not, generate new summary:
       a. Find all articles in date range for the entity
       b. Summarize each article (if not already summarized)
       c. Generate meta-summary from all individual summaries
       d. Save to storage
    4. Return period summary with statistics
    
    Args:
        request: PeriodSummaryRequest with entity info and date range
        
    Returns:
        Period summary with individual summaries and meta-summary
    """
    try:
        from backend.core.llm_generation import LLMGenerator
        from backend.core.vector_db import VectorDatabase
        from backend.core.period_summary_store import PeriodSummaryStore
        
        logger.info(f"Generating period summary for {request.entity_type}: {request.entity_name}")
        logger.info(f"Date range: {request.start_date} to {request.end_date}")
        
        # Initialize period summary store
        period_store = PeriodSummaryStore()
        
        # Check if summary already exists
        existing_summary = period_store.get_period_summary(
            entity_type=request.entity_type,
            entity_name=request.entity_name,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        if existing_summary:
            logger.info(f"Found existing period summary (age: {period_store.get_summary_age_days(request.entity_type, request.entity_name, request.start_date, request.end_date):.1f} days)")
            
            # Return cached summary with proper structure
            return {
                "success": True,
                "entity_type": request.entity_type,
                "entity_name": request.entity_name,
                "date_range": {
                    "start": existing_summary["start_date"],
                    "end": existing_summary["end_date"]
                },
                "statistics": existing_summary["statistics"],
                "period_summary": existing_summary["summary"],
                "key_points": existing_summary.get("key_points", []),
                "keywords": existing_summary.get("keywords", []),
                "topics": existing_summary.get("topics", []),
                "from_cache": True,
                "last_updated": existing_summary.get("last_updated")
            }
        
        # Generate new summary
        logger.info("No cached summary found, generating new one...")
        
        # Initialize database
        enhanced_db = VectorDatabase(collection_name="political_articles")
        
        # Get all articles from database (ChromaDB get() doesn't support $contains)
        # Note: ids are always returned, no need to include them
        results = enhanced_db.collection.get(
            include=["documents", "metadatas"]
        )
        
        if not results or not results.get("documents"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No articles found in database"
            )
        
        logger.info(f"Retrieved {len(results['documents'])} total articles, filtering by entity and date...")
        
        # Filter by entity type, entity name, and date range
        articles_to_summarize = []
        article_summaries = []
        
        for i, doc in enumerate(results["documents"]):
            metadata = results["metadatas"][i]
            article_id = results["ids"][i]
            article_date = metadata.get("date", "")
            
            # Filter by entity type and name
            if request.entity_type == "party":
                parties = metadata.get("parties", "")
                if isinstance(parties, str):
                    parties_list = [p.strip() for p in parties.split(",") if p.strip()]
                else:
                    parties_list = parties if isinstance(parties, list) else []
                
                if request.entity_name not in parties_list:
                    continue
            elif request.entity_type == "figure":
                people = metadata.get("people", "")
                if isinstance(people, str):
                    people_list = [p.strip() for p in people.split(",") if p.strip()]
                else:
                    people_list = people if isinstance(people, list) else []
                
                if request.entity_name not in people_list:
                    continue
            else:
                continue
            
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
                summary_result = llm_generator.generate_speech_summary(
                    article_content=article['content'],
                    article_title=article['title'],
                    language="Bangla"
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
        period_summary_prompt = f"""{request.entity_name} এর জন্য {request.start_date} থেকে {request.end_date} পর্যন্ত নিম্নলিখিত আর্টিকেল সামারিগুলো বিশ্লেষণ করুন।

আর্টিকেল সামারি:
{combined_summaries}

নিম্নলিখিত ফরম্যাটে একটি বিস্তৃত বিশ্লেষণ তৈরি করুন (অবশ্যই বাংলায়):

সারসংক্ষেপ:
[২০০-৩০০ শব্দের একটি সংক্ষিপ্ত সারসংক্ষেপ লিখুন যা সামগ্রিক থিম, প্রধান ঘটনা, ট্রেন্ড এবং প্রভাবগুলো তুলে ধরে]

মূল পয়েন্ট:
- [মূল পয়েন্ট ১]
- [মূল পয়েন্ট ২]
- [মূল পয়েন্ট ৩]
[৫-৮টি সবচেয়ে গুরুত্বপূর্ণ পয়েন্ট যোগ করুন]

মূল শব্দ:
[কমা দিয়ে আলাদা করে ৮-১২টি সবচেয়ে প্রাসঙ্গিক কীওয়ার্ড/বাক্যাংশের তালিকা]

আলোচিত বিষয়:
[কমা দিয়ে আলাদা করে ৫-৮টি প্রধান বিষয়/থিমের তালিকা]

গুরুত্বপূর্ণ: সম্পূর্ণ উত্তর অবশ্যই বাংলায় দিন।"""
        
        meta_analysis = llm_generator._call_llm(
            prompt=period_summary_prompt,
            system_prompt="আপনি একজন বিশেষজ্ঞ রাজনৈতিক বিশ্লেষক। অনুরোধ অনুযায়ী বাংলায় সংগঠিত বিশ্লেষণ প্রদান করুন।",
            temperature=0.3,
            max_tokens=2000
        )
        
        # Helper function to clean text - remove ### and extra whitespace
        def clean_text(text: str) -> str:
            # Remove ### markers at start of lines
            text = text.replace('###', '').strip()
            # Remove multiple spaces
            import re
            text = re.sub(r'\s+', ' ', text)
            return text.strip()
        
        # Parse the structured response (support both Bangla and English headers)
        meta_summary = ""
        key_points = []
        keywords = []
        topics = []
        
        try:
            sections = meta_analysis.split('\n\n')
            
            for section in sections:
                section = section.strip()
                
                # Check for summary headers (Bangla or English)
                if any(header in section for header in ['SUMMARY:', 'সারসংক্ষেপ:', '**সারসংক্ষেপ**', 'সারসংক্ষেপঃ']):
                    for header in ['SUMMARY:', 'সারসংক্ষেপ:', '**সারসংক্ষেপ**', 'সারসংক্ষেপঃ']:
                        if header in section:
                            meta_summary = clean_text(section.replace(header, ''))
                            break
                
                # Check for key points headers
                elif any(header in section for header in ['KEY POINTS:', 'মূল পয়েন্ট:', '**মূল পয়েন্ট**', 'মূল পয়েন্টঃ']):
                    for header in ['KEY POINTS:', 'মূল পয়েন্ট:', '**মূল পয়েন্ট**', 'মূল পয়েন্টঃ']:
                        if header in section:
                            points_text = section.replace(header, '').strip()
                            key_points = [clean_text(p.strip('- •')) for p in points_text.split('\n') if p.strip() and (p.strip().startswith('-') or p.strip().startswith('•'))]
                            break
                
                # Check for keywords headers
                elif any(header in section for header in ['KEYWORDS:', 'মূল শব্দ:', '**মূল শব্দ**', 'মূল শব্দঃ']):
                    for header in ['KEYWORDS:', 'মূল শব্দ:', '**মূল শব্দ**', 'মূল শব্দঃ']:
                        if header in section:
                            keywords_text = section.replace(header, '').strip()
                            keywords = [clean_text(k) for k in keywords_text.split(',') if k.strip()]
                            break
                
                # Check for topics headers
                elif any(header in section for header in ['TOPICS:', 'আলোচিত বিষয়:', '**আলোচিত বিষয়**', 'আলোচিত বিষয়ঃ']):
                    for header in ['TOPICS:', 'আলোচিত বিষয়:', '**আলোচিত বিষয়**', 'আলোচিত বিষয়ঃ']:
                        if header in section:
                            topics_text = section.replace(header, '').strip()
                            topics = [clean_text(t) for t in topics_text.split(',') if t.strip()]
                            break
        except Exception as e:
            logger.warning(f"Failed to parse structured response: {e}")
            meta_summary = clean_text(meta_analysis)
        
        # Calculate statistics
        total_articles = len(article_summaries)
        newly_summarized = len([s for s in article_summaries if not s.get('already_summarized', False)])
        
        # Save period summary to storage
        period_store.save_period_summary(
            entity_type=request.entity_type,
            entity_name=request.entity_name,
            start_date=request.start_date,
            end_date=request.end_date,
            summary=meta_summary,
            key_points=key_points,
            keywords=keywords,
            topics=topics,
            total_articles=total_articles,
            newly_summarized=newly_summarized,
            already_summarized=total_articles - newly_summarized
        )
        
        logger.info(f"✓ Period summary saved to storage")
        
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
            "latest_date": article_summaries[-1]['date'] if article_summaries else None,
            "from_cache": False
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Period summary generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate period summary: {str(e)}"
        )


@router.get(
    "/summary/period/{entity_type}/{entity_name}",
    summary="Get all period summaries for an entity"
)
async def get_period_summaries(entity_type: str, entity_name: str):
    """
    Get all stored period summaries for a party or figure.
    
    Args:
        entity_type: "party" or "figure"
        entity_name: Name of the entity
        
    Returns:
        All period summaries for the entity
    """
    try:
        from backend.core.period_summary_store import PeriodSummaryStore
        
        if entity_type not in ["party", "figure"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="entity_type must be 'party' or 'figure'"
            )
        
        period_store = PeriodSummaryStore()
        summaries = period_store.get_all_period_summaries(entity_type, entity_name)
        
        # Convert to list format with proper structure
        summaries_list = []
        for date_key, summary_data in summaries.items():
            summaries_list.append({
                "date_range": {
                    "start": summary_data["start_date"],
                    "end": summary_data["end_date"]
                },
                "summary": summary_data["summary"],
                "key_points": summary_data.get("key_points", []),
                "keywords": summary_data.get("keywords", []),
                "topics": summary_data.get("topics", []),
                "statistics": summary_data.get("statistics", {}),
                "last_updated": summary_data.get("last_updated")
            })
        
        # Sort by start date (most recent first)
        summaries_list.sort(key=lambda x: x["date_range"]["start"], reverse=True)
        
        return {
            "success": True,
            "entity_type": entity_type,
            "entity_name": entity_name,
            "period_summaries": summaries_list,
            "total_summaries": len(summaries_list)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve period summaries: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve period summaries: {str(e)}"
        )

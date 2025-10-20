"""
Backend API endpoint for analyzing stored articles of a specific party or figure using LLM.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

router = APIRouter(prefix="/analysis", tags=["analysis"])
logger = logging.getLogger(__name__)


class PartyAnalysisRequest(BaseModel):
    """Request model for party-based analysis."""
    party: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    max_articles: Optional[int] = 50


class FigureAnalysisRequest(BaseModel):
    """Request model for figure-based analysis."""
    figure: str
    party: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    max_articles: Optional[int] = 50


class AnalysisResponse(BaseModel):
    """Response model for analysis results."""
    success: bool
    party_or_figure: str
    total_articles_analyzed: int
    date_range: Dict[str, str]
    analysis: Dict[str, Any]
    processing_time: float


def extract_llm_sections(analysis_text: str) -> Dict[str, Any]:
    """
    Extract keywords, topics, and summary from LLM response.
    
    Args:
        analysis_text: Full LLM response text
        
    Returns:
        Dict with extracted keywords, topics, summary, and full_analysis
    """
    import re
    
    result = {
        "keywords": [],
        "topics": [],
        "summary": "",
        "full_analysis": analysis_text
    }
    
    # Extract TOP_KEYWORDS section
    keywords_match = re.search(r'\*\*TOP_KEYWORDS\*\*\s*\n(.*?)(?=\n\*\*|$)', analysis_text, re.DOTALL)
    if keywords_match:
        keywords_text = keywords_match.group(1).strip()
        # Split by comma and clean
        result["keywords"] = [k.strip() for k in keywords_text.split(',') if k.strip()][:10]
    
    # Extract TOPICS_COVERED section
    topics_match = re.search(r'\*\*TOPICS_COVERED\*\*\s*\n(.*?)(?=\n\*\*|$)', analysis_text, re.DOTALL)
    if topics_match:
        topics_text = topics_match.group(1).strip()
        # Split by comma and clean
        result["topics"] = [t.strip() for t in topics_text.split(',') if t.strip()]
    
    # Extract SUMMARY section
    summary_match = re.search(r'\*\*SUMMARY\*\*\s*\n(.*?)(?=\n\*\*|$)', analysis_text, re.DOTALL)
    if summary_match:
        result["summary"] = summary_match.group(1).strip()
    
    logger.info(f"Extracted from LLM: {len(result['keywords'])} keywords, {len(result['topics'])} topics")
    
    return result


async def generate_article_summaries(articles: List[Dict], db, llm) -> tuple:
    """
    Generate individual summaries for articles that don't have them yet.
    
    Args:
        articles: List of articles to generate summaries for
        db: VectorDatabase instance
        llm: LLMGenerator instance
        
    Returns:
        Tuple of (summaries_generated, summaries_skipped)
    """
    logger.info(f"🔄 Generating individual summaries for {len(articles)} articles...")
    
    summaries_generated = 0
    summaries_skipped = 0
    
    for idx, article in enumerate(articles, 1):
        article_id = article.get('id')
        
        # Check if article already has a summary
        article_metadata_result = db.collection.get(
            ids=[article_id],
            include=["metadatas"]
        )
        
        if article_metadata_result and article_metadata_result.get('metadatas'):
            metadata = article_metadata_result['metadatas'][0]
            
            # Skip if already summarized
            if metadata.get('summary') and metadata.get('is_summarized'):
                logger.info(f"  [{idx}/{len(articles)}] ✓ Skipped (already has summary): {article.get('title', 'No title')[:50]}...")
                summaries_skipped += 1
                article['summary'] = metadata.get('summary')  # Use existing summary
                continue
        
        # Generate summary for this article
        try:
            logger.info(f"  [{idx}/{len(articles)}] 🤖 Generating summary: {article.get('title', 'No title')[:50]}...")
            
            content = article.get('content', '')
            
            # Skip if content is too short
            if len(content) < 100:
                logger.info(f"  [{idx}/{len(articles)}] ⚠️ Skipped (content too short)")
                article['summary'] = "Content too short for summary"
                continue
            
            # Detect language
            is_bangla = any('\u0980' <= char <= '\u09FF' for char in content[:200])
            
            # Create summary prompt
            if is_bangla:
                summary_prompt = f"নিচের আর্টিকেলটি ৩-৪টি সংক্ষিপ্ত বাক্যে সংক্ষেপে বলুন (শুধুমাত্র বাংলায় উত্তর দিন):\n\n{content}"
            else:
                summary_prompt = f"Summarize the following article in 3-4 concise sentences:\n\n{content}"
            
            # Generate summary
            summary = llm._call_llm(summary_prompt)
            
            # Update database with summary
            article_full = db.collection.get(
                ids=[article_id],
                include=["metadatas", "documents"]
            )
            
            if article_full and article_full.get('metadatas'):
                article_metadata = article_full['metadatas'][0]
                article_content = article_full['documents'][0] if article_full.get('documents') else content
                
                # Store summary in metadata
                article_metadata["summary"] = summary
                article_metadata["is_summarized"] = True
                article_metadata["summarized_at"] = datetime.now().isoformat()
                
                # Update database
                db.collection.update(
                    ids=[article_id],
                    documents=[article_content],  # Keep original content
                    metadatas=[article_metadata]   # Add summary to metadata
                )
                
                # Add summary to article for display
                article['summary'] = summary
                
                summaries_generated += 1
                logger.info(f"  [{idx}/{len(articles)}] ✓ Summary generated and stored")
                
        except Exception as e:
            logger.error(f"  [{idx}/{len(articles)}] ❌ Failed to generate summary: {e}")
            article['summary'] = None  # Mark as failed
    
    logger.info(f"📊 Summary Generation Complete:")
    logger.info(f"  - Generated: {summaries_generated} new summaries")
    logger.info(f"  - Skipped: {summaries_skipped} (already had summaries)")
    logger.info(f"  - Total: {len(articles)} articles processed")
    
    return summaries_generated, summaries_skipped


async def generate_summary_of_summaries(articles: List[Dict], llm, entity_name: str, entity_type: str = "party") -> str:
    """
    Generate a comprehensive summary from all individual article summaries.
    This creates a "Summary of Summaries" for the AI Analysis section.
    
    Args:
        articles: List of articles with individual summaries
        llm: LLMGenerator instance
        entity_name: Name of party or figure
        entity_type: "party" or "figure"
        
    Returns:
        Comprehensive summary text combining all individual summaries
    """
    logger.info(f"🔄 Generating comprehensive summary from {len(articles)} article summaries...")
    
    # Collect all individual summaries (ONLY the summary text, not article details)
    summaries_text = []
    for article in articles:
        summary = article.get('summary', '')
        
        if summary and summary not in ["Content too short for summary", "Summary not available"]:
            # Just add the summary text, without article number or title
            summaries_text.append(summary.strip())
    
    if not summaries_text:
        logger.warning("No valid summaries found to combine")
        return f"No summaries available for {entity_name}"
    
    logger.info(f"📝 Collected {len(summaries_text)} valid summaries for synthesis")
    
    # Detect language from first summary
    first_summary = summaries_text[0] if summaries_text else ""
    is_bangla = any('\u0980' <= char <= '\u09FF' for char in first_summary)
    
    # Combine all summaries into one text block
    all_summaries_combined = "\n\n".join(summaries_text)
    
    # Create prompt for synthesizing summaries
    if is_bangla:
        prompt = f"""আপনি একজন রাজনৈতিক বিশ্লেষক। নিচে {entity_name} সম্পর্কে {len(summaries_text)}টি আলাদা আলাদা নিউজ আর্টিকেলের সংক্ষিপ্তসার দেওয়া হয়েছে।

⚠️ গুরুত্বপূর্ণ নির্দেশনা:
- এই সংক্ষিপ্তসারগুলো আবার আলাদাভাবে উল্লেখ করবেন না
- "Article 1", "প্রথম আর্টিকেল", "Summary:" ইত্যাদি লিখবেন না
- শুধুমাত্র একটি flowing comprehensive summary লিখুন
- সব তথ্য একসাথে মিশিয়ে একটি cohesive narrative তৈরি করুন

সংক্ষিপ্তসারগুলো:
{all_summaries_combined}

উপরের সব তথ্য থেকে {entity_name} এর সাম্প্রতিক কার্যক্রম সম্পর্কে একটি flowing comprehensive summary লিখুন (4-5টি প্যারাগ্রাফে) যেখানে থাকবে:
- সামগ্রিক রাজনৈতিক অবস্থান এবং কৌশল
- প্রধান থিম এবং দাবিসমূহ
- গুরুত্বপূর্ণ বক্তব্য এবং কার্যক্রম
- সাম্প্রতিক উন্নয়ন এবং ট্রেন্ড

শুধুমাত্র synthesized narrative summary লিখুন (বাংলায়):"""
    else:
        prompt = f"""You are a political analyst. Below are {len(summaries_text)} individual news article summaries about {entity_name}.

⚠️ CRITICAL INSTRUCTIONS:
- Do NOT list the summaries separately
- Do NOT write "Article 1", "First article", "Summary:" etc.
- Write ONLY a flowing comprehensive summary
- Synthesize all information into a cohesive narrative

Summaries:
{all_summaries_combined}

Write a flowing comprehensive summary (4-5 paragraphs) about {entity_name}'s recent activities that covers:
- Overall political positioning and strategy
- Main themes and demands
- Key statements and activities
- Recent developments and trends

Write ONLY the synthesized narrative summary:"""
    
    try:
        combined_summary = llm._call_llm(prompt)
        logger.info(f"✅ Comprehensive summary generated ({len(combined_summary)} characters)")
        return combined_summary
    except Exception as e:
        logger.error(f"❌ Failed to generate comprehensive summary: {e}")
        # Fallback: Just combine summaries with line breaks
        return "\n\n".join(summaries_text)


@router.post(
    "/party",
    response_model=AnalysisResponse,
    summary="Analyze stored articles for a specific party"
)
async def analyze_party_articles(request: PartyAnalysisRequest):
    """
    Analyze all stored articles mentioning a specific political party.
    
    Uses Gemini LLM to generate comprehensive analysis including:
    - Overall stance and positioning
    - Key themes and topics
    - Major events and developments
    - Sentiment trends
    - Notable quotes and statements
    
    Args:
        request: PartyAnalysisRequest with party name and optional filters
        
    Returns:
        AnalysisResponse with comprehensive party analysis
    """
    import time
    start_time = time.time()
    
    try:
        from backend.core.vector_db import VectorDatabase
        from backend.core.llm_generation import LLMGenerator
        from backend.core.ai_summary_store import AISummaryStore
        
        logger.info(f"Starting party analysis for: {request.party}")
        
        # Initialize vector database, summary store, and LLM
        db = VectorDatabase(collection_name="political_articles")
        summary_store = AISummaryStore()
        llm = LLMGenerator()
        
        logger.info(f"Retrieving ALL articles for party: {request.party}")
        
        # Normalize the party name for matching
        party_name = request.party.strip()
        
        # Get ALL articles from the database (not just semantic search results)
        all_results = db.collection.get(include=["metadatas", "documents"])
        
        # Filter articles that mention this party
        matching_articles = []
        seen_urls = set()
        
        for i, (metadata, document, doc_id) in enumerate(zip(
            all_results.get("metadatas", []),
            all_results.get("documents", []),
            all_results.get("ids", [])
        )):
            # Check if this party is mentioned in the article
            parties_str = metadata.get("parties", "")
            parties_list = [p.strip() for p in parties_str.split(',') if p.strip()]
            
            is_match = party_name in parties_list
            
            if is_match:
                article_url = metadata.get("url", "")
                
                # Skip duplicates
                if article_url and article_url in seen_urls:
                    continue
                if article_url:
                    seen_urls.add(article_url)
                
                # Apply date filtering if provided
                article_date = metadata.get("date", "")
                if request.start_date or request.end_date:
                    try:
                        from datetime import datetime
                        article_date_obj = datetime.strptime(article_date, '%Y-%m-%d')
                        
                        if request.start_date:
                            date_from_obj = datetime.strptime(request.start_date, '%Y-%m-%d')
                            if article_date_obj < date_from_obj:
                                continue
                        
                        if request.end_date:
                            date_to_obj = datetime.strptime(request.end_date, '%Y-%m-%d')
                            if article_date_obj > date_to_obj:
                                continue
                    except ValueError:
                        continue
                
                matching_articles.append({
                    'id': doc_id,
                    'title': metadata.get('title', 'No title'),
                    'content': document or metadata.get('content', ''),
                    'preview': metadata.get('preview', ''),
                    'date': article_date,
                    'source': metadata.get('source', 'Unknown'),
                    'url': article_url,
                    'parties': parties_list
                })
        
        articles = matching_articles
        
        if not articles:
            return AnalysisResponse(
                success=False,
                party_or_figure=request.party,
                total_articles_analyzed=0,
                date_range={"start": request.start_date or "N/A", "end": request.end_date or "N/A"},
                analysis={"message": "No articles found for the specified party"},
                processing_time=time.time() - start_time
            )
        
        logger.info(f"Found {len(articles)} articles for {request.party}")
        
        # Sort articles by date (most recent first)
        def parse_date(article):
            date_str = article.get('date', '')
            if not date_str:
                return None
            try:
                # Try parsing different date formats
                from datetime import datetime
                for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%Y/%m/%d', '%d/%m/%Y']:
                    try:
                        return datetime.strptime(date_str, fmt)
                    except:
                        continue
                return None
            except:
                return None
        
        # Sort articles by date descending (most recent first)
        articles_with_dates = [(a, parse_date(a)) for a in articles]
        articles_with_dates.sort(key=lambda x: x[1] if x[1] else datetime.min, reverse=True)
        articles_sorted = [a[0] for a in articles_with_dates]
        
        logger.info(f"Sorted {len(articles_sorted)} articles by date (most recent first)")
        
        # Prepare articles for analysis - use only the requested number (most recent ones)
        articles_to_analyze = articles_sorted[:request.max_articles]
        
        logger.info(f"Selected {len(articles_to_analyze)} most recent articles for analysis")
        
        # Check if we have enough articles for meaningful analysis
        if len(articles_to_analyze) < 3:
            logger.warning(f"Only {len(articles_to_analyze)} articles found - may not be enough for comprehensive analysis")
        
        # ===== GENERATE INDIVIDUAL SUMMARIES FOR EACH ARTICLE (PARTY ANALYSIS) =====
        await generate_article_summaries(articles_to_analyze, db, llm)
        
        # ===== GENERATE COMPREHENSIVE SUMMARY FROM ALL INDIVIDUAL SUMMARIES =====
        logger.info("🔄 Creating comprehensive summary from article summaries...")
        comprehensive_summary = await generate_summary_of_summaries(
            articles_to_analyze, 
            llm, 
            request.party,
            "party"
        )
        logger.info(f"✅ Comprehensive summary created: {len(comprehensive_summary)} characters")
        
        # ===== PREPARE ARTICLES FOR COMPREHENSIVE ANALYSIS =====
        articles_text = []
        
        logger.info(f"Preparing {len(articles_to_analyze)} articles for comprehensive LLM analysis")
        
        for idx, article in enumerate(articles_to_analyze, 1):
            title = article.get('title', 'No title')
            content = article.get('content', article.get('preview', ''))
            date = article.get('date', 'No date')
            source = article.get('source', 'Unknown')
            
            # Format article with clear structure
            article_text = f"""
Article #{idx}
Date: {date}
Source: {source}
Title: {title}
Content: {content}
---
"""
            articles_text.append(article_text)
        
        # Create comprehensive prompt for party analysis
        prompt = f"""You are analyzing {len(articles_to_analyze)} most recent news articles about {request.party}.

Provide a comprehensive analysis in the following format. Start with KEYWORDS and TOPICS sections:

**TOP_KEYWORDS**
[Provide exactly 10 most relevant keywords, comma-separated, in order of importance]

**TOPICS_COVERED**
[Provide 5-7 main topics/themes covered in these articles, comma-separated]

**SUMMARY**
[A concise 2-3 paragraph summary of the party's recent activities, positioning, and major developments based on these articles]

**Overall Positioning & Stance**
[Analysis here]

**Key Themes & Issues**
[Analysis here]

**Major Developments**
[Analysis here]

**Leadership & Key Figures**
[Analysis here]

**Public Sentiment**
[Analysis here]

**Strategic Direction**
[Analysis here]

**Key Quotes**
[3-5 notable quotes here]

=== ARTICLES TO ANALYZE ({len(articles_to_analyze)} articles) ===
{chr(10).join(articles_text)}

Provide ONLY the structured analysis. Do NOT include introductory text like "Based on the provided articles" or "Here is my analysis". Start directly with the first section heading.
"""
        
        system_prompt = """You are a political analyst for Bangladesh politics. Provide direct, structured analysis without preambles or meta-commentary. Start immediately with the analysis sections."""
        
        # Log the request details
        logger.info(f"🤖 LLM REQUEST DETAILS:")
        logger.info(f"  - Entity: {request.party}")
        logger.info(f"  - Articles to analyze: {len(articles_to_analyze)}")
        logger.info(f"  - Date range: {request.start_date or 'N/A'} to {request.end_date or 'N/A'}")
        logger.info(f"  - Prompt length: {len(prompt)} characters")
        logger.info(f"  - System prompt: {system_prompt}")
        
        # Print the full prompt to terminal
        logger.info("=" * 80)
        logger.info("📝 FULL PROMPT SENT TO LLM:")
        logger.info("=" * 80)
        logger.info(f"\n{prompt}\n")
        logger.info("=" * 80)
        
        try:
            analysis_result = llm._call_llm(
                prompt=prompt,
                system_prompt=system_prompt
            )
            
            logger.info("=" * 80)
            logger.info("✅ LLM RESPONSE RECEIVED (PARTY ANALYSIS):")
            logger.info("=" * 80)
            logger.info(f"  - Response length: {len(analysis_result)} characters")
            logger.info(f"\n{analysis_result}\n")
            logger.info("=" * 80)
            
        except ValueError as ve:
            # Handle Gemini safety filters or other content issues
            logger.error(f"LLM content generation failed: {ve}")
            
            # Provide a fallback analysis based on available data
            analysis_result = f"""**Overall Positioning & Stance**
{request.party} is covered in {len(articles_to_analyze)} articles from {', '.join(set([a.get('source', 'Unknown') for a in articles_to_analyze]))}.

**Article Summary**
- Total articles: {len(articles_to_analyze)}
- Date range: {min([a.get('date', '') for a in articles_to_analyze if a.get('date')], default='N/A')} to {max([a.get('date', '') for a in articles_to_analyze if a.get('date')], default='N/A')}
- Sources: {', '.join(set([a.get('source', 'Unknown') for a in articles_to_analyze]))}

**Recent Headlines**
{chr(10).join(['- ' + a.get('title', 'No title') for a in articles_to_analyze[:5]])}

**Recommendation**
Try adjusting the date range or search parameters to find more articles for a comprehensive analysis.
"""
            logger.info("Using fallback analysis due to LLM error")
        
        # Extract keywords, topics, and summary from LLM response
        extracted = extract_llm_sections(analysis_result)
        
        logger.info(f"📊 Extracted Analysis Components:")
        logger.info(f"  - Keywords: {extracted['keywords'][:5]}..." if len(extracted['keywords']) > 5 else f"  - Keywords: {extracted['keywords']}")
        logger.info(f"  - Topics: {extracted['topics']}")
        logger.info(f"  - Summary length: {len(extracted['summary'])} chars")
        
        # Save AI summary to persistent storage
        try:
            summary_store.save_party_summary(
                party_name=request.party,
                keywords=extracted['keywords'],
                topics=extracted['topics'],
                summary=extracted['summary'],
                articles_analyzed=len(articles_to_analyze)
            )
            logger.info(f"💾 Saved AI summary for party: {request.party}")
        except Exception as e:
            logger.error(f"Failed to save party summary: {e}")
        
        # Structure the analysis response with article summaries
        analysis = {
            "raw_analysis": analysis_result,
            "keywords": extracted['keywords'],
            "topics": extracted['topics'],
            "summary": extracted['summary'],
            "comprehensive_summary": comprehensive_summary,  # NEW: Summary of all article summaries
            "articles_count": len(articles_to_analyze),
            "date_range": {
                "earliest": min([a.get('date', '') for a in articles_to_analyze if a.get('date')], default='N/A'),
                "latest": max([a.get('date', '') for a in articles_to_analyze if a.get('date')], default='N/A')
            },
            "sources": list(set([a.get('source', 'Unknown') for a in articles_to_analyze])),
            "sample_titles": [a.get('title', 'No title') for a in articles_to_analyze[:5]],
            # NEW: Include article summaries (all analyzed articles with their summaries)
            "article_summaries": [
                {
                    "title": a.get('title', 'No title'),
                    "date": a.get('date', 'No date'),
                    "source": a.get('source', 'Unknown'),
                    "summary": a.get('summary', 'Summary not available'),
                    "url": a.get('url', '')
                }
                for a in articles_to_analyze
            ]
        }
        
        processing_time = time.time() - start_time
        logger.info(f"Party analysis completed in {processing_time:.2f}s")
        
        return AnalysisResponse(
            success=True,
            party_or_figure=request.party,
            total_articles_analyzed=len(articles_to_analyze),
            date_range=analysis["date_range"],
            analysis=analysis,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Failed to analyze party articles: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@router.post(
    "/figure",
    response_model=AnalysisResponse,
    summary="Analyze stored articles for a specific political figure"
)
async def analyze_figure_articles(request: FigureAnalysisRequest):
    """
    Analyze all stored articles mentioning a specific political figure.
    
    Uses Gemini LLM to generate comprehensive analysis including:
    - Key activities and statements
    - Political positioning
    - Major events
    - Relationships with other parties/figures
    - Public perception
    
    Args:
        request: FigureAnalysisRequest with figure name and optional filters
        
    Returns:
        AnalysisResponse with comprehensive figure analysis
    """
    import time
    start_time = time.time()
    
    try:
        from backend.core.vector_db import VectorDatabase
        from backend.core.llm_generation import LLMGenerator
        from backend.core.ai_summary_store import AISummaryStore
        
        logger.info(f"Starting figure analysis for: {request.figure}")
        
        # Initialize vector database, summary store, and LLM
        db = VectorDatabase(collection_name="political_articles")
        summary_store = AISummaryStore()
        llm = LLMGenerator()
        
        logger.info(f"Retrieving ALL articles for figure: {request.figure} from party: {request.party}")
        
        # Normalize the figure name for matching
        figure_name = request.figure.strip()
        
        # Get ALL articles from the database (not just semantic search results)
        all_results = db.collection.get(include=["metadatas", "documents"])
        
        # Filter articles that mention this figure
        matching_articles = []
        seen_urls = set()
        
        for i, (metadata, document, doc_id) in enumerate(zip(
            all_results.get("metadatas", []),
            all_results.get("documents", []),
            all_results.get("ids", [])
        )):
            # Parse people_affiliations
            people_affiliations_str = metadata.get("people_affiliations", "{}")
            try:
                import json
                people_affiliations = json.loads(people_affiliations_str) if people_affiliations_str else {}
            except:
                people_affiliations = {}
            
            # Check if this figure is mentioned
            is_match = False
            if request.party:
                # If party specified, check if figure is affiliated with that party
                is_match = (figure_name in people_affiliations and 
                           people_affiliations[figure_name] == request.party)
            else:
                # If no party specified, just check if figure is mentioned
                is_match = figure_name in people_affiliations
            
            if is_match:
                article_url = metadata.get("url", "")
                
                # Skip duplicates
                if article_url and article_url in seen_urls:
                    continue
                if article_url:
                    seen_urls.add(article_url)
                
                # Apply date filtering if provided
                article_date = metadata.get("date", "")
                if request.start_date or request.end_date:
                    try:
                        article_date_obj = datetime.strptime(article_date, '%Y-%m-%d')
                        
                        if request.start_date:
                            date_from_obj = datetime.strptime(request.start_date, '%Y-%m-%d')
                            if article_date_obj < date_from_obj:
                                continue
                        
                        if request.end_date:
                            date_to_obj = datetime.strptime(request.end_date, '%Y-%m-%d')
                            if article_date_obj > date_to_obj:
                                continue
                    except ValueError:
                        continue
                
                matching_articles.append({
                    'id': doc_id,
                    'title': metadata.get('title', 'No title'),
                    'content': document or metadata.get('content', ''),
                    'preview': metadata.get('preview', ''),
                    'date': article_date,
                    'source': metadata.get('source', 'Unknown'),
                    'url': article_url,
                    'parties': metadata.get('parties', '').split(',') if metadata.get('parties') else []
                })
        
        articles = matching_articles
        
        if not articles:
            return AnalysisResponse(
                success=False,
                party_or_figure=request.figure,
                total_articles_analyzed=0,
                date_range={"start": request.start_date or "N/A", "end": request.end_date or "N/A"},
                analysis={"message": "No articles found for the specified figure"},
                processing_time=time.time() - start_time
            )
        
        logger.info(f"Found {len(articles)} articles for {request.figure}")
        
        # Sort articles by date (most recent first)
        def parse_date(article):
            date_str = article.get('date', '')
            if not date_str:
                return None
            try:
                # Try parsing different date formats
                from datetime import datetime
                for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%Y/%m/%d', '%d/%m/%Y']:
                    try:
                        return datetime.strptime(date_str, fmt)
                    except:
                        continue
                return None
            except:
                return None
        
        # Sort articles by date descending (most recent first)
        articles_with_dates = [(a, parse_date(a)) for a in articles]
        articles_with_dates.sort(key=lambda x: x[1] if x[1] else datetime.min, reverse=True)
        articles_sorted = [a[0] for a in articles_with_dates]
        
        logger.info(f"Sorted {len(articles_sorted)} articles by date (most recent first)")
        
        # Prepare articles for analysis - use only the requested number (most recent ones)
        articles_to_analyze = articles_sorted[:request.max_articles]
        
        logger.info(f"Selected {len(articles_to_analyze)} most recent articles for analysis")
        
        # Check if we have enough articles for meaningful analysis
        if len(articles_to_analyze) < 3:
            logger.warning(f"Only {len(articles_to_analyze)} articles found - may not be enough for comprehensive analysis")
        
        # ===== GENERATE INDIVIDUAL SUMMARIES FOR EACH ARTICLE (FIGURE ANALYSIS) =====
        llm = LLMGenerator()
        await generate_article_summaries(articles_to_analyze, db, llm)
        
        # ===== GENERATE COMPREHENSIVE SUMMARY FROM ALL INDIVIDUAL SUMMARIES =====
        logger.info("🔄 Creating comprehensive summary from article summaries (FIGURE)...")
        comprehensive_summary = await generate_summary_of_summaries(
            articles_to_analyze, 
            llm, 
            request.figure,
            "figure"
        )
        logger.info(f"✅ Comprehensive summary created: {len(comprehensive_summary)} characters")
        
        # ===== PREPARE ARTICLES FOR COMPREHENSIVE ANALYSIS =====
        articles_text = []
        
        logger.info(f"Preparing {len(articles_to_analyze)} articles for comprehensive LLM analysis")
        
        for idx, article in enumerate(articles_to_analyze, 1):
            title = article.get('title', 'No title')
            content = article.get('content', article.get('preview', ''))
            date = article.get('date', 'No date')
            source = article.get('source', 'Unknown')
            
            # Format article with clear structure
            article_text = f"""
Article #{idx}
Date: {date}
Source: {source}
Title: {title}
Content: {content}
---
"""
            articles_text.append(article_text)
        
        # Create comprehensive prompt for figure analysis
        prompt = f"""You are analyzing {len(articles_to_analyze)} most recent news articles about {request.figure}.

Provide a comprehensive analysis in the following format. Start with KEYWORDS and TOPICS sections:

**TOP_KEYWORDS**
[Provide exactly 10 most relevant keywords, comma-separated, in order of importance]

**TOPICS_COVERED**
[Provide 5-7 main topics/themes covered in these articles, comma-separated]

**SUMMARY**
[A concise 2-3 paragraph summary of this person's recent activities, role, and major developments based on these articles]

**Profile & Role**
[Analysis here]

**Key Activities**
[Analysis here]

**Policy Positions**
[Analysis here]

**Political Relationships**
[Analysis here]

**Public Image**
[Analysis here]

**Recent Developments**
[Analysis here]

**Notable Quotes**
[3-5 significant quotes here]

=== ARTICLES TO ANALYZE ({len(articles_to_analyze)} articles) ===
{chr(10).join(articles_text)}

Provide ONLY the structured analysis. Do NOT include introductory text like "Based on the provided articles" or "Here is my analysis". Start directly with the first section heading.
"""
        
        system_prompt = """You are a political analyst for Bangladesh politics. Provide direct, structured analysis without preambles or meta-commentary. Start immediately with the analysis sections."""
        
        # Log the request details
        logger.info(f"🤖 LLM REQUEST DETAILS:")
        logger.info(f"  - Entity: {request.figure}")
        logger.info(f"  - Articles to analyze: {len(articles_to_analyze)}")
        logger.info(f"  - Date range: {request.start_date or 'N/A'} to {request.end_date or 'N/A'}")
        logger.info(f"  - Prompt length: {len(prompt)} characters")
        logger.info(f"  - System prompt: {system_prompt}")
        
        # Print the full prompt to terminal
        logger.info("=" * 80)
        logger.info("📝 FULL PROMPT SENT TO LLM:")
        logger.info("=" * 80)
        logger.info(f"\n{prompt}\n")
        logger.info("=" * 80)
        
        try:
            analysis_result = llm._call_llm(
                prompt=prompt,
                system_prompt=system_prompt
            )
            
            logger.info("=" * 80)
            logger.info("✅ LLM RESPONSE RECEIVED (FIGURE ANALYSIS):")
            logger.info("=" * 80)
            logger.info(f"  - Response length: {len(analysis_result)} characters")
            logger.info(f"\n{analysis_result}\n")
            logger.info("=" * 80)
            
        except ValueError as ve:
            # Handle Gemini safety filters or other content issues
            logger.error(f"LLM content generation failed: {ve}")
            
            # Provide a fallback analysis based on available data
            analysis_result = f"""**Profile & Role**
{request.figure} is mentioned in {len(articles_to_analyze)} articles from {', '.join(set([a.get('source', 'Unknown') for a in articles_to_analyze]))}.

**Limited Data Notice**
Only {len(articles_to_analyze)} articles were found. A comprehensive analysis requires more data. The LLM analysis could not be generated due to content restrictions.

**Article Summary**
- Total articles: {len(articles_to_analyze)}
- Date range: {min([a.get('date', '') for a in articles_to_analyze if a.get('date')], default='N/A')} to {max([a.get('date', '') for a in articles_to_analyze if a.get('date')], default='N/A')}
- Sources: {', '.join(set([a.get('source', 'Unknown') for a in articles_to_analyze]))}

**Recent Headlines**
{chr(10).join(['- ' + a.get('title', 'No title') for a in articles_to_analyze[:5]])}

**Recommendation**
Try adjusting the date range or search parameters to find more articles for a comprehensive analysis.
"""
            logger.info("Using fallback analysis due to LLM error")
        
        # Extract keywords, topics, and summary from LLM response
        extracted = extract_llm_sections(analysis_result)
        
        logger.info(f"📊 Extracted Analysis Components:")
        logger.info(f"  - Keywords: {extracted['keywords'][:5]}..." if len(extracted['keywords']) > 5 else f"  - Keywords: {extracted['keywords']}")
        logger.info(f"  - Topics: {extracted['topics']}")
        logger.info(f"  - Summary length: {len(extracted['summary'])} chars")
        
        # Structure the analysis response
        # Fix: parties field can be a list, so we need to handle it properly
        associated_parties = []
        for a in articles_to_analyze:
            parties = a.get('parties', [])
            # Handle both list and string formats
            if isinstance(parties, list):
                associated_parties.extend(parties)
            elif isinstance(parties, str) and parties:
                associated_parties.append(parties)
        
        # Save AI summary to persistent storage
        try:
            associated_party = list(set(associated_parties))[0] if associated_parties else None
            summary_store.save_figure_summary(
                figure_name=request.figure,
                keywords=extracted['keywords'],
                topics=extracted['topics'],
                summary=extracted['summary'],
                articles_analyzed=len(articles_to_analyze),
                associated_party=associated_party
            )
            logger.info(f"💾 Saved AI summary for figure: {request.figure}")
        except Exception as e:
            logger.error(f"Failed to save figure summary: {e}")
        
        analysis = {
            "raw_analysis": analysis_result,
            "keywords": extracted['keywords'],
            "topics": extracted['topics'],
            "summary": extracted['summary'],
            "comprehensive_summary": comprehensive_summary,  # NEW: Summary of all article summaries
            "articles_count": len(articles_to_analyze),
            "date_range": {
                "earliest": min([a.get('date', '') for a in articles_to_analyze if a.get('date')], default='N/A'),
                "latest": max([a.get('date', '') for a in articles_to_analyze if a.get('date')], default='N/A')
            },
            "sources": list(set([a.get('source', 'Unknown') for a in articles_to_analyze])),
            "associated_parties": list(set(associated_parties)) if associated_parties else [],
            "sample_titles": [a.get('title', 'No title') for a in articles_to_analyze[:5]],
            # NEW: Include article summaries (all analyzed articles with their summaries)
            "article_summaries": [
                {
                    "title": a.get('title', 'No title'),
                    "date": a.get('date', 'No date'),
                    "source": a.get('source', 'Unknown'),
                    "summary": a.get('summary', 'Summary not available'),
                    "url": a.get('url', '')
                }
                for a in articles_to_analyze
            ]
        }
        
        processing_time = time.time() - start_time
        logger.info(f"Figure analysis completed in {processing_time:.2f}s")
        
        return AnalysisResponse(
            success=True,
            party_or_figure=request.figure,
            total_articles_analyzed=len(articles_to_analyze),
            date_range=analysis["date_range"],
            analysis=analysis,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Failed to analyze figure articles: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )

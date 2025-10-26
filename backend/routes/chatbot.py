"""
Chatbot API Routes

Intelligent chatbot endpoint for answering research questions
about Bangladesh politics using RAG with gpt-4o-mini.

Features:
- LLM-based query classification
- Smart article retrieval
- Context-aware answer generation
- Support for complex research questions

Author: RAG-IR System
"""

import logging
import time
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, status, Depends

from backend.core.vector_db import VectorDatabase
from backend.core.query_classifier import LLMQueryClassifier
from backend.core.optimized_retrieval import OptimizedRetriever
from backend.core.llm_generation import LLMGenerator
from backend.auth import require_auth

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/chatbot", tags=["Chatbot"], dependencies=[Depends(require_auth)])

# Initialize components (will be set in main.py or startup)
vector_db: Optional[VectorDatabase] = None
classifier: Optional[LLMQueryClassifier] = None
retriever: Optional[OptimizedRetriever] = None
answer_generator: Optional[LLMGenerator] = None


# Request/Response Models
class ChatRequest(BaseModel):
    """Request model for chatbot queries."""
    query: str = Field(..., description="User question/query")
    top_k: int = Field(20, description="Number of articles to retrieve")
    include_sources: bool = Field(True, description="Include source articles in response")
    language: Optional[str] = Field(None, description="Preferred language for answer (English/Bangla)")


class SourceArticle(BaseModel):
    """Source article information."""
    title: str
    date: str
    source: str
    url: Optional[str] = None
    relevance_score: Optional[float] = None


class ChatResponse(BaseModel):
    """Response model for chatbot queries."""
    query: str = Field(..., description="Original query")
    answer: str = Field(..., description="Generated answer")
    intent: Dict[str, Any] = Field(..., description="Classified query intent")
    sources: List[SourceArticle] = Field(default_factory=list, description="Source articles used")
    total_articles_retrieved: int = Field(0, description="Total articles retrieved")
    processing_time: float = Field(0.0, description="Total processing time in seconds")
    model_used: str = Field("gpt-4o-mini", description="Model used for generation")


def initialize_chatbot_components():
    """Initialize chatbot components."""
    global vector_db, classifier, retriever, answer_generator
    
    try:
        # Initialize VectorDatabase
        logger.info("Initializing VectorDatabase...")
        vector_db = VectorDatabase(
            persist_directory="./chroma_db",
            collection_name="political_articles"
        )
        
        # Initialize Query Classifier with gpt-4o-mini
        logger.info("Initializing LLMQueryClassifier with gpt-4o-mini...")
        classifier = LLMQueryClassifier(model="gpt-4o-mini")
        
        # Initialize Retriever
        logger.info("Initializing OptimizedRetriever...")
        retriever = OptimizedRetriever(
            vector_db=vector_db,
            classifier=classifier
        )
        
        # Initialize Answer Generator with gpt-4o-mini
        logger.info("Initializing Answer Generator with gpt-4o-mini...")
        answer_generator = LLMGenerator(
            model="gpt-4o-mini",
            temperature=0.3,  # Balanced creativity
            max_tokens=2000  # Long answers for complex questions
        )
        
        logger.info("✓ Chatbot components initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize chatbot components: {e}")
        raise


@router.post("/chat", response_model=ChatResponse, summary="Chat with Political News Chatbot")
async def chat(request: ChatRequest):
    """
    Intelligent chatbot for answering questions about Bangladesh politics.
    
    Uses:
    - gpt-4o-mini for query classification
    - ChromaDB for vector search
    - gpt-4o-mini for answer generation    Supports:
    - Simple queries: "What did BNP say about elections?"
    - Comparison: "Compare BNP and JI positions"
    - Trend analysis: "How has security situation changed?"
    - Complex research questions
    - English and Bangla queries
    
    Args:
        request: ChatRequest with query and options
    
    Returns:
        ChatResponse with answer, sources, and metadata
    """
    
    start_time = time.time()
    
    # Check if components are initialized
    if not all([vector_db, classifier, retriever, answer_generator]):
        initialize_chatbot_components()
    
    try:
        logger.info(f"Processing query: {request.query[:100]}...")
        
        # Step 1: Classify Query
        logger.info("Step 1: Classifying query...")
        intent = await classifier.classify_query(request.query)
        logger.info(f"Query classified: type={intent['type']}, "
                   f"entities={intent['entities']}, topics={intent['topics']}")
        
        # Step 2: Retrieve Relevant Articles
        logger.info("Step 2: Retrieving relevant articles...")
        retrieval_result = await retriever.retrieve_for_chatbot(
            query=request.query,
            top_k=request.top_k,
            rerank=True
        )
        
        articles = retrieval_result['articles']
        logger.info(f"Retrieved {len(articles)} articles")
        
        if not articles:
            # No articles found - Generate answer using LLM's general knowledge
            logger.warning("No articles found. Using LLM general knowledge...")
            answer = await generate_answer(
                query=request.query,
                context="No specific articles found in database.",
                intent=intent,
                language=request.language
            )
            
            return ChatResponse(
                query=request.query,
                answer=answer,
                intent=intent,
                sources=[],
                total_articles_retrieved=0,
                processing_time=time.time() - start_time,
                model_used="gpt-4o-mini"
            )
        
        # Step 3: Prepare Context
        logger.info("Step 3: Preparing context from articles...")
        context = prepare_context_from_articles(articles, max_tokens=6000)
        
        # Step 4: Generate Answer
        logger.info("Step 4: Generating answer with gpt-4o-mini...")
        answer = await generate_answer(
            query=request.query,
            context=context,
            intent=intent,
            language=request.language
        )
        
        # Step 5: Prepare Source Articles
        sources = []
        if request.include_sources:
            for article in articles[:10]:  # Top 10 sources
                # Extract from metadata if not in top-level
                metadata = article.get('metadata', {})
                title = article.get('title') or metadata.get('title', 'N/A')
                date = article.get('date') or metadata.get('date', 'N/A')
                source = article.get('source') or metadata.get('source', 'N/A')
                url = article.get('url') or metadata.get('url')
                
                sources.append(SourceArticle(
                    title=title,
                    date=date,
                    source=source,
                    url=url,
                    relevance_score=article.get('rerank_score') or article.get('relevance_score')
                ))
        
        processing_time = time.time() - start_time
        logger.info(f"✓ Query processed successfully in {processing_time:.2f}s")
        
        return ChatResponse(
            query=request.query,
            answer=answer,
            intent=intent,
            sources=sources,
            total_articles_retrieved=len(articles),
            processing_time=processing_time,
            model_used="gpt-4o-mini"
        )
        
    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process query: {str(e)}"
        )


def prepare_context_from_articles(
    articles: List[Dict],
    max_tokens: int = 6000
) -> str:
    """
    Prepare context text from retrieved articles.
    
    Args:
        articles: List of article dictionaries
        max_tokens: Maximum tokens to use (~4 chars per token)
    
    Returns:
        Formatted context string
    """
    
    context_parts = []
    total_chars = 0
    max_chars = max_tokens * 4  # Rough estimate
    
    for i, article in enumerate(articles, 1):
        # Extract metadata properly
        metadata = article.get('metadata', {})
        title = article.get('title') or metadata.get('title', 'N/A')
        date = article.get('date') or metadata.get('date', 'N/A')
        source = article.get('source') or metadata.get('source', 'N/A')
        
        # Get document/content
        content = article.get('document') or article.get('content') or article.get('text', '')
        
        # Prepare article summary
        article_text = f"""
Article {i}:
Title: {title}
Date: {date}
Source: {source}
Parties: {', '.join(article.get('parties', [])) if article.get('parties') else 'N/A'}
People: {', '.join(article.get('people', [])) if article.get('people') else 'N/A'}

Content: {content[:1000]}...

---
"""
        
        # Check token limit
        if total_chars + len(article_text) > max_chars:
            break
        
        context_parts.append(article_text)
        total_chars += len(article_text)
    
    return '\n'.join(context_parts)


async def generate_answer(
    query: str,
    context: str,
    intent: Dict,
    language: Optional[str] = None
) -> str:
    """
    Generate answer using LLM with context.
    
    Args:
        query: User query
        context: Article context
        intent: Query classification intent
        language: Preferred language
    
    Returns:
        Generated answer
    """
    
    # Determine answer language
    if language:
        lang_instruction = f"Answer in {language}."
    elif intent.get('raw_query', '').encode('utf-8').decode('utf-8', 'ignore') != intent.get('raw_query', ''):
        # Query contains non-ASCII (likely Bangla)
        lang_instruction = "Answer in Bangla (বাংলায় উত্তর দিন)."
    else:
        lang_instruction = "Answer in English."
    
    # Customize prompt based on query type
    query_type = intent.get('type', 'general')
    
    if query_type == 'comparison':
        task_instruction = "Compare the entities mentioned, highlighting similarities and differences."
    elif intent.get('trend_analysis'):
        task_instruction = "Analyze trends and changes over time, showing how the situation evolved."
    elif query_type == 'entity_focus':
        task_instruction = "Focus on the specific entity's actions, statements, and positions."
    else:
        task_instruction = "Provide a comprehensive answer based on the articles."
    
    system_prompt = """You are an expert political analyst specializing in Bangladesh politics.

Your task is to answer questions based on the provided news articles about ALL political parties and figures in Bangladesh.

Guidelines:
1. PRIMARY: Base your answer on the provided articles whenever possible
2. Cite specific articles when making claims (e.g., "According to Daily Star on Oct 15...")
3. IMPORTANT: If the specific question is not directly answered in the articles:
   - Provide general context based on what IS in the articles
   - Use your knowledge of Bangladesh politics to give a helpful answer
   - Clearly indicate: "While the specific details aren't in these articles, based on the political context..."
4. For general questions (e.g., "security risks", "political reforms"):
   - Extract relevant themes and patterns from available articles
   - Synthesize information to answer the broader question
   - Don't just say "articles don't contain this" - be helpful!
5. Be objective and balanced - present ALL parties' perspectives equally
6. For comparison questions, structure similarities and differences clearly
7. For trend questions, show chronological progression
8. Keep answers concise but comprehensive (2-3 paragraphs for simple queries, more for complex ones)
9. If NO relevant articles are provided, acknowledge this and provide a brief general overview using your knowledge
"""

    user_prompt = f"""Question: {query}

{lang_instruction}
{task_instruction}

Relevant Articles:
{context}

Answer:"""

    # Generate answer
    answer = answer_generator._call_llm(
        prompt=user_prompt,
        system_prompt=system_prompt,
        temperature=0.3,
        max_tokens=2000
    )
    
    return answer.strip()


# Health check endpoint
@router.get("/health", summary="Check chatbot health")
async def chatbot_health():
    """Check if chatbot components are initialized."""
    
    components_status = {
        'vector_db': vector_db is not None,
        'classifier': classifier is not None,
        'retriever': retriever is not None,
        'answer_generator': answer_generator is not None
    }
    
    all_ready = all(components_status.values())
    
    return {
        'status': 'ready' if all_ready else 'not_ready',
        'components': components_status,
        'model': 'gpt-4o-mini',
        'article_count': vector_db.collection.count() if vector_db else 0
    }

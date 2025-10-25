"""
Optimized Retrieval Module

Smart retrieval for full articles (NO chunking needed).
Uses intelligent filtering, re-ranking, and query classification.

Strategy:
1. Classify query intent
2. Apply smart filters
3. Semantic search with ChromaDB
4. Re-rank by relevance + importance + recency
5. Return top-k results

Author: RAG-IR System
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from backend.core.vector_db import VectorDatabase
from backend.core.query_classifier import LLMQueryClassifier
from backend.core.llm_generation import LLMGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OptimizedRetriever:
    """
    Smart retrieval system without chunking.
    
    Uses full articles with intelligent filtering and re-ranking.
    Designed for 5k-100k+ articles.
    """
    
    def __init__(
        self,
        vector_db: VectorDatabase,
        classifier: Optional[LLMQueryClassifier] = None,
        model: str = "gpt-4o-mini"
    ):
        """
        Initialize the optimized retriever.
        
        Args:
            vector_db: VectorDatabase instance
            classifier: Query classifier (optional, will create with gpt-4o-mini if None)
            model: Model to use for classification (default: gpt-4o-mini)
        """
        self.vector_db = vector_db
        
        # Initialize classifier if not provided
        if classifier is None:
            classifier = LLMQueryClassifier(model=model)
            logger.info(f"Created LLMQueryClassifier with model: {model}")
        
        self.classifier = classifier
        
        logger.info("OptimizedRetriever initialized with gpt-4o-mini")
    
    async def retrieve_for_chatbot(
        self,
        query: str,
        filters: Optional[Dict] = None,
        top_k: int = 20,
        rerank: bool = True
    ) -> Dict[str, Any]:
        """
        Main retrieval method for chatbot queries.
        
        Args:
            query: User query string
            filters: Optional filters (parties, people, dates, etc.)
            top_k: Number of results to return
            rerank: Whether to re-rank results
        
        Returns:
            {
                'query': str,
                'intent': Dict,  # Classification result
                'articles': List[Dict],  # Retrieved articles
                'total_retrieved': int,
                'strategy': str,  # Retrieval strategy used
                'processing_time': float
            }
        """
        
        start_time = datetime.now()
        
        # Step 1: Classify query intent
        if self.classifier:
            intent = await self.classifier.classify_query(query)
            logger.info(f"Query classified: type={intent['type']}, "
                       f"method={intent['classification_method']}")
        else:
            # No classifier - use simple intent
            intent = {
                'type': 'general',
                'entities': [],
                'topics': [],
                'time_constraint': None,
                'comparison': False,
                'complexity': 'simple',
                'confidence': 0.5,
                'classification_method': 'none'
            }
        
        # Step 2: Build enhanced filters
        enhanced_filters = self._build_enhanced_filters(
            query=query,
            intent=intent,
            base_filters=filters
        )
        
        logger.info(f"Enhanced filters: {enhanced_filters}")
        
        # Step 3: Determine retrieval strategy
        strategy = self._select_strategy(intent)
        logger.info(f"Using retrieval strategy: {strategy}")
        
        # Step 4: Retrieve articles
        retrieve_n = top_k * 2 if rerank else top_k  # Get extra for re-ranking
        
        articles = self._retrieve_articles(
            query=query,
            filters=enhanced_filters,
            n_results=retrieve_n,
            strategy=strategy
        )
        
        logger.info(f"Retrieved {len(articles)} articles before re-ranking")
        
        # Step 5: Re-rank if enabled
        if rerank and articles:
            articles = self._rerank_results(
                articles=articles,
                query=query,
                intent=intent
            )
            articles = articles[:top_k]  # Take top-k after re-ranking
            logger.info(f"Re-ranked to {len(articles)} articles")
        
        # Step 6: Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            'query': query,
            'intent': intent,
            'articles': articles,
            'total_retrieved': len(articles),
            'strategy': strategy,
            'processing_time': processing_time
        }
    
    def _build_enhanced_filters(
        self,
        query: str,
        intent: Dict,
        base_filters: Optional[Dict]
    ) -> Dict[str, Any]:
        """
        Build enhanced filters based on query intent.
        
        Args:
            query: User query
            intent: Classification result
            base_filters: Base filters from user
        
        Returns:
            Enhanced filter dictionary
        """
        filters = base_filters.copy() if base_filters else {}
        
        # Add entity filters
        if intent['entities']:
            # Check if entities are parties or people
            parties = []
            people = []
            
            for entity in intent['entities']:
                # Simple heuristic: check if entity is all caps (likely party)
                if entity.isupper() or entity in ['Interim Government']:
                    parties.append(entity)
                else:
                    people.append(entity)
            
            if parties:
                filters['parties'] = parties
            if people:
                filters['people'] = people
        
        # Add time filters
        if intent['time_constraint']:
            time_info = intent['time_constraint']
            filters['start_date'] = time_info['start']
            filters['end_date'] = time_info['end']
        
        # Add topic filters (as themes)
        if intent['topics']:
            filters['themes'] = intent['topics']
        
        return filters
    
    def _select_strategy(self, intent: Dict) -> str:
        """
        Select retrieval strategy based on intent.
        
        Args:
            intent: Classification result
        
        Returns:
            Strategy name
        """
        if intent['comparison']:
            return 'comparison'
        elif intent['type'] == 'entity_focus':
            return 'entity_focused'
        elif intent['type'] == 'topic_focus':
            return 'topic_focused'
        elif intent['time_constraint']:
            return 'time_range'
        else:
            return 'general_search'
    
    def _retrieve_articles(
        self,
        query: str,
        filters: Dict,
        n_results: int,
        strategy: str
    ) -> List[Dict]:
        """
        Retrieve articles using vector DB.
        
        Args:
            query: Search query
            filters: Filter dictionary
            n_results: Number of results
            strategy: Retrieval strategy
        
        Returns:
            List of article dictionaries
        """
        
        try:
            # Use VectorDatabase retrieve_similar_articles method
            results = self.vector_db.retrieve_similar_articles(
                query=query,
                top_k=n_results,  # Fixed: parameter name is top_k, not n_results
                filter_parties=filters.get('parties'),
                filter_people=filters.get('people'),
                filter_date_from=filters.get('start_date'),
                filter_date_to=filters.get('end_date'),
                filter_themes=filters.get('themes'),
                filter_category=filters.get('categories'),
                filter_is_speech=filters.get('is_speech'),
                filter_language=filters.get('language')
            )
            
            # Fallback: If no results with filters, try without filters
            if len(results) == 0 and (filters.get('themes') or filters.get('parties') or filters.get('people')):
                logger.warning(f"No results with filters. Trying without filters...")
                results = self.vector_db.retrieve_similar_articles(
                    query=query,
                    top_k=n_results,
                    filter_date_from=filters.get('start_date'),
                    filter_date_to=filters.get('end_date'),
                    filter_language=filters.get('language')
                )
                logger.info(f"Fallback retrieval returned {len(results)} articles")
            
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving articles: {e}")
            return []
    
    def _rerank_results(
        self,
        articles: List[Dict],
        query: str,
        intent: Dict
    ) -> List[Dict]:
        """
        Re-rank results by relevance + importance + recency.
        
        Scoring factors:
        1. Semantic similarity (from vector search) - 40%
        2. Article importance (speeches > analysis > news) - 30%
        3. Recency (newer = better) - 20%
        4. LLM analysis completeness - 10%
        
        Args:
            articles: Retrieved articles
            query: Original query
            intent: Query intent
        
        Returns:
            Re-ranked articles
        """
        
        scored_articles = []
        
        for article in articles:
            score = 0.0
            
            # 1. Semantic similarity (already in article if available)
            similarity = article.get('similarity_score', 0.5)
            score += similarity * 0.4
            
            # 2. Article importance
            importance_score = 0.0
            if article.get('is_speech'):
                importance_score = 1.0  # Speeches most important
            elif article.get('is_stance'):
                importance_score = 0.8  # Stance articles important
            elif article.get('llm_summary'):
                importance_score = 0.6  # LLM-analyzed articles
            else:
                importance_score = 0.4  # Regular news
            
            score += importance_score * 0.3
            
            # 3. Recency
            recency_score = self._calculate_recency_score(
                article_date=article.get('date'),
                intent=intent
            )
            score += recency_score * 0.2
            
            # 4. LLM analysis completeness
            completeness = 0.0
            if article.get('llm_summary'):
                completeness += 0.4
            if article.get('llm_keywords'):
                completeness += 0.3
            if article.get('llm_topics'):
                completeness += 0.3
            
            score += completeness * 0.1
            
            # Store score with article
            article['rerank_score'] = score
            scored_articles.append((score, article))
        
        # Sort by score (descending)
        scored_articles.sort(key=lambda x: x[0], reverse=True)
        
        # Return articles (without scores)
        return [article for score, article in scored_articles]
    
    def _calculate_recency_score(
        self,
        article_date: Optional[str],
        intent: Dict
    ) -> float:
        """
        Calculate recency score based on article date.
        
        Args:
            article_date: Article date string (YYYY-MM-DD)
            intent: Query intent
        
        Returns:
            Recency score (0.0-1.0)
        """
        
        if not article_date:
            return 0.5  # Neutral score
        
        try:
            # Parse article date
            article_dt = datetime.strptime(article_date, '%Y-%m-%d')
            now = datetime.now()
            days_old = (now - article_dt).days
            
            # If query has time constraint, prioritize articles in that range
            if intent.get('time_constraint'):
                time_range_days = intent['time_constraint'].get('days', 7)
                if days_old <= time_range_days:
                    return 1.0  # Perfect match
                elif days_old <= time_range_days * 2:
                    return 0.7  # Close match
            
            # General recency scoring
            if days_old <= 7:
                return 1.0
            elif days_old <= 30:
                return 0.8
            elif days_old <= 90:
                return 0.6
            elif days_old <= 180:
                return 0.4
            else:
                return 0.2
            
        except Exception as e:
            logger.warning(f"Error parsing date {article_date}: {e}")
            return 0.5
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get retriever statistics.
        
        Returns:
            Statistics dictionary
        """
        
        return {
            'vector_db_count': self.vector_db.collection.count(),
            'has_classifier': self.classifier is not None,
            'classification_method': 'hybrid' if self.classifier else 'none'
        }


# Example usage
async def test_retriever():
    """Test the optimized retriever with GPT-5-nano."""
    
    # Initialize components
    vector_db = VectorDatabase(
        persist_directory="./chroma_db",
        collection_name="political_articles"
    )
    
    retriever = OptimizedRetriever(
        vector_db=vector_db,
        model="gpt-4o-mini"  # Use gpt-4o-mini
    )
    
    # Test query
    query = "What did Tareq Rahman say about election reforms?"
    
    print("=" * 80)
    print("OPTIMIZED RETRIEVER TEST")
    print("=" * 80)
    print(f"\nQuery: {query}")
    
    result = await retriever.retrieve_for_chatbot(
        query=query,
        top_k=10,
        rerank=True
    )
    
    print(f"\nIntent: {result['intent']['type']}")
    print(f"Entities: {result['intent']['entities']}")
    print(f"Topics: {result['intent']['topics']}")
    print(f"Strategy: {result['strategy']}")
    print(f"Retrieved: {result['total_retrieved']} articles")
    print(f"Processing Time: {result['processing_time']:.3f}s")
    
    print(f"\nTop 5 Articles:")
    for i, article in enumerate(result['articles'][:5], 1):
        print(f"\n{i}. {article.get('title', 'N/A')[:80]}")
        print(f"   Date: {article.get('date', 'N/A')}")
        print(f"   Score: {article.get('rerank_score', 0):.3f}")
        print(f"   Parties: {article.get('parties', [])}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_retriever())

"""
Query Classification Module - LLM-Based

Purely LLM-based approach for accurate query understanding.
Uses gpt-5-nano for intelligent query classification and intent extraction.

Strategy:
- LLM classification for all queries (no rule-based fallback)
- gpt-5-nano for fast and accurate intent detection
- Handles any query type including complex research questions

Author: RAG-IR System
"""

import re
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from backend.core.scraping import POLITICAL_ENTITIES
from backend.core.llm_generation import LLMGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMQueryClassifier:
    """
    Pure LLM-based query classifier for accurate intent detection.
    
    Uses gpt-5-nano for intelligent query understanding.
    NO manual rules, NO keyword matching - 100% LLM-powered.
    """
    
    def __init__(self, model: str = "gpt-5-nano"):
        """
        Initialize the pure LLM-based query classifier.
        
        Args:
            model: LLM model to use (default: gpt-5-nano)
        """
        # Create LLM generator with gpt-5-nano
        self.llm = LLMGenerator(
            model=model,
            temperature=0.1,  # Low temperature for consistent classification
            max_tokens=500  # Short responses for classification
        )
        logger.info(f"Created new LLMGenerator with model: {model}")
        
        # Load entity names for LLM prompt (metadata only, no manual detection)
        self.entities = list(POLITICAL_ENTITIES.keys())
        
        # Define available topics for LLM (metadata only)
        self.topics = [
            'Election', 'Reform', 'Democracy', 'Economy', 
            'Human Rights', 'Judiciary', 'Law and Order',
            'Security', 'Coalition', 'Foreign Relations'
        ]
        
        logger.info(f"LLMQueryClassifier initialized")
        logger.info(f"Model: {self.llm.model}")
        logger.info(f"Mode: 100% LLM-powered (no manual rules)")
        logger.info(f"Available entities: {len(self.entities)}")
        logger.info(f"Available topics: {len(self.topics)}")
    
    async def classify_query(self, query: str) -> Dict[str, Any]:
        """
        Main LLM-based classification method.
        
        Args:
            query: User query string (can be in English or Bangla)
        
        Returns:
            Classification result dictionary:
            {
                'type': str,  # entity_focus | topic_focus | comparison | time_range | trend_analysis | general
                'entities': List[str],  # Detected political entities
                'topics': List[str],  # Detected topics/themes
                'time_constraint': Optional[Dict],  # Time range if specified
                'comparison': bool,  # Is comparison query
                'trend_analysis': bool,  # Is trend/timeline analysis
                'complexity': str,  # simple | medium | complex
                'confidence': float,  # 0.0-1.0
                'classification_method': str,  # llm
                'raw_query': str  # Original query
            }
        """
        
        if not query or not query.strip():
            return self._empty_classification()
        
        try:
            logger.info(f"Classifying query with LLM: {query[:100]}...")
            
            # Use LLM for classification
            llm_result = await self._classify_with_llm(query)
            llm_result['classification_method'] = 'llm'
            llm_result['raw_query'] = query
            
            logger.info(f"LLM classification complete: type={llm_result['type']}, "
                       f"confidence={llm_result['confidence']:.2f}, "
                       f"entities={llm_result['entities']}, "
                       f"topics={llm_result['topics']}")
            
            return llm_result
            
        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
            # Return basic classification on error
            return {
                'type': 'general',
                'entities': [],
                'topics': [],
                'time_constraint': None,
                'comparison': False,
                'trend_analysis': False,
                'complexity': 'medium',
                'confidence': 0.3,
                'classification_method': 'error_fallback',
                'raw_query': query,
                'error': str(e)
            }
    
    async def _classify_with_llm(self, query: str) -> Dict[str, Any]:
        """
        LLM-based classification using gpt-5-nano.
        
        Args:
            query: User query string (English or Bangla)
        
        Returns:
            Classification result from LLM
        """
        
        # Prepare entity and topic lists for prompt
        entity_list = ', '.join(self.entities[:30])  # First 30 entities
        topic_list = ', '.join(self.topics)
        
        system_prompt = """You are an expert query intent classifier for a Bangladesh political news RAG system.

Your task is to analyze user queries and extract:
1. Query type (entity_focus, topic_focus, comparison, time_range, trend_analysis, general)
2. Political entities mentioned (parties, figures)
3. Topics/themes discussed
4. Time constraints if any
5. Whether it's a comparison or trend analysis query

Be intelligent about:
- Understanding both English and Bangla queries
- Mapping informal names to official entities (e.g., "Tareq" → "Tareq Rahman", "acting chairman" → "Tareq Rahman")
- Detecting implicit time references ("recent", "latest", "this month")
- Identifying research-style questions (e.g., "What are the main actors?", "How has X changed?")

Return ONLY valid JSON with no markdown formatting."""

        user_prompt = f"""Available Political Entities in Database:
{entity_list}... and others

Available Topics/Themes:
{topic_list}

Query to Classify: "{query}"

Return JSON in this exact format:
{{
  "type": "entity_focus | topic_focus | comparison | time_range | trend_analysis | general",
  "entities": ["list of exact entity names from database"],
  "topics": ["list of relevant topics"],
  "time_constraint": {{"period": "recent|today|week|month|quarter|custom", "days": 7, "start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}} or null,
  "comparison": true or false,
  "trend_analysis": true or false,
  "complexity": "simple | medium | complex",
  "confidence": 0.9,
  "reasoning": "brief explanation of classification"
}}

Classification Guidelines:
- type="entity_focus": Query about specific party/figure (e.g., "What did BNP say?")
- type="topic_focus": Query about general topic (e.g., "Election reform news")
- type="comparison": Comparing multiple entities (e.g., "Compare NCP and JI")
- type="time_range": Primarily about specific time period (e.g., "Articles from August")
- type="trend_analysis": Changes over time (e.g., "How has political situation changed?")
- type="general": Unclear or broad query

- comparison=true: When comparing 2+ entities
- trend_analysis=true: When asking about changes/trends over time periods
- confidence: High (0.8-1.0) if clear, Medium (0.5-0.7) if somewhat clear, Low (0.3-0.4) if ambiguous

Important:
- For Bangla queries, translate intent to English entity names
- Extract dates/time periods mentioned (Aug 2024, Oct 2025, "last month", etc.)
- Identify all mentioned entities even if not explicitly named (e.g., "interim government advisors" → "Interim Government")"""

        # Call LLM
        response = self.llm._call_llm(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.1,  # Very low for consistent classification
            max_tokens=500
        )
        
        # Parse JSON response
        try:
            # Try direct JSON parsing
            result = json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code block
            json_match = re.search(
                r'```(?:json)?\s*(\{.*?\})\s*```',
                response,
                re.DOTALL
            )
            if json_match:
                result = json.loads(json_match.group(1))
            else:
                # Try to find any JSON object in response
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(0))
                else:
                    logger.error(f"Failed to parse LLM response: {response}")
                    raise ValueError(f"Failed to parse LLM response as JSON")
        
        # Ensure all required fields exist
        result.setdefault('type', 'general')
        result.setdefault('entities', [])
        result.setdefault('topics', [])
        result.setdefault('time_constraint', None)
        result.setdefault('comparison', False)
        result.setdefault('trend_analysis', False)
        result.setdefault('complexity', 'medium')
        result.setdefault('confidence', 0.8)
        result.setdefault('reasoning', '')
        
        # Validate and clean entity names
        result['entities'] = self._validate_entities(result['entities'])
        
        # Parse time constraint if present
        if result['time_constraint']:
            result['time_constraint'] = self._parse_time_constraint(
                result['time_constraint']
            )
        
        return result
    
    def _validate_entities(self, entities: List[str]) -> List[str]:
        """
        Validate and clean entity names against known entities.
        
        Args:
            entities: List of entity names from LLM
        
        Returns:
            Cleaned list of valid entity names
        """
        validated = []
        entity_lower_map = {e.lower(): e for e in self.entities}
        
        for entity in entities:
            # Direct match
            if entity in self.entities:
                validated.append(entity)
            # Case-insensitive match
            elif entity.lower() in entity_lower_map:
                validated.append(entity_lower_map[entity.lower()])
            # Partial match
            else:
                for known_entity in self.entities:
                    if entity.lower() in known_entity.lower() or known_entity.lower() in entity.lower():
                        validated.append(known_entity)
                        break
        
        return list(set(validated))  # Remove duplicates
    
    def _parse_time_constraint(self, time_data: Dict) -> Dict:
        """
        Parse and standardize time constraint data.
        
        Args:
            time_data: Time constraint dictionary from LLM
        
        Returns:
            Standardized time constraint dictionary
        """
        now = datetime.now()
        
        period = time_data.get('period', 'recent')
        days = time_data.get('days', 7)
        
        # Calculate dates if not provided
        if not time_data.get('start') or not time_data.get('end'):
            if period == 'today':
                start = end = now.strftime('%Y-%m-%d')
            elif period == 'week':
                start = (now - timedelta(days=7)).strftime('%Y-%m-%d')
                end = now.strftime('%Y-%m-%d')
            elif period == 'month':
                start = (now - timedelta(days=30)).strftime('%Y-%m-%d')
                end = now.strftime('%Y-%m-%d')
            elif period == 'quarter':
                start = (now - timedelta(days=90)).strftime('%Y-%m-%d')
                end = now.strftime('%Y-%m-%d')
            else:  # recent or custom
                start = (now - timedelta(days=days)).strftime('%Y-%m-%d')
                end = now.strftime('%Y-%m-%d')
        else:
            start = time_data.get('start')
            end = time_data.get('end')
        
        return {
            'period': period,
            'days': days,
            'start': start,
            'end': end
        }
    
    def _empty_classification(self) -> Dict[str, Any]:
        """Return empty classification for invalid queries."""
        return {
            'type': 'general',
            'entities': [],
            'topics': [],
            'time_constraint': None,
            'comparison': False,
            'trend_analysis': False,
            'complexity': 'simple',
            'confidence': 0.0,
            'classification_method': 'empty'
        }


# Example usage and testing
async def test_classifier():
    """Test the LLM-based classifier with research questions."""
    
    # Initialize classifier with gpt-5-nano
    classifier = LLMQueryClassifier(model="gpt-5-nano")
    
    # Test queries (including research questions)
    test_queries = [
        # Simple queries
        "What did Tareq Rahman say about elections?",
        "Recent BNP activities",
        "নির্বাচন সংস্কার নিয়ে কি বলা হয়েছে?",
        
        # Comparison queries
        "Compare BNP and Awami League reform positions",
        "Difference between JI and NCP stance on July Charter",
        
        # Trend analysis queries
        "How has the political situation changed from Aug to Oct 2024?",
        "Security threats over time",
        
        # Complex research questions
        "Who are the main actors and what are their current interests regarding the election?",
        "What are the interests of external actors (USA, India, China) regarding the election?",
        "What are the chances of post-election violence and who are likely victims?",
    ]
    
    print("=" * 80)
    print("LLM QUERY CLASSIFIER TEST - GPT-5-NANO")
    print("=" * 80)
    print(f"Model: {classifier.llm.model}")
    print(f"Provider: {classifier.llm.provider}")
    print("=" * 80)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n[{i}/{len(test_queries)}] Query: {query}")
        print("-" * 80)
        
        try:
            result = await classifier.classify_query(query)
            
            print(f"  ✓ Type: {result['type']}")
            print(f"  ✓ Entities: {result['entities']}")
            print(f"  ✓ Topics: {result['topics']}")
            
            if result['time_constraint']:
                tc = result['time_constraint']
                print(f"  ✓ Time: {tc['period']} ({tc['start']} to {tc['end']})")
            else:
                print(f"  ✓ Time: None")
            
            print(f"  ✓ Comparison: {result['comparison']}")
            print(f"  ✓ Trend Analysis: {result['trend_analysis']}")
            print(f"  ✓ Complexity: {result['complexity']}")
            print(f"  ✓ Confidence: {result['confidence']:.2f}")
            print(f"  ✓ Method: {result['classification_method']}")
            
            if result.get('reasoning'):
                print(f"  ✓ Reasoning: {result['reasoning']}")
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
        
        print()


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_classifier())

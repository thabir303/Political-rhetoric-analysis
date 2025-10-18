"""
Aggregation utilities for party/figure-specific analysis.

This module provides functions to aggregate keywords, topics, and election impact
across multiple articles for a specific party or political figure.
"""

from typing import List, Dict, Tuple
from collections import Counter
import re


def aggregate_keywords(articles: List[Dict], top_n: int = 3) -> List[str]:
    """
    Aggregate keywords from multiple articles and return top N most frequent.
    
    Args:
        articles: List of article dictionaries with 'keywords' field
        top_n: Number of top keywords to return (default: 3)
    
    Returns:
        List of top N most frequent keywords
    """
    keyword_counter = Counter()
    
    for article in articles:
        keywords_str = article.get("keywords", "")
        if keywords_str:
            # Split by comma and clean whitespace
            keywords = [k.strip() for k in keywords_str.split(",") if k.strip()]
            keyword_counter.update(keywords)
    
    # Get top N keywords
    top_keywords = [kw for kw, count in keyword_counter.most_common(top_n)]
    return top_keywords


def aggregate_topics(articles: List[Dict], top_n: int = 5) -> List[str]:
    """
    Aggregate topics from multiple articles and return top N most frequent.
    
    Args:
        articles: List of article dictionaries with 'topics' field
        top_n: Number of top topics to return (default: 5)
    
    Returns:
        List of top N most frequent topics
    """
    topic_counter = Counter()
    
    for article in articles:
        topics_str = article.get("topics", "")
        if topics_str:
            # Split by comma and clean whitespace
            topics = [t.strip() for t in topics_str.split(",") if t.strip()]
            topic_counter.update(topics)
    
    # Get top N topics
    top_topics = [topic for topic, count in topic_counter.most_common(top_n)]
    return top_topics


def aggregate_election_impact(articles: List[Dict], max_points: int = 5) -> Dict[str, any]:
    """
    Aggregate election impact information from multiple articles.
    
    Args:
        articles: List of article dictionaries with election impact metadata
        max_points: Maximum number of key points to return (default: 5)
    
    Returns:
        Dictionary with aggregated election impact analysis:
        {
            "has_impact": bool,
            "total_articles_with_impact": int,
            "key_points": List[str],
            "main_themes": List[str]
        }
    """
    impact_counter = Counter()
    election_keywords = Counter()
    articles_with_impact = 0
    
    # Common election-related keywords (Bangla)
    election_terms = [
        'নির্বাচন', 'ভোট', 'প্রার্থী', 'দল', 'সংস্কার', 'গণতন্ত্র',
        'আন্দোলন', 'জনগণ', 'ক্ষমতা', 'সরকার', 'বিরোধী', 'জোট'
    ]
    
    for article in articles:
        # Check if article has election impact
        has_impact = article.get("has_election_impact", False)
        if isinstance(has_impact, str):
            has_impact = has_impact.lower() == "true"
        
        if has_impact:
            articles_with_impact += 1
            
            # Extract election impact description
            impact_desc = article.get("election_impact_description", "")
            if impact_desc:
                # Count mentions of election terms
                for term in election_terms:
                    count = impact_desc.count(term)
                    if count > 0:
                        election_keywords[term] += count
        
        # Also check keywords and topics for election-related content
        keywords_str = article.get("keywords", "")
        topics_str = article.get("topics", "")
        
        for term in election_terms:
            if term in keywords_str or term in topics_str:
                election_keywords[term] += 1
    
    # Generate key points based on most common themes
    key_points = []
    top_themes = [theme for theme, count in election_keywords.most_common(max_points)]
    
    if articles_with_impact > 0:
        key_points.append(f"মোট {articles_with_impact}টি নিবন্ধে নির্বাচনের প্রভাব উল্লেখ রয়েছে")
    
    if top_themes:
        themes_str = ", ".join(top_themes[:3])
        key_points.append(f"প্রধান বিষয়: {themes_str}")
    
    return {
        "has_impact": articles_with_impact > 0,
        "total_articles_with_impact": articles_with_impact,
        "key_points": key_points,
        "main_themes": top_themes
    }


def create_aggregated_analysis(
    articles: List[Dict],
    entity_type: str = "figure",
    entity_name: str = ""
) -> Dict[str, any]:
    """
    Create comprehensive aggregated analysis for a party or figure.
    
    Args:
        articles: List of article dictionaries
        entity_type: Type of entity ("figure" or "party")
        entity_name: Name of the entity being analyzed
    
    Returns:
        Dictionary with complete aggregated analysis:
        {
            "entity_name": str,
            "entity_type": str,
            "total_articles": int,
            "top_keywords": List[str],
            "top_topics": List[str],
            "election_impact": Dict,
            "coverage_summary": str
        }
    """
    total_articles = len(articles)
    
    # Aggregate keywords (top 3)
    top_keywords = aggregate_keywords(articles, top_n=3)
    
    # Aggregate topics (top 5)
    top_topics = aggregate_topics(articles, top_n=5)
    
    # Aggregate election impact
    election_impact = aggregate_election_impact(articles, max_points=5)
    
    # Create coverage summary
    entity_label = "ব্যক্তির" if entity_type == "figure" else "দলের"
    coverage_summary = (
        f"{entity_name} {entity_label} সম্পর্কে মোট {total_articles}টি নিবন্ধ পাওয়া গেছে। "
        f"প্রধান কীওয়ার্ড: {', '.join(top_keywords[:3]) if top_keywords else 'কোনো কীওয়ার্ড নেই'}। "
        f"প্রধান বিষয়: {', '.join(top_topics[:3]) if top_topics else 'কোনো বিষয় নেই'}।"
    )
    
    return {
        "entity_name": entity_name,
        "entity_type": entity_type,
        "total_articles": total_articles,
        "top_keywords": top_keywords,
        "top_topics": top_topics,
        "election_impact": election_impact,
        "coverage_summary": coverage_summary
    }


def get_keyword_frequencies(articles: List[Dict]) -> List[Tuple[str, int]]:
    """
    Get keyword frequencies across all articles.
    
    Args:
        articles: List of article dictionaries
    
    Returns:
        List of (keyword, count) tuples sorted by frequency
    """
    keyword_counter = Counter()
    
    for article in articles:
        keywords_str = article.get("keywords", "")
        if keywords_str:
            keywords = [k.strip() for k in keywords_str.split(",") if k.strip()]
            keyword_counter.update(keywords)
    
    return keyword_counter.most_common()


def get_topic_frequencies(articles: List[Dict]) -> List[Tuple[str, int]]:
    """
    Get topic frequencies across all articles.
    
    Args:
        articles: List of article dictionaries
    
    Returns:
        List of (topic, count) tuples sorted by frequency
    """
    topic_counter = Counter()
    
    for article in articles:
        topics_str = article.get("topics", "")
        if topics_str:
            topics = [t.strip() for t in topics_str.split(",") if t.strip()]
            topic_counter.update(topics)
    
    return topic_counter.most_common()

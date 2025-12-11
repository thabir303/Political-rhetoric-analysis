"""
AI-Powered Article Category Classifier

Classifies political articles into 9 predefined categories using LLM:
1. Reform
2. Elections
3. Trial of The Fascist Government
4. National Security
5. Conspiracy
6. External Actors
7. Proportional Representation (PR) system
8. Legal Basis of July Charter
9. Others
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
import json
import re

from backend.core.llm_generation import LLMGenerator

logger = logging.getLogger(__name__)

# Define the 9 categories with their descriptions
CATEGORIES = {
    "Reform": {
        "description": "Articles about political, judicial, electoral, or institutional reforms",
        "keywords": ["reform", "সংস্কার", "restructure", "পুনর্গঠন", "change", "পরিবর্তন", "overhaul"]
    },
    "Elections": {
        "description": "Articles about elections, voting, election commission, electoral process",
        "keywords": ["election", "নির্বাচন", "voting", "ভোট", "ballot", "candidate", "প্রার্থী", "election commission"]
    },
    "Trial of The Fascist Government": {
        "description": "Articles about trials, prosecution, or accountability of the previous fascist government",
        "keywords": ["trial", "বিচার", "prosecution", "অভিযোগ", "fascist", "ফ্যাসিস্ট", "স্বৈরাচার", "accountability", "জবাবদিহিতা"]
    },
    "National Security": {
        "description": "Articles about national security, defense, border issues, terrorism, law and order",
        "keywords": ["security", "নিরাপত্তা", "defense", "প্রতিরক্ষা", "border", "সীমান্ত", "terrorism", "সন্ত্রাস", "law and order"]
    },
    "Conspiracy": {
        "description": "Articles about political conspiracies, plots, or alleged secret plans",
        "keywords": ["conspiracy", "ষড়যন্ত্র", "plot", "চক্রান্ত", "scheme", "কূটকৌশল", "secret plan"]
    },
    "External Actors": {
        "description": "Articles about foreign involvement, international relations, external influence",
        "keywords": ["foreign", "বিদেশী", "international", "আন্তর্জাতিক", "external", "বহিঃস্থ", "India", "ভারত", "USA", "China"]
    },
    "Proportional Representation (PR) system": {
        "description": "Articles about proportional representation electoral system",
        "keywords": ["proportional representation", "PR system", "সমানুপাতিক প্রতিনিধিত্ব", "electoral system", "নির্বাচনী ব্যবস্থা"]
    },
    "Legal Basis of July Charter": {
        "description": "Articles about July Charter, legal framework, constitutional matters related to July movement",
        "keywords": ["July Charter", "জুলাই সনদ", "legal basis", "আইনি ভিত্তি", "constitution", "সংবিধান", "July movement"]
    },
    "Others": {
        "description": "Articles that don't fit into any of the above categories",
        "keywords": []
    }
}


class CategoryClassifier:
    """AI-powered classifier for categorizing political articles."""
    
    def __init__(self):
        """Initialize the classifier with LLM."""
        self.llm = LLMGenerator(model="gpt-5-nano")
        logger.info("CategoryClassifier initialized with gpt-5-nano")
    
    def classify_article(
        self,
        title: str,
        content: str,
        language: str = "Bangla"
    ) -> Dict:
        """
        Classify an article into one or more categories.
        
        Args:
            title: Article title
            content: Article content
            language: Article language (Bangla or English)
            
        Returns:
            Dict containing:
                - categories: List of assigned categories
                - primary_category: Main category
                - confidence_scores: Dict of category:score
                - reasoning: AI's reasoning for classification
        """
        try:
            # Prepare the classification prompt
            prompt = self._build_classification_prompt(title, content, language)
            
            # Get LLM response
            logger.info(f"Classifying article: {title[:50]}...")
            response = self.llm._call_llm(
                prompt=prompt,
                system_prompt="You are an expert political analyst specializing in Bangladesh politics.",
                temperature=0.3
            )
            
            # Parse the response
            result = self._parse_classification_response(response)
            
            logger.info(f"Classification complete: {result['primary_category']}")
            return result
            
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            # Raise the error instead of using fallback - we want LLM-only classification
            raise Exception(f"LLM classification failed: {e}")
    
    def _build_classification_prompt(
        self,
        title: str,
        content: str,
        language: str
    ) -> str:
        """Build the classification prompt for LLM."""
        
        # Truncate content if too long (keep first 2000 chars)
        truncated_content = content[:2000] if len(content) > 2000 else content
        
        categories_desc = "\n".join([
            f"{i+1}. **{cat}**: {info['description']}"
            for i, (cat, info) in enumerate(CATEGORIES.items())
        ])
        
        if language == "Bangla":
            prompt = f"""You are an expert political analyst specializing in Bangladesh politics. 

Classify the following {language} article into ONE or MORE of these categories ONLY if the article contains direct SPEECHES, STATEMENTS, or QUOTES from political figures or parties about these topics:

{categories_desc}

**CRITICAL CLASSIFICATION RULES:**
1. **ONLY categorize if**: The article contains direct speeches, statements, quotes, or declarations from political parties/figures discussing the category topic
2. **DO NOT categorize if**: The article only mentions the topic in passing, or discusses it without political party/figure involvement
3. **Speech indicators**: Look for quotes, "বলেন", "বলেছেন", "জানান", "মন্তব্য", "বক্তব্য", "বিবৃতি", and more...
4. An article can belong to MULTIPLE categories if political speeches cover multiple topics
5. Choose "Others" if no clear political speech/statement about specific categories
6. For each category, provide confidence score (0-100) and extract the relevant speech excerpt

**Article:**
Title: {title}

Content: {truncated_content}

**Required Output Format (JSON):**
{{
    "categories": ["Category1", "Category2", ...],
    "primary_category": "Category1",
    "confidence_scores": {{
        "Category1": 85,
        "Category2": 60
    }},
    "reasoning": "Brief explanation focusing on which political figure/party said what about which category",
    "relevant_excerpts": {{
        "Category1": "Exact quote or speech excerpt about this category",
        "Category2": "Exact quote or speech excerpt about this category"
    }}
}}

Respond ONLY with valid JSON, no additional text."""
        else:
            prompt = f"""You are an expert political analyst specializing in Bangladesh politics. 

Classify the following English article into ONE or MORE of these categories ONLY if the article contains direct SPEECHES, STATEMENTS, or QUOTES from political figures or parties about these topics:

{categories_desc}

**CRITICAL CLASSIFICATION RULES:**
1. **ONLY categorize if**: The article contains direct speeches, statements, quotes, or declarations from political parties/figures discussing the category topic
2. **DO NOT categorize if**: The article only mentions the topic in passing, or discusses it without political party/figure involvement
3. **Speech indicators**: Look for quotes, "said", "stated", "declared", "announced", "mentioned", etc.
4. An article can belong to MULTIPLE categories if political speeches cover multiple topics
5. Choose "Others" if no clear political speech/statement about specific categories
6. For each category, provide confidence score (0-100) and extract the relevant speech excerpt

**Article:**
Title: {title}

Content: {truncated_content}

**Required Output Format (JSON):**
{{
    "categories": ["Category1", "Category2", ...],
    "primary_category": "Category1",
    "confidence_scores": {{
        "Category1": 85,
        "Category2": 60
    }},
    "reasoning": "Brief explanation focusing on which political figure/party said what about which category",
    "relevant_excerpts": {{
        "Category1": "Exact quote or speech excerpt about this category",
        "Category2": "Exact quote or speech excerpt about this category"
    }}
}}

Respond ONLY with valid JSON, no additional text."""
        
        return prompt
    
    def _parse_classification_response(self, response: str) -> Dict:
        """Parse LLM response and extract classification data."""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)
                
                # Validate the response
                if "categories" in data and "primary_category" in data:
                    # Ensure all categories are valid
                    valid_categories = [
                        cat for cat in data["categories"]
                        if cat in CATEGORIES
                    ]
                    
                    if not valid_categories:
                        valid_categories = ["Others"]
                    
                    primary = data.get("primary_category")
                    if primary not in CATEGORIES:
                        primary = valid_categories[0]
                    
                    return {
                        "categories": valid_categories,
                        "primary_category": primary,
                        "confidence_scores": data.get("confidence_scores", {}),
                        "reasoning": data.get("reasoning", ""),
                        "relevant_excerpts": data.get("relevant_excerpts", {})
                    }
            
            # If parsing fails, use fallback
            raise ValueError("Invalid JSON response")
            
        except Exception as e:
            logger.warning(f"Failed to parse LLM response: {e}")
            raise
    
    def batch_classify(
        self,
        articles: List[Dict],
        language: str = "Bangla"
    ) -> List[Dict]:
        """
        Classify multiple articles in batch.
        
        Args:
            articles: List of dicts with 'title' and 'content'
            language: Article language
            
        Returns:
            List of classification results
        """
        results = []
        
        for i, article in enumerate(articles):
            try:
                title = article.get("title", "")
                content = article.get("content", "")
                
                result = self.classify_article(title, content, language)
                result["article_id"] = article.get("id", f"article_{i}")
                results.append(result)
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Classified {i + 1}/{len(articles)} articles")
                    
            except Exception as e:
                logger.error(f"Error classifying article {i}: {e}")
                results.append({
                    "article_id": article.get("id", f"article_{i}"),
                    "categories": ["Others"],
                    "primary_category": "Others",
                    "confidence_scores": {"Others": 0},
                    "reasoning": f"Error: {str(e)}",
                    "error": str(e)
                })
        
        logger.info(f"Batch classification complete: {len(results)} articles")
        return results


def get_category_info(category_name: str) -> Optional[Dict]:
    """Get information about a specific category."""
    return CATEGORIES.get(category_name)


def get_all_categories() -> List[str]:
    """Get list of all available categories."""
    return list(CATEGORIES.keys())


def get_category_statistics(classifications: List[Dict]) -> Dict:
    """
    Calculate statistics from classification results.
    
    Args:
        classifications: List of classification results
        
    Returns:
        Dict with statistics
    """
    from collections import Counter
    
    all_categories = []
    primary_categories = []
    
    for result in classifications:
        all_categories.extend(result.get("categories", []))
        primary = result.get("primary_category")
        if primary:
            primary_categories.append(primary)
    
    category_counts = Counter(all_categories)
    primary_counts = Counter(primary_categories)
    
    return {
        "total_articles": len(classifications),
        "category_distribution": dict(category_counts),
        "primary_category_distribution": dict(primary_counts),
        "articles_per_category": {
            cat: category_counts.get(cat, 0)
            for cat in CATEGORIES.keys()
        },
        "avg_categories_per_article": len(all_categories) / len(classifications) if classifications else 0
    }


if __name__ == "__main__":
    # Test the classifier
    print("=" * 80)
    print("CATEGORY CLASSIFIER TEST")
    print("=" * 80)
    
    classifier = CategoryClassifier()
    
    # Test article in Bangla
    test_article = {
        "title": "নির্বাচন কমিশন সংস্কারের দাবিতে বিএনপির সমাবেশ",
        "content": """
        বিএনপি গতকাল নির্বাচন কমিশনের সংস্কার এবং আগামী নির্বাচনে সমানুপাতিক প্রতিনিধিত্ব পদ্ধতি 
        চালু করার দাবিতে একটি বড় সমাবেশের আয়োজন করেছে। দলের ভারপ্রাপ্ত চেয়ারম্যান তারেক রহমান 
        বক্তব্যে বলেন, পূর্ববর্তী সরকারের ফ্যাসিবাদী শাসনের বিচার এবং নতুন সংবিধান প্রণয়ন জরুরি।
        """
    }
    
    result = classifier.classify_article(
        test_article["title"],
        test_article["content"],
        language="Bangla"
    )
    
    print(f"\nArticle: {test_article['title']}")
    print(f"\nCategories: {', '.join(result['categories'])}")
    print(f"Primary Category: {result['primary_category']}")
    print(f"\nConfidence Scores:")
    for cat, score in result['confidence_scores'].items():
        print(f"  - {cat}: {score}%")
    print(f"\nReasoning: {result['reasoning']}")
    print("\n" + "=" * 80)

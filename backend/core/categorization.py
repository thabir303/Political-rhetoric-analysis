"""
Article Categorization Module

Processes scraped articles and categorizes them into political themes,
extracts keywords, identifies political figures, and performs NLP analysis.
"""

import re
from typing import Dict, List, Set, Tuple, Optional
from datetime import datetime
from collections import Counter
import logging

# Import name normalizer for Bengali-English name mapping
from backend.core.name_normalizer import get_canonical_name, deduplicate_names
# Import the authoritative POLITICAL_ENTITIES from scraping module
from backend.core.scraping import POLITICAL_ENTITIES

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import NLP libraries
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available. TF-IDF features will be limited.")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logger.warning("numpy not available. Some features will be limited.")

# Key political themes and keywords
POLITICAL_THEMES = {
    "Election Commission": [
        "election", "election commission", "EC", "voter", "voting",
        "নির্বাচন", "নির্বাচন কমিশন", "ভোটার", "ভোট"
    ],
    "Judiciary": [
        "court", "supreme court", "high court", "judge", "justice",
        "আদালত", "সুপ্রিম কোর্ট", "হাইকোর্ট", "বিচারক"
    ],
    "Reform": [
        "reform", "reformation", "restructure", "overhaul",
        "সংস্কার", "পুনর্গঠন"
    ],
    "Democracy": [
        "democracy", "democratic", "autocracy", "dictatorship",
        "গণতন্ত্র", "গণতান্ত্রিক", "স্বৈরাচার"
    ],
    "Human Rights": [
        "human rights", "rights violation", "torture", "disappearance",
        "মানবাধিকার", "নির্যাতন", "গুম"
    ],
    "Economy": [
        "economy", "economic", "inflation", "GDP", "budget",
        "অর্থনীতি", "মূল্যস্ফীতি", "বাজেট"
    ],
    "Law and Order": [
        "law and order", "police", "security", "crime", "violence",
        "আইন শৃঙ্খলা", "পুলিশ", "নিরাপত্তা", "অপরাধ"
    ]
}

# Speech-related keywords
SPEECH_KEYWORDS = [
    "speech", "spoke", "said", "stated", "declared", "announced",
    "address", "remarks", "commented", "expressed", "rally", "meeting",
    "বক্তব্য", "বক্তা", "বলেন", "বলেছেন", "ঘোষণা", "মন্তব্য",
    "সভা", "সমাবেশ", "জনসভা"
]

# Stance-related keywords
STANCE_KEYWORDS = [
    "position", "stance", "opinion", "view", "oppose", "support",
    "demand", "call for", "urge", "criticize", "condemn", "praise",
    "অবস্থান", "মতামত", "দাবি", "সমর্থন", "বিরোধিতা", "নিন্দা"
]

# Common stopwords (both English and Bangla)
STOPWORDS = set([
    # English
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "up", "about", "into", "through", "during",
    "is", "are", "was", "were", "been", "be", "have", "has", "had", "do",
    "does", "did", "will", "would", "could", "should", "may", "might",
    "this", "that", "these", "those", "i", "you", "he", "she", "it", "we",
    # Bangla
    "এবং", "বা", "কিন্তু", "তবে", "যে", "যা", "যার", "যাকে", "যাদের",
    "এ", "ও", "সে", "তিনি", "তারা", "আমি", "আমরা", "তুমি", "তোমরা"
])


class ArticleCategorizer:
    """Categorizes articles into political themes and extracts key information."""
    
    def __init__(self):
        """Initialize the categorizer."""
        self.tfidf_vectorizer = None
        if SKLEARN_AVAILABLE:
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=100,
                stop_words='english',
                ngram_range=(1, 2)
            )
    
    def categorize_article(self, article: Dict) -> Dict:
        """
        Categorize an article and extract key information.
        
        Args:
            article: Dictionary containing article data with keys:
                - title: Article title
                - content: Article content
                - date: Publication date (optional)
                - mentions: List of mentioned entities (optional)
        
        Returns:
            Dictionary containing:
                - categories: List of political themes
                - people: List of canonical political figures mentioned
                - parties: List of political parties mentioned
                - people_affiliations: Dictionary mapping canonical names to parties
                - keywords: List of extracted keywords
                - dates: List of dates mentioned
                - is_speech: Boolean indicating if article discusses speeches
                - is_stance: Boolean indicating if article discusses political stance
                - themes: Dictionary of theme scores
        """
        title = article.get('title', '')
        content = article.get('content', '')
        combined_text = f"{title} {content}"
        
        # Extract all components with name normalization
        parties_and_figures = self._identify_parties_and_figures(combined_text)
        parties = list(parties_and_figures.keys())
        
        # Extract all people and normalize to canonical names
        people_raw = self._identify_people(combined_text)
        people_canonical = [get_canonical_name(name) for name in people_raw]
        people_canonical = deduplicate_names(people_canonical)
        
        # Create people_affiliations mapping
        people_affiliations = {}
        for canonical_name in people_canonical:
            # Find which party this person belongs to
            for party_key, party_data in POLITICAL_ENTITIES.items():
                canonical_figures = list(party_data.get("figures", {}).keys())
                if canonical_name in canonical_figures:
                    people_affiliations[canonical_name] = party_key
                    break
        
        themes = self._identify_themes(combined_text)
        keywords = self._extract_keywords(combined_text)
        dates = self._extract_dates(combined_text)
        is_speech = self._is_speech_article(combined_text)
        is_stance = self._is_stance_article(combined_text)
        
        # Build categories list
        categories = []
        
        # Add party categories
        categories.extend(parties)
        
        # Add theme categories
        categories.extend([theme for theme, score in themes.items() if score > 0])
        
        # Add speech category if applicable
        if is_speech:
            categories.append("Speech Analysis")
        
        # Add stance category if applicable
        if is_stance:
            categories.append("Political Stance")
        
        # Remove duplicates
        categories = list(set(categories))
        
        return {
            'categories': categories,
            'people': people_canonical,  # Now returns canonical names
            'parties': parties,
            'people_affiliations': people_affiliations,  # New field
            'keywords': keywords,
            'dates': dates,
            'is_speech': is_speech,
            'is_stance': is_stance,
            'themes': themes,
            'metadata': {
                'total_categories': len(categories),
                'total_people': len(people_canonical),
                'total_parties': len(parties),
                'total_keywords': len(keywords),
                'total_dates': len(dates)
            }
        }
    
    def _identify_parties_and_figures(self, text: str) -> Dict[str, List[str]]:
        """
        Identify political parties mentioned in text along with their figures.
        Uses the new POLITICAL_ENTITIES structure from scraping module.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary mapping party names to list of canonical figures found
        """
        text_lower = text.lower()
        result = {}
        
        for party_key, party_data in POLITICAL_ENTITIES.items():
            party_mentioned = False
            figures_found = []
            
            # Check if party name is mentioned
            for party_name in party_data.get('party_names', []):
                if party_name.lower() in text_lower:
                    party_mentioned = True
                    break
            
            # Check if any figure is mentioned (with normalization)
            figures_dict = party_data.get('figures', {})
            for canonical_name, variants in figures_dict.items():
                for variant in variants:
                    if variant.lower() in text_lower:
                        # Add canonical name
                        if canonical_name not in figures_found:
                            figures_found.append(canonical_name)
                        break
            
            # Add to result if party or any figure is mentioned
            if party_mentioned or figures_found:
                result[party_key] = figures_found
        
        return result
    
    def _identify_parties(self, text: str) -> List[str]:
        """
        Identify political parties mentioned in text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of party keys
        """
        parties_and_figures = self._identify_parties_and_figures(text)
        return list(parties_and_figures.keys())
    
    def _identify_people(self, text: str) -> List[str]:
        """
        Identify political figures mentioned in text (returns raw names for normalization).
        Now includes partial name matching for better detection.
        FIXED: Better Unicode/Bengali text handling without word boundary issues.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of figure names (will be normalized by caller)
        """
        text_lower = text.lower()
        people = []
        people_canonical_found = set()  # Track canonical names already found
        
        # Extract all name variants found in text
        for party_key, party_data in POLITICAL_ENTITIES.items():
            figures_dict = party_data.get('figures', {})
            for canonical_name, variants in figures_dict.items():
                # Skip if we already found this person
                if canonical_name in people_canonical_found:
                    continue
                    
                # Check each variant
                for variant in variants:
                    variant_lower = variant.lower()
                    
                    # Direct substring match (most reliable for Bengali)
                    if variant_lower in text_lower:
                        people.append(variant)
                        people_canonical_found.add(canonical_name)
                        break
                    
                    # Partial match for compound names
                    # For example: "ইউনূস" should match "ড. ইউনূস" or "মুহাম্মদ ইউনূস"
                    variant_parts = variant_lower.split()
                    if len(variant_parts) > 1:
                        # Check if any significant part (>3 chars) of the name is in text
                        for part in variant_parts:
                            if len(part) > 3:
                                # For Bengali text, use simple substring match with context
                                # Check if the part appears with space/punctuation before or after
                                import re
                                # Pattern that works for both English and Bengali:
                                # Look for the part with space, punctuation, or start/end of string
                                pattern = r'(?:^|[\s,।\.\-\(\)]){part}(?:[\s,।\.\-\(\)]|$)'.format(
                                    part=re.escape(part)
                                )
                                if re.search(pattern, text_lower, re.UNICODE):
                                    people.append(variant)
                                    people_canonical_found.add(canonical_name)
                                    break
                        if canonical_name in people_canonical_found:
                            break
        
        return people
    
    def _identify_themes(self, text: str) -> Dict[str, int]:
        """
        Identify political themes in text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary of theme names and their occurrence counts
        """
        text_lower = text.lower()
        themes = {}
        
        for theme, keywords in POLITICAL_THEMES.items():
            count = 0
            for keyword in keywords:
                # Count occurrences of each keyword
                count += text_lower.count(keyword.lower())
            
            if count > 0:
                themes[theme] = count
        
        return themes
    
    def _is_speech_article(self, text: str) -> bool:
        """
        Determine if article discusses speeches or statements.
        
        Args:
            text: Text to analyze
            
        Returns:
            True if article is about speeches
        """
        text_lower = text.lower()
        speech_count = 0
        
        for keyword in SPEECH_KEYWORDS:
            if keyword.lower() in text_lower:
                speech_count += 1
        
        # If at least 2 speech-related keywords are found
        return speech_count >= 2
    
    def _is_stance_article(self, text: str) -> bool:
        """
        Determine if article discusses political stances or positions.
        
        Args:
            text: Text to analyze
            
        Returns:
            True if article discusses political stances
        """
        text_lower = text.lower()
        stance_count = 0
        
        for keyword in STANCE_KEYWORDS:
            if keyword.lower() in text_lower:
                stance_count += 1
        
        # If at least 2 stance-related keywords are found
        return stance_count >= 2
    
    def _extract_keywords(self, text: str, top_n: int = 15) -> List[str]:
        """
        Extract keywords using frequency analysis and TF-IDF.
        
        Args:
            text: Text to analyze
            top_n: Number of top keywords to return
            
        Returns:
            List of keywords
        """
        # Clean text
        text = self._clean_text(text)
        
        # Split into words
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter out stopwords and short words
        filtered_words = [
            word for word in words
            if len(word) > 3 and word not in STOPWORDS
        ]
        
        # Count word frequencies
        word_freq = Counter(filtered_words)
        
        # Get top N words by frequency
        keywords = [word for word, count in word_freq.most_common(top_n)]
        
        # If TF-IDF is available, combine with TF-IDF results
        if SKLEARN_AVAILABLE and len(filtered_words) > 10:
            try:
                tfidf_keywords = self._extract_tfidf_keywords(text, top_n)
                # Combine and deduplicate
                keywords = list(set(keywords + tfidf_keywords))[:top_n]
            except:
                pass
        
        return keywords
    
    def _extract_tfidf_keywords(self, text: str, top_n: int = 15) -> List[str]:
        """
        Extract keywords using TF-IDF.
        
        Args:
            text: Text to analyze
            top_n: Number of top keywords to return
            
        Returns:
            List of keywords
        """
        if not SKLEARN_AVAILABLE:
            return []
        
        try:
            # Create a simple corpus with the text
            corpus = [text]
            
            # Fit and transform
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(corpus)
            
            # Get feature names
            feature_names = self.tfidf_vectorizer.get_feature_names_out()
            
            # Get scores for the document
            scores = tfidf_matrix.toarray()[0]
            
            # Sort by score
            top_indices = scores.argsort()[-top_n:][::-1]
            
            # Get top keywords
            keywords = [feature_names[i] for i in top_indices if scores[i] > 0]
            
            return keywords
        except Exception as e:
            logger.warning(f"TF-IDF extraction failed: {e}")
            return []
    
    def _extract_dates(self, text: str) -> List[str]:
        """
        Extract dates from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of dates in YYYY-MM-DD format
        """
        dates = []
        
        # Pattern for various date formats
        date_patterns = [
            # YYYY-MM-DD or YYYY/MM/DD
            r'\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b',
            # DD-MM-YYYY or DD/MM/YYYY
            r'\b(\d{1,2})[-/](\d{1,2})[-/](\d{4})\b',
            # Month DD, YYYY
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})\b',
            # DD Month YYYY
            r'\b(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})\b',
        ]
        
        months = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
        
        for pattern in date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    groups = match.groups()
                    
                    # Handle different formats
                    if len(groups) == 3:
                        if groups[0].isdigit() and len(groups[0]) == 4:
                            # YYYY-MM-DD
                            year, month, day = groups
                        elif groups[2].isdigit() and len(groups[2]) == 4:
                            # DD-MM-YYYY or Month DD, YYYY
                            if groups[0].lower() in months:
                                month = str(months[groups[0].lower()])
                                day = groups[1]
                                year = groups[2]
                            else:
                                day, month, year = groups
                        else:
                            continue
                        
                        # Validate and format
                        year = int(year)
                        month = int(month)
                        day = int(day)
                        
                        if 1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31:
                            date_str = f"{year:04d}-{month:02d}-{day:02d}"
                            if date_str not in dates:
                                dates.append(date_str)
                except:
                    continue
        
        return sorted(dates)
    
    def _clean_text(self, text: str) -> str:
        """
        Clean text for processing.
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned text
        """
        # Remove URLs
        text = re.sub(r'http\S+|www\S+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove special characters but keep Bangla characters
        text = re.sub(r'[^\w\s\u0980-\u09FF]', ' ', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    def batch_categorize(self, articles: List[Dict]) -> List[Dict]:
        """
        Categorize multiple articles in batch.
        
        Args:
            articles: List of article dictionaries
            
        Returns:
            List of categorization results
        """
        results = []
        
        for i, article in enumerate(articles):
            try:
                result = self.categorize_article(article)
                result['article_index'] = i
                results.append(result)
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Categorized {i + 1}/{len(articles)} articles")
            except Exception as e:
                logger.error(f"Error categorizing article {i}: {e}")
                results.append({
                    'article_index': i,
                    'error': str(e),
                    'categories': [],
                    'people': [],
                    'parties': [],
                    'keywords': [],
                    'dates': []
                })
        
        logger.info(f"Batch categorization complete: {len(results)} articles")
        return results


def categorize_scraped_articles(articles: List[Dict]) -> List[Dict]:
    """
    Convenience function to categorize scraped articles.
    
    Args:
        articles: List of scraped articles
        
    Returns:
        List of articles with categorization data added
    """
    categorizer = ArticleCategorizer()
    
    enriched_articles = []
    
    for article in articles:
        # Categorize the article
        categorization = categorizer.categorize_article(article)
        
        # Add categorization data to article
        enriched_article = article.copy()
        enriched_article['categorization'] = categorization
        
        enriched_articles.append(enriched_article)
    
    return enriched_articles


def save_categorized_articles_to_db(articles: List[Dict]):
    """
    Save categorized articles to the vector database.
    
    Args:
        articles: List of categorized articles
    """
    from database import vector_store
    
    logger.info(f"Saving {len(articles)} categorized articles to database...")
    
    for article in articles:
        try:
            categorization = article.get('categorization', {})
            
            # Prepare metadata
            metadata = {
                'date': article.get('date', ''),
                'category': article.get('category', 'general'),
                'source': article.get('source', ''),
                'title': article.get('title', ''),
                'language': article.get('language', 'Unknown'),
                'url': article.get('url', ''),
                # Add categorization data
                'parties': ', '.join(categorization.get('parties', [])),
                'people': ', '.join(categorization.get('people', [])),
                'themes': ', '.join(categorization.get('categories', [])),
                'keywords': ', '.join(categorization.get('keywords', [])[:10]),
                'is_speech': str(categorization.get('is_speech', False)),
                'is_stance': str(categorization.get('is_stance', False))
            }
            
            if 'author' in article and article['author']:
                metadata['author'] = article['author']
            
            # Add to vector database
            vector_store.add_article(
                content=article['content'],
                metadata=metadata
            )
            
            logger.info(f"Saved: {article['title'][:50]}...")
            
        except Exception as e:
            logger.error(f"Error saving article to database: {e}")
    
    logger.info("Finished saving categorized articles to database")


# Analysis functions
def analyze_categorization_results(results: List[Dict]) -> Dict:
    """
    Analyze categorization results to get insights.
    
    Args:
        results: List of categorization results
        
    Returns:
        Dictionary with analysis insights
    """
    total_articles = len(results)
    
    # Count categories
    all_categories = []
    all_parties = []
    all_people = []
    all_keywords = []
    speech_count = 0
    stance_count = 0
    
    for result in results:
        all_categories.extend(result.get('categories', []))
        all_parties.extend(result.get('parties', []))
        all_people.extend(result.get('people', []))
        all_keywords.extend(result.get('keywords', []))
        
        if result.get('is_speech'):
            speech_count += 1
        if result.get('is_stance'):
            stance_count += 1
    
    category_counts = Counter(all_categories)
    party_counts = Counter(all_parties)
    people_counts = Counter(all_people)
    keyword_counts = Counter(all_keywords)
    
    return {
        'total_articles': total_articles,
        'speech_articles': speech_count,
        'stance_articles': stance_count,
        'top_categories': category_counts.most_common(10),
        'top_parties': party_counts.most_common(10),
        'top_people': people_counts.most_common(10),
        'top_keywords': keyword_counts.most_common(20),
        'avg_categories_per_article': len(all_categories) / total_articles if total_articles > 0 else 0,
        'avg_people_per_article': len(all_people) / total_articles if total_articles > 0 else 0
    }


if __name__ == "__main__":
    # Example usage
    print("=" * 80)
    print("ARTICLE CATEGORIZATION MODULE")
    print("=" * 80)
    
    # Test with sample article
    sample_article = {
        'title': 'Tareq Rahman speaks at BNP rally on election reforms',
        'content': '''
        BNP acting chairman Tareq Rahman delivered a speech at a party rally yesterday,
        calling for comprehensive reforms to the Election Commission. He criticized the
        interim government's stance on electoral reforms and demanded immediate action.
        Mirza Fakhrul was also present at the rally. The event took place on October 5, 2024.
        Rahman stated that democratic reforms are crucial for the country's future.
        ''',
        'date': '2024-10-05',
        'source': 'Daily Star'
    }
    
    print("\nTest Article:")
    print(f"Title: {sample_article['title']}")
    print(f"Content: {sample_article['content'][:100]}...")
    
    # Categorize
    categorizer = ArticleCategorizer()
    result = categorizer.categorize_article(sample_article)
    
    print("\n" + "=" * 80)
    print("CATEGORIZATION RESULTS")
    print("=" * 80)
    
    print(f"\nCategories: {', '.join(result['categories'])}")
    print(f"Political Parties: {', '.join(result['parties'])}")
    print(f"People Mentioned: {', '.join(result['people'])}")
    print(f"Keywords: {', '.join(result['keywords'][:10])}")
    print(f"Dates: {', '.join(result['dates'])}")
    print(f"Is Speech Article: {result['is_speech']}")
    print(f"Is Stance Article: {result['is_stance']}")
    
    print("\nTheme Scores:")
    for theme, score in result['themes'].items():
        print(f"  - {theme}: {score}")
    
    print("\n" + "=" * 80)
    print("Module ready for use!")
    print("=" * 80)

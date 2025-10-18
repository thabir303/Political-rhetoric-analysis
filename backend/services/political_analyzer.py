"""
LLM Analysis Module for Political Articles

Performs analysis on stored political articles:
- Speech summaries
- Key points extraction
- Topics covered
- Top keywords
- Political stands/positions
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from political_storage import PoliticalArticleStorage, POLITICAL_STRUCTURE

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import LLM libraries
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("Google Gemini not available")

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers not available")


class PoliticalArticleAnalyzer:
    """
    Analyzes stored political articles using LLM.
    """
    
    def __init__(
        self,
        storage_directory: str = "./political_chroma_db",
        llm_model: str = "gemini",
        api_key: Optional[str] = None
    ):
        """
        Initialize the analyzer.
        
        Args:
            storage_directory: Directory for political article storage
            llm_model: LLM model to use ("gemini" or "transformers")
            api_key: API key for Gemini (if using Gemini)
        """
        # Initialize storage
        logger.info("Initializing political article storage...")
        self.storage = PoliticalArticleStorage(persist_directory=storage_directory)
        
        # Initialize LLM
        self.llm_model = llm_model
        self.llm = None
        
        if llm_model == "gemini" and GEMINI_AVAILABLE:
            if api_key:
                genai.configure(api_key=api_key)
                self.llm = genai.GenerativeModel('gemini-pro')
                logger.info("Initialized Gemini model")
            else:
                logger.warning("Gemini API key not provided")
        elif llm_model == "transformers" and TRANSFORMERS_AVAILABLE:
            self.llm = pipeline("text2text-generation", model="google/flan-t5-base")
            logger.info("Initialized Transformers model")
        else:
            logger.warning("No LLM available. Using rule-based analysis.")
    
    def analyze_speech(self, article_content: str, article_metadata: Dict) -> Dict[str, Any]:
        """
        Analyze a political speech article.
        
        Args:
            article_content: Article text
            article_metadata: Article metadata
            
        Returns:
            Analysis results
        """
        analysis = {
            "title": article_metadata.get("title", ""),
            "date": article_metadata.get("date", ""),
            "party": article_metadata.get("party_name", ""),
            "mentioned_figures": article_metadata.get("mentioned_figures", ""),
            "source": article_metadata.get("source", "")
        }
        
        if self.llm and self.llm_model == "gemini":
            # Use Gemini for analysis
            prompt = f"""
Analyze this political article and provide:
1. Summary (2-3 sentences)
2. Key Points (3-5 bullet points)
3. Topics Covered (3-5 topics)
4. Top Keywords (5-10 keywords)
5. Political Stand/Position (describe the political stance)

Article Title: {article_metadata.get('title', '')}
Article Content: {article_content}

Provide the analysis in JSON format with keys: summary, key_points, topics, keywords, political_stand
"""
            try:
                response = self.llm.generate_content(prompt)
                # Parse response
                result_text = response.text
                # Try to extract JSON
                if "{" in result_text and "}" in result_text:
                    start = result_text.find("{")
                    end = result_text.rfind("}") + 1
                    json_str = result_text[start:end]
                    llm_analysis = json.loads(json_str)
                    analysis.update(llm_analysis)
                else:
                    analysis["llm_response"] = result_text
            except Exception as e:
                logger.error(f"Gemini analysis error: {str(e)}")
                analysis["error"] = str(e)
        
        else:
            # Rule-based analysis
            analysis["summary"] = article_content[:300] + "..."
            analysis["key_points"] = self._extract_key_points(article_content)
            analysis["topics"] = self._extract_topics(article_content)
            analysis["keywords"] = self._extract_keywords(article_content)
            analysis["political_stand"] = self._infer_political_stand(
                article_content,
                article_metadata
            )
        
        return analysis
    
    def _extract_key_points(self, text: str) -> List[str]:
        """Extract key points from text (rule-based)."""
        # Simple sentence extraction
        sentences = text.split(".")
        key_points = []
        
        keywords = [
            "বলেন", "বলেছেন", "said", "stated", "announced",
            "announced", "declared", "urged", "called for"
        ]
        
        for sentence in sentences[:20]:  # Check first 20 sentences
            sentence = sentence.strip()
            if len(sentence) > 30:  # Minimum length
                for keyword in keywords:
                    if keyword in sentence.lower():
                        key_points.append(sentence + ".")
                        break
                if len(key_points) >= 5:
                    break
        
        return key_points[:5]
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract topics from text (rule-based)."""
        topics = []
        
        topic_keywords = {
            "election": ["election", "নির্বাচন", "vote", "voting"],
            "government": ["government", "সরকার", "administration"],
            "economy": ["economy", "অর্থনীতি", "economic", "price"],
            "corruption": ["corruption", "দুর্নীতি", "scandal"],
            "democracy": ["democracy", "গণতন্ত্র", "democratic"],
            "protest": ["protest", "আন্দোলন", "demonstration"],
            "reform": ["reform", "সংস্কার", "change"],
            "justice": ["justice", "ন্যায়বিচার", "court", "legal"]
        }
        
        text_lower = text.lower()
        for topic, keywords in topic_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    topics.append(topic)
                    break
        
        return topics[:5]
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text (rule-based)."""
        # Simple word frequency
        words = text.lower().split()
        
        # Filter common words
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at",
            "to", "for", "of", "with", "by", "from", "as", "is", "was",
            "এ", "এর", "ও", "এবং", "যে", "যা", "এই", "সে", "তার"
        }
        
        word_freq = {}
        for word in words:
            if len(word) > 3 and word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        return [word for word, _ in sorted_words[:10]]
    
    def _infer_political_stand(self, text: str, metadata: Dict) -> str:
        """Infer political stand (rule-based)."""
        text_lower = text.lower()
        
        # Sentiment indicators
        positive_words = ["support", "welcome", "praise", "good", "সমর্থন", "স্বাগত"]
        negative_words = ["oppose", "criticize", "condemn", "bad", "বিরোধিতা", "সমালোচনা"]
        neutral_words = ["discuss", "comment", "state", "বলেন", "আলোচনা"]
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        neutral_count = sum(1 for word in neutral_words if word in text_lower)
        
        if positive_count > negative_count and positive_count > neutral_count:
            return "Supportive"
        elif negative_count > positive_count and negative_count > neutral_count:
            return "Critical/Opposing"
        else:
            return "Neutral/Informative"
    
    def analyze_party_articles(
        self,
        party_id: str,
        limit: int = 10,
        date_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze articles for a specific party.
        
        Args:
            party_id: Party identifier
            limit: Maximum number of articles to analyze
            date_filter: Optional date filter (YYYY-MM-DD)
            
        Returns:
            List of analysis results
        """
        logger.info(f"\nAnalyzing articles for: {POLITICAL_STRUCTURE[party_id]['name']}")
        
        # Get articles
        where = None
        if date_filter:
            where = {"date": date_filter}
        
        articles = self.storage.get_articles_by_party(party_id, limit=limit, where=where)
        
        if not articles:
            logger.warning(f"No articles found for {party_id}")
            return []
        
        logger.info(f"Found {len(articles)} articles to analyze")
        
        # Analyze each article
        results = []
        for i, article in enumerate(articles, 1):
            logger.info(f"Analyzing article {i}/{len(articles)}: {article['metadata'].get('title', '')[:50]}...")
            
            analysis = self.analyze_speech(article["content"], article["metadata"])
            analysis["article_id"] = article["id"]
            results.append(analysis)
        
        return results
    
    def analyze_figure_articles(
        self,
        figure_name: str,
        party_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Analyze articles mentioning a specific political figure.
        
        Args:
            figure_name: Name of the political figure
            party_id: Optional party filter
            limit: Maximum number of articles to analyze
            
        Returns:
            List of analysis results
        """
        logger.info(f"\nAnalyzing articles for: {figure_name}")
        
        # Get articles
        articles = self.storage.get_articles_by_figure(
            figure_name,
            party_id=party_id,
            limit=limit
        )
        
        if not articles:
            logger.warning(f"No articles found for {figure_name}")
            return []
        
        logger.info(f"Found {len(articles)} articles to analyze")
        
        # Analyze each article
        results = []
        for i, article in enumerate(articles, 1):
            logger.info(f"Analyzing article {i}/{len(articles)}: {article['metadata'].get('title', '')[:50]}...")
            
            analysis = self.analyze_speech(article["content"], article["metadata"])
            analysis["article_id"] = article["id"]
            results.append(analysis)
        
        return results
    
    def generate_party_report(self, party_id: str, limit: int = 50) -> Dict[str, Any]:
        """
        Generate comprehensive report for a political party.
        
        Args:
            party_id: Party identifier
            limit: Maximum number of articles to analyze
            
        Returns:
            Comprehensive report
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Generating report for: {POLITICAL_STRUCTURE[party_id]['name']}")
        logger.info(f"{'='*60}\n")
        
        # Get party statistics
        party_stats = self.storage.get_party_statistics(party_id)
        
        # Analyze articles
        analyses = self.analyze_party_articles(party_id, limit=limit)
        
        # Aggregate results
        all_topics = []
        all_keywords = []
        all_stands = []
        
        for analysis in analyses:
            if "topics" in analysis:
                all_topics.extend(analysis["topics"])
            if "keywords" in analysis:
                all_keywords.extend(analysis["keywords"])
            if "political_stand" in analysis:
                all_stands.append(analysis["political_stand"])
        
        # Count frequencies
        from collections import Counter
        topic_freq = Counter(all_topics)
        keyword_freq = Counter(all_keywords)
        stand_freq = Counter(all_stands)
        
        report = {
            "party_id": party_id,
            "party_name": POLITICAL_STRUCTURE[party_id]["name"],
            "statistics": party_stats,
            "articles_analyzed": len(analyses),
            "top_topics": dict(topic_freq.most_common(10)),
            "top_keywords": dict(keyword_freq.most_common(20)),
            "political_stands_distribution": dict(stand_freq),
            "recent_analyses": analyses[:5],
            "generated_at": datetime.now().isoformat()
        }
        
        return report
    
    def generate_figure_report(
        self,
        figure_name: str,
        party_id: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Generate comprehensive report for a political figure.
        
        Args:
            figure_name: Name of the political figure
            party_id: Optional party filter
            limit: Maximum number of articles to analyze
            
        Returns:
            Comprehensive report
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Generating report for: {figure_name}")
        logger.info(f"{'='*60}\n")
        
        # Analyze articles
        analyses = self.analyze_figure_articles(figure_name, party_id=party_id, limit=limit)
        
        if not analyses:
            return {
                "figure_name": figure_name,
                "error": "No articles found"
            }
        
        # Aggregate results
        all_topics = []
        all_keywords = []
        all_stands = []
        
        for analysis in analyses:
            if "topics" in analysis:
                all_topics.extend(analysis["topics"])
            if "keywords" in analysis:
                all_keywords.extend(analysis["keywords"])
            if "political_stand" in analysis:
                all_stands.append(analysis["political_stand"])
        
        # Count frequencies
        from collections import Counter
        topic_freq = Counter(all_topics)
        keyword_freq = Counter(all_keywords)
        stand_freq = Counter(all_stands)
        
        report = {
            "figure_name": figure_name,
            "articles_analyzed": len(analyses),
            "top_topics": dict(topic_freq.most_common(10)),
            "top_keywords": dict(keyword_freq.most_common(20)),
            "political_stands_distribution": dict(stand_freq),
            "recent_analyses": analyses[:5],
            "generated_at": datetime.now().isoformat()
        }
        
        return report


def main():
    """Command-line interface for political article analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Analyze stored political articles using LLM"
    )
    parser.add_argument(
        "--storage-dir",
        type=str,
        default="./political_chroma_db",
        help="Directory for article storage"
    )
    parser.add_argument(
        "--party",
        type=str,
        choices=list(POLITICAL_STRUCTURE.keys()),
        help="Analyze specific party"
    )
    parser.add_argument(
        "--figure",
        type=str,
        help="Analyze specific political figure"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum articles to analyze"
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate comprehensive report"
    )
    parser.add_argument(
        "--llm-model",
        type=str,
        choices=["gemini", "transformers", "rule-based"],
        default="rule-based",
        help="LLM model to use"
    )
    parser.add_argument(
        "--gemini-api-key",
        type=str,
        help="Gemini API key"
    )
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = PoliticalArticleAnalyzer(
        storage_directory=args.storage_dir,
        llm_model=args.llm_model,
        api_key=args.gemini_api_key
    )
    
    # Generate report or analyze
    if args.report:
        if args.party:
            report = analyzer.generate_party_report(args.party, limit=args.limit)
            print(json.dumps(report, indent=2, ensure_ascii=False))
        elif args.figure:
            report = analyzer.generate_figure_report(
                args.figure,
                limit=args.limit
            )
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            print("Error: Specify --party or --figure for report generation")
    else:
        if args.party:
            results = analyzer.analyze_party_articles(args.party, limit=args.limit)
            print(json.dumps(results, indent=2, ensure_ascii=False))
        elif args.figure:
            results = analyzer.analyze_figure_articles(args.figure, limit=args.limit)
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            print("Error: Specify --party or --figure for analysis")


if __name__ == "__main__":
    main()

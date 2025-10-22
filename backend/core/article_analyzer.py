"""
Article Analyzer with LLM Integration

Analyzes scraped articles using Gemini LLM for:
1. Top 2-3 keywords extraction
2. Top 2 topic identification
3. 2026 Bangladesh election impact detection
4. Returns structured JSON for frontend display
"""

import os
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

# Import political entities configuration
from political_entities_config import POLITICAL_ENTITIES, get_party_list_for_prompt, get_figures_list_for_prompt

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-generativeai not available. Install with: pip install google-generativeai")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class ArticleAnalyzer:
    """
    Analyzes political articles using Gemini LLM.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the analyzer.
        
        Args:
            api_key: Gemini API key (defaults to GEMINI_API_KEY env variable)
        """
        if not GEMINI_AVAILABLE:
            raise ImportError("google-generativeai not installed. Install with: pip install google-generativeai")
        
        # Get API key
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key not found. Set GEMINI_API_KEY environment variable.")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
        
        logger.info("ArticleAnalyzer initialized with Gemini")
    
    def analyze_article(self, article: Dict) -> Dict:
        """
        Analyze a single article using LLM.
        
        Args:
            article: Dictionary containing article data with keys:
                - title: Article title
                - content: Article content
                - parties: List of detected parties (from categorization)
                - people: List of detected figures (from categorization)
        
        Returns:
            Dictionary containing:
                - summary: Brief 3-4 sentence summary
                - keywords: List of 2-3 top keywords
                - topics: List of 2 main topics covered
                - has_election_impact: Boolean indicating 2026 election relevance
                - election_impact_description: Description of election impact (if any)
                - election_impact_parties: List of parties affected
        """
        title = article.get('title', '')
        content = article.get('content', '')
        detected_parties = article.get('parties', [])
        detected_people = article.get('people', [])
        
        # Build the analysis prompt
        prompt = self._build_analysis_prompt(title, content, detected_parties, detected_people)
        
        try:
            # Call Gemini API
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 1000,
                }
            )
            
            # Parse JSON response
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            elif response_text.startswith("```"):
                response_text = response_text.replace("```", "").strip()
            
            # Parse JSON
            analysis = json.loads(response_text)
            
            # Validate and normalize the response
            analysis = self._validate_analysis(analysis)
            
            logger.info(f"✅ Analyzed: {title[:50]}... | Keywords: {analysis['keywords']} | Election Impact: {analysis['has_election_impact']}")
            
            return analysis
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Response text: {response_text[:500]}")
            return self._get_fallback_analysis()
        
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return self._get_fallback_analysis()
    
    def _build_analysis_prompt(
        self,
        title: str,
        content: str,
        detected_parties: List[str],
        detected_people: List[str]
    ) -> str:
        """
        Build the analysis prompt for Gemini.
        
        Args:
            title: Article title
            content: Article content
            detected_parties: Parties detected by categorization
            detected_people: Figures detected by categorization
        
        Returns:
            Formatted prompt string
        """
        # Build allowed parties and figures list from POLITICAL_ENTITIES
        allowed_parties = list(POLITICAL_ENTITIES.keys())
        
        # Build figures list with their party affiliations
        figures_by_party = {}
        for party, data in POLITICAL_ENTITIES.items():
            if "figures" in data:
                figures_by_party[party] = data["figures"]
        
        # Create formatted list for prompt
        party_figure_list = []
        for party, figures in figures_by_party.items():
            party_figure_list.append(f"  - {party}: {', '.join(figures)}")
        
        prompt = f"""You are a political analyst specializing in Bangladesh politics and the upcoming 2026 Bangladesh national elections.

**ALLOWED POLITICAL ENTITIES (ONLY use names from this list):**

**Political Parties:**
{', '.join(allowed_parties)}

**Political Figures by Party:**
{chr(10).join(party_figure_list)}

**Article to Analyze:**
Title: {title}
Content: {content}

**Your Task:**
Analyze this article and return a JSON response with the following structure:

{{
  "summary": "A brief 3-4 sentence summary in BANGLA (বাংলা)",
  "keywords": ["keyword1", "keyword2", "keyword3"],
  "topics": ["Topic 1", "Topic 2"],
  "parties": ["Party1", "Party2"],
  "figures": ["Figure1", "Figure2"],
  "has_election_impact": true or false,
  "election_impact_description": "Brief description in BANGLA about 2026 elections",
  "election_impact_parties": ["Party1", "Party2"]
}}

**CRITICAL INSTRUCTIONS:**

1. **Summary**: Write 3-4 sentences in BANGLA (বাংলা) ONLY, regardless of article language.

2. **Keywords**: Extract 2-3 most important keywords (in English):
   - Political significance
   - Security concerns  
   - Election-related terms
   - Key policy areas
   Examples: "election reform", "security concern", "democracy", "political alliance"

3. **Topics**: Identify exactly 2 main topics from these categories:
   - Election Commission Reform
   - Political Alliance
   - Security Concerns
   - Democracy & Human Rights
   - Economic Policy
   - Judicial Reform
   - Law and Order
   - International Relations
   - Party Strategy
   - Election Preparedness

4. **Parties**: Extract political parties mentioned in the article.
   - ONLY use party names from the allowed list above
   - Use exact canonical names (e.g., "BNP", "Jamaat-e-Islami", "NCP", "Interim Government")
   - If a party is mentioned but not in the allowed list, DO NOT include it
   - Return empty array [] if no allowed parties are mentioned

5. **Figures**: Extract political figures mentioned in the article.
   - ONLY use figure names from the allowed list above
   - Use exact names as shown in the list (e.g., "তারেক রহমান", "নাহিদ ইসলাম", "ড.মুহাম্মদ ইউনূস")
   - If a figure is mentioned but not in the allowed list, DO NOT include it
   - Return empty array [] if no allowed figures are mentioned

6. **Election Impact**: Determine if this article has relevance to the 2026 Bangladesh national elections.
   Set `has_election_impact` to `true` if the article discusses:
   - Election reforms, election commission, or voting systems
   - Party strategies or alliances for 2026 elections
   - Policies that could influence voter decisions
   - Security concerns affecting elections
   - Election preparedness or roadmap

7. **Election Impact Description**: If `has_election_impact` is true, write 1-2 sentences in BANGLA (বাংলা) explaining how this relates to 2026 elections. Otherwise, leave as empty string "".

8. **Election Impact Parties**: List parties affected by the election-related content.
   - ONLY use party names from the allowed list
   - Leave empty array [] if no specific parties are affected

**IMPORTANT RULES:**
- Return ONLY valid JSON, no additional text
- Summary MUST be in BANGLA (বাংলা) regardless of article language
- Election Impact Description MUST be in BANGLA (বাংলা) if provided
- Parties and Figures MUST use exact names from the allowed lists above
- DO NOT invent or add parties/figures not in the allowed lists
- Keywords and topics should be in English for consistency
- If you cannot find any allowed parties/figures, return empty arrays []

Return the JSON now:"""
        
        return prompt
    
    def _validate_analysis(self, analysis: Dict) -> Dict:
        """
        Validate and normalize the LLM analysis response.
        
        Args:
            analysis: Raw analysis dictionary from LLM
        
        Returns:
            Validated and normalized analysis dictionary
        """
        validated = {
            "summary": analysis.get("summary", ""),
            "keywords": analysis.get("keywords", [])[:3],  # Limit to 3
            "topics": analysis.get("topics", [])[:2],  # Limit to 2
            "parties": analysis.get("parties", []),  # NEW: LLM-extracted parties
            "figures": analysis.get("figures", []),  # NEW: LLM-extracted figures
            "has_election_impact": bool(analysis.get("has_election_impact", False)),
            "election_impact_description": analysis.get("election_impact_description", ""),
            "election_impact_parties": analysis.get("election_impact_parties", [])
        }
        
        # Ensure lists are actually lists
        if not isinstance(validated["keywords"], list):
            validated["keywords"] = []
        if not isinstance(validated["topics"], list):
            validated["topics"] = []
        if not isinstance(validated["parties"], list):
            validated["parties"] = []
        if not isinstance(validated["figures"], list):
            validated["figures"] = []
        if not isinstance(validated["election_impact_parties"], list):
            validated["election_impact_parties"] = []
        
        # Convert to strings and limit length
        validated["keywords"] = [str(k)[:50] for k in validated["keywords"][:3]]
        validated["topics"] = [str(t)[:100] for t in validated["topics"][:2]]
        
        # Validate parties against POLITICAL_ENTITIES
        allowed_parties = list(POLITICAL_ENTITIES.keys())
        validated["parties"] = [
            str(p) for p in validated["parties"] 
            if str(p) in allowed_parties
        ]
        
        # Validate figures against POLITICAL_ENTITIES
        allowed_figures = []
        for party_data in POLITICAL_ENTITIES.values():
            if "figures" in party_data:
                allowed_figures.extend(party_data["figures"])
        
        validated["figures"] = [
            str(f) for f in validated["figures"] 
            if str(f) in allowed_figures
        ][:10]  # Limit to 10 figures max
        
        validated["election_impact_parties"] = [
            str(p) for p in validated["election_impact_parties"]
            if str(p) in allowed_parties
        ]
        
        # If no election impact, clear related fields
        if not validated["has_election_impact"]:
            validated["election_impact_description"] = ""
            validated["election_impact_parties"] = []
        
        return validated
    
    def _get_fallback_analysis(self) -> Dict:
        """
        Get fallback analysis when LLM fails.
        
        Returns:
            Basic analysis dictionary
        """
        return {
            "summary": "",
            "keywords": [],
            "topics": [],
            "parties": [],  # NEW
            "figures": [],  # NEW
            "has_election_impact": False,
            "election_impact_description": "",
            "election_impact_parties": []
        }
    
    def batch_analyze(
        self,
        articles: List[Dict],
        delay: float = 2.0
    ) -> List[Dict]:
        """
        Analyze multiple articles in batch with rate limiting.
        
        Args:
            articles: List of article dictionaries
            delay: Delay between API calls in seconds
        
        Returns:
            List of analyzed articles with analysis data
        """
        import time
        
        analyzed_articles = []
        
        for i, article in enumerate(articles):
            try:
                logger.info(f"Analyzing article {i+1}/{len(articles)}: {article.get('title', '')[:50]}...")
                
                # Analyze the article
                analysis = self.analyze_article(article)
                
                # Add analysis to article
                enriched_article = article.copy()
                enriched_article.update(analysis)
                
                analyzed_articles.append(enriched_article)
                
                # Rate limiting
                if i < len(articles) - 1:
                    time.sleep(delay)
                
            except Exception as e:
                logger.error(f"Error analyzing article {i}: {e}")
                # Add article without analysis
                enriched_article = article.copy()
                enriched_article.update(self._get_fallback_analysis())
                analyzed_articles.append(enriched_article)
        
        logger.info(f"Batch analysis complete: {len(analyzed_articles)} articles")
        
        return analyzed_articles


# Convenience function
def analyze_scraped_articles(articles: List[Dict]) -> List[Dict]:
    """
    Analyze scraped articles with LLM.
    
    Args:
        articles: List of scraped articles (already categorized)
    
    Returns:
        List of articles with LLM analysis added
    """
    analyzer = ArticleAnalyzer()
    return analyzer.batch_analyze(articles)


if __name__ == "__main__":
    # Test the analyzer
    print("=" * 80)
    print("ARTICLE ANALYZER TEST")
    print("=" * 80)
    
    sample_article = {
        'title': 'BNP demands independent election commission before 2026 polls',
        'content': '''
        Bangladesh Nationalist Party acting chairman Tareq Rahman today called for 
        the establishment of an independent and impartial election commission before 
        the 2026 national elections. Speaking at a party rally, he emphasized that 
        free and fair elections are impossible without reforms to the electoral system.
        
        Rahman criticized the current interim government's approach to election reforms 
        and demanded immediate action. He also expressed concerns about potential 
        security threats that could disrupt the electoral process.
        
        BNP leaders including Mirza Fakhrul Islam Alamgir echoed these demands, 
        stating that the party would not participate in elections without proper reforms.
        The rally was attended by thousands of supporters who showed solidarity with 
        the party's stance on democratic reforms.
        ''',
        'parties': ['BNP', 'Interim Government'],
        'people': ['Tareq Rahman', 'Mirza Fakhrul Islam Alamgir']
    }
    
    try:
        analyzer = ArticleAnalyzer()
        result = analyzer.analyze_article(sample_article)
        
        print("\n" + "=" * 80)
        print("ANALYSIS RESULT")
        print("=" * 80)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"\nError: {e}")
        print("Make sure GEMINI_API_KEY is set in your .env file")
    
    print("\n" + "=" * 80)
    print("Module ready for use!")
    print("=" * 80)

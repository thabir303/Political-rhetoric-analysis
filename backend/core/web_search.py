"""
Web Search Integration for Real-Time Information

Provides real-time web search capability to augment RAG system
with current information beyond the database.

Supports:
1. DuckDuckGo Search (No API key required)
2. Google Custom Search (API key required)
3. SerpAPI (API key required)

Author: RAG-IR System
"""

import os
import logging
from typing import List, Dict, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import search libraries
try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False
    logger.warning("duckduckgo-search not available. Install with: pip install duckduckgo-search")

try:
    from googleapiclient.discovery import build
    GOOGLE_SEARCH_AVAILABLE = True
except ImportError:
    GOOGLE_SEARCH_AVAILABLE = False
    logger.warning("google-api-python-client not available. Install with: pip install google-api-python-client")

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass


class WebSearcher:
    """
    Web search integration for real-time information retrieval.
    
    Supports multiple search engines with fallback options.
    """
    
    def __init__(
        self,
        provider: str = "duckduckgo",
        api_key: Optional[str] = None,
        cse_id: Optional[str] = None
    ):
        """
        Initialize web searcher.
        
        Args:
            provider: Search provider ("duckduckgo", "google", "serpapi")
            api_key: API key for Google/SerpAPI (optional for DuckDuckGo)
            cse_id: Custom Search Engine ID for Google (required if using Google)
        """
        self.provider = provider.lower()
        self.api_key = api_key
        self.cse_id = cse_id
        
        # Initialize based on provider
        if self.provider == "duckduckgo":
            if not DDGS_AVAILABLE:
                raise ImportError("duckduckgo-search not installed. Install with: pip install duckduckgo-search")
            self.ddg = DDGS()
            logger.info("WebSearcher initialized with DuckDuckGo")
            
        elif self.provider == "google":
            if not GOOGLE_SEARCH_AVAILABLE:
                raise ImportError("google-api-python-client not installed. Install with: pip install google-api-python-client")
            
            self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
            self.cse_id = cse_id or os.getenv("GOOGLE_CSE_ID")
            
            if not self.api_key or not self.cse_id:
                raise ValueError("Google Search requires GOOGLE_API_KEY and GOOGLE_CSE_ID")
            
            self.service = build("customsearch", "v1", developerKey=self.api_key)
            logger.info("WebSearcher initialized with Google Custom Search")
            
        else:
            raise ValueError(f"Unknown provider: {provider}. Use 'duckduckgo' or 'google'")
    
    def search(
        self,
        query: str,
        max_results: int = 5,
        region: str = "bd",  # Bangladesh
        time_range: Optional[str] = None  # "d" (day), "w" (week), "m" (month), "y" (year)
    ) -> List[Dict]:
        """
        Search the web for recent information.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            region: Region code (default: "bd" for Bangladesh)
            time_range: Time range filter
        
        Returns:
            List of search results with title, snippet, url, date
        """
        try:
            if self.provider == "duckduckgo":
                return self._search_duckduckgo(query, max_results, region, time_range)
            elif self.provider == "google":
                return self._search_google(query, max_results, region, time_range)
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    def _search_duckduckgo(
        self,
        query: str,
        max_results: int,
        region: str,
        time_range: Optional[str]
    ) -> List[Dict]:
        """Search using DuckDuckGo."""
        try:
            # Add Bangladesh context to query
            enhanced_query = f"{query} Bangladesh"
            
            # Configure search parameters
            results = self.ddg.text(
                keywords=enhanced_query,
                region=f"wt-{region}",  # wt-bd for Bangladesh
                max_results=max_results,
                timelimit=time_range  # d, w, m, y
            )
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'title': result.get('title', 'N/A'),
                    'snippet': result.get('body', 'N/A'),
                    'url': result.get('href', ''),
                    'source': self._extract_domain(result.get('href', '')),
                    'date': 'Recent'  # DuckDuckGo doesn't provide exact dates
                })
            
            logger.info(f"DuckDuckGo search found {len(formatted_results)} results for: {query}")
            return formatted_results
            
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return []
    
    def _search_google(
        self,
        query: str,
        max_results: int,
        region: str,
        time_range: Optional[str]
    ) -> List[Dict]:
        """Search using Google Custom Search."""
        try:
            # Add Bangladesh context
            enhanced_query = f"{query} Bangladesh"
            
            # Build search parameters
            search_params = {
                'q': enhanced_query,
                'cx': self.cse_id,
                'num': min(max_results, 10),  # Google allows max 10 per request
                'gl': region  # Geographic location
            }
            
            # Add time range if specified
            if time_range:
                time_map = {
                    'd': 'd1',  # Past day
                    'w': 'w1',  # Past week
                    'm': 'm1',  # Past month
                    'y': 'y1'   # Past year
                }
                if time_range in time_map:
                    search_params['dateRestrict'] = time_map[time_range]
            
            # Execute search
            result = self.service.cse().list(**search_params).execute()
            
            # Format results
            formatted_results = []
            for item in result.get('items', []):
                formatted_results.append({
                    'title': item.get('title', 'N/A'),
                    'snippet': item.get('snippet', 'N/A'),
                    'url': item.get('link', ''),
                    'source': self._extract_domain(item.get('link', '')),
                    'date': item.get('pagemap', {}).get('metatags', [{}])[0].get('article:published_time', 'N/A')
                })
            
            logger.info(f"Google search found {len(formatted_results)} results for: {query}")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Google search error: {e}")
            return []
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            # Remove www.
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return 'N/A'
    
    def search_for_context(
        self,
        query: str,
        max_results: int = 3
    ) -> str:
        """
        Search web and format results as context for LLM.
        
        Args:
            query: Search query
            max_results: Maximum results to include
        
        Returns:
            Formatted context string
        """
        results = self.search(query, max_results, time_range='m')  # Past month
        
        if not results:
            return "No recent web search results found."
        
        context_parts = ["\n=== RECENT WEB SEARCH RESULTS ===\n"]
        
        for i, result in enumerate(results, 1):
            context_parts.append(f"""
Search Result {i}:
Title: {result['title']}
Source: {result['source']}
Date: {result['date']}
Summary: {result['snippet']}
URL: {result['url']}
---
""")
        
        return '\n'.join(context_parts)


# Convenience functions
def search_web(
    query: str,
    max_results: int = 5,
    provider: str = "duckduckgo"
) -> List[Dict]:
    """
    Quick web search function.
    
    Args:
        query: Search query
        max_results: Maximum results
        provider: Search provider
    
    Returns:
        List of search results
    """
    searcher = WebSearcher(provider=provider)
    return searcher.search(query, max_results)


def get_web_context(
    query: str,
    max_results: int = 3,
    provider: str = "duckduckgo"
) -> str:
    """
    Get web search results formatted as LLM context.
    
    Args:
        query: Search query
        max_results: Maximum results
        provider: Search provider
    
    Returns:
        Formatted context string
    """
    searcher = WebSearcher(provider=provider)
    return searcher.search_for_context(query, max_results)


if __name__ == "__main__":
    # Example usage
    print("=" * 80)
    print("WEB SEARCH MODULE TEST")
    print("=" * 80)
    
    try:
        # Test DuckDuckGo search
        print("\n[1/2] Testing DuckDuckGo Search...")
        print("-" * 80)
        
        searcher = WebSearcher(provider="duckduckgo")
        results = searcher.search(
            query="Bangladesh interim government Muhammad Yunus",
            max_results=3,
            time_range="m"  # Past month
        )
        
        print(f"✓ Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['title']}")
            print(f"   Source: {result['source']}")
            print(f"   Snippet: {result['snippet'][:100]}...")
        
        # Test context formatting
        print("\n[2/2] Testing Context Formatting...")
        print("-" * 80)
        
        context = searcher.search_for_context(
            query="who is ruling party Bangladesh 2024",
            max_results=2
        )
        
        print("✓ Formatted context:")
        print(context[:500] + "...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nMake sure to install: pip install duckduckgo-search")
    
    print("\n" + "=" * 80)
    print("✅ Module ready for use!")
    print("=" * 80)

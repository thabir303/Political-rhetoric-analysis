"""
Example script demonstrating how to use the RAG-IR API.
"""
import requests
import json
from typing import List, Dict, Any


class RAGIRClient:
    """Client for interacting with the RAG-IR API."""
    
    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        self.base_url = base_url
    
    def check_health(self) -> Dict[str, Any]:
        """Check API health status."""
        response = requests.get(f"{self.base_url}/health")
        return response.json()
    
    def add_article(
        self,
        content: str,
        date: str = None,
        category: str = None,
        persons: List[str] = None,
        title: str = None,
        source: str = None
    ) -> Dict[str, Any]:
        """Add a single article."""
        data = {
            "content": content,
            "metadata": {}
        }
        
        if date:
            data["metadata"]["date"] = date
        if category:
            data["metadata"]["category"] = category
        if persons:
            data["metadata"]["persons"] = persons
        if title:
            data["metadata"]["title"] = title
        if source:
            data["metadata"]["source"] = source
        
        response = requests.post(f"{self.base_url}/articles", json=data)
        return response.json()
    
    def add_articles_bulk(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Add multiple articles in bulk."""
        data = {"articles": articles}
        response = requests.post(f"{self.base_url}/articles/bulk", json=data)
        return response.json()
    
    def query_articles(
        self,
        query: str,
        top_k: int = 5,
        filter_category: str = None,
        filter_date: str = None,
        filter_persons: List[str] = None
    ) -> Dict[str, Any]:
        """Query articles by similarity."""
        data = {
            "query": query,
            "top_k": top_k
        }
        
        if filter_category:
            data["filter_category"] = filter_category
        if filter_date:
            data["filter_date"] = filter_date
        if filter_persons:
            data["filter_persons"] = filter_persons
        
        response = requests.post(f"{self.base_url}/query", json=data)
        return response.json()
    
    def get_article(self, article_id: str) -> Dict[str, Any]:
        """Get a specific article by ID."""
        response = requests.get(f"{self.base_url}/articles/{article_id}")
        return response.json()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        response = requests.get(f"{self.base_url}/stats")
        return response.json()


def main():
    """Example usage of the RAG-IR API."""
    
    # Initialize client
    client = RAGIRClient()
    
    print("=" * 80)
    print("RAG-IR API Example Usage")
    print("=" * 80)
    
    # 1. Check health
    print("\n1. Checking API health...")
    health = client.check_health()
    print(f"Status: {health['status']}")
    print(f"Total articles: {health['total_articles']}")
    
    # 2. Add sample articles
    print("\n2. Adding sample articles...")
    
    sample_articles = [
        {
            "content": "Artificial Intelligence is transforming healthcare by enabling early disease detection and personalized treatment plans. Machine learning algorithms can analyze medical images with high accuracy.",
            "metadata": {
                "date": "2025-10-10",
                "category": "technology",
                "persons": ["Dr. Sarah Johnson", "Prof. Michael Chen"],
                "title": "AI Revolutionizes Healthcare",
                "source": "https://example.com/ai-healthcare"
            }
        },
        {
            "content": "Climate change continues to be a pressing global issue. Recent studies show rising temperatures and extreme weather events are becoming more frequent. World leaders gather to discuss carbon reduction strategies.",
            "metadata": {
                "date": "2025-10-09",
                "category": "environment",
                "persons": ["Dr. Emily Green", "Ambassador John Smith"],
                "title": "Climate Summit Highlights",
                "source": "https://example.com/climate-summit"
            }
        },
        {
            "content": "The stock market experienced significant volatility today as investors reacted to the latest economic indicators. Tech stocks led the decline while energy sector showed gains.",
            "metadata": {
                "date": "2025-10-08",
                "category": "finance",
                "persons": ["Janet Wilson", "Robert Martinez"],
                "title": "Market Update: Tech Stocks Decline",
                "source": "https://example.com/market-update"
            }
        },
        {
            "content": "Breakthrough in quantum computing achieved by researchers at the Quantum Lab. The new quantum processor can solve complex problems exponentially faster than classical computers.",
            "metadata": {
                "date": "2025-10-07",
                "category": "technology",
                "persons": ["Dr. Lisa Wang", "Prof. David Brown"],
                "title": "Quantum Computing Breakthrough",
                "source": "https://example.com/quantum-breakthrough"
            }
        },
        {
            "content": "The upcoming election is heating up with candidates presenting their economic policies. Key issues include healthcare reform, education funding, and infrastructure development.",
            "metadata": {
                "date": "2025-10-06",
                "category": "politics",
                "persons": ["Senator Alice Cooper", "Governor Bob Wilson"],
                "title": "Election 2025: Economic Policies",
                "source": "https://example.com/election-2025"
            }
        }
    ]
    
    # Add articles in bulk
    result = client.add_articles_bulk(sample_articles)
    print(f"Inserted {result['inserted_count']} articles")
    
    # 3. Query examples
    print("\n3. Querying articles...")
    
    # Query 1: General search
    print("\n   Query 1: 'artificial intelligence technology'")
    results = client.query_articles("artificial intelligence technology", top_k=3)
    print(f"   Found {results['total_results']} results (in {results['processing_time']:.3f}s)")
    for i, result in enumerate(results['results'], 1):
        print(f"   {i}. {result['metadata'].get('title', 'Untitled')} (distance: {result['distance']:.4f})")
    
    # Query 2: With category filter
    print("\n   Query 2: 'recent developments' (category: technology)")
    results = client.query_articles(
        "recent developments",
        top_k=5,
        filter_category="technology"
    )
    print(f"   Found {results['total_results']} results")
    for i, result in enumerate(results['results'], 1):
        print(f"   {i}. {result['metadata'].get('title', 'Untitled')}")
    
    # Query 3: Search by person
    print("\n   Query 3: Articles mentioning specific person")
    results = client.query_articles(
        "Dr. Lisa Wang",
        top_k=5
    )
    print(f"   Found {results['total_results']} results")
    for i, result in enumerate(results['results'], 1):
        persons = result['metadata'].get('persons', '')
        if isinstance(persons, str):
            persons = persons.split(',')
        print(f"   {i}. {result['metadata'].get('title', 'Untitled')} - Persons: {persons}")
    
    # 4. Get statistics
    print("\n4. Database statistics...")
    stats = client.get_stats()
    print(f"   {json.dumps(stats['statistics'], indent=2)}")
    
    print("\n" + "=" * 80)
    print("Example completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the API.")
        print("Make sure the server is running: python main.py")
    except Exception as e:
        print(f"Error: {e}")

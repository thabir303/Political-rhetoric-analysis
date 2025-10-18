"""
Political Storage Module

Manages party-wise and figure-wise article storage in separate ChromaDB collections.
Allows independent scraping → storage and later analysis operations.
"""

import os
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
from pathlib import Path

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers not available")


# Political parties and their figures
POLITICAL_STRUCTURE = {
    "bnp": {
        "name": "Bangladesh Nationalist Party (BNP)",
        "collection_name": "bnp_articles",
        "figures": [
            "Tareq Rahman", "Tarique Rahman", "তারেক রহমান",
            "Mirza Fakhrul", "Mirza Fakhrul Islam Alamgir", "মির্জা ফখরুল",
            "Salahuddin Ahmed", "সালাউদ্দিন আহমেদ"
        ],
        "keywords": ["BNP", "Bangladesh Nationalist Party", "বিএনপি", "বাংলাদেশ জাতীয়তাবাদী দল"]
    },
    "ji": {
        "name": "Jamaat-e-Islami (JI)",
        "collection_name": "ji_articles",
        "figures": [
            "Shafiqur Rahman", "শফিকুর রহমান",
            "Abu Taher", "আবু তাহের",
            "Golam Parwar", "গোলাম পারওয়ার"
        ],
        "keywords": ["Jamaat", "Jamaat-e-Islami", "JI", "জামায়াত", "জামায়াতে ইসলামী"]
    },
    "ncp": {
        "name": "National Citizens Party (NCP)",
        "collection_name": "ncp_articles",
        "figures": [
            "Nahid Islam", "নাহিদ ইসলাম",
            "Sarjis Alam", "সরজিস আলম",
            "Hasnat Abdullah", "হাসনাত আবদুল্লাহ",
            "Nasiruddin Patwary", "নাসিরউদ্দিন পাটোয়ারী",
            "Akhter Hossain", "আখতার হোসেন",
            "Tasnim Zara"
        ],
        "keywords": ["National Citizens Party", "NCP", "জাতীয় নাগরিক পার্টি"]
    },
    "ab_party": {
        "name": "Amar Bangladesh Party",
        "collection_name": "ab_party_articles",
        "figures": [
            "Barrister Fuad", "ব্যারিস্টার ফুয়াদ"
        ],
        "keywords": ["AB Party", "Amar Bangladesh Party", "আমার বাংলাদেশ পার্টি"]
    },
    "gop": {
        "name": "Gono Odhikar Parishad (GOP)",
        "collection_name": "gop_articles",
        "figures": [
            "Nurul Haque", "নুরুল হক",
            "Rashed", "রাশেদ"
        ],
        "keywords": ["Gono Odhikar Parishad", "GOP", "গণ অধিকার পরিষদ"]
    },
    "gono_songhati": {
        "name": "Gono Songhati Andolon",
        "collection_name": "gono_songhati_articles",
        "figures": [
            "Jonayed Saki", "জোনায়েদ সাকী"
        ],
        "keywords": ["Gono Songhati Andolon", "গণ সংহতি আন্দোলন"]
    },
    "interim_government": {
        "name": "Interim Government",
        "collection_name": "interim_government_articles",
        "figures": [
            "Dr. Yunus", "ড. ইউনূস",
            "Shafiqul Alam", "শফিকুল আলম",
            "Mahfuz Alam", "মাহফুজ আলম",
            "Asif Nazrul", "আসিফ নজরুল",
            "Rizwana Hasan", "রিজওয়ানা হাসান",
            "Lt Gen Jahangir Alam Chowdhury", "জাহাঙ্গীর আলম চৌধুরী",
            "Ali Riaz",
            "Badiul Alam Majumder", "বদিউল আলম মজুমদার",
            "AMM Nasir Uddin",
            "General Waqar Uz Zaman", "ওয়াকার উজ জামান",
            "IGP Baharul Alam",
            "DMP Commissioner Sajjat Ali",
            "Mahfuz Anam", "মাহফুজ আনাম",
            "Mahmudur Rahman", "মাহমুদুর রহমান"
        ],
        "keywords": ["Interim Government", "অন্তর্বর্তী সরকার"]
    }
}


class PoliticalArticleStorage:
    """
    Storage manager for party-wise and figure-wise articles.
    
    Creates separate ChromaDB collections for each political party
    and organizes articles by political figures within each collection.
    """
    
    def __init__(
        self,
        persist_directory: str = "./political_chroma_db",
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize the political article storage.
        
        Args:
            persist_directory: Directory for persistent storage
            embedding_model: Name of the embedding model
        """
        self.persist_directory = Path(persist_directory)
        self.embedding_model_name = embedding_model
        
        # Create persist directory
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        logger.info(f"Initializing Political Storage at: {self.persist_directory}")
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize embedding function
        logger.info(f"Loading embedding model: {embedding_model}")
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=embedding_model
            )
        else:
            logger.warning("Using default embedding function")
            self.embedding_function = None
        
        # Initialize collections for each party
        self.collections = {}
        self._initialize_all_collections()
        
        logger.info(f"Political Storage initialized successfully")
        self._print_storage_stats()
    
    def _initialize_all_collections(self):
        """Initialize collections for all political parties."""
        for party_id, party_info in POLITICAL_STRUCTURE.items():
            collection_name = party_info["collection_name"]
            try:
                # Try to get existing collection
                collection = self.client.get_collection(
                    name=collection_name,
                    embedding_function=self.embedding_function
                )
                logger.info(f"Retrieved existing collection: {collection_name}")
            except Exception:
                # Create new collection
                collection = self.client.create_collection(
                    name=collection_name,
                    embedding_function=self.embedding_function,
                    metadata={
                        "description": f"Articles related to {party_info['name']}",
                        "party_id": party_id,
                        "party_name": party_info['name']
                    }
                )
                logger.info(f"Created new collection: {collection_name}")
            
            self.collections[party_id] = collection
    
    def _print_storage_stats(self):
        """Print statistics for all collections."""
        logger.info("\n=== Political Storage Statistics ===")
        for party_id, collection in self.collections.items():
            party_name = POLITICAL_STRUCTURE[party_id]["name"]
            count = collection.count()
            logger.info(f"{party_name}: {count} articles")
        logger.info("=" * 36)
    
    def detect_party_and_figures(self, text: str, title: str = "") -> Dict[str, Any]:
        """
        Detect which party and figures are mentioned in the article.
        
        Args:
            text: Article text
            title: Article title
            
        Returns:
            Dictionary with party_id, party_name, and mentioned_figures
        """
        combined_text = f"{title} {text}".lower()
        
        results = []
        
        # Check each party
        for party_id, party_info in POLITICAL_STRUCTURE.items():
            score = 0
            mentioned_figures = []
            
            # Check party keywords
            for keyword in party_info["keywords"]:
                if keyword.lower() in combined_text:
                    score += 2
            
            # Check political figures
            for figure in party_info["figures"]:
                if figure.lower() in combined_text:
                    score += 5
                    # Normalize figure name
                    normalized_figure = figure.split()[0]  # Take first name
                    if normalized_figure not in mentioned_figures:
                        mentioned_figures.append(figure)
            
            if score > 0:
                results.append({
                    "party_id": party_id,
                    "party_name": party_info["name"],
                    "score": score,
                    "mentioned_figures": mentioned_figures
                })
        
        # Sort by score and return highest
        if results:
            results.sort(key=lambda x: x["score"], reverse=True)
            return results[0]
        
        return None
    
    def store_article(
        self,
        article: Dict[str, Any],
        party_id: Optional[str] = None
    ) -> bool:
        """
        Store an article in the appropriate party collection.
        
        Args:
            article: Article dictionary with keys: title, content, url, date, source
            party_id: Optional party ID. If None, will auto-detect.
            
        Returns:
            True if stored successfully, False otherwise
        """
        try:
            # Auto-detect party if not provided
            if party_id is None:
                detection = self.detect_party_and_figures(
                    article.get("content", ""),
                    article.get("title", "")
                )
                if detection is None:
                    logger.warning(f"No political party detected for article: {article.get('title', 'Unknown')}")
                    return False
                party_id = detection["party_id"]
                mentioned_figures = detection["mentioned_figures"]
            else:
                # If party_id provided, still detect figures
                detection = self.detect_party_and_figures(
                    article.get("content", ""),
                    article.get("title", "")
                )
                mentioned_figures = detection["mentioned_figures"] if detection else []
            
            # Get collection
            collection = self.collections[party_id]
            
            # Prepare metadata
            metadata = {
                "title": article.get("title", ""),
                "url": article.get("url", ""),
                "date": article.get("date", ""),
                "source": article.get("source", ""),
                "party_id": party_id,
                "party_name": POLITICAL_STRUCTURE[party_id]["name"],
                "mentioned_figures": ", ".join(mentioned_figures),
                "figure_count": len(mentioned_figures),
                "stored_at": datetime.now().isoformat()
            }
            
            # Add optional fields
            if "category" in article:
                metadata["category"] = article["category"]
            if "keywords" in article:
                metadata["keywords"] = ", ".join(article["keywords"]) if isinstance(article["keywords"], list) else article["keywords"]
            
            # Generate unique ID
            article_id = f"{party_id}_{article.get('url', '').replace('/', '_').replace(':', '_')}"
            if not article_id or article_id == f"{party_id}_":
                article_id = f"{party_id}_{datetime.now().timestamp()}"
            
            # Store in collection
            collection.add(
                ids=[article_id],
                documents=[article.get("content", "")],
                metadatas=[metadata]
            )
            
            logger.info(f"Stored article in {party_id} collection: {article.get('title', 'Unknown')[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error storing article: {str(e)}")
            return False
    
    def store_articles_bulk(
        self,
        articles: List[Dict[str, Any]],
        party_id: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Store multiple articles.
        
        Args:
            articles: List of article dictionaries
            party_id: Optional party ID for all articles. If None, will auto-detect each.
            
        Returns:
            Dictionary with success and failure counts per party
        """
        stats = {}
        
        for article in articles:
            detection_party_id = party_id
            if detection_party_id is None:
                detection = self.detect_party_and_figures(
                    article.get("content", ""),
                    article.get("title", "")
                )
                if detection:
                    detection_party_id = detection["party_id"]
            
            if detection_party_id:
                if detection_party_id not in stats:
                    stats[detection_party_id] = {"success": 0, "failed": 0}
                
                if self.store_article(article, detection_party_id):
                    stats[detection_party_id]["success"] += 1
                else:
                    stats[detection_party_id]["failed"] += 1
        
        # Print summary
        logger.info("\n=== Bulk Storage Summary ===")
        for party_id, counts in stats.items():
            party_name = POLITICAL_STRUCTURE[party_id]["name"]
            logger.info(f"{party_name}: {counts['success']} success, {counts['failed']} failed")
        logger.info("=" * 28)
        
        return stats
    
    def get_articles_by_party(
        self,
        party_id: str,
        limit: int = 10,
        where: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Get articles from a specific party collection.
        
        Args:
            party_id: Party identifier
            limit: Maximum number of articles to return
            where: Optional metadata filter
            
        Returns:
            List of articles with metadata
        """
        if party_id not in self.collections:
            logger.error(f"Invalid party_id: {party_id}")
            return []
        
        collection = self.collections[party_id]
        
        try:
            results = collection.get(
                limit=limit,
                where=where
            )
            
            articles = []
            for i in range(len(results["ids"])):
                article = {
                    "id": results["ids"][i],
                    "content": results["documents"][i] if "documents" in results else "",
                    "metadata": results["metadatas"][i] if "metadatas" in results else {}
                }
                articles.append(article)
            
            return articles
            
        except Exception as e:
            logger.error(f"Error retrieving articles: {str(e)}")
            return []
    
    def get_articles_by_figure(
        self,
        figure_name: str,
        party_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get articles mentioning a specific political figure.
        
        Args:
            figure_name: Name of the political figure
            party_id: Optional party to search in. If None, searches all parties.
            limit: Maximum number of articles to return
            
        Returns:
            List of articles mentioning the figure
        """
        articles = []
        
        # Determine which collections to search
        collections_to_search = {}
        if party_id:
            if party_id in self.collections:
                collections_to_search[party_id] = self.collections[party_id]
        else:
            collections_to_search = self.collections
        
        # Search each collection
        for pid, collection in collections_to_search.items():
            try:
                # Search in mentioned_figures metadata
                results = collection.get(
                    limit=limit,
                    where={
                        "mentioned_figures": {
                            "$contains": figure_name
                        }
                    }
                )
                
                for i in range(len(results["ids"])):
                    article = {
                        "id": results["ids"][i],
                        "content": results["documents"][i] if "documents" in results else "",
                        "metadata": results["metadatas"][i] if "metadatas" in results else {},
                        "party_id": pid
                    }
                    articles.append(article)
                    
            except Exception as e:
                logger.error(f"Error searching in {pid} collection: {str(e)}")
        
        return articles[:limit]
    
    def search_articles(
        self,
        query: str,
        party_id: Optional[str] = None,
        limit: int = 10,
        where: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search across party collections.
        
        Args:
            query: Search query
            party_id: Optional party to search in. If None, searches all parties.
            limit: Maximum number of results per collection
            where: Optional metadata filter
            
        Returns:
            List of relevant articles with similarity scores
        """
        results = []
        
        # Determine which collections to search
        collections_to_search = {}
        if party_id:
            if party_id in self.collections:
                collections_to_search[party_id] = self.collections[party_id]
        else:
            collections_to_search = self.collections
        
        # Search each collection
        for pid, collection in collections_to_search.items():
            try:
                search_results = collection.query(
                    query_texts=[query],
                    n_results=limit,
                    where=where
                )
                
                if search_results and len(search_results["ids"]) > 0:
                    for i in range(len(search_results["ids"][0])):
                        result = {
                            "id": search_results["ids"][0][i],
                            "content": search_results["documents"][0][i],
                            "metadata": search_results["metadatas"][0][i],
                            "distance": search_results["distances"][0][i] if "distances" in search_results else None,
                            "party_id": pid,
                            "party_name": POLITICAL_STRUCTURE[pid]["name"]
                        }
                        results.append(result)
                        
            except Exception as e:
                logger.error(f"Error searching in {pid} collection: {str(e)}")
        
        # Sort by distance (similarity)
        if results:
            results.sort(key=lambda x: x.get("distance", float("inf")))
        
        return results[:limit]
    
    def get_party_statistics(self, party_id: str) -> Dict[str, Any]:
        """
        Get statistics for a specific party collection.
        
        Args:
            party_id: Party identifier
            
        Returns:
            Dictionary with collection statistics
        """
        if party_id not in self.collections:
            logger.error(f"Invalid party_id: {party_id}")
            return {}
        
        collection = self.collections[party_id]
        party_info = POLITICAL_STRUCTURE[party_id]
        
        stats = {
            "party_id": party_id,
            "party_name": party_info["name"],
            "total_articles": collection.count(),
            "figures": party_info["figures"],
            "figure_count": len(party_info["figures"])
        }
        
        # Get figure-wise article counts
        figure_stats = {}
        for figure in party_info["figures"]:
            try:
                results = collection.get(
                    where={
                        "mentioned_figures": {
                            "$contains": figure
                        }
                    }
                )
                figure_stats[figure] = len(results["ids"]) if results else 0
            except:
                figure_stats[figure] = 0
        
        stats["figure_article_counts"] = figure_stats
        
        return stats
    
    def get_all_statistics(self) -> Dict[str, Any]:
        """
        Get statistics for all party collections.
        
        Returns:
            Dictionary with all collection statistics
        """
        all_stats = {
            "total_collections": len(self.collections),
            "parties": {}
        }
        
        total_articles = 0
        for party_id in self.collections:
            party_stats = self.get_party_statistics(party_id)
            all_stats["parties"][party_id] = party_stats
            total_articles += party_stats["total_articles"]
        
        all_stats["total_articles"] = total_articles
        
        return all_stats
    
    def delete_collection(self, party_id: str) -> bool:
        """
        Delete a party collection.
        
        Args:
            party_id: Party identifier
            
        Returns:
            True if deleted successfully
        """
        if party_id not in self.collections:
            logger.error(f"Invalid party_id: {party_id}")
            return False
        
        try:
            collection_name = POLITICAL_STRUCTURE[party_id]["collection_name"]
            self.client.delete_collection(name=collection_name)
            del self.collections[party_id]
            logger.info(f"Deleted collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting collection: {str(e)}")
            return False
    
    def reset_all_collections(self) -> bool:
        """
        Delete all party collections and reinitialize.
        
        Returns:
            True if reset successfully
        """
        try:
            for party_id in list(self.collections.keys()):
                self.delete_collection(party_id)
            
            # Reinitialize
            self._initialize_all_collections()
            logger.info("All collections reset successfully")
            return True
        except Exception as e:
            logger.error(f"Error resetting collections: {str(e)}")
            return False


# Convenience function
def create_political_storage(persist_directory: str = "./political_chroma_db") -> PoliticalArticleStorage:
    """
    Create a political article storage instance.
    
    Args:
        persist_directory: Directory for persistent storage
        
    Returns:
        PoliticalArticleStorage instance
    """
    return PoliticalArticleStorage(persist_directory=persist_directory)


if __name__ == "__main__":
    # Example usage
    storage = create_political_storage()
    
    # Print statistics
    stats = storage.get_all_statistics()
    print("\n=== Political Storage Statistics ===")
    print(f"Total Articles: {stats['total_articles']}")
    print(f"Total Collections: {stats['total_collections']}")
    for party_id, party_stats in stats["parties"].items():
        print(f"\n{party_stats['party_name']}:")
        print(f"  Total Articles: {party_stats['total_articles']}")
        print(f"  Political Figures: {party_stats['figure_count']}")

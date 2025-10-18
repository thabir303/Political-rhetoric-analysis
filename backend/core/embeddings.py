"""
Embeddings Generation Module

Generates sentence embeddings for articles using sentence-transformers.
Provides utilities for embedding storage, retrieval, and similarity search.
"""

import os
import json
import pickle
from typing import List, Dict, Optional, Union, Tuple
import logging
from pathlib import Path
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.error("sentence-transformers not available. Please install: pip install sentence-transformers")

# Try to import numpy
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logger.error("numpy not available. Please install: pip install numpy")


class EmbeddingGenerator:
    """
    Generate and manage sentence embeddings for articles.
    
    Uses sentence-transformers with all-MiniLM-L6-v2 model (384 dimensions).
    Provides caching and batch processing capabilities.
    """
    
    def __init__(
        self,
        model_name: str = 'all-MiniLM-L6-v2',
        cache_dir: Optional[str] = None,
        device: Optional[str] = None
    ):
        """
        Initialize the embedding generator.
        
        Args:
            model_name: Name of the sentence-transformers model
            cache_dir: Directory to cache embeddings (optional)
            device: Device to use ('cpu', 'cuda', or None for auto-detect)
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers is required. "
                "Install with: pip install sentence-transformers"
            )
        
        self.model_name = model_name
        self.cache_dir = cache_dir
        self.device = device
        
        # Initialize model
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name, device=device)
        logger.info(f"Model loaded successfully. Embedding dimension: {self.get_embedding_dimension()}")
        
        # Setup cache
        if cache_dir:
            self.cache_path = Path(cache_dir)
            self.cache_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Embedding cache directory: {self.cache_path}")
        else:
            self.cache_path = None
        
        # In-memory cache
        self._memory_cache: Dict[str, np.ndarray] = {}
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by the model.
        
        Returns:
            Embedding dimension (384 for all-MiniLM-L6-v2)
        """
        return self.model.get_sentence_embedding_dimension()
    
    def generate_embeddings(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 32,
        show_progress: bool = False,
        normalize: bool = True
    ) -> Union[np.ndarray, List[np.ndarray]]:
        """
        Generate embeddings for one or more texts.
        
        Args:
            texts: Single text string or list of texts
            batch_size: Batch size for processing
            show_progress: Show progress bar
            normalize: Normalize embeddings to unit length
        
        Returns:
            Single embedding array or list of embedding arrays
        """
        # Handle single text
        if isinstance(texts, str):
            embedding = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                normalize_embeddings=normalize
            )
            return embedding
        
        # Handle list of texts
        if not texts:
            return []
        
        logger.info(f"Generating embeddings for {len(texts)} texts...")
        
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            normalize_embeddings=normalize,
            convert_to_numpy=True
        )
        
        logger.info(f"Generated {len(embeddings)} embeddings of dimension {embeddings.shape[1]}")
        
        return embeddings
    
    def generate_article_embeddings(
        self,
        articles: List[Dict],
        text_field: str = 'content',
        title_field: Optional[str] = 'title',
        combine_title_content: bool = True,
        batch_size: int = 32,
        show_progress: bool = True
    ) -> List[Dict]:
        """
        Generate embeddings for a list of articles.
        
        Args:
            articles: List of article dictionaries
            text_field: Field name for article content
            title_field: Field name for article title (optional)
            combine_title_content: Combine title and content for embedding
            batch_size: Batch size for processing
            show_progress: Show progress bar
        
        Returns:
            List of dictionaries with original article data + 'embedding' field
        """
        if not articles:
            logger.warning("No articles provided")
            return []
        
        # Prepare texts for embedding
        texts = []
        for article in articles:
            if combine_title_content and title_field and title_field in article:
                # Combine title and content
                title = article.get(title_field, '')
                content = article.get(text_field, '')
                text = f"{title} {content}".strip()
            else:
                # Use content only
                text = article.get(text_field, '')
            
            texts.append(text)
        
        # Generate embeddings
        embeddings = self.generate_embeddings(
            texts,
            batch_size=batch_size,
            show_progress=show_progress
        )
        
        # Add embeddings to articles
        enriched_articles = []
        for i, article in enumerate(articles):
            enriched_article = article.copy()
            enriched_article['embedding'] = embeddings[i]
            enriched_article['embedding_dimension'] = len(embeddings[i])
            enriched_articles.append(enriched_article)
        
        logger.info(f"Added embeddings to {len(enriched_articles)} articles")
        
        return enriched_articles
    
    def compute_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray,
        metric: str = 'cosine'
    ) -> float:
        """
        Compute similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            metric: Similarity metric ('cosine', 'euclidean', 'dot')
        
        Returns:
            Similarity score
        """
        if metric == 'cosine':
            # Cosine similarity
            similarity = np.dot(embedding1, embedding2) / (
                np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
            )
        elif metric == 'dot':
            # Dot product (assumes normalized embeddings)
            similarity = np.dot(embedding1, embedding2)
        elif metric == 'euclidean':
            # Euclidean distance (inverted to similarity)
            distance = np.linalg.norm(embedding1 - embedding2)
            similarity = 1 / (1 + distance)
        else:
            raise ValueError(f"Unknown metric: {metric}")
        
        return float(similarity)
    
    def find_similar_articles(
        self,
        query_embedding: np.ndarray,
        article_embeddings: List[np.ndarray],
        articles: List[Dict],
        top_k: int = 5,
        metric: str = 'cosine'
    ) -> List[Dict]:
        """
        Find most similar articles to a query embedding.
        
        Args:
            query_embedding: Query embedding vector
            article_embeddings: List of article embeddings
            articles: List of article dictionaries
            top_k: Number of top results to return
            metric: Similarity metric
        
        Returns:
            List of dictionaries with article data and similarity scores
        """
        if len(article_embeddings) != len(articles):
            raise ValueError("Number of embeddings must match number of articles")
        
        # Compute similarities
        similarities = []
        for i, article_embedding in enumerate(article_embeddings):
            similarity = self.compute_similarity(
                query_embedding,
                article_embedding,
                metric=metric
            )
            similarities.append({
                'article': articles[i],
                'similarity': similarity,
                'index': i
            })
        
        # Sort by similarity
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Return top-k
        return similarities[:top_k]
    
    def search_by_query(
        self,
        query: str,
        articles: List[Dict],
        top_k: int = 5,
        text_field: str = 'content',
        title_field: Optional[str] = 'title',
        combine_title_content: bool = True,
        metric: str = 'cosine'
    ) -> List[Dict]:
        """
        Search articles by natural language query.
        
        Args:
            query: Search query text
            articles: List of article dictionaries
            top_k: Number of results to return
            text_field: Field name for article content
            title_field: Field name for article title
            combine_title_content: Combine title and content
            metric: Similarity metric
        
        Returns:
            List of most relevant articles with similarity scores
        """
        # Generate query embedding
        query_embedding = self.generate_embeddings(query)
        
        # Generate article embeddings if not already present
        if 'embedding' not in articles[0]:
            articles = self.generate_article_embeddings(
                articles,
                text_field=text_field,
                title_field=title_field,
                combine_title_content=combine_title_content,
                show_progress=False
            )
        
        # Extract embeddings
        article_embeddings = [article['embedding'] for article in articles]
        
        # Find similar articles
        results = self.find_similar_articles(
            query_embedding,
            article_embeddings,
            articles,
            top_k=top_k,
            metric=metric
        )
        
        return results
    
    def save_embeddings(
        self,
        embeddings: Union[np.ndarray, List[np.ndarray]],
        filepath: str,
        metadata: Optional[Dict] = None
    ):
        """
        Save embeddings to disk.
        
        Args:
            embeddings: Embedding array or list of arrays
            filepath: Path to save file
            metadata: Optional metadata to save with embeddings
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Prepare data
        data = {
            'embeddings': embeddings,
            'metadata': metadata or {},
            'model_name': self.model_name,
            'embedding_dimension': self.get_embedding_dimension()
        }
        
        # Save based on file extension
        if filepath.suffix == '.pkl':
            with open(filepath, 'wb') as f:
                pickle.dump(data, f)
        elif filepath.suffix == '.npy':
            np.save(filepath, embeddings)
            # Save metadata separately
            if metadata:
                metadata_path = filepath.with_suffix('.json')
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
        else:
            # Default to pickle
            with open(filepath, 'wb') as f:
                pickle.dump(data, f)
        
        logger.info(f"Saved embeddings to: {filepath}")
    
    def load_embeddings(
        self,
        filepath: str
    ) -> Tuple[Union[np.ndarray, List[np.ndarray]], Dict]:
        """
        Load embeddings from disk.
        
        Args:
            filepath: Path to load file
        
        Returns:
            Tuple of (embeddings, metadata)
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"Embeddings file not found: {filepath}")
        
        # Load based on file extension
        if filepath.suffix == '.pkl':
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
            embeddings = data.get('embeddings')
            metadata = data.get('metadata', {})
        elif filepath.suffix == '.npy':
            embeddings = np.load(filepath)
            # Load metadata separately
            metadata_path = filepath.with_suffix('.json')
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
            else:
                metadata = {}
        else:
            # Try pickle
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
            embeddings = data.get('embeddings')
            metadata = data.get('metadata', {})
        
        logger.info(f"Loaded embeddings from: {filepath}")
        
        return embeddings, metadata
    
    def cache_embeddings(
        self,
        key: str,
        embedding: np.ndarray
    ):
        """
        Cache an embedding in memory.
        
        Args:
            key: Cache key (e.g., article ID or hash)
            embedding: Embedding to cache
        """
        self._memory_cache[key] = embedding
    
    def get_cached_embedding(
        self,
        key: str
    ) -> Optional[np.ndarray]:
        """
        Retrieve cached embedding.
        
        Args:
            key: Cache key
        
        Returns:
            Cached embedding or None if not found
        """
        return self._memory_cache.get(key)
    
    def clear_cache(self):
        """Clear the in-memory embedding cache."""
        self._memory_cache.clear()
        logger.info("Cleared embedding cache")
    
    def get_cache_size(self) -> int:
        """Get number of embeddings in cache."""
        return len(self._memory_cache)


# Convenience functions
def generate_embeddings(
    texts: Union[str, List[str]],
    model_name: str = 'all-MiniLM-L6-v2',
    batch_size: int = 32,
    show_progress: bool = False,
    normalize: bool = True
) -> Union[np.ndarray, List[np.ndarray]]:
    """
    Quick function to generate embeddings without creating an EmbeddingGenerator instance.
    
    Args:
        texts: Single text or list of texts
        model_name: Name of sentence-transformers model
        batch_size: Batch size for processing
        show_progress: Show progress bar
        normalize: Normalize embeddings
    
    Returns:
        Embedding(s)
    """
    generator = EmbeddingGenerator(model_name=model_name)
    return generator.generate_embeddings(
        texts,
        batch_size=batch_size,
        show_progress=show_progress,
        normalize=normalize
    )


def generate_article_embeddings(
    articles: List[Dict],
    model_name: str = 'all-MiniLM-L6-v2',
    text_field: str = 'content',
    title_field: Optional[str] = 'title',
    combine_title_content: bool = True,
    batch_size: int = 32,
    show_progress: bool = True
) -> List[Dict]:
    """
    Quick function to generate article embeddings.
    
    Args:
        articles: List of article dictionaries
        model_name: Name of sentence-transformers model
        text_field: Field name for content
        title_field: Field name for title
        combine_title_content: Combine title and content
        batch_size: Batch size
        show_progress: Show progress
    
    Returns:
        Articles with embeddings added
    """
    generator = EmbeddingGenerator(model_name=model_name)
    return generator.generate_article_embeddings(
        articles,
        text_field=text_field,
        title_field=title_field,
        combine_title_content=combine_title_content,
        batch_size=batch_size,
        show_progress=show_progress
    )


def search_articles(
    query: str,
    articles: List[Dict],
    top_k: int = 5,
    model_name: str = 'all-MiniLM-L6-v2'
) -> List[Dict]:
    """
    Quick function to search articles by query.
    
    Args:
        query: Search query
        articles: List of articles
        top_k: Number of results
        model_name: Model name
    
    Returns:
        Top-k most relevant articles
    """
    generator = EmbeddingGenerator(model_name=model_name)
    return generator.search_by_query(query, articles, top_k=top_k)


if __name__ == "__main__":
    # Example usage
    print("=" * 80)
    print("EMBEDDING GENERATION MODULE")
    print("=" * 80)
    
    # Sample articles
    sample_articles = [
        {
            'id': '1',
            'title': 'BNP Rally on Election Reforms',
            'content': '''
            Tareq Rahman delivered a powerful speech at a BNP rally, calling for
            comprehensive election reforms. He emphasized the importance of free
            and fair elections for democracy.
            ''',
            'date': '2024-10-05'
        },
        {
            'id': '2',
            'title': 'Dr. Yunus Discusses Economic Reforms',
            'content': '''
            Chief Adviser Dr. Muhammad Yunus outlined the interim government's
            economic reform agenda, focusing on inflation control and GDP growth.
            ''',
            'date': '2024-10-06'
        },
        {
            'id': '3',
            'title': 'Judiciary Independence Debate',
            'content': '''
            Legal experts debate the independence of the judiciary system.
            Supreme Court judges express concerns about political interference
            in judicial matters.
            ''',
            'date': '2024-10-07'
        }
    ]
    
    print(f"\nSample Articles: {len(sample_articles)}")
    for article in sample_articles:
        print(f"  - {article['title']}")
    
    # Initialize generator
    print("\n" + "-" * 80)
    print("Initializing Embedding Generator...")
    generator = EmbeddingGenerator(model_name='all-MiniLM-L6-v2')
    
    print(f"✓ Model: {generator.model_name}")
    print(f"✓ Embedding dimension: {generator.get_embedding_dimension()}")
    
    # Generate embeddings
    print("\n" + "-" * 80)
    print("Generating Article Embeddings...")
    enriched_articles = generator.generate_article_embeddings(
        sample_articles,
        show_progress=False
    )
    
    print(f"✓ Generated embeddings for {len(enriched_articles)} articles")
    print(f"✓ Embedding shape: {enriched_articles[0]['embedding'].shape}")
    
    # Test similarity search
    print("\n" + "-" * 80)
    print("Testing Similarity Search...")
    
    queries = [
        "election reforms and democracy",
        "economic policy and inflation",
        "court system independence"
    ]
    
    for query in queries:
        print(f"\nQuery: '{query}'")
        results = generator.search_by_query(
            query,
            enriched_articles,
            top_k=2
        )
        
        print("Top Results:")
        for i, result in enumerate(results, 1):
            article = result['article']
            similarity = result['similarity']
            print(f"  {i}. {article['title']}")
            print(f"     Similarity: {similarity:.4f}")
    
    # Test saving/loading
    print("\n" + "-" * 80)
    print("Testing Save/Load...")
    
    # Extract embeddings
    embeddings = [article['embedding'] for article in enriched_articles]
    metadata = {
        'num_articles': len(sample_articles),
        'model': 'all-MiniLM-L6-v2',
        'date': '2024-10-10'
    }
    
    # Save
    test_file = 'test_embeddings.pkl'
    generator.save_embeddings(embeddings, test_file, metadata)
    print(f"✓ Saved embeddings to: {test_file}")
    
    # Load
    loaded_embeddings, loaded_metadata = generator.load_embeddings(test_file)
    print(f"✓ Loaded embeddings: {len(loaded_embeddings)} items")
    print(f"✓ Metadata: {loaded_metadata}")
    
    # Cleanup
    import os
    if os.path.exists(test_file):
        os.remove(test_file)
        print(f"✓ Cleaned up test file")
    
    print("\n" + "=" * 80)
    print("✅ Module ready for use!")
    print("=" * 80)

"""
Vector database operations using ChromaDB.
"""
import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional, Tuple
import uuid
import logging
from datetime import datetime

from backend.config import settings

logger = logging.getLogger(__name__)


class VectorStore:
    """Manages vector database operations with ChromaDB."""
    
    def __init__(self):
        """Initialize ChromaDB client and embedding model."""
        self.client = None
        self.collection = None
        self.embedding_model = None
        self._initialize()
    
    def _initialize(self):
        """Initialize database connection and embedding model."""
        try:
            # Initialize ChromaDB client with persistence
            self.client = chromadb.Client(
                ChromaSettings(
                    persist_directory=settings.chroma_persist_directory,
                    anonymized_telemetry=False,
                )
            )
            
            # Get or create collection with metadata indexing
            self.collection = self.client.get_or_create_collection(
                name=settings.chroma_collection_name,
                metadata={
                    "hnsw:space": "cosine",  # Use cosine similarity
                    "description": "Article embeddings with metadata",
                }
            )
            
            # Initialize embedding model
            logger.info(f"Loading embedding model: {settings.embedding_model}")
            self.embedding_model = SentenceTransformer(settings.embedding_model)
            
            logger.info("Vector store initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise
    
    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of float values representing the embedding
        """
        try:
            embedding = self.embedding_model.encode(text, convert_to_tensor=False)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    def add_article(
        self,
        content: str,
        metadata: Dict[str, Any],
        article_id: Optional[str] = None
    ) -> str:
        """
        Add a single article to the vector database.
        
        Args:
            content: Article text content
            metadata: Article metadata (date, category, persons, etc.)
            article_id: Optional custom ID, generates UUID if not provided
            
        Returns:
            Article ID
        """
        try:
            # Generate ID if not provided
            if article_id is None:
                article_id = str(uuid.uuid4())
            
            # Generate embedding
            embedding = self._generate_embedding(content)
            
            # Prepare metadata - ensure all values are serializable
            processed_metadata = self._process_metadata(metadata)
            processed_metadata["timestamp"] = datetime.now().isoformat()
            
            # Add to collection
            self.collection.add(
                embeddings=[embedding],
                documents=[content],
                metadatas=[processed_metadata],
                ids=[article_id]
            )
            
            logger.info(f"Added article with ID: {article_id}")
            return article_id
            
        except Exception as e:
            logger.error(f"Failed to add article: {e}")
            raise
    
    def add_articles_bulk(
        self,
        contents: List[str],
        metadatas: List[Dict[str, Any]],
        article_ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Add multiple articles in bulk for better performance.
        
        Args:
            contents: List of article text contents
            metadatas: List of article metadata dictionaries
            article_ids: Optional list of custom IDs
            
        Returns:
            List of article IDs
        """
        try:
            # Generate IDs if not provided
            if article_ids is None:
                article_ids = [str(uuid.uuid4()) for _ in contents]
            
            # Generate embeddings in batch
            embeddings = [self._generate_embedding(content) for content in contents]
            
            # Process metadata
            processed_metadatas = []
            timestamp = datetime.now().isoformat()
            for metadata in metadatas:
                processed = self._process_metadata(metadata)
                processed["timestamp"] = timestamp
                processed_metadatas.append(processed)
            
            # Add to collection
            self.collection.add(
                embeddings=embeddings,
                documents=contents,
                metadatas=processed_metadatas,
                ids=article_ids
            )
            
            logger.info(f"Added {len(article_ids)} articles in bulk")
            return article_ids
            
        except Exception as e:
            logger.error(f"Failed to add articles in bulk: {e}")
            raise
    
    def query_articles(
        self,
        query_text: str,
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[str], List[Dict[str, Any]], List[str], List[float]]:
        """
        Query similar articles based on text similarity.
        
        Args:
            query_text: Search query text
            top_k: Number of results to return
            filter_dict: Optional metadata filters (e.g., {"category": "politics"})
            
        Returns:
            Tuple of (ids, metadatas, documents, distances)
        """
        try:
            # Generate query embedding
            query_embedding = self._generate_embedding(query_text)
            
            # Build where clause for filtering
            where_clause = None
            if filter_dict:
                where_clause = self._build_where_clause(filter_dict)
            
            # Query collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_clause,
                include=["documents", "metadatas", "distances"]
            )
            
            # Extract results
            ids = results["ids"][0] if results["ids"] else []
            metadatas = results["metadatas"][0] if results["metadatas"] else []
            documents = results["documents"][0] if results["documents"] else []
            distances = results["distances"][0] if results["distances"] else []
            
            logger.info(f"Query returned {len(ids)} results")
            return ids, metadatas, documents, distances
            
        except Exception as e:
            logger.error(f"Failed to query articles: {e}")
            raise
    
    def get_article_by_id(self, article_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific article by ID.
        
        Args:
            article_id: Article ID
            
        Returns:
            Article data or None if not found
        """
        try:
            result = self.collection.get(
                ids=[article_id],
                include=["documents", "metadatas"]
            )
            
            if result["ids"]:
                return {
                    "id": result["ids"][0],
                    "content": result["documents"][0],
                    "metadata": result["metadatas"][0]
                }
            return None
            
        except Exception as e:
            logger.error(f"Failed to get article by ID: {e}")
            raise
    
    def delete_article(self, article_id: str) -> bool:
        """
        Delete an article by ID.
        
        Args:
            article_id: Article ID to delete
            
        Returns:
            True if successful
        """
        try:
            self.collection.delete(ids=[article_id])
            logger.info(f"Deleted article with ID: {article_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete article: {e}")
            raise
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the collection.
        
        Returns:
            Dictionary with collection statistics
        """
        try:
            count = self.collection.count()
            return {
                "total_articles": count,
                "collection_name": settings.chroma_collection_name,
                "embedding_model": settings.embedding_model,
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            raise
    
    def _process_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process metadata to ensure ChromaDB compatibility.
        ChromaDB supports: str, int, float, bool
        
        Args:
            metadata: Raw metadata dictionary
            
        Returns:
            Processed metadata dictionary
        """
        processed = {}
        
        for key, value in metadata.items():
            if value is None:
                continue
            elif isinstance(value, (str, int, float, bool)):
                processed[key] = value
            elif isinstance(value, list):
                # Convert list to comma-separated string
                processed[key] = ",".join(str(item) for item in value)
            else:
                # Convert other types to string
                processed[key] = str(value)
        
        return processed
    
    def _build_where_clause(self, filter_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build ChromaDB where clause from filter dictionary.
        
        Args:
            filter_dict: Dictionary of filters
            
        Returns:
            ChromaDB where clause
        """
        where_conditions = []
        
        for key, value in filter_dict.items():
            if value is not None:
                if isinstance(value, list):
                    # For list filters (e.g., persons), check if any match
                    value_str = ",".join(str(item) for item in value)
                    where_conditions.append({key: {"$contains": value_str}})
                else:
                    where_conditions.append({key: {"$eq": value}})
        
        # Combine conditions with AND
        if len(where_conditions) == 1:
            return where_conditions[0]
        elif len(where_conditions) > 1:
            return {"$and": where_conditions}
        
        return {}
    
    def reset_collection(self):
        """Reset the collection (delete all data). Use with caution!"""
        try:
            self.client.delete_collection(name=settings.chroma_collection_name)
            self.collection = self.client.create_collection(
                name=settings.chroma_collection_name,
                metadata={
                    "hnsw:space": "cosine",
                    "description": "Article embeddings with metadata",
                }
            )
            logger.warning("Collection reset - all data deleted")
        except Exception as e:
            logger.error(f"Failed to reset collection: {e}")
            raise


# Global vector store instance
vector_store = VectorStore()

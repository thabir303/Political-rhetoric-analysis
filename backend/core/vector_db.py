"""
Vector Database Module for ChromaDB

Provides comprehensive interface to ChromaDB for storing and retrieving
article embeddings with rich metadata filtering capabilities.
"""

import os
from typing import List, Dict, Optional, Union, Any
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


class VectorDatabase:
    """
    ChromaDB vector database for article embeddings.
    
    Provides storage, retrieval, and filtering of articles with embeddings.
    """
    
    def __init__(
        self,
        persist_directory: str = "./chroma_db",
        collection_name: str = "article_embeddings",
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize the vector database.
        
        Args:
            persist_directory: Directory for persistent storage
            collection_name: Name of the collection
            embedding_model: Name of the embedding model
        """
        self.persist_directory = Path(persist_directory)
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model
        
        # Create persist directory
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        logger.info(f"Initializing ChromaDB at: {self.persist_directory}")
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
        
        # Get or create collection
        self._initialize_collection()
        
        logger.info(f"Vector database initialized successfully")
        logger.info(f"Collection: {self.collection_name}")
        logger.info(f"Current document count: {self.collection.count()}")
    
    def _initialize_collection(self):
        """Initialize or get the collection."""
        try:
            # Try to get existing collection
            self.collection = self.client.get_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )
            logger.info(f"Retrieved existing collection: {self.collection_name}")
        except Exception:
            # Create new collection
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function,
                metadata={"description": "Article embeddings with rich metadata"}
            )
            logger.info(f"Created new collection: {self.collection_name}")
    
    def store_embeddings(
        self,
        articles: List[Dict],
        embeddings: Optional[List] = None,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Store article embeddings with metadata in ChromaDB.
        
        Args:
            articles: List of article dictionaries with metadata
            embeddings: Optional pre-computed embeddings
            batch_size: Batch size for insertion
        
        Returns:
            Dictionary with storage statistics
        
        Expected article format:
            {
                'id': 'unique_id',  # Optional, will be generated if not provided
                'title': 'Article title',
                'content': 'Article content',
                'date': 'YYYY-MM-DD',
                'source': 'Newspaper name',
                'category': 'Politics',
                'parties': ['BNP', 'Interim Government'],
                'people': ['Tareq Rahman', 'Dr. Yunus'],
                'keywords': ['election', 'reform', 'democracy'],
                'themes': ['Election Commission', 'Reform'],
                'is_speech': True,
                'is_stance': False,
                'url': 'https://...',
                'language': 'English',
                
                # Optional: LLM-generated summary data
                'llm_summary': {
                    'summary': 'Speech summary text...',
                    'key_points': ['Point 1', 'Point 2', 'Point 3'],
                    'stance_analysis': 'Political stance analysis...',
                    'political_figure': 'Tareq Rahman',
                    'political_party': 'BNP'
                },
                
                # Optional: LLM-generated keywords
                'llm_keywords': {
                    'keywords': ['keyword1', 'keyword2', ...],
                    'phrases': ['key phrase 1', 'key phrase 2', ...],
                    'topics': ['Topic 1', 'Topic 2', 'Topic 3']
                }
            }
        """
        if not articles:
            logger.warning("No articles provided to store")
            return {'success': False, 'message': 'No articles provided'}
        
        logger.info(f"Storing {len(articles)} articles...")
        
        # Check for existing URLs to prevent duplicates
        existing_urls = set()
        try:
            all_existing = self.collection.get()
            for metadata in all_existing.get('metadatas', []):
                url = metadata.get('url')
                if url:
                    existing_urls.add(url)
            logger.info(f"Found {len(existing_urls)} existing URLs in database")
        except Exception as e:
            logger.warning(f"Could not check existing URLs: {e}")
        
        # Filter out duplicates
        unique_articles = []
        duplicate_count = 0
        
        for article in articles:
            url = article.get('url', '')
            if url and url in existing_urls:
                duplicate_count += 1
                logger.debug(f"Skipping duplicate URL: {url}")
            else:
                unique_articles.append(article)
                if url:
                    existing_urls.add(url)  # Track for this batch too
        
        if duplicate_count > 0:
            logger.info(f"Filtered out {duplicate_count} duplicate articles")
        
        if not unique_articles:
            logger.warning("All articles were duplicates, nothing to store")
            return {
                'success': True, 
                'message': 'All articles were duplicates',
                'total': len(articles),
                'stored': 0,
                'duplicates': duplicate_count
            }
        
        logger.info(f"Storing {len(unique_articles)} unique articles...")
        
        # Prepare data
        ids = []
        documents = []
        metadatas = []
        article_embeddings = []
        
        for i, article in enumerate(unique_articles):
            # Generate ID if not provided
            article_id = article.get('id', f"article_{datetime.now().timestamp()}_{i}")
            ids.append(article_id)
            
            # Prepare document (title + content)
            title = article.get('title', '')
            content = article.get('content', '')
            document = f"{title}\n\n{content}".strip()
            documents.append(document)
            
            # Prepare metadata
            metadata = self._prepare_metadata(article)
            metadatas.append(metadata)
            
            # Handle embeddings
            if embeddings:
                article_embeddings.append(embeddings[i])
            elif 'embedding' in article:
                article_embeddings.append(article['embedding'].tolist() if hasattr(article['embedding'], 'tolist') else article['embedding'])
        
        # Store in batches
        total_stored = 0
        errors = []
        
        for i in range(0, len(unique_articles), batch_size):
            batch_end = min(i + batch_size, len(unique_articles))
            
            try:
                batch_ids = ids[i:batch_end]
                batch_docs = documents[i:batch_end]
                batch_meta = metadatas[i:batch_end]
                
                if embeddings or any('embedding' in a for a in unique_articles):
                    batch_emb = article_embeddings[i:batch_end]
                    self.collection.add(
                        ids=batch_ids,
                        documents=batch_docs,
                        metadatas=batch_meta,
                        embeddings=batch_emb
                    )
                else:
                    # Let ChromaDB generate embeddings
                    self.collection.add(
                        ids=batch_ids,
                        documents=batch_docs,
                        metadatas=batch_meta
                    )
                
                total_stored += len(batch_ids)
                logger.info(f"Stored batch {i//batch_size + 1}: {len(batch_ids)} articles")
                
            except Exception as e:
                error_msg = f"Error storing batch {i//batch_size + 1}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        result = {
            'success': total_stored > 0,
            'total_articles': len(articles),
            'unique_articles': len(unique_articles),
            'duplicates': duplicate_count,
            'stored': total_stored,
            'errors': errors,
            'collection_size': self.collection.count()
        }
        
        logger.info(f"Storage complete: {total_stored}/{len(articles)} articles stored ({duplicate_count} duplicates filtered)")
        
        return result
    
    def _prepare_metadata(self, article: Dict) -> Dict:
        """
        Prepare metadata for ChromaDB storage.
        
        ChromaDB metadata must be flat (no nested dicts or lists of dicts).
        Lists of strings and basic types are supported.
        
        Args:
            article: Article dictionary
        
        Returns:
            Flattened metadata dictionary
        """
        metadata = {}
        
        # Basic fields
        if 'title' in article:
            metadata['title'] = str(article['title'])
        
        if 'date' in article:
            # Store date as both string and timestamp for comparison
            date_str = str(article['date'])
            metadata['date'] = date_str
            
            # Try to parse and store as timestamp for numeric comparison
            try:
                from datetime import datetime
                dt = datetime.strptime(date_str, '%Y-%m-%d')
                metadata['date_ts'] = int(dt.timestamp())
            except:
                pass
        
        if 'source' in article:
            metadata['source'] = str(article['source'])
        
        if 'category' in article:
            metadata['category'] = str(article['category'])
        
        if 'url' in article:
            metadata['url'] = str(article['url'])
        
        if 'language' in article:
            metadata['language'] = str(article['language'])
        
        if 'author' in article:
            metadata['author'] = str(article['author'])
        
        # Handle lists (convert to comma-separated strings for ChromaDB)
        if 'parties' in article:
            parties = article['parties']
            if isinstance(parties, list):
                metadata['parties'] = ', '.join(str(p) for p in parties)
            else:
                metadata['parties'] = str(parties)
        
        if 'people' in article:
            people = article['people']
            if isinstance(people, list):
                metadata['people'] = ', '.join(str(p) for p in people)
            else:
                metadata['people'] = str(people)
        
        # Handle people_affiliations (NEW - stores canonical name -> party mapping)
        if 'people_affiliations' in article:
            import json
            people_affiliations = article['people_affiliations']
            if isinstance(people_affiliations, dict):
                metadata['people_affiliations'] = json.dumps(people_affiliations)
            else:
                metadata['people_affiliations'] = str(people_affiliations)
        
        if 'keywords' in article:
            keywords = article['keywords']
            if isinstance(keywords, list):
                metadata['keywords'] = ', '.join(str(k) for k in keywords[:20])  # Limit keywords
            else:
                metadata['keywords'] = str(keywords)
        
        if 'themes' in article:
            themes = article['themes']
            if isinstance(themes, list):
                metadata['themes'] = ', '.join(str(t) for t in themes)
            else:
                metadata['themes'] = str(themes)
        
        # Boolean fields
        if 'is_speech' in article:
            metadata['is_speech'] = str(article['is_speech'])
        
        if 'is_stance' in article:
            metadata['is_stance'] = str(article['is_stance'])
        
        # Handle categorization data if present
        if 'categorization' in article:
            cat = article['categorization']
            
            if 'parties' in cat and 'parties' not in metadata:
                metadata['parties'] = ', '.join(str(p) for p in cat['parties'])
            
            if 'people' in cat and 'people' not in metadata:
                metadata['people'] = ', '.join(str(p) for p in cat['people'])
            
            if 'keywords' in cat and 'keywords' not in metadata:
                metadata['keywords'] = ', '.join(str(k) for k in cat['keywords'][:20])
            
            if 'categories' in cat and 'themes' not in metadata:
                metadata['themes'] = ', '.join(str(t) for t in cat['categories'])
            
            if 'is_speech' in cat and 'is_speech' not in metadata:
                metadata['is_speech'] = str(cat['is_speech'])
            
            if 'is_stance' in cat and 'is_stance' not in metadata:
                metadata['is_stance'] = str(cat['is_stance'])
        
        # Handle enhanced political entity detection fields
        if 'political_entities' in article:
            # Store the detailed party -> figures mapping as JSON string
            import json
            metadata['political_entities'] = json.dumps(article['political_entities'])
        
        if 'mentioned_figures' in article:
            # Store as comma-separated list
            if isinstance(article['mentioned_figures'], list):
                metadata['mentioned_figures'] = ', '.join(str(f) for f in article['mentioned_figures'])
            else:
                metadata['mentioned_figures'] = str(article['mentioned_figures'])
        
        if 'primary_parties' in article:
            # Store as comma-separated list
            if isinstance(article['primary_parties'], list):
                metadata['primary_parties'] = ', '.join(str(p) for p in article['primary_parties'])
            else:
                metadata['primary_parties'] = str(article['primary_parties'])
        
        # Handle LLM-generated summaries and keywords
        if 'llm_summary' in article:
            llm = article['llm_summary']
            
            # Store speech summary (truncate if too long for metadata)
            if 'summary' in llm and llm['summary']:
                metadata['llm_summary'] = str(llm['summary'])[:500]  # Limit to 500 chars
            
            # Store key points as comma-separated
            if 'key_points' in llm and llm['key_points']:
                metadata['llm_key_points'] = ', '.join(str(p) for p in llm['key_points'])
            
            # Store stance analysis
            if 'stance_analysis' in llm and llm['stance_analysis']:
                metadata['llm_stance'] = str(llm['stance_analysis'])[:500]  # Limit to 500 chars
            
            # Store political figure and party from LLM analysis
            if 'political_figure' in llm and llm['political_figure']:
                metadata['llm_figure'] = str(llm['political_figure'])
            
            if 'political_party' in llm and llm['political_party']:
                metadata['llm_party'] = str(llm['political_party'])
        
        # Handle LLM-generated keywords
        if 'llm_keywords' in article:
            llm_kw = article['llm_keywords']
            
            # Store keywords (merge with existing or replace)
            if 'keywords' in llm_kw and llm_kw['keywords']:
                llm_keywords = ', '.join(str(k) for k in llm_kw['keywords'][:15])
                if 'keywords' not in metadata:
                    metadata['keywords'] = llm_keywords
                else:
                    # Merge LLM keywords with existing
                    metadata['llm_extra_keywords'] = llm_keywords
            
            # Store key phrases
            if 'phrases' in llm_kw and llm_kw['phrases']:
                metadata['llm_phrases'] = ', '.join(str(p) for p in llm_kw['phrases'])
            
            # Store main topics
            if 'topics' in llm_kw and llm_kw['topics']:
                metadata['llm_topics'] = ', '.join(str(t) for t in llm_kw['topics'])
        
        return metadata
    
    def retrieve_similar_articles(
        self,
        query: Union[str, List[float]],
        top_k: int = 5,
        filter_parties: Optional[List[str]] = None,
        filter_people: Optional[List[str]] = None,
        filter_date_from: Optional[str] = None,
        filter_date_to: Optional[str] = None,
        filter_category: Optional[str] = None,
        filter_themes: Optional[List[str]] = None,
        filter_is_speech: Optional[bool] = None,
        filter_is_stance: Optional[bool] = None,
        filter_source: Optional[str] = None,
        filter_language: Optional[str] = None
    ) -> List[Dict]:
        """
        Retrieve similar articles based on query with optional filters.
        
        This function retrieves articles from the vector database and includes
        LLM-generated speech summaries and keywords when available.
        
        Args:
            query: Text query or embedding vector
            top_k: Number of results to return
            filter_parties: Filter by political parties (e.g., ['BNP', 'Interim Government'])
                           Articles matching ANY of the specified parties will be returned.
            filter_people: Filter by political figures (e.g., ['Tareq Rahman', 'Dr. Yunus'])
                          Articles mentioning ANY of the specified people will be returned.
            filter_date_from: Filter by date from (YYYY-MM-DD format, e.g., '2024-08-05')
                             Only articles on or after this date will be returned.
            filter_date_to: Filter by date to (YYYY-MM-DD format, e.g., '2025-09-30')
                           Only articles on or before this date will be returned.
            filter_category: Filter by category (e.g., 'Politics', 'Election')
            filter_themes: Filter by themes (e.g., ['Election Commission', 'Reform'])
            filter_is_speech: Filter speech articles (True = only speeches, False = exclude speeches)
            filter_is_stance: Filter stance articles (True = only stance articles)
            filter_source: Filter by source newspaper (e.g., 'Prothom Alo')
            filter_language: Filter by language (e.g., 'English', 'Bangla')
        
        Returns:
            List of similar articles with metadata, similarity scores, and LLM analysis:
            [
                {
                    'id': 'article_123',
                    'document': 'Article title and content...',
                    'metadata': {...},
                    'similarity': 0.85,
                    'parties': ['BNP', 'Interim Government'],
                    'people': ['Tareq Rahman'],
                    'keywords': ['election', 'reform', 'democracy'],
                    'themes': ['Election Commission'],
                    'is_speech': True,
                    'llm_summary': {  # LLM-generated summary (if available)
                        'summary': 'Brief speech summary...',
                        'key_points': ['Point 1', 'Point 2', ...],
                        'stance_analysis': 'Political stance analysis...',
                        'political_figure': 'Tareq Rahman',
                        'political_party': 'BNP'
                    },
                    'llm_keywords': {  # LLM-extracted keywords (if available)
                        'keywords': ['election', 'reform', ...],
                        'phrases': ['election commission', 'caretaker government', ...],
                        'topics': ['Election Reform', 'Democracy', ...]
                    }
                },
                ...
            ]
            
        Examples:
            # Filter by political figure and date range
            results = db.retrieve_similar_articles(
                query="What are BNP's views on election reform?",
                filter_people=['Tareq Rahman'],
                filter_date_from='2024-08-05',
                filter_date_to='2025-09-30',
                top_k=10
            )
            
            # Filter by party and get speeches only
            results = db.retrieve_similar_articles(
                query="Interim Government policies",
                filter_parties=['Interim Government'],
                filter_is_speech=True,
                top_k=5
            )
        """
        # Build where clauses for filters
        where_clause, where_document = self._build_where_clause(
            filter_parties=filter_parties,
            filter_people=filter_people,
            filter_date_from=filter_date_from,
            filter_date_to=filter_date_to,
            filter_category=filter_category,
            filter_themes=filter_themes,
            filter_is_speech=filter_is_speech,
            filter_is_stance=filter_is_stance,
            filter_source=filter_source,
            filter_language=filter_language
        )
        
        # Query the collection
        try:
            # If using list-based filters (parties, people, themes), fetch more results
            # since we'll post-filter in Python
            fetch_count = top_k
            if filter_parties or filter_people or filter_themes:
                # Fetch 5x more results to ensure we have enough after filtering
                fetch_count = min(top_k * 5, 100)  # Cap at 100 to avoid performance issues
                logger.info(f"Fetching {fetch_count} results for post-filtering (requested: {top_k})")
            
            query_params = {
                "n_results": fetch_count
            }
            
            # Add where clause if present
            if where_clause:
                query_params["where"] = where_clause
            
            # Add where_document if present
            if where_document:
                query_params["where_document"] = where_document
            
            if isinstance(query, str):
                # Text query
                query_params["query_texts"] = [query]
            else:
                # Embedding vector query
                query_params["query_embeddings"] = [query]
            
            results = self.collection.query(**query_params)
            
            # Format results
            formatted_results = self._format_results(results)
            
            # Post-filter for parties, people, themes (since ChromaDB doesn't support substring matching)
            if filter_parties or filter_people or filter_themes:
                formatted_results = self._post_filter_results(
                    formatted_results,
                    filter_parties=filter_parties,
                    filter_people=filter_people,
                    filter_themes=filter_themes
                )
                # Trim to requested top_k after filtering
                formatted_results = formatted_results[:top_k]
            
            logger.info(f"Retrieved {len(formatted_results)} similar articles")
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error retrieving articles: {e}")
            return []
    
    def retrieve_articles_by_figure_or_party(
        self,
        query: str,
        political_figure: Optional[str] = None,
        political_party: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        speeches_only: bool = False,
        top_k: int = 10
    ) -> Dict[str, Any]:
        """
        Convenience method to retrieve articles for a specific political figure or party
        with their speech summaries and keywords.
        
        This method is specifically designed for backend API endpoints that need to
        fetch articles and summaries for a selected political figure/party.
        
        Args:
            query: Search query (e.g., "election reform", "democracy")
            political_figure: Filter by political figure (e.g., "Tareq Rahman")
            political_party: Filter by political party (e.g., "BNP", "Interim Government")
            date_from: Start date for filtering (YYYY-MM-DD, e.g., "2024-08-05")
            date_to: End date for filtering (YYYY-MM-DD, e.g., "2025-09-30")
            speeches_only: If True, return only speech articles
            top_k: Maximum number of articles to return
        
        Returns:
            Dictionary with organized results:
            {
                'query': 'Original query',
                'filters': {
                    'political_figure': 'Tareq Rahman',
                    'political_party': 'BNP',
                    'date_from': '2024-08-05',
                    'date_to': '2025-09-30',
                    'speeches_only': True
                },
                'total_results': 10,
                'articles': [
                    {
                        'id': 'article_123',
                        'title': 'Article Title',
                        'date': '2024-09-15',
                        'source': 'Newspaper Name',
                        'similarity': 0.85,
                        'parties': ['BNP'],
                        'people': ['Tareq Rahman'],
                        'is_speech': True,
                        'summary': 'Brief speech summary from LLM...',
                        'key_points': ['Point 1', 'Point 2', 'Point 3'],
                        'stance_analysis': 'Political stance analysis...',
                        'keywords': ['election', 'reform', 'democracy'],
                        'key_phrases': ['election commission', 'caretaker government'],
                        'topics': ['Election Reform', 'Democracy']
                    },
                    ...
                ],
                'summaries_by_date': {
                    '2024-09-15': [
                        {
                            'summary': '...',
                            'key_points': [...],
                            'article_id': 'article_123'
                        }
                    ],
                    ...
                }
            }
        
        Examples:
            # Get all articles and summaries for Tareq Rahman in a date range
            results = db.retrieve_articles_by_figure_or_party(
                query="What are the recent statements?",
                political_figure="Tareq Rahman",
                date_from="2024-08-05",
                date_to="2025-09-30",
                top_k=20
            )
            
            # Get BNP party speeches only
            results = db.retrieve_articles_by_figure_or_party(
                query="Party policies and stances",
                political_party="BNP",
                speeches_only=True,
                top_k=15
            )
        """
        # Build filter lists
        filter_people = [political_figure] if political_figure else None
        filter_parties = [political_party] if political_party else None
        
        # Retrieve articles
        articles = self.retrieve_similar_articles(
            query=query,
            filter_people=filter_people,
            filter_parties=filter_parties,
            filter_date_from=date_from,
            filter_date_to=date_to,
            filter_is_speech=speeches_only if speeches_only else None,
            top_k=top_k
        )
        
        # Organize results
        organized_articles = []
        summaries_by_date = {}
        
        for article in articles:
            # Extract metadata first
            metadata = article.get('metadata', {})
            
            # Extract core information
            article_data = {
                'id': article.get('id'),
                'title': metadata.get('title', ''),
                'date': metadata.get('date', ''),
                'source': metadata.get('source', ''),
                'similarity': article.get('similarity', 0),
                'parties': article.get('parties', []),
                'people': article.get('people', []),
                'is_speech': article.get('is_speech', False),
                'is_summarized': str(metadata.get('is_summarized', 'False')).lower() == 'true',  # Convert to boolean
                'url': metadata.get('url', '')
            }
            
            # Add LLM summary and related data
            # If article is summarized, document itself is the summary
            is_summarized = str(metadata.get('is_summarized', 'False')).lower() == 'true'
            if is_summarized:
                # Document is the summary, get other LLM data from metadata
                article_data['summary'] = article.get('document', '')
                
                # Get key_points from metadata
                if 'llm_key_points' in metadata and metadata['llm_key_points']:
                    article_data['key_points'] = [p.strip() for p in str(metadata['llm_key_points']).split(',') if p.strip()]
                else:
                    article_data['key_points'] = []
                
                # Get stance_analysis from metadata  
                if 'llm_stance_analysis' in metadata and metadata['llm_stance_analysis']:
                    article_data['stance_analysis'] = metadata['llm_stance_analysis']
                else:
                    article_data['stance_analysis'] = None
                    
            elif 'llm_summary' in article:
                # Old format: llm_summary object exists
                llm = article['llm_summary']
                article_data['summary'] = llm.get('summary', '')
                article_data['key_points'] = llm.get('key_points', [])
                article_data['stance_analysis'] = llm.get('stance_analysis', '')
            else:
                # No LLM summary available, set defaults
                article_data['summary'] = ''
                article_data['key_points'] = []
                article_data['stance_analysis'] = ''
                
                # Group summaries by date
                date = article_data['date']
                if date:
                    if date not in summaries_by_date:
                        summaries_by_date[date] = []
                    summaries_by_date[date].append({
                        'summary': article_data['summary'],
                        'key_points': article_data['key_points'],
                        'stance_analysis': article_data['stance_analysis'],
                        'article_id': article_data['id'],
                        'title': article_data['title']
                    })
            
            # Add LLM keywords and topics
            if is_summarized:
                # Get keywords and topics directly from metadata
                if 'llm_keywords' in metadata and metadata['llm_keywords']:
                    article_data['keywords'] = [k.strip() for k in str(metadata['llm_keywords']).split(',') if k.strip()]
                else:
                    article_data['keywords'] = []
                
                if 'llm_topics' in metadata and metadata['llm_topics']:
                    article_data['topics'] = [t.strip() for t in str(metadata['llm_topics']).split(',') if t.strip()]
                else:
                    article_data['topics'] = []
                    
                article_data['key_phrases'] = []  # Not stored separately in new format
                
            elif 'llm_keywords' in article:
                # Old format: llm_keywords object exists
                llm_kw = article['llm_keywords']
                article_data['keywords'] = llm_kw.get('keywords', [])
                article_data['key_phrases'] = llm_kw.get('phrases', [])
                article_data['topics'] = llm_kw.get('topics', [])
            else:
                # Fallback to regular keywords or set defaults
                article_data['keywords'] = article.get('keywords', [])
                article_data['key_phrases'] = []
                article_data['topics'] = []
            
            organized_articles.append(article_data)
        
        # Build response
        response = {
            'query': query,
            'filters': {
                'political_figure': political_figure,
                'political_party': political_party,
                'date_from': date_from,
                'date_to': date_to,
                'speeches_only': speeches_only
            },
            'total_results': len(organized_articles),
            'articles': organized_articles,
            'summaries_by_date': summaries_by_date
        }
        
        logger.info(f"Retrieved {len(organized_articles)} articles for {political_figure or political_party}")
        
        return response
    
    def _build_where_clause(
        self,
        filter_parties: Optional[List[str]] = None,
        filter_people: Optional[List[str]] = None,
        filter_date_from: Optional[str] = None,
        filter_date_to: Optional[str] = None,
        filter_category: Optional[str] = None,
        filter_themes: Optional[List[str]] = None,
        filter_is_speech: Optional[bool] = None,
        filter_is_stance: Optional[bool] = None,
        filter_source: Optional[str] = None,
        filter_language: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Build ChromaDB where clause for filtering.
        
        Note: ChromaDB metadata limitations:
        - Only supports: str, int, float, bool (no lists)
        - Operators: $gt, $gte, $lt, $lte, $ne, $eq, $in, $nin
        - NO $contains operator!
        
        For list-based fields (parties, people, themes) stored as comma-separated strings,
        we use post-filtering in Python since ChromaDB doesn't support substring matching.
        
        Returns:
            Tuple of (where_clause, where_document)
        """
        where_document = None
        conditions = []
        
        # NOTE: parties, people, themes filtering done via post-processing
        # because they're stored as comma-separated strings and ChromaDB
        # doesn't support substring matching ($contains doesn't work)
        
        # Category filter
        if filter_category:
            conditions.append({"category": {"$eq": filter_category}})
        
        # Boolean filters
        if filter_is_speech is not None:
            conditions.append({"is_speech": {"$eq": str(filter_is_speech)}})
        
        if filter_is_stance is not None:
            conditions.append({"is_stance": {"$eq": str(filter_is_stance)}})
        
        # Source filter
        if filter_source:
            conditions.append({"source": {"$eq": filter_source}})
        
        # Language filter
        if filter_language:
            conditions.append({"language": {"$eq": filter_language}})
        
        # Date filters - use timestamps for comparison
        if filter_date_from or filter_date_to:
            try:
                from datetime import datetime
                
                if filter_date_from:
                    dt_from = datetime.strptime(filter_date_from, '%Y-%m-%d')
                    ts_from = int(dt_from.timestamp())
                    conditions.append({"date_ts": {"$gte": ts_from}})
                
                if filter_date_to:
                    dt_to = datetime.strptime(filter_date_to, '%Y-%m-%d')
                    ts_to = int(dt_to.timestamp())
                    conditions.append({"date_ts": {"$lte": ts_to}})
            except Exception as e:
                logger.warning(f"Error parsing date filters: {e}")
        
        # Combine conditions
        where_clause = None
        if conditions:
            if len(conditions) == 1:
                where_clause = conditions[0]
            else:
                where_clause = {"$and": conditions}
        
        return where_clause, where_document
    
    def _format_results(self, results: Dict) -> List[Dict]:
        """
        Format ChromaDB query results.
        
        Args:
            results: Raw ChromaDB results
        
        Returns:
            Formatted list of article dictionaries
        """
        formatted = []
        
        if not results or 'ids' not in results or not results['ids']:
            return formatted
        
        # Extract data
        ids = results['ids'][0] if results['ids'] else []
        documents = results['documents'][0] if results['documents'] else []
        metadatas = results['metadatas'][0] if results['metadatas'] else []
        distances = results['distances'][0] if results['distances'] else []
        
        # Format each result
        for i in range(len(ids)):
            metadata = metadatas[i] if i < len(metadatas) else {}
            document_content = documents[i] if i < len(documents) else ''
            
            article = {
                'id': ids[i],
                'document': document_content,
                'metadata': metadata,
                'distance': distances[i] if i < len(distances) else None,
                'similarity': 1 - distances[i] if i < len(distances) else None  # Convert distance to similarity
            }
            
            # Parse metadata fields
            # metadata = article['metadata']  # Already extracted above
            
            # Parse comma-separated lists back to lists
            if 'parties' in metadata:
                article['parties'] = [p.strip() for p in metadata['parties'].split(',') if p.strip()]
            
            if 'people' in metadata:
                article['people'] = [p.strip() for p in metadata['people'].split(',') if p.strip()]
            
            if 'keywords' in metadata:
                article['keywords'] = [k.strip() for k in metadata['keywords'].split(',') if k.strip()]
            
            if 'themes' in metadata:
                article['themes'] = [t.strip() for t in metadata['themes'].split(',') if t.strip()]
            
            # Parse boolean fields
            if 'is_speech' in metadata:
                article['is_speech'] = metadata['is_speech'].lower() == 'true'
            
            if 'is_stance' in metadata:
                article['is_stance'] = metadata['is_stance'].lower() == 'true'
            
            # Parse LLM-generated summaries and metadata
            llm_summary = {}
            if 'llm_summary' in metadata:
                llm_summary['summary'] = metadata['llm_summary']
            
            if 'llm_key_points' in metadata:
                llm_summary['key_points'] = [p.strip() for p in metadata['llm_key_points'].split(',') if p.strip()]
            
            # Check both old and new field names for stance analysis
            if 'llm_stance_analysis' in metadata:
                llm_summary['stance_analysis'] = metadata['llm_stance_analysis']
            elif 'llm_stance' in metadata:
                llm_summary['stance_analysis'] = metadata['llm_stance']
            
            if 'llm_figure' in metadata:
                llm_summary['political_figure'] = metadata['llm_figure']
            
            if 'llm_party' in metadata:
                llm_summary['political_party'] = metadata['llm_party']
            
            if llm_summary:
                article['llm_summary'] = llm_summary
            
            # Parse LLM-generated keywords and topics
            llm_keywords = {}
            # Check both old and new field names for keywords
            if 'llm_keywords' in metadata:
                llm_keywords['keywords'] = [k.strip() for k in metadata['llm_keywords'].split(',') if k.strip()]
            elif 'llm_extra_keywords' in metadata:
                llm_keywords['keywords'] = [k.strip() for k in metadata['llm_extra_keywords'].split(',') if k.strip()]
            
            if 'llm_phrases' in metadata:
                llm_keywords['phrases'] = [p.strip() for p in metadata['llm_phrases'].split(',') if p.strip()]
            
            if 'llm_topics' in metadata:
                llm_keywords['topics'] = [t.strip() for t in metadata['llm_topics'].split(',') if t.strip()]
            
            if llm_keywords:
                article['llm_keywords'] = llm_keywords
            
            formatted.append(article)
        
        return formatted
    
    def _post_filter_results(
        self,
        results: List[Dict],
        filter_parties: Optional[List[str]] = None,
        filter_people: Optional[List[str]] = None,
        filter_themes: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Post-process filter results for precise list matching.
        
        Args:
            results: Formatted results
            filter_parties: Party filters
            filter_people: People filters
            filter_themes: Theme filters
        
        Returns:
            Filtered results
        """
        filtered = []
        
        for result in results:
            # Check party filter
            if filter_parties:
                result_parties = result.get('parties', [])
                if not any(party in result_parties for party in filter_parties):
                    continue
            
            # Check people filter
            if filter_people:
                result_people = result.get('people', [])
                if not any(person in result_people for person in filter_people):
                    continue
            
            # Check theme filter
            if filter_themes:
                result_themes = result.get('themes', [])
                if not any(theme in result_themes for theme in filter_themes):
                    continue
            
            filtered.append(result)
        
        return filtered
    
    def get_article_by_id(self, article_id: str) -> Optional[Dict]:
        """
        Get a specific article by ID.
        
        Args:
            article_id: Article ID
        
        Returns:
            Article dictionary or None
        """
        try:
            results = self.collection.get(ids=[article_id])
            
            if results and results['ids']:
                return {
                    'id': results['ids'][0],
                    'document': results['documents'][0] if results['documents'] else '',
                    'metadata': results['metadatas'][0] if results['metadatas'] else {}
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving article {article_id}: {e}")
            return None
    
    def delete_article(self, article_id: str) -> bool:
        """
        Delete an article by ID.
        
        Args:
            article_id: Article ID
        
        Returns:
            True if successful
        """
        try:
            self.collection.delete(ids=[article_id])
            logger.info(f"Deleted article: {article_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting article {article_id}: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """
        Get database statistics.
        
        Returns:
            Statistics dictionary
        """
        count = self.collection.count()
        
        # Try to get some sample metadata
        try:
            sample = self.collection.peek(limit=100)
            
            # Collect unique values
            sources = set()
            languages = set()
            categories = set()
            
            if sample and 'metadatas' in sample:
                for metadata in sample['metadatas']:
                    if 'source' in metadata:
                        sources.add(metadata['source'])
                    if 'language' in metadata:
                        languages.add(metadata['language'])
                    if 'category' in metadata:
                        categories.add(metadata['category'])
            
            return {
                'total_articles': count,
                'collection_name': self.collection_name,
                'embedding_model': self.embedding_model_name,
                'sources': list(sources),
                'languages': list(languages),
                'categories': list(categories)
            }
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {
                'total_articles': count,
                'collection_name': self.collection_name,
                'embedding_model': self.embedding_model_name
            }
    
    def reset_collection(self):
        """Reset (delete) the collection. Use with caution!"""
        try:
            self.client.delete_collection(name=self.collection_name)
            logger.info(f"Deleted collection: {self.collection_name}")
            self._initialize_collection()
            logger.info("Collection reset complete")
        except Exception as e:
            logger.error(f"Error resetting collection: {e}")


# Convenience functions
def initialize_database(
    persist_directory: str = "./chroma_db",
    collection_name: str = "article_embeddings"
) -> VectorDatabase:
    """
    Initialize and return a VectorDatabase instance.
    
    Args:
        persist_directory: Directory for storage
        collection_name: Collection name
    
    Returns:
        VectorDatabase instance
    """
    return VectorDatabase(
        persist_directory=persist_directory,
        collection_name=collection_name
    )


if __name__ == "__main__":
    # Example usage
    print("=" * 80)
    print("VECTOR DATABASE MODULE")
    print("=" * 80)
    
    # Initialize database
    print("\n[1/4] Initializing Vector Database...")
    print("-" * 80)
    
    db = VectorDatabase(
        persist_directory="./test_chroma_db",
        collection_name="test_articles"
    )
    
    print(f"✓ Database initialized")
    print(f"✓ Collection: {db.collection_name}")
    
    # Sample articles
    print("\n[2/4] Storing Sample Articles...")
    print("-" * 80)
    
    sample_articles = [
        {
            'title': 'BNP Rally on Election Reforms',
            'content': '''
            BNP acting chairman Tareq Rahman delivered a speech at a party rally,
            calling for comprehensive election reforms. He emphasized the importance
            of free and fair elections for democracy.
            ''',
            'date': '2024-10-05',
            'source': 'Daily Star',
            'category': 'Politics',
            'parties': ['BNP', 'Interim Government'],
            'people': ['Tareq Rahman', 'Mirza Fakhrul'],
            'keywords': ['election', 'reform', 'democracy', 'BNP'],
            'themes': ['Election Commission', 'Reform'],
            'is_speech': True,
            'is_stance': True,
            'language': 'English'
        },
        {
            'title': 'Dr. Yunus on Economic Policy',
            'content': '''
            Chief Adviser Dr. Muhammad Yunus discussed the interim government's
            economic reform agenda, focusing on inflation control and GDP growth.
            ''',
            'date': '2024-10-06',
            'source': 'Dhaka Tribune',
            'category': 'Politics',
            'parties': ['Interim Government'],
            'people': ['Dr. Yunus', 'Dr. Muhammad Yunus'],
            'keywords': ['economy', 'inflation', 'GDP', 'reform'],
            'themes': ['Economy', 'Reform'],
            'is_speech': True,
            'is_stance': False,
            'language': 'English'
        },
        {
            'title': 'Judiciary Independence Debate',
            'content': '''
            Legal experts debate judiciary independence. Supreme Court judges
            express concerns about political interference in judicial matters.
            ''',
            'date': '2024-10-07',
            'source': 'Prothom Alo',
            'category': 'Politics',
            'parties': [],
            'people': [],
            'keywords': ['judiciary', 'independence', 'court', 'legal'],
            'themes': ['Judiciary', 'Democracy'],
            'is_speech': False,
            'is_stance': True,
            'language': 'English'
        }
    ]
    
    result = db.store_embeddings(sample_articles)
    print(f"✓ Stored {result['stored']}/{result['total_articles']} articles")
    
    # Test retrieval
    print("\n[3/4] Testing Retrieval...")
    print("-" * 80)
    
    # Query 1: Election reforms
    print("\nQuery: 'election reforms and democracy'")
    results = db.retrieve_similar_articles(
        query="election reforms and democracy",
        top_k=2
    )
    
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result['metadata'].get('title', 'N/A')}")
        print(f"     Similarity: {result['similarity']:.4f}")
    
    # Query 2: With filters
    print("\nQuery: 'reforms' (filtered by BNP)")
    results = db.retrieve_similar_articles(
        query="reforms",
        top_k=5,
        filter_parties=['BNP']
    )
    
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result['metadata'].get('title', 'N/A')}")
        print(f"     Parties: {result.get('parties', [])}")
    
    # Statistics
    print("\n[4/4] Database Statistics...")
    print("-" * 80)
    
    stats = db.get_statistics()
    print(f"✓ Total articles: {stats['total_articles']}")
    print(f"✓ Sources: {', '.join(stats.get('sources', []))}")
    print(f"✓ Languages: {', '.join(stats.get('languages', []))}")
    
    # Cleanup
    print("\n" + "-" * 80)
    print("Cleaning up test database...")
    db.reset_collection()
    
    print("\n" + "=" * 80)
    print("✅ Module ready for use!")
    print("=" * 80)

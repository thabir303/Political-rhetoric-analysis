# RAG-IR: RAG-based Information Retrieval System

A FastAPI backend with ChromaDB vector database for storing and querying article embeddings with metadata. Includes comprehensive web scraping for Bangladeshi newspapers.

## Features

### Backend & Database
- 🚀 FastAPI backend with automatic API documentation
- 🔍 Semantic search using sentence-transformers embeddings
- 💾 ChromaDB vector database with persistent storage
- 📊 Article metadata storage (date, category, persons)
- 🔎 Efficient indexing and similarity search
- 📝 Bulk article insertion support
- 🎯 Metadata-based filtering

### Web Scraping
- 🗞️ Scrape 4 major Bangladeshi newspapers (Prothom Alo, Jugantor, Daily Star, Dhaka Tribune)
- 👥 Track 55 political figures across 7 organizations
- 🌐 Support for both Bangla and English articles
- 📅 Date-based filtering (Aug 2024 - Sep 2025)
- 🤖 Automatic mention detection and categorization

### Article Categorization
- 🏷️ Automatic categorization into 7 political themes
- 🎤 Speech analysis detection
- 📊 Political stance identification
- 🔑 NLP-powered keyword extraction (TF-IDF)
- 📅 Date extraction from article content
- 🌍 Bilingual support (English + Bangla)

### Embeddings Generation
- 🧠 Sentence embeddings using `all-MiniLM-L6-v2` (384 dimensions)
- 🔍 Semantic similarity search
- 📦 Batch processing for efficiency
- 💾 Save/load embeddings with caching
- ⚡ Fast similarity computation (cosine, euclidean, dot product)
- 🌐 Bilingual text support

### Vector Database
- 📚 ChromaDB integration with persistent storage
- 🎯 Rich metadata filtering (parties, people, dates, themes)
- 🔍 Semantic search with similarity scores
- 📊 Automatic embedding generation
- 🚀 Batch operations for performance
- 📈 Database statistics and management

## Project Structure

```
RAG-IR/
├── config/
│   ├── __init__.py
│   └── settings.py          # Application configuration
├── models/
│   ├── __init__.py
│   └── schemas.py           # Pydantic models for validation
├── database/
│   ├── __init__.py
│   └── vector_store.py      # ChromaDB vector store operations
├── api/
│   ├── __init__.py
│   └── routes.py            # API endpoints
├── scripts/
│   ├── __init__.py
│   ├── example_usage.py     # API usage examples
│   ├── run_scraper.py       # CLI scraping tool
│   ├── test_scraping.py     # Scraper tests
│   ├── test_categorization.py  # Categorization tests
│   ├── test_embeddings.py   # Embeddings tests
│   ├── test_vector_db.py    # Vector database tests
│   └── scrape_and_categorize.py  # Complete pipeline
├── scraping.py              # Newspaper scraping module
├── categorization.py        # Article categorization module
├── embeddings.py            # Embeddings generation module
├── vector_db.py             # Vector database module
├── main.py                  # Application entry point
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
├── CATEGORIZATION_GUIDE.md # Categorization documentation
├── CATEGORIZATION_QUICKSTART.md  # Quick reference
├── EMBEDDINGS_GUIDE.md     # Embeddings documentation
├── VECTOR_DB_GUIDE.md      # Vector database documentation
└── README.md
```

## Installation

### 1. Clone or navigate to the project directory

```bash
cd /home/bs01127/Desktop/RAG-IR
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Linux/Mac
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
# Edit .env with your configuration
```

## Configuration

Edit the `.env` file to customize:

- **Server settings**: Host, port
- **ChromaDB**: Persist directory, collection name
- **Embedding model**: Default is `all-MiniLM-L6-v2`
- **CORS**: Allowed origins

## Running the Application

### Development mode (with auto-reload)

```bash
python main.py
```

Or with uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
kill -9 $(sudo lsof -t -i:8000)
```

### Production mode

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Frontend Application

### Quick Start

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at: http://localhost:5173

### Features

- 🎨 Modern UI with React + TypeScript + Tailwind CSS
- 🔍 Real-time semantic search interface
- 📊 Rich article cards with metadata display
- ⚡ Fast hot-reload development with Vite
- 📱 Responsive design for mobile and desktop

### Frontend Documentation

See [frontend/README.md](./frontend/README.md) for complete frontend documentation including:
- Project structure
- Component architecture
- API integration
- Customization guide
- Build and deployment

## API Endpoints

### Health Check
- `GET /api/v1/health` - Check service status

### Article Management
- `POST /api/v1/articles` - Create a single article
- `POST /api/v1/articles/bulk` - Create multiple articles in bulk
- `GET /api/v1/articles/{article_id}` - Get article by ID
- `DELETE /api/v1/articles/{article_id}` - Delete article

### Query
- `POST /api/v1/query` - Search articles by semantic similarity

### Statistics
- `GET /api/v1/stats` - Get database statistics

## Web Scraping

### Scraping Newspapers

Scrape articles from Bangladeshi newspapers:

```bash
# Scrape all newspapers
python scripts/run_scraper.py --save

# Scrape specific newspaper
python scripts/run_scraper.py --source dailystar --output articles.json

# Custom date range
python scripts/run_scraper.py \
  --start-date 2024-08-05 \
  --end-date 2024-10-10 \
  --save
```

### Tracked Political Entities

- **7 Organizations**: BNP, JI, NCP, AB Party, GOP, Gono Songhati, Interim Government
- **55+ Political Figures**: Including Tareq Rahman, Dr. Yunus, Nahid Islam, and more
- **4 Newspapers**: Prothom Alo, Jugantor, Daily Star, Dhaka Tribune

See `SCRAPING_GUIDE.md` for complete documentation.

## Article Categorization

### Automatic Categorization

Categorize articles into political themes:

```python
from categorization import ArticleCategorizer

categorizer = ArticleCategorizer()

article = {
    'title': 'BNP Rally on Election Reforms',
    'content': 'Tareq Rahman spoke at a rally...',
    'date': '2024-10-05'
}

result = categorizer.categorize_article(article)

print(result['categories'])  # ['BNP', 'Election Commission', 'Speech Analysis']
print(result['people'])      # ['Tareq Rahman']
print(result['keywords'])    # Top 15 keywords
print(result['themes'])      # Theme scores
```

### Categories Detected

1. **Political Parties**: BNP, JI, NCP, AB Party, GOP, Gono Songhati, Interim Government
2. **Themes**: Election Commission, Judiciary, Reform, Democracy, Human Rights, Economy, Law and Order
3. **Article Types**: Speech Analysis, Political Stance
4. **Extracted Data**: Keywords (TF-IDF), Dates, People, Parties

### Complete Pipeline

Scrape and categorize in one command:

```bash
# Scrape, categorize, and save to database
python scripts/scrape_and_categorize.py --save --output results.json

# Show detailed analysis
python scripts/scrape_and_categorize.py \
  --source dailystar \
  --show-details \
  --limit 5
```

### Test Categorization

```bash
# Run comprehensive tests
python scripts/test_categorization.py

# Should show: ✅ ALL TESTS PASSED (8/8)
```

See `CATEGORIZATION_GUIDE.md` for complete documentation and `CATEGORIZATION_QUICKSTART.md` for quick reference.

## Embeddings Generation

### Generate Embeddings

Generate sentence embeddings for semantic search:

```python
from embeddings import generate_embeddings, generate_article_embeddings

# Single text
text = "Political reforms and democracy"
embedding = generate_embeddings(text)
print(embedding.shape)  # (384,)

# Multiple texts
texts = ["Text 1", "Text 2", "Text 3"]
embeddings = generate_embeddings(texts)
print(embeddings.shape)  # (3, 384)

# Articles with automatic title+content combination
articles = [
    {'title': 'Article Title', 'content': 'Article content...'},
    # ... more articles
]

enriched = generate_article_embeddings(articles)
# Each article now has 'embedding' field
```

### Semantic Search

Search articles by meaning, not just keywords:

```python
from embeddings import search_articles

query = "election reforms and voting rights"
results = search_articles(query, articles, top_k=5)

for result in results:
    article = result['article']
    similarity = result['similarity']
    print(f"{article['title']}: {similarity:.4f}")
```

### Model Information

- **Model**: `all-MiniLM-L6-v2` (sentence-transformers)
- **Dimension**: 384
- **Speed**: ~100ms for batch of 32 texts (CPU)
- **Similarity**: Cosine similarity (0.0 to 1.0)
- **Languages**: English + Bangla support

### Complete Pipeline with Embeddings

```python
from scraping import scrape_all_newspapers
from categorization import categorize_scraped_articles
from embeddings import generate_article_embeddings

# 1. Scrape
articles = scrape_all_newspapers(start_date='2024-08-05', end_date='2024-10-10')

# 2. Categorize
categorized = categorize_scraped_articles(articles)

# 3. Generate embeddings
enriched = generate_article_embeddings(categorized)

# Each article now has:
# - content, title, date, source
# - categorization (themes, keywords, people, parties)
# - embedding (384-dim vector for similarity search)
```

### Test Embeddings

```bash
### Test Embeddings

```bash
# Run comprehensive tests
python scripts/test_embeddings.py
```

**For complete documentation, see [EMBEDDINGS_GUIDE.md](./EMBEDDINGS_GUIDE.md)**

---

## Vector Database

The `vector_db.py` module provides comprehensive ChromaDB integration for storing and retrieving articles with rich metadata filtering.

### Basic Usage

```python
from vector_db import VectorDatabase

# Initialize database
db = VectorDatabase(
    persist_directory="./chroma_db",
    collection_name="article_embeddings"
)

# Store articles
articles = [
    {
        'title': 'BNP Rally on Election Reforms',
        'content': 'Tareq Rahman calls for election reforms...',
        'date': '2024-10-05',
        'source': 'Daily Star',
        'parties': ['BNP'],
        'people': ['Tareq Rahman'],
        'keywords': ['election', 'reform'],
        'themes': ['Election Commission'],
        'is_speech': True,
        'language': 'English'
    }
]

result = db.store_embeddings(articles)
print(f"Stored {result['stored']} articles")
```

### Semantic Search

```python
# Simple query
results = db.retrieve_similar_articles(
    query="election reforms and democracy",
    top_k=5
)

for r in results:
    print(f"{r['metadata']['title']}: {r['similarity']:.4f}")
```

### Advanced Filtering

```python
# Filter by multiple criteria
results = db.retrieve_similar_articles(
    query="political statement",
    top_k=10,
    filter_parties=['BNP', 'JI'],
    filter_people=['Tareq Rahman'],
    filter_date_from='2024-10-01',
    filter_date_to='2024-10-31',
    filter_themes=['Election Commission'],
    filter_is_speech=True
)
```

### Complete Pipeline with Vector DB

```python
from scraping import scrape_all_sources
from categorization import ArticleCategorizer
from vector_db import VectorDatabase

# 1. Scrape articles
articles = scrape_all_sources()

# 2. Categorize
categorizer = ArticleCategorizer()
for article in articles:
    cat = categorizer.categorize_article(article)
    article.update({
        'parties': cat['parties'],
        'people': cat['people'],
        'keywords': cat['keywords'],
        'themes': cat['categories'],
        'is_speech': cat['is_speech'],
        'is_stance': cat['is_stance']
    })

# 3. Store in vector database (auto-generates embeddings)
db = VectorDatabase()
result = db.store_embeddings(articles)
print(f"Stored {result['stored']} articles")

# 4. Query with semantic search
results = db.retrieve_similar_articles(
    query="What did political leaders say about reforms?",
    top_k=5,
    filter_is_speech=True
)

for r in results:
    print(f"{r['metadata']['title']}")
    print(f"  Parties: {r.get('parties', [])}")
    print(f"  Similarity: {r['similarity']:.4f}")
```

### Database Management

```python
# Get statistics
stats = db.get_statistics()
print(f"Total articles: {stats['total_articles']}")
print(f"Sources: {', '.join(stats['sources'])}")

# Get article by ID
article = db.get_article_by_id('article_123')

# Delete article
db.delete_article('article_123')
```

### Test Vector Database

```bash
# Run comprehensive tests
python scripts/test_vector_db.py
```

**For complete documentation, see [VECTOR_DB_GUIDE.md](./VECTOR_DB_GUIDE.md)**

# Should show: ✅ ALL TESTS PASSED (10/10)
```

See `EMBEDDINGS_GUIDE.md` for complete documentation including advanced usage, performance optimization, and API reference.

## Usage Examples

### 1. Store an Article

```bash
curl -X POST "http://localhost:8000/api/v1/articles" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "This is an article about artificial intelligence...",
    "metadata": {
      "date": "2025-10-10",
      "category": "technology",
      "persons": ["John Doe", "Jane Smith"],
      "source": "https://example.com/article",
      "title": "AI in 2025"
    }
  }'
```

### 2. Query Articles

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "artificial intelligence",
    "top_k": 5,
    "filter_category": "technology"
  }'
```

### 3. Bulk Insert Articles

```bash
curl -X POST "http://localhost:8000/api/v1/articles/bulk" \
  -H "Content-Type: application/json" \
  -d '{
    "articles": [
      {
        "content": "First article content...",
        "metadata": {"category": "tech", "date": "2025-10-10"}
      },
      {
        "content": "Second article content...",
        "metadata": {"category": "politics", "date": "2025-10-09"}
      }
    ]
  }'
```

## Architecture

### Vector Store Implementation

The `VectorStore` class provides:
- **Embedding generation**: Uses sentence-transformers for creating embeddings
- **Efficient indexing**: ChromaDB's HNSW algorithm for fast similarity search
- **Metadata filtering**: Query with category, date, or person filters
- **Bulk operations**: Optimized batch insertions
- **Persistence**: Data stored on disk for durability

### Metadata Schema

Articles support the following metadata:
- `date`: Publication date (string)
- `category`: Article category (string)
- `persons`: List of persons mentioned (list of strings)
- `source`: Source URL or identifier (string)
- `author`: Article author (string)
- `title`: Article title (string)

### Indexing Strategy

ChromaDB uses:
- **HNSW (Hierarchical Navigable Small World)**: Fast approximate nearest neighbor search
- **Cosine similarity**: For measuring document similarity
- **Metadata indexing**: Efficient filtering on metadata fields

## Python Code Example

```python
import requests

# Initialize API client
BASE_URL = "http://localhost:8000/api/v1"

# Store an article
response = requests.post(
    f"{BASE_URL}/articles",
    json={
        "content": "Your article content here...",
        "metadata": {
            "date": "2025-10-10",
            "category": "technology",
            "persons": ["Person A", "Person B"],
            "title": "Article Title"
        }
    }
)
article = response.json()
print(f"Stored article ID: {article['id']}")

# Query articles
response = requests.post(
    f"{BASE_URL}/query",
    json={
        "query": "search query here",
        "top_k": 5,
        "filter_category": "technology"
    }
)
results = response.json()
print(f"Found {results['total_results']} results")
for result in results['results']:
    print(f"- {result['metadata']['title']} (similarity: {result['distance']})")
```

## Best Practices

1. **Batch Insertions**: Use bulk endpoints for inserting multiple articles
2. **Metadata Indexing**: Include relevant metadata for efficient filtering
3. **Query Optimization**: Use filters to narrow down search space
4. **Error Handling**: Check API responses and handle errors appropriately
5. **Environment Variables**: Keep sensitive config in `.env` file

## Performance Tips

- **Embedding Model**: `all-MiniLM-L6-v2` is fast and efficient (384 dimensions)
- **Batch Size**: Insert articles in batches of 50-100 for optimal performance
- **Top-K**: Limit results to what you need (default 5)
- **Filters**: Use metadata filters to reduce search space

## Troubleshooting

### ChromaDB Connection Issues
- Check if `chroma_db` directory has write permissions
- Verify `CHROMA_PERSIST_DIRECTORY` in `.env`

### Slow Queries
- Reduce `top_k` value
- Use metadata filters
- Consider using a smaller embedding model

### Memory Issues
- Adjust batch size for bulk operations
- Monitor ChromaDB memory usage

## License

MIT

## Contributing

Feel free to submit issues and enhancement requests!

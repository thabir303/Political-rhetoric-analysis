# RAG-IR: RAG-based Information Retrieval System

A FastAPI backend with ChromaDB vector database for storing and querying article embeddings with metadata.

## Features

- 🚀 FastAPI backend with automatic API documentation
- 🔍 Semantic search using sentence-transformers embeddings
- 💾 ChromaDB vector database with persistent storage
- 📊 Article metadata storage (date, category, persons)
- 🔎 Efficient indexing and similarity search
- 📝 Bulk article insertion support
- 🎯 Metadata-based filtering

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
├── main.py                  # Application entry point
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
├── .gitignore
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
```

### Production mode

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

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

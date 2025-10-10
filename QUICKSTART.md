# Quick Start Guide

## Setup and Run (5 minutes)

### 1. Create and activate virtual environment
```bash
cd /home/bs01127/Desktop/RAG-IR
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

This will install:
- FastAPI + Uvicorn (web framework)
- ChromaDB (vector database)
- sentence-transformers (embeddings)
- All other required packages

### 3. Run the server
```bash
python main.py
```

Or with uvicorn:
```bash
uvicorn main:app --reload
```

### 4. Test the API

Open your browser and go to:
- **Interactive Docs**: http://localhost:8000/docs
- **API Root**: http://localhost:8000

### 5. Run the example script

In a new terminal (keep the server running):
```bash
cd /home/bs01127/Desktop/RAG-IR
source venv/bin/activate
python scripts/example_usage.py
```

## Project Structure

```
RAG-IR/
├── config/              # Configuration and settings
│   ├── __init__.py
│   └── settings.py
├── models/              # Pydantic models for validation
│   ├── __init__.py
│   └── schemas.py
├── database/            # Vector database operations
│   ├── __init__.py
│   └── vector_store.py
├── api/                 # API endpoints
│   ├── __init__.py
│   └── routes.py
├── scripts/             # Example and utility scripts
│   ├── __init__.py
│   └── example_usage.py
├── main.py              # Application entry point
├── requirements.txt     # Dependencies
└── .env                 # Environment configuration
```

## Key Features

### ✅ Vector Database (ChromaDB)
- Persistent storage on disk
- Fast similarity search (HNSW algorithm)
- Cosine similarity for semantic search
- Automatic embedding generation

### ✅ Metadata Support
- date: Publication date
- category: Article category
- persons: List of mentioned persons
- source: Source URL
- title: Article title
- author: Article author

### ✅ Efficient Indexing
- Metadata filtering for fast queries
- Bulk insertion support
- Optimized batch operations

### ✅ API Endpoints
- POST /api/v1/articles - Add single article
- POST /api/v1/articles/bulk - Bulk insert
- POST /api/v1/query - Semantic search
- GET /api/v1/articles/{id} - Get article by ID
- DELETE /api/v1/articles/{id} - Delete article
- GET /api/v1/health - Health check
- GET /api/v1/stats - Database statistics

## Quick API Examples

### Add an Article
```bash
curl -X POST "http://localhost:8000/api/v1/articles" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Your article content here...",
    "metadata": {
      "date": "2025-10-10",
      "category": "technology",
      "persons": ["John Doe"],
      "title": "Article Title"
    }
  }'
```

### Query Articles
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "artificial intelligence",
    "top_k": 5,
    "filter_category": "technology"
  }'
```

### Get Statistics
```bash
curl http://localhost:8000/api/v1/stats
```

## Python Client Example

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Add article
response = requests.post(
    f"{BASE_URL}/articles",
    json={
        "content": "Article content...",
        "metadata": {
            "date": "2025-10-10",
            "category": "tech",
            "persons": ["Alice", "Bob"],
            "title": "My Article"
        }
    }
)
print(response.json())

# Query
response = requests.post(
    f"{BASE_URL}/query",
    json={
        "query": "search terms",
        "top_k": 5
    }
)
results = response.json()
for article in results['results']:
    print(f"{article['metadata']['title']}: {article['distance']}")
```

## Troubleshooting

### Import errors after installation?
Make sure virtual environment is activated:
```bash
source venv/bin/activate
```

### Port already in use?
Change port in `.env` file or use:
```bash
uvicorn main:app --port 8001
```

### ChromaDB permission issues?
Ensure write permissions:
```bash
chmod -R 755 chroma_db/
```

## Next Steps

1. ✅ Server is running
2. ✅ Try the example script
3. ✅ Explore the API docs at /docs
4. 🔨 Integrate with your scraper
5. 🔨 Build your frontend

## Performance Tips

- Use bulk endpoints for multiple articles
- Add metadata for better filtering
- Limit top_k to reduce query time
- Use category/date filters to narrow search

Enjoy building your RAG-IR system! 🚀

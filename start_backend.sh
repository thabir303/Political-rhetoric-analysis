#!/bin/bash

echo "=========================================="
echo "Starting RAG-IR Backend Server"
echo "=========================================="
echo ""
echo "📁 Backend Structure:"
echo "  backend/"
echo "    ├── core/      (scraping, embeddings, llm, vector_db)"
echo "    ├── services/  (political storage & analysis)"
echo "    ├── routes/    (general, articles, scraping, analysis)"
echo "    ├── models/    (pydantic schemas)"
echo "    ├── database/  (vector store)"
echo "    └── config/    (settings)"
echo ""
echo "🚀 Key Endpoints:"
echo "  POST /api/v1/scraping/newspapers  →  Scrape ONLY (NO LLM)"
echo "  POST /api/v1/analysis/llm         →  LLM Analysis ONLY"
echo ""
echo "📖 Documentation: http://localhost:8000/docs"
echo ""
echo "=========================================="
echo ""

# Activate virtual environment
source venv/bin/activate

# Start server
uvicorn backend_main:app --reload --host 0.0.0.0 --port 8000

#!/bin/bash

# Example API Requests for the New Backend Structure

BASE_URL="http://localhost:8000/api/v1"

echo "=========================================="
echo "RAG-IR Backend API Examples"
echo "=========================================="
echo ""

# Example 1: Health Check
echo "1. Health Check"
echo "   GET $BASE_URL/health"
echo ""
# curl -X GET "$BASE_URL/health"
echo ""

# Example 2: Scrape Newspapers (NO LLM)
echo "2. Scrape Newspapers (NO LLM Analysis)"
echo "   POST $BASE_URL/scraping/newspapers"
echo ""
cat << 'EOF'
curl -X POST "$BASE_URL/scraping/newspapers" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-10-01",
    "end_date": "2024-10-14",
    "newspapers": ["ProthomAlo", "Jugantor"]
  }'
EOF
echo ""
echo ""

# Example 3: LLM Analysis (Separate)
echo "3. Run LLM Analysis on Stored Articles"
echo "   POST $BASE_URL/analysis/llm"
echo ""
cat << 'EOF'
curl -X POST "$BASE_URL/analysis/llm" \
  -H "Content-Type: application/json" \
  -d '{
    "party": "BNP",
    "date_from": "2024-10-01",
    "date_to": "2024-10-14",
    "limit": 10,
    "language": "Bangla",
    "include_summary": true,
    "include_keywords": true,
    "include_stance": true
  }'
EOF
echo ""
echo ""

# Example 4: Query Articles
echo "4. Query Articles (Semantic Search)"
echo "   POST $BASE_URL/articles/query"
echo ""
cat << 'EOF'
curl -X POST "$BASE_URL/articles/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "election reform",
    "top_k": 10,
    "filter_category": "Politics"
  }'
EOF
echo ""
echo ""

# Example 5: Generate Party Report
echo "5. Generate Party Report"
echo "   POST $BASE_URL/analysis/party-report"
echo ""
cat << 'EOF'
curl -X POST "$BASE_URL/analysis/party-report" \
  -H "Content-Type: application/json" \
  -d '{
    "party": "bnp",
    "limit": 50,
    "language": "Bangla"
  }'
EOF
echo ""
echo ""

# Example 6: Scrape Political Articles (Party-wise)
echo "6. Scrape Political Articles (Party-wise Storage)"
echo "   POST $BASE_URL/scraping/political"
echo ""
cat << 'EOF'
curl -X POST "$BASE_URL/scraping/political?party=bnp&start_date=2024-10-01&end_date=2024-10-14"
EOF
echo ""
echo ""

# Example 7: Statistics
echo "7. Get Statistics"
echo "   GET $BASE_URL/stats"
echo ""
# curl -X GET "$BASE_URL/stats"
echo ""

echo "=========================================="
echo "To execute any example, uncomment the curl command"
echo "or copy and run it manually"
echo "=========================================="

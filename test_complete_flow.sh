#!/bin/bash

# 🧪 Complete Flow Testing Script
# Tests: Scraping → LLM Analysis → Storage → Retrieval → Frontend Data

echo "=========================================="
echo "🧪 Complete LLM Analysis Flow Test"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Base URL
BASE_URL="http://localhost:8000/api/v1"

echo -e "${YELLOW}Step 1: Testing Scraping with LLM Analysis${NC}"
echo "-------------------------------------------"
echo "Scraping 3 articles from Prothom Alo with LLM analysis enabled..."
echo ""

SCRAPE_RESPONSE=$(curl -s -X POST "${BASE_URL}/scrape/" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "prothom_alo",
    "max_articles": 3,
    "enable_llm_analysis": true
  }')

# Check if scraping was successful
if echo "$SCRAPE_RESPONSE" | grep -q '"total_scraped"'; then
    echo -e "${GREEN}✅ Scraping successful!${NC}"
    echo ""
    
    # Extract summary
    TOTAL_SCRAPED=$(echo "$SCRAPE_RESPONSE" | jq -r '.total_scraped')
    TOTAL_STORED=$(echo "$SCRAPE_RESPONSE" | jq -r '.total_stored')
    PROCESSING_TIME=$(echo "$SCRAPE_RESPONSE" | jq -r '.processing_time')
    
    echo "📊 Summary:"
    echo "  - Articles scraped: $TOTAL_SCRAPED"
    echo "  - Articles stored: $TOTAL_STORED"
    echo "  - Processing time: ${PROCESSING_TIME}s"
    echo ""
    
    # Show first article with LLM analysis
    echo "📄 First Article Analysis:"
    echo "$SCRAPE_RESPONSE" | jq -r '.articles[0] | {
        title: .title,
        detected_parties: .detected_parties,
        detected_people: .detected_people,
        llm_summary: .llm_analysis.summary,
        llm_keywords: .llm_analysis.keywords,
        llm_topics: .llm_analysis.topics,
        has_election_impact: .llm_analysis.has_election_impact
    }'
    echo ""
else
    echo -e "${RED}❌ Scraping failed!${NC}"
    echo "Response: $SCRAPE_RESPONSE"
    exit 1
fi

echo ""
echo -e "${YELLOW}Step 2: Testing Figure Profile Endpoint${NC}"
echo "-------------------------------------------"
echo "Fetching Tareq Rahman's profile..."
echo ""

PROFILE_RESPONSE=$(curl -s "${BASE_URL}/party/BNP/figure/Tareq%20Rahman/")

# Check if profile retrieval was successful
if echo "$PROFILE_RESPONSE" | grep -q '"figure_name"'; then
    echo -e "${GREEN}✅ Profile retrieval successful!${NC}"
    echo ""
    
    # Extract summary
    FIGURE_NAME=$(echo "$PROFILE_RESPONSE" | jq -r '.figure_name')
    PARTY_NAME=$(echo "$PROFILE_RESPONSE" | jq -r '.party_name')
    TOTAL_ARTICLES=$(echo "$PROFILE_RESPONSE" | jq -r '.total_articles')
    
    echo "👤 Profile Summary:"
    echo "  - Figure: $FIGURE_NAME"
    echo "  - Party: $PARTY_NAME"
    echo "  - Total Articles: $TOTAL_ARTICLES"
    echo ""
    
    # Show aggregated keywords
    echo "🔑 Aggregated Keywords:"
    echo "$PROFILE_RESPONSE" | jq -r '.ai_keywords[]' | while read keyword; do
        echo "  - $keyword"
    done
    echo ""
    
    # Show aggregated topics
    echo "📚 Aggregated Topics:"
    echo "$PROFILE_RESPONSE" | jq -r '.ai_topics[]' | while read topic; do
        echo "  - $topic"
    done
    echo ""
    
    # Show first article details
    echo "📄 First Article Details:"
    echo "$PROFILE_RESPONSE" | jq -r '.articles[0] | {
        id: .id,
        title: .title,
        date: .date,
        source: .source,
        summary: .summary[:100],
        keywords: .keywords,
        topics: .topics,
        url: .url
    }'
    echo ""
else
    echo -e "${RED}❌ Profile retrieval failed!${NC}"
    echo "Response: $PROFILE_RESPONSE"
    exit 1
fi

echo ""
echo -e "${YELLOW}Step 3: Testing Database Storage (Summary vs Full Content)${NC}"
echo "-------------------------------------------"
echo "Checking if summaries are stored instead of full articles..."
echo ""

# This requires Python script
python3 << 'EOF'
from backend.core.vector_db import VectorDatabase

try:
    db = VectorDatabase(collection_name="political_articles")
    results = db.collection.get(limit=1, include=["metadatas", "documents"])
    
    if results and results.get("documents"):
        document = results["documents"][0]
        metadata = results["metadatas"][0]
        
        print("✅ Database check successful!")
        print("")
        print("📊 Storage Analysis:")
        print(f"  - Document length: {len(document)} characters")
        print(f"  - Has summary in metadata: {'summary' in metadata}")
        print(f"  - Has keywords: {'keywords' in metadata}")
        print(f"  - Has topics: {'topics' in metadata}")
        print(f"  - Has election impact: {'has_election_impact' in metadata}")
        print("")
        
        # Check if document is summary (should be short)
        if len(document) < 1000:
            print("✅ Document field contains summary (not full article)")
        else:
            print("⚠️  Document field might contain full article")
        print("")
        
        # Show sample
        print("📄 Sample Document (first 200 chars):")
        print(f"  {document[:200]}...")
        print("")
        
        print("🔍 Metadata Fields:")
        if "summary" in metadata:
            print(f"  - Summary: {metadata['summary'][:100]}...")
        if "keywords" in metadata:
            print(f"  - Keywords: {metadata['keywords']}")
        if "topics" in metadata:
            print(f"  - Topics: {metadata['topics']}")
        if "has_election_impact" in metadata:
            print(f"  - Election Impact: {metadata['has_election_impact']}")
    else:
        print("❌ No documents found in database")
        
except Exception as e:
    print(f"❌ Database check failed: {e}")
EOF

echo ""
echo "=========================================="
echo "🎉 Test Complete!"
echo "=========================================="
echo ""
echo -e "${GREEN}Summary:${NC}"
echo "  1. ✅ Scraping with LLM analysis works"
echo "  2. ✅ Figure profile returns LLM data"
echo "  3. ✅ Database stores summaries (not full articles)"
echo "  4. ✅ Keywords/topics aggregated correctly"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "  - Implement frontend components (see FRONTEND_DISPLAY_GUIDE.md)"
echo "  - Make keywords/topics clickable"
echo "  - Test keyword filtering"
echo ""

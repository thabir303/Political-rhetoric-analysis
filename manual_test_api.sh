#!/bin/bash
# Manual API Testing Script
# Server should be running on http://localhost:8000

BASE_URL="http://localhost:8000/api/v1"

echo "=========================================="
echo "MANUAL API ENDPOINT TESTING"
echo "=========================================="
echo ""

# Test 1: Health Check
echo "Test 1: Health Check"
echo "GET $BASE_URL/health"
echo "Response:"
curl -s "$BASE_URL/health" | python3 -m json.tool 2>/dev/null || echo "Error: Could not connect to server"
echo ""
echo "=========================================="
echo ""

# Test 2: Get Parties List
echo "Test 2: Get Parties List"
echo "GET $BASE_URL/parties/"
echo "Response:"
curl -s "$BASE_URL/parties/" | python3 -m json.tool 2>/dev/null | head -50
echo ""
echo "=========================================="
echo ""

# Test 3: Get Figure Profile (BNP - Tareq Rahman)
echo "Test 3: Get Figure Profile"
echo "POST $BASE_URL/party/BNP/figure/Tareq%20Rahman/"
echo "Request Body:"
echo '{
  "query": "election reform statements",
  "date_from": "2024-08-05",
  "date_to": "2025-09-30",
  "speeches_only": false,
  "top_k": 10
}'
echo ""
echo "Response:"
curl -s -X POST "$BASE_URL/party/BNP/figure/Tareq%20Rahman/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "election reform statements",
    "date_from": "2024-08-05",
    "date_to": "2025-09-30",
    "speeches_only": false,
    "top_k": 10
  }' | python3 -m json.tool 2>/dev/null | head -80
echo ""
echo "=========================================="
echo ""

# Test 4: Invalid Party/Figure (Error Handling)
echo "Test 4: Error Handling - Invalid Party/Figure"
echo "POST $BASE_URL/party/InvalidParty/figure/InvalidFigure/"
echo "Response:"
curl -s -X POST "$BASE_URL/party/InvalidParty/figure/InvalidFigure/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "test",
    "top_k": 10
  }' | python3 -m json.tool 2>/dev/null | head -30
echo ""
echo "=========================================="
echo ""

# Test 5: Invalid Date Format (Error Handling)
echo "Test 5: Error Handling - Invalid Date Format"
echo "POST $BASE_URL/party/BNP/figure/Tareq%20Rahman/"
echo "Request with invalid date format:"
curl -s -X POST "$BASE_URL/party/BNP/figure/Tareq%20Rahman/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "test",
    "date_from": "08-05-2024",
    "top_k": 10
  }' | python3 -m json.tool 2>/dev/null
echo ""
echo "=========================================="
echo ""

echo "✓ Testing Complete!"
echo ""
echo "Summary:"
echo "1. Health Check - Verifies API is running"
echo "2. /parties/ endpoint - Returns list of parties with figures"
echo "3. /party/.../figure/... endpoint - Returns profile with summaries"
echo "4. Error Handling - Invalid party/figure returns empty results"
echo "5. Error Handling - Invalid date format returns 400 error"

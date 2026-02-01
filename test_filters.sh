#!/bin/bash
# Example curl requests with filters for the RAG query API

echo "=== Query Examples with Filters ==="
echo ""

echo "1. Filter by specific domain (bakkah.net only):"
echo ""
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What courses are available?",
    "filters": {
      "domains": ["bakkah.net"]
    }
  }' | jq '.answer'

echo ""
echo "---"
echo ""

echo "2. Filter by multiple domains:"
echo ""
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Tell me about Islamic education",
    "filters": {
      "domains": ["bakkah.net", "islamqa.info"]
    }
  }' | jq

echo ""
echo "---"
echo ""

echo "3. Filter by content type (HTML only):"
echo ""
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is available?",
    "filters": {
      "content_type": ["html"]
    }
  }' | jq

echo ""
echo "---"
echo ""

echo "4. Filter by language (English):"
echo ""
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What courses does bakkah offer?",
    "filters": {
      "language": "en"
    }
  }' | jq

echo ""
echo "---"
echo ""

echo "5. Combined filters (domain + content type):"
echo ""
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Islamic studies information",
    "filters": {
      "domains": ["bakkah.net"],
      "content_type": ["html"]
    }
  }' | jq

echo ""
echo "---"
echo ""

echo "6. Filter by date range (recent content):"
echo ""
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Latest courses",
    "filters": {
      "crawled_after": "2025-01-01T00:00:00Z"
    }
  }' | jq

echo ""
echo "---"
echo ""

echo "7. No filters (search all domains):"
echo ""
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What information is available?",
    "filters": null
  }' | jq

echo ""
echo "---"
echo ""

echo "8. Get only answer with domain filter:"
echo ""
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Tell me about courses",
    "filters": {
      "domains": ["bakkah.net"]
    }
  }' | jq '{answer: .answer, filtered_domains: .sources[].domain | unique}'

echo ""
echo "Done!"

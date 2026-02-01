# API Usage Examples

This document provides comprehensive examples of using the Web Crawler RAG API.

## Table of Contents
- [Authentication](#authentication)
- [Basic Query](#basic-query)
- [Advanced Query](#advanced-query)
- [Crawling](#crawling)
- [Status Monitoring](#status-monitoring)
- [Python Client Example](#python-client-example)
- [JavaScript/Node.js Example](#javascript-example)
- [cURL Examples](#curl-examples)

## Authentication

Currently, the API doesn't require authentication. For production use, consider adding:
- API keys
- OAuth2
- JWT tokens

## Basic Query

### Simple Question

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is Python programming language?"
  }'
```

Response:
```json
{
  "query": "What is Python programming language?",
  "answer": "Python is a high-level, interpreted programming language...",
  "sources": [
    {
      "url": "https://docs.python.org/3/",
      "domain": "docs.python.org",
      "title": "Python Documentation",
      "snippet": "Python is an interpreted, high-level...",
      "similarity_score": 0.92,
      "highlighted_text": "Python is an interpreted, high-level",
      "content_type": "html"
    }
  ],
  "llm_provider": "gemini",
  "confidence_score": 0.88,
  "processing_time_ms": 1250.5
}
```

## Advanced Query

### With Custom Parameters

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Compare async programming in Python vs JavaScript",
    "llm_provider": "deepseek",
    "context": "Focus on practical use cases and performance",
    "top_k": 10,
    "snippet_length": 500,
    "temperature": 0.3,
    "include_sources": true
  }'
```

### Query Without Sources

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Quick answer needed",
    "include_sources": false
  }'
```

## Crawling

### Trigger Manual Crawl

```bash
curl -X POST "http://localhost:8000/api/v1/crawl" \
  -H "Content-Type: application/json" \
  -d '{
    "domains": [
      "docs.python.org",
      "fastapi.tiangolo.com"
    ],
    "force_recrawl": false
  }'
```

### Force Recrawl

```bash
curl -X POST "http://localhost:8000/api/v1/crawl" \
  -H "Content-Type: application/json" \
  -d '{
    "domains": ["example.com"],
    "force_recrawl": true
  }'
```

## Status Monitoring

### Check Crawl Status

```bash
curl -X GET "http://localhost:8000/api/v1/status"
```

### Get Detailed Statistics

```bash
curl -X GET "http://localhost:8000/api/v1/stats"
```

### View Recent Logs

```bash
# Get last 50 logs
curl -X GET "http://localhost:8000/api/v1/logs?limit=50"

# Filter by domain
curl -X GET "http://localhost:8000/api/v1/logs?limit=100&domain=example.com"
```

### Health Check

```bash
curl -X GET "http://localhost:8000/api/v1/health"
```

## Python Client Example

```python
import requests
from typing import Dict, List

class WebCrawlerRAGClient:
    """Python client for Web Crawler RAG API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"
    
    def query(
        self,
        query: str,
        llm_provider: str = None,
        context: str = None,
        top_k: int = None,
        temperature: float = None
    ) -> Dict:
        """Query the RAG system"""
        payload = {"query": query}
        
        if llm_provider:
            payload["llm_provider"] = llm_provider
        if context:
            payload["context"] = context
        if top_k:
            payload["top_k"] = top_k
        if temperature:
            payload["temperature"] = temperature
        
        response = requests.post(f"{self.api_base}/query", json=payload)
        response.raise_for_status()
        return response.json()
    
    def crawl(self, domains: List[str], force_recrawl: bool = False) -> Dict:
        """Trigger crawl of domains"""
        payload = {
            "domains": domains,
            "force_recrawl": force_recrawl
        }
        
        response = requests.post(f"{self.api_base}/crawl", json=payload)
        response.raise_for_status()
        return response.json()
    
    def get_status(self) -> Dict:
        """Get crawl status"""
        response = requests.get(f"{self.api_base}/status")
        response.raise_for_status()
        return response.json()
    
    def get_health(self) -> Dict:
        """Check system health"""
        response = requests.get(f"{self.api_base}/health")
        response.raise_for_status()
        return response.json()
    
    def get_logs(self, limit: int = 100, domain: str = None) -> Dict:
        """Get crawl logs"""
        params = {"limit": limit}
        if domain:
            params["domain"] = domain
        
        response = requests.get(f"{self.api_base}/logs", params=params)
        response.raise_for_status()
        return response.json()


# Usage example
if __name__ == "__main__":
    client = WebCrawlerRAGClient()
    
    # Query
    result = client.query(
        query="What are the main features of FastAPI?",
        llm_provider="gemini",
        top_k=5
    )
    
    print(f"Answer: {result['answer']}")
    print(f"\nSources ({len(result['sources'])}):")
    for source in result['sources']:
        print(f"  - {source['url']} (score: {source['similarity_score']:.2f})")
    
    # Check status
    status = client.get_status()
    print(f"\nTotal pages in database: {status['total_pages_in_db']}")
```

## JavaScript Example

```javascript
class WebCrawlerRAGClient {
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
    this.apiBase = `${baseUrl}/api/v1`;
  }

  async query(options) {
    const response = await fetch(`${this.apiBase}/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(options),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  async crawl(domains, forceRecrawl = false) {
    const response = await fetch(`${this.apiBase}/crawl`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        domains,
        force_recrawl: forceRecrawl,
      }),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  async getStatus() {
    const response = await fetch(`${this.apiBase}/status`);
    
    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  async getHealth() {
    const response = await fetch(`${this.apiBase}/health`);
    
    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }
}

// Usage example
(async () => {
  const client = new WebCrawlerRAGClient();

  try {
    // Query
    const result = await client.query({
      query: 'What is machine learning?',
      llm_provider: 'gemini',
      top_k: 5,
    });

    console.log('Answer:', result.answer);
    console.log('\nSources:');
    result.sources.forEach(source => {
      console.log(`  - ${source.url} (${source.similarity_score.toFixed(2)})`);
    });

    // Check health
    const health = await client.getHealth();
    console.log('\nSystem Status:', health.status);
  } catch (error) {
    console.error('Error:', error);
  }
})();
```

## cURL Examples

### Complete Workflow Example

```bash
#!/bin/bash

API_BASE="http://localhost:8000/api/v1"

# 1. Check health
echo "Checking health..."
curl -X GET "$API_BASE/health"

echo -e "\n\n"

# 2. Add domains to crawl
echo "Triggering crawl..."
curl -X POST "$API_BASE/crawl" \
  -H "Content-Type: application/json" \
  -d '{
    "domains": ["docs.python.org"],
    "force_recrawl": false
  }'

echo -e "\n\n"

# 3. Wait a bit for crawling to start
sleep 5

# 4. Check status
echo "Checking status..."
curl -X GET "$API_BASE/status"

echo -e "\n\n"

# 5. Query the system
echo "Querying..."
curl -X POST "$API_BASE/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is Python?",
    "top_k": 3
  }'

echo -e "\n\n"

# 6. View logs
echo "Getting logs..."
curl -X GET "$API_BASE/logs?limit=10"
```

## Error Handling

### Example with Error Handling (Python)

```python
import requests
from requests.exceptions import RequestException

def safe_query(query: str):
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/query",
            json={"query": query},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.Timeout:
        print("Request timed out")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error: {e}")
        if e.response is not None:
            print(f"Details: {e.response.json()}")
    except RequestException as e:
        print(f"Request error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    
    return None
```

## Rate Limiting

The API includes rate limiting (default: 100 requests per 60 seconds).

Example handling rate limits:

```python
import time
import requests

def query_with_retry(query: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            response = requests.post(
                "http://localhost:8000/api/v1/query",
                json={"query": query}
            )
            
            if response.status_code == 429:  # Rate limited
                wait_time = int(response.headers.get('Retry-After', 60))
                print(f"Rate limited. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff
    
    return None
```

## Batch Processing

### Process Multiple Queries

```python
import asyncio
import aiohttp

async def batch_query(queries: list):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for query in queries:
            task = asyncio.create_task(
                query_async(session, query)
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        return results

async def query_async(session, query):
    async with session.post(
        'http://localhost:8000/api/v1/query',
        json={'query': query}
    ) as response:
        return await response.json()

# Usage
queries = [
    "What is Python?",
    "What is JavaScript?",
    "What is TypeScript?"
]

results = asyncio.run(batch_query(queries))
```

## Monitoring and Analytics

### Track Query Performance

```python
import time
from datetime import datetime

def query_with_metrics(query: str):
    start_time = time.time()
    
    response = requests.post(
        "http://localhost:8000/api/v1/query",
        json={"query": query}
    )
    
    end_time = time.time()
    
    result = response.json()
    
    metrics = {
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "client_time_ms": (end_time - start_time) * 1000,
        "server_time_ms": result.get("processing_time_ms"),
        "sources_count": len(result.get("sources", [])),
        "confidence_score": result.get("confidence_score")
    }
    
    print(f"Metrics: {metrics}")
    return result
```

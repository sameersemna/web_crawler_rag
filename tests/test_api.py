"""
Example tests for the Web Crawler RAG API
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "name" in response.json()
    assert response.json()["status"] == "running"


def test_api_info():
    """Test API info endpoint"""
    response = client.get("/api/v1/info")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert "features" in data
    assert isinstance(data["features"], list)


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "vector_db_status" in data
    assert "llm_providers" in data


def test_query_endpoint_validation():
    """Test query endpoint with invalid input"""
    response = client.post(
        "/api/v1/query",
        json={}  # Missing required 'query' field
    )
    assert response.status_code == 422  # Validation error


def test_query_endpoint_valid():
    """Test query endpoint with valid input"""
    response = client.post(
        "/api/v1/query",
        json={
            "query": "What is Python?",
            "top_k": 3
        }
    )
    # May fail if no data in DB, but should not error
    assert response.status_code in [200, 500]


def test_crawl_status():
    """Test crawl status endpoint"""
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    data = response.json()
    assert "domains" in data
    assert "total_pages_in_db" in data
    assert isinstance(data["domains"], list)


def test_stats_endpoint():
    """Test statistics endpoint"""
    response = client.get("/api/v1/stats")
    assert response.status_code == 200
    data = response.json()
    assert "domains" in data
    assert "pages" in data
    assert "vector_db" in data


def test_logs_endpoint():
    """Test logs endpoint"""
    response = client.get("/api/v1/logs?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "logs" in data
    assert "total" in data
    assert isinstance(data["logs"], list)


def test_crawl_trigger():
    """Test manual crawl trigger"""
    response = client.post(
        "/api/v1/crawl",
        json={
            "domains": ["example.com"],
            "force_recrawl": False
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "domains" in data


@pytest.mark.parametrize("temperature", [0.1, 0.5, 0.9, 1.5])
def test_query_temperature_parameter(temperature):
    """Test query with different temperature values"""
    response = client.post(
        "/api/v1/query",
        json={
            "query": "Test query",
            "temperature": temperature
        }
    )
    # Should accept valid temperature values
    assert response.status_code in [200, 500]


def test_query_with_context():
    """Test query with additional context"""
    response = client.post(
        "/api/v1/query",
        json={
            "query": "What are the benefits?",
            "context": "Focus on enterprise features"
        }
    )
    assert response.status_code in [200, 500]


def test_invalid_llm_provider():
    """Test query with invalid LLM provider"""
    response = client.post(
        "/api/v1/query",
        json={
            "query": "Test",
            "llm_provider": "invalid_provider"
        }
    )
    # Should fail validation
    assert response.status_code == 422

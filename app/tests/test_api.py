"""Test API endpoints"""

import pytest


def test_root_endpoint(client):
    """Test root endpoint returns correct message"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "AskDocs API"
    assert data["version"] == "0.1.0"
    assert data["status"] == "running"


def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "askdocs-rag-agent"
    assert data["version"] == "0.1.0"


def test_docs_available(client):
    """Test Swagger docs are accessible"""
    response = client.get("/docs")
    assert response.status_code == 200
    assert b"Swagger UI" in response.content or b"FastAPI" in response.content


def test_openapi_schema(client):
    """Test OpenAPI schema is available"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "AskDocs RAG Agent"
    assert schema["info"]["version"] == "0.1.0"

"""Tests for /ask question-answering endpoint"""
import pytest
from unittest.mock import patch
from app.llm.mock_provider import MockLLMProvider
from app.tests.utils import document_api_call


def test_ask_question_success(client, sample_document_with_chunks):
    """Test asking a question with mock LLM"""
    request_data = {
        "question": "How many vacation days do employees get?",
        "top_k": 3,
        "include_sources": True
    }

    response = client.post("/ask/", json=request_data)

    assert response.status_code == 200
    data = response.json()

    # Document API call
    document_api_call(
        "ask_question.json",
        "POST",
        "/ask/",
        request_data,
        data,
        response.status_code
    )

    # Check response structure
    assert "question" in data
    assert "answer" in data
    assert "sources" in data
    assert "timestamp" in data
    assert "model_used" in data

    # Check question matches
    assert data["question"] == "How many vacation days do employees get?"

    # Check answer exists
    assert isinstance(data["answer"], str)
    assert len(data["answer"]) > 0

    # Check sources
    assert isinstance(data["sources"], list)
    assert len(data["sources"]) > 0
    assert len(data["sources"]) <= 3  # top_k = 3

    # Check source structure
    source = data["sources"][0]
    assert "chunk_id" in source
    assert "filename" in source
    assert "page_number" in source
    assert "similarity_score" in source
    assert "text_excerpt" in source


def test_ask_question_without_sources(client, sample_document_with_chunks):
    """Test asking question without requesting sources"""
    response = client.post(
        "/ask/",
        json={
            "question": "What is the sick leave policy?",
            "include_sources": False
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Should have answer but empty sources
    assert "answer" in data
    assert data["sources"] == []


def test_ask_question_no_documents(client):
    """Test asking question when no documents are uploaded"""
    response = client.post(
        "/ask/",
        json={"question": "Any question?"}
    )

    assert response.status_code == 404
    assert "No relevant information found" in response.json()["detail"]


def test_ask_question_invalid_top_k(client, sample_document_with_chunks):
    """Test with invalid top_k parameter"""
    # top_k too large
    response = client.post(
        "/ask/",
        json={
            "question": "Test question",
            "top_k": 100  # Max is 20
        }
    )

    assert response.status_code == 422  # Validation error


def test_ask_question_empty_string(client, sample_document_with_chunks):
    """Test with empty question"""
    response = client.post(
        "/ask/",
        json={"question": ""}
    )

    assert response.status_code == 422  # Validation error


def test_ask_question_long_string(client, sample_document_with_chunks):
    """Test with very long question"""
    response = client.post(
        "/ask/",
        json={"question": "x" * 1001}  # Max is 1000
    )

    assert response.status_code == 422  # Validation error


def test_ask_health_check(client):
    """Test /ask/health endpoint"""
    response = client.get("/ask/health")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"
    assert data["service"] == "question-answering"
    assert "llm_provider" in data


def test_ask_question_default_parameters(client, sample_document_with_chunks):
    """Test that default parameters work correctly"""
    response = client.post(
        "/ask/",
        json={"question": "What are the work hours?"}
    )

    assert response.status_code == 200
    data = response.json()

    # Should use defaults: top_k=5, include_sources=True
    assert len(data["sources"]) <= 5
    assert len(data["sources"]) > 0


def test_ask_question_model_used(client, sample_document_with_chunks):
    """Test that model_used field is populated"""
    response = client.post(
        "/ask/",
        json={"question": "What is the remote work policy?"}
    )

    assert response.status_code == 200
    data = response.json()

    # Should indicate which LLM provider was used
    assert data["model_used"] in ["mock", "gemini", "azure"]


def test_source_citation_format(client, sample_document_with_chunks):
    """Test that source citations are properly formatted"""
    response = client.post(
        "/ask/",
        json={
            "question": "Tell me about health insurance",
            "top_k": 2
        }
    )

    assert response.status_code == 200
    data = response.json()

    for source in data["sources"]:
        # Check all required fields
        assert isinstance(source["chunk_id"], int)
        assert isinstance(source["filename"], str)
        assert isinstance(source["page_number"], int)
        assert isinstance(source["similarity_score"], float)
        assert isinstance(source["text_excerpt"], str)

        # Score should be between 0 and 1
        assert 0 <= source["similarity_score"] <= 1

        # Text excerpt should not be too long
        assert len(source["text_excerpt"]) <= 203  # 200 + "..."

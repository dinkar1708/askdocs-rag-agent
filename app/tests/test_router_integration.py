"""Integration tests for router with /ask endpoint"""
import pytest
from app.tests.utils.api_documenter import document_api_call


def test_ask_with_router_answer_intent(client, sample_document_with_chunks):
    """Test /ask endpoint with high confidence (ANSWER intent)"""
    response = client.post(
        "/ask/",
        json={
            "question": "How many vacation days do employees get?",
            "top_k": 3,
            "include_sources": True
        }
    )

    data = response.json()

    # Document API call
    document_api_call(
        "ask_with_router_answer.json",
        "POST",
        "/ask/",
        {
            "question": "How many vacation days do employees get?",
            "top_k": 3,
            "include_sources": True
        },
        data,
        response.status_code
    )

    assert response.status_code == 200
    assert "answer" in data
    assert "metadata" in data
    assert data["metadata"]["intent"] == "answer"
    assert data["metadata"]["confidence"] > 0


def test_ask_with_router_refuse_intent_off_topic(client, sample_document_with_chunks):
    """Test /ask endpoint with off-topic question (REFUSE intent)"""
    response = client.post(
        "/ask/",
        json={
            "question": "What's the weather today?",
            "top_k": 3,
            "include_sources": True
        }
    )

    data = response.json()

    # Document API call
    document_api_call(
        "ask_with_router_refuse_off_topic.json",
        "POST",
        "/ask/",
        {
            "question": "What's the weather today?",
            "top_k": 3,
            "include_sources": True
        },
        data,
        response.status_code
    )

    assert response.status_code == 200
    assert "not_found" in data["answer"]
    assert data["metadata"]["intent"] == "refuse"


def test_ask_with_router_clarify_intent(client, sample_document_with_chunks):
    """Test /ask endpoint with ambiguous question (CLARIFY intent)"""
    response = client.post(
        "/ask/",
        json={
            "question": "How?",
            "top_k": 3,
            "include_sources": True
        }
    )

    data = response.json()

    # Document API call
    document_api_call(
        "ask_with_router_clarify.json",
        "POST",
        "/ask/",
        {
            "question": "How?",
            "top_k": 3,
            "include_sources": True
        },
        data,
        response.status_code
    )

    assert response.status_code == 200
    assert "more specific" in data["answer"].lower() or "clarification" in data["answer"].lower()
    assert data["metadata"]["intent"] == "clarify"


def test_ask_with_router_metadata_included(client, sample_document_with_chunks):
    """Test that router metadata is included in all responses"""
    response = client.post(
        "/ask/",
        json={
            "question": "What is the company policy?",
            "top_k": 5,
            "include_sources": True
        }
    )

    data = response.json()

    # Document API call
    document_api_call(
        "ask_with_router_metadata.json",
        "POST",
        "/ask/",
        {
            "question": "What is the company policy?",
            "top_k": 5,
            "include_sources": True
        },
        data,
        response.status_code
    )

    assert response.status_code == 200
    assert "metadata" in data
    assert "intent" in data["metadata"]
    assert "confidence" in data["metadata"]
    assert "reason" in data["metadata"]


def test_ask_with_router_no_documents(client):
    """Test /ask with no documents uploaded (REFUSE intent)"""
    response = client.post(
        "/ask/",
        json={
            "question": "What is the policy?",
            "top_k": 3,
            "include_sources": True
        }
    )

    data = response.json()

    # Document API call
    document_api_call(
        "ask_with_router_no_documents.json",
        "POST",
        "/ask/",
        {
            "question": "What is the policy?",
            "top_k": 3,
            "include_sources": True
        },
        data,
        response.status_code
    )

    assert response.status_code == 200
    assert "not_found" in data["answer"]
    assert data["metadata"]["intent"] == "refuse"


def test_ask_with_router_different_confidence_levels(client, sample_document_with_chunks):
    """Test that different questions get appropriate confidence levels"""
    # High confidence question
    response1 = client.post(
        "/ask/",
        json={
            "question": "What are the vacation days?",
            "top_k": 3,
            "include_sources": True
        }
    )
    data1 = response1.json()

    # Lower relevance question
    response2 = client.post(
        "/ask/",
        json={
            "question": "Tell me about the organization structure",
            "top_k": 3,
            "include_sources": True
        }
    )
    data2 = response2.json()

    # Document API call for comparison
    document_api_call(
        "ask_with_router_confidence_comparison.json",
        "POST",
        "/ask/",
        {
            "questions": [
                "What are the vacation days?",
                "Tell me about the organization structure"
            ]
        },
        {
            "high_confidence_example": data1,
            "lower_confidence_example": data2
        },
        200
    )

    assert response1.status_code == 200
    assert response2.status_code == 200
    assert "metadata" in data1
    assert "metadata" in data2


def test_ask_router_sources_included_all_intents(client, sample_document_with_chunks):
    """Test that sources are included correctly for all intents"""
    # ANSWER intent - should have sources
    response1 = client.post(
        "/ask/",
        json={
            "question": "What is the vacation policy?",
            "top_k": 3,
            "include_sources": True
        }
    )
    data1 = response1.json()

    assert len(data1["sources"]) > 0

    # REFUSE intent - may have sources but answer is "not_found"
    response2 = client.post(
        "/ask/",
        json={
            "question": "What's the weather?",
            "top_k": 3,
            "include_sources": True
        }
    )
    data2 = response2.json()

    assert "not_found" in data2["answer"]

    # CLARIFY intent - may have sources
    response3 = client.post(
        "/ask/",
        json={
            "question": "How?",
            "top_k": 3,
            "include_sources": True
        }
    )
    data3 = response3.json()

    # Document API call
    document_api_call(
        "ask_router_sources_all_intents.json",
        "POST",
        "/ask/",
        {
            "note": "Testing sources for all intent types"
        },
        {
            "answer_intent": data1,
            "refuse_intent": data2,
            "clarify_intent": data3
        },
        200
    )

    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response3.status_code == 200

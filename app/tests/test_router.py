"""Tests for query router"""
import pytest
from app.graph.router import QueryRouter, QueryIntent, get_query_router


def test_router_high_confidence_answer():
    """Test router returns ANSWER intent for high confidence"""
    router = QueryRouter(
        high_confidence_threshold=0.5,
        low_confidence_threshold=0.3
    )

    chunks = [
        {"chunk_id": 1, "similarity_score": 0.85, "text": "vacation policy info"},
        {"chunk_id": 2, "similarity_score": 0.72, "text": "more vacation info"}
    ]

    result = router.route(
        question="What is the vacation policy?",
        chunks=chunks
    )

    assert result["intent"] == QueryIntent.ANSWER
    assert result["confidence"] == 0.85
    assert "high confidence" in result["reason"].lower()


def test_router_medium_confidence_answer():
    """Test router returns ANSWER for medium confidence"""
    router = QueryRouter(
        high_confidence_threshold=0.5,
        low_confidence_threshold=0.3
    )

    chunks = [
        {"chunk_id": 1, "similarity_score": 0.45, "text": "some info"}
    ]

    result = router.route(
        question="What are the work hours?",
        chunks=chunks
    )

    assert result["intent"] == QueryIntent.ANSWER
    assert result["confidence"] == 0.45
    assert "medium confidence" in result["reason"].lower()


def test_router_low_confidence_refuse():
    """Test router returns REFUSE for low confidence"""
    router = QueryRouter(
        high_confidence_threshold=0.5,
        low_confidence_threshold=0.3
    )

    chunks = [
        {"chunk_id": 1, "similarity_score": 0.15, "text": "unrelated text"}
    ]

    result = router.route(
        question="What is the meaning of life?",
        chunks=chunks
    )

    assert result["intent"] == QueryIntent.REFUSE
    assert result["confidence"] == 0.15
    assert "confidence too low" in result["reason"].lower()


def test_router_no_chunks_refuse():
    """Test router returns REFUSE when no chunks found"""
    router = QueryRouter()

    result = router.route(
        question="What is the policy?",
        chunks=[]
    )

    assert result["intent"] == QueryIntent.REFUSE
    assert result["confidence"] == 0.0
    assert "no relevant documents" in result["reason"].lower()


def test_router_off_topic_question():
    """Test router detects off-topic questions"""
    router = QueryRouter()

    chunks = [
        {"chunk_id": 1, "similarity_score": 0.6, "text": "company policy"}
    ]

    # Test weather question
    result = router.route(
        question="What's the weather today?",
        chunks=chunks
    )

    assert result["intent"] == QueryIntent.REFUSE
    assert "not related" in result["reason"].lower()


def test_router_ambiguous_question_clarify():
    """Test router returns CLARIFY for ambiguous questions"""
    router = QueryRouter(
        high_confidence_threshold=0.5,
        low_confidence_threshold=0.3
    )

    chunks = [
        {"chunk_id": 1, "similarity_score": 0.4, "text": "policy info"}
    ]

    # Test ambiguous question
    result = router.route(
        question="Tell me about it",
        chunks=chunks
    )

    assert result["intent"] == QueryIntent.CLARIFY
    assert "ambiguous" in result["reason"].lower()


def test_router_short_question_clarify():
    """Test router treats very short questions as ambiguous"""
    router = QueryRouter(
        high_confidence_threshold=0.5,
        low_confidence_threshold=0.3
    )

    chunks = [
        {"chunk_id": 1, "similarity_score": 0.4, "text": "some text"}
    ]

    result = router.route(
        question="How?",
        chunks=chunks
    )

    assert result["intent"] == QueryIntent.CLARIFY
    assert "ambiguous" in result["reason"].lower()


def test_router_is_off_topic():
    """Test off-topic detection method"""
    router = QueryRouter()

    # Test various off-topic patterns
    assert router._is_off_topic("What's the weather like?") is True
    assert router._is_off_topic("Tell me a joke") is True
    assert router._is_off_topic("Who won the game?") is True
    assert router._is_off_topic("What's on the news?") is True

    # Test on-topic questions
    assert router._is_off_topic("What is the vacation policy?") is False
    assert router._is_off_topic("How do I submit expenses?") is False


def test_router_is_ambiguous():
    """Test ambiguous question detection"""
    router = QueryRouter()

    # Test ambiguous patterns
    assert router._is_ambiguous("Tell me about it") is True
    assert router._is_ambiguous("What about that?") is True
    assert router._is_ambiguous("How?") is True
    assert router._is_ambiguous("Why?") is True

    # Test clear questions
    assert router._is_ambiguous("What is the vacation policy?") is False
    assert router._is_ambiguous("How many sick days do I get?") is False


def test_router_singleton():
    """Test get_query_router returns singleton"""
    router1 = get_query_router()
    router2 = get_query_router()

    assert router1 is router2


def test_router_format_response_answer():
    """Test formatting response for ANSWER intent"""
    router = QueryRouter()

    response = router.format_response(
        intent=QueryIntent.ANSWER,
        confidence=0.85,
        reason="High confidence",
        answer="The answer is 42"
    )

    assert response["intent"] == QueryIntent.ANSWER
    assert response["confidence"] == 0.85
    assert response["reason"] == "High confidence"
    assert response["answer"] == "The answer is 42"


def test_router_format_response_clarify():
    """Test formatting response for CLARIFY intent"""
    router = QueryRouter()

    response = router.format_response(
        intent=QueryIntent.CLARIFY,
        confidence=0.4,
        reason="Ambiguous",
        clarification_prompt="Please be more specific"
    )

    assert response["intent"] == QueryIntent.CLARIFY
    assert response["confidence"] == 0.4
    assert response["reason"] == "Ambiguous"
    assert "clarification_needed" in response
    assert response["clarification_needed"] == "Please be more specific"


def test_router_format_response_refuse():
    """Test formatting response for REFUSE intent"""
    router = QueryRouter()

    response = router.format_response(
        intent=QueryIntent.REFUSE,
        confidence=0.1,
        reason="Low confidence"
    )

    assert response["intent"] == QueryIntent.REFUSE
    assert response["confidence"] == 0.1
    assert response["reason"] == "Low confidence"
    assert "message" in response
    assert "not_found" in response["message"]


def test_router_multiple_off_topic_keywords():
    """Test off-topic detection with multiple keywords"""
    router = QueryRouter()

    # Test multiple off-topic patterns
    off_topic_questions = [
        "What's the weather forecast?",
        "Can you tell me a funny joke?",
        "What movie should I watch?",
        "Give me a recipe for cookies",
        "What's the current news?",
        "What time is it now?"
    ]

    for question in off_topic_questions:
        assert router._is_off_topic(question) is True


def test_router_edge_case_empty_question():
    """Test router with empty or whitespace question"""
    router = QueryRouter()

    chunks = [{"chunk_id": 1, "similarity_score": 0.5, "text": "text"}]

    # Empty question should be treated as ambiguous
    result = router.route(question="", chunks=chunks)
    assert result["intent"] == QueryIntent.CLARIFY

    # Whitespace only
    result = router.route(question="   ", chunks=chunks)
    assert result["intent"] == QueryIntent.CLARIFY


def test_router_confidence_boundaries():
    """Test router behavior at threshold boundaries"""
    router = QueryRouter(
        high_confidence_threshold=0.5,
        low_confidence_threshold=0.3
    )

    chunks = [{"chunk_id": 1, "similarity_score": 0.5, "text": "text"}]

    # Exactly at high threshold
    result = router.route(
        question="What is the policy?",
        chunks=chunks
    )
    assert result["intent"] == QueryIntent.ANSWER
    assert result["confidence"] == 0.5

    # Exactly at low threshold
    chunks[0]["similarity_score"] = 0.3
    result = router.route(
        question="What is the policy?",
        chunks=chunks
    )
    assert result["intent"] == QueryIntent.ANSWER
    assert result["confidence"] == 0.3

    # Just below low threshold
    chunks[0]["similarity_score"] = 0.29
    result = router.route(
        question="What is the policy?",
        chunks=chunks
    )
    assert result["intent"] == QueryIntent.REFUSE
    assert result["confidence"] == 0.29

"""
Tests for LangGraph Query Routing

Tests cover all three routing paths:
1. ANSWER: Clear, high-confidence queries
2. CLARIFY: Ambiguous or vague queries
3. REFUSE: Off-topic or low-confidence queries
"""

import pytest
from app.graph.query_routing_graph import (
    classify_query_threshold,
    classify_query_llm,
    route_query,
    QueryRoutingState
)
from app.llm.mock_provider import MockLLMProvider


# ============================================================================
# Test Helpers
# ============================================================================

def create_chunks_with_score(score: float, count: int = 3):
    """Create mock chunks with given similarity score"""
    return [
        {
            "chunk_id": i,
            "text": f"Sample text chunk {i}",
            "filename": "test.pdf",
            "page_number": i,
            "similarity_score": score
        }
        for i in range(count)
    ]


# ============================================================================
# Threshold-based Classification Tests
# ============================================================================

def test_threshold_routing_high_confidence_answer():
    """Test: High confidence score (0.8) → ANSWER intent"""
    state: QueryRoutingState = {
        "question": "What is the vacation policy?",
        "chunks": create_chunks_with_score(0.8),
        "intent": "",
        "confidence": 0.0,
        "reason": "",
        "classification_method": "",
        "llm_reasoning": ""
    }

    result = classify_query_threshold(state)

    assert result["intent"] == "answer"
    assert result["confidence"] == 0.8
    assert "high confidence" in result["reason"].lower()
    assert result["classification_method"] == "threshold"


def test_threshold_routing_medium_confidence_answer():
    """Test: Medium confidence (0.4) with clear question → ANSWER intent"""
    state: QueryRoutingState = {
        "question": "How many sick days do employees get per year?",
        "chunks": create_chunks_with_score(0.4),
        "intent": "",
        "confidence": 0.0,
        "reason": "",
        "classification_method": "",
        "llm_reasoning": ""
    }

    result = classify_query_threshold(state)

    assert result["intent"] == "answer"
    assert result["confidence"] == 0.4
    assert result["classification_method"] == "threshold"


def test_threshold_routing_medium_confidence_ambiguous_clarify():
    """Test: Medium confidence (0.4) with ambiguous question → CLARIFY intent"""
    state: QueryRoutingState = {
        "question": "What about that?",
        "chunks": create_chunks_with_score(0.4),
        "intent": "",
        "confidence": 0.0,
        "reason": "",
        "classification_method": "",
        "llm_reasoning": ""
    }

    result = classify_query_threshold(state)

    assert result["intent"] == "clarify"
    assert result["confidence"] == 0.4
    assert "ambiguous" in result["reason"].lower()
    assert result["classification_method"] == "threshold"


def test_threshold_routing_low_confidence_refuse():
    """Test: Low confidence (0.1) → REFUSE intent"""
    state: QueryRoutingState = {
        "question": "What is the refund policy?",
        "chunks": create_chunks_with_score(0.1),
        "intent": "",
        "confidence": 0.0,
        "reason": "",
        "classification_method": "",
        "llm_reasoning": ""
    }

    result = classify_query_threshold(state)

    assert result["intent"] == "refuse"
    assert result["confidence"] == 0.1
    assert "too low" in result["reason"].lower()
    assert result["classification_method"] == "threshold"


def test_threshold_routing_no_chunks_refuse():
    """Test: No chunks retrieved → REFUSE intent"""
    state: QueryRoutingState = {
        "question": "What's the weather today?",
        "chunks": [],
        "intent": "",
        "confidence": 0.0,
        "reason": "",
        "classification_method": "",
        "llm_reasoning": ""
    }

    result = classify_query_threshold(state)

    assert result["intent"] == "refuse"
    assert result["confidence"] == 0.0
    assert "no relevant documents" in result["reason"].lower()


def test_threshold_routing_empty_question_clarify():
    """Test: Empty question → CLARIFY intent"""
    state: QueryRoutingState = {
        "question": "",
        "chunks": create_chunks_with_score(0.5),
        "intent": "",
        "confidence": 0.0,
        "reason": "",
        "classification_method": "",
        "llm_reasoning": ""
    }

    result = classify_query_threshold(state)

    assert result["intent"] == "clarify"
    assert "empty" in result["reason"].lower()


def test_threshold_routing_short_vague_question_clarify():
    """Test: Single word question (too short) → CLARIFY intent"""
    state: QueryRoutingState = {
        "question": "Policy",
        "chunks": create_chunks_with_score(0.4),
        "intent": "",
        "confidence": 0.0,
        "reason": "",
        "classification_method": "",
        "llm_reasoning": ""
    }

    result = classify_query_threshold(state)

    assert result["intent"] == "clarify"
    assert "ambiguous" in result["reason"].lower()


def test_threshold_routing_pronoun_question_clarify():
    """Test: Question with vague pronouns → CLARIFY intent"""
    for question in ["Tell me about it", "What is it", "How does it work"]:
        state: QueryRoutingState = {
            "question": question,
            "chunks": create_chunks_with_score(0.4),
            "intent": "",
            "confidence": 0.0,
            "reason": "",
            "classification_method": "",
            "llm_reasoning": ""
        }

        result = classify_query_threshold(state)

        assert result["intent"] == "clarify"
        assert "ambiguous" in result["reason"].lower()


# ============================================================================
# LLM-based Classification Tests
# ============================================================================

def test_llm_routing_answerable_question():
    """Test: LLM classifies clear question as answerable → ANSWER intent"""
    mock_llm = MockLLMProvider()
    # Mock LLM response
    mock_llm.set_next_response('{"classification": "answerable", "reasoning": "Clear policy question"}')

    state: QueryRoutingState = {
        "question": "What is the vacation policy?",
        "chunks": create_chunks_with_score(0.7),
        "intent": "",
        "confidence": 0.0,
        "reason": "",
        "classification_method": "",
        "llm_reasoning": ""
    }

    result = classify_query_llm(state, mock_llm)

    assert result["intent"] == "answer"
    assert result["classification_method"] == "llm"
    assert "answerable" in result["reason"].lower()


def test_llm_routing_ambiguous_question():
    """Test: LLM classifies vague question as ambiguous → CLARIFY intent"""
    mock_llm = MockLLMProvider()
    mock_llm.set_next_response('{"classification": "ambiguous", "reasoning": "Uses pronouns without context"}')

    state: QueryRoutingState = {
        "question": "What about that?",
        "chunks": create_chunks_with_score(0.5),
        "intent": "",
        "confidence": 0.0,
        "reason": "",
        "classification_method": "",
        "llm_reasoning": ""
    }

    result = classify_query_llm(state, mock_llm)

    assert result["intent"] == "clarify"
    assert result["classification_method"] == "llm"
    assert "ambiguous" in result["reason"].lower()


def test_llm_routing_off_topic_question():
    """Test: LLM classifies off-topic question → REFUSE intent"""
    mock_llm = MockLLMProvider()
    mock_llm.set_next_response('{"classification": "off_topic", "reasoning": "Not related to documents"}')

    state: QueryRoutingState = {
        "question": "What's the weather today?",
        "chunks": create_chunks_with_score(0.2),
        "intent": "",
        "confidence": 0.0,
        "reason": "",
        "classification_method": "",
        "llm_reasoning": ""
    }

    result = classify_query_llm(state, mock_llm)

    assert result["intent"] == "refuse"
    assert result["classification_method"] == "llm"
    assert "off-topic" in result["reason"].lower() or "off_topic" in result["reason"].lower()


def test_llm_routing_answerable_but_low_confidence_refuse():
    """Test: LLM says answerable but retrieval confidence too low → REFUSE intent"""
    mock_llm = MockLLMProvider()
    mock_llm.set_next_response('{"classification": "answerable", "reasoning": "Clear question"}')

    state: QueryRoutingState = {
        "question": "What is the refund policy?",
        "chunks": create_chunks_with_score(0.1),  # Very low confidence
        "intent": "",
        "confidence": 0.0,
        "reason": "",
        "classification_method": "",
        "llm_reasoning": ""
    }

    result = classify_query_llm(state, mock_llm)

    # Even though LLM says answerable, low retrieval confidence → refuse
    assert result["intent"] == "refuse"
    assert "confidence too low" in result["reason"].lower()


def test_llm_routing_fallback_on_error():
    """Test: LLM classification error → fallback to threshold-based"""
    mock_llm = MockLLMProvider()
    # Mock an invalid response that will cause JSON parsing error
    mock_llm.set_next_response("Invalid JSON response")

    state: QueryRoutingState = {
        "question": "What is the vacation policy?",
        "chunks": create_chunks_with_score(0.7),
        "intent": "",
        "confidence": 0.0,
        "reason": "",
        "classification_method": "",
        "llm_reasoning": ""
    }

    result = classify_query_llm(state, mock_llm)

    # Should fall back to threshold-based routing
    assert result["classification_method"] == "threshold"
    assert result["intent"] in ["answer", "clarify", "refuse"]


# ============================================================================
# Full Graph Tests (Integration)
# ============================================================================

@pytest.mark.asyncio
async def test_route_query_with_llm():
    """Test: Full routing flow with LLM classification"""
    mock_llm = MockLLMProvider()
    mock_llm.set_next_response('{"classification": "answerable", "reasoning": "Policy question"}')

    result = await route_query(
        question="What is the vacation policy?",
        chunks=create_chunks_with_score(0.7),
        llm_provider=mock_llm,
        use_llm_classification=True
    )

    assert result["intent"] == "answer"
    assert result["confidence"] == 0.7
    assert result["classification_method"] == "llm"
    assert "reasoning" in result.get("llm_reasoning", "").lower() or result.get("llm_reasoning") != ""


@pytest.mark.asyncio
async def test_route_query_threshold_only():
    """Test: Full routing flow with threshold-based classification only"""
    result = await route_query(
        question="What is the vacation policy?",
        chunks=create_chunks_with_score(0.7),
        llm_provider=None,
        use_llm_classification=False
    )

    assert result["intent"] == "answer"
    assert result["confidence"] == 0.7
    assert result["classification_method"] == "threshold"


# ============================================================================
# Edge Cases
# ============================================================================

def test_reranking_score_priority():
    """Test: Reranking score takes priority over similarity score"""
    chunks = [
        {
            "chunk_id": 1,
            "text": "Sample text",
            "filename": "test.pdf",
            "page_number": 1,
            "similarity_score": 0.3,  # Low similarity
            "reranking_score": 0.9  # High reranking score
        }
    ]

    state: QueryRoutingState = {
        "question": "What is the policy?",
        "chunks": chunks,
        "intent": "",
        "confidence": 0.0,
        "reason": "",
        "classification_method": "",
        "llm_reasoning": ""
    }

    result = classify_query_threshold(state)

    # Should use reranking_score (0.9) not similarity_score (0.3)
    assert result["intent"] == "answer"
    assert result["confidence"] == 0.9


def test_whitespace_only_question():
    """Test: Question with only whitespace → CLARIFY intent"""
    state: QueryRoutingState = {
        "question": "   \t\n   ",
        "chunks": create_chunks_with_score(0.5),
        "intent": "",
        "confidence": 0.0,
        "reason": "",
        "classification_method": "",
        "llm_reasoning": ""
    }

    result = classify_query_threshold(state)

    assert result["intent"] == "clarify"
    assert "empty" in result["reason"].lower() or "whitespace" in result["reason"].lower()


def test_exactly_at_threshold_boundary():
    """Test: Score exactly at threshold boundary"""
    # Test at HIGH_THRESHOLD (0.5)
    state: QueryRoutingState = {
        "question": "What is the policy?",
        "chunks": create_chunks_with_score(0.5),
        "intent": "",
        "confidence": 0.0,
        "reason": "",
        "classification_method": "",
        "llm_reasoning": ""
    }

    result = classify_query_threshold(state)
    assert result["intent"] == "answer"  # >= 0.5 should answer

    # Test at LOW_THRESHOLD (0.3)
    state["chunks"] = create_chunks_with_score(0.3)
    result = classify_query_threshold(state)
    # At 0.3 with clear question should answer (>= LOW_THRESHOLD, not ambiguous)
    assert result["intent"] == "answer"

    # Test just below LOW_THRESHOLD
    state["chunks"] = create_chunks_with_score(0.29)
    result = classify_query_threshold(state)
    assert result["intent"] == "refuse"  # < 0.3 should refuse

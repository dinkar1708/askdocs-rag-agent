"""Test mock LLM provider"""

import pytest

from app.llm.mock_provider import MockLLMProvider


def test_mock_provider_initialization():
    """Test mock provider initializes correctly"""
    llm = MockLLMProvider()
    assert llm.call_count == 0
    assert len(llm.sample_responses) > 0


def test_mock_generate(mock_llm):
    """Test simple text generation"""
    response = mock_llm.generate("What is the capital of France?")
    assert isinstance(response, str)
    assert "Mock LLM response" in response
    assert mock_llm.call_count == 1


def test_mock_generate_with_context_vacation(mock_llm):
    """Test vacation question"""
    result = mock_llm.generate_with_context(
        question="How many vacation days do I get?",
        context="Employee handbook section 5..."
    )

    assert result["answer"] is not None
    assert "15 days" in result["answer"]
    assert result["confidence"] > 0.9
    assert len(result["sources"]) > 0
    assert result["provider"] == "mock"
    assert mock_llm.call_count == 1


def test_mock_generate_with_context_benefits(mock_llm):
    """Test benefits question"""
    result = mock_llm.generate_with_context(
        question="What health insurance do we have?",
        context="Benefits guide..."
    )

    assert "insurance" in result["answer"].lower() or "benefits" in result["answer"].lower()
    assert result["confidence"] > 0
    assert result["provider"] == "mock"


def test_mock_generate_not_found(mock_llm):
    """Test NOT_FOUND response when no context"""
    result = mock_llm.generate_with_context(
        question="What is the weather today?",
        context=""
    )

    assert result["answer"] == "NOT_FOUND"
    assert result["confidence"] == 0.0
    assert len(result["sources"]) == 0


def test_mock_call_counter(mock_llm):
    """Test call counter increments"""
    assert mock_llm.call_count == 0

    mock_llm.generate("test 1")
    assert mock_llm.call_count == 1

    mock_llm.generate_with_context("test 2", "context")
    assert mock_llm.call_count == 2

    mock_llm.reset_call_count()
    assert mock_llm.call_count == 0


def test_mock_sources_structure(mock_llm):
    """Test sources have correct structure"""
    result = mock_llm.generate_with_context(
        question="Vacation policy?",
        context="Some context"
    )

    if len(result["sources"]) > 0:
        source = result["sources"][0]
        assert "document" in source
        assert "page" in source
        assert "chunk_id" in source


def test_mock_deterministic_responses(mock_llm):
    """Test same question gives same response"""
    result1 = mock_llm.generate_with_context(
        question="How many vacation days?",
        context="context"
    )

    mock_llm.reset_call_count()

    result2 = mock_llm.generate_with_context(
        question="How many vacation days?",
        context="context"
    )

    assert result1["answer"] == result2["answer"]
    assert result1["confidence"] == result2["confidence"]

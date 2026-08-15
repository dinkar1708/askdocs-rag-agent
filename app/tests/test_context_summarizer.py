"""Tests for Context Summarization"""

import pytest
from app.services.context_summarizer import ContextSummarizer, AdaptiveSummarizer
from app.llm.mock_provider import MockLLMProvider


@pytest.fixture
def mock_llm():
    """Create mock LLM provider for testing"""
    return MockLLMProvider()


@pytest.fixture
def simple_summarizer(mock_llm):
    """Create simple context summarizer"""
    return ContextSummarizer(mock_llm, max_history_turns=3)


@pytest.fixture
def adaptive_summarizer(mock_llm):
    """Create adaptive context summarizer"""
    return AdaptiveSummarizer(mock_llm, max_history_turns=3, importance_threshold=0.7)


def test_no_summarization_needed(simple_summarizer):
    """Test that short history is not summarized"""
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"}
    ]

    result = simple_summarizer.summarize_history(messages)

    assert len(result) == 2
    assert result == messages  # No change


def test_basic_summarization(simple_summarizer):
    """Test basic summarization of long history"""
    messages = [
        {"role": "user", "content": "Question 1"},
        {"role": "assistant", "content": "Answer 1"},
        {"role": "user", "content": "Question 2"},
        {"role": "assistant", "content": "Answer 2"},
        {"role": "user", "content": "Question 3"},
        {"role": "assistant", "content": "Answer 3"},
        {"role": "user", "content": "Question 4"},  # Recent (kept)
        {"role": "assistant", "content": "Answer 4"},  # Recent (kept)
        {"role": "user", "content": "Question 5"},  # Recent (kept)
    ]

    result = simple_summarizer.summarize_history(messages)

    # Should have: 1 summary + 3 recent messages = 4 total
    assert len(result) < len(messages)
    assert result[0]["role"] == "system"  # Summary
    assert "[Previous conversation summary:" in result[0]["content"]
    assert result[-1]["content"] == "Question 5"  # Most recent kept


def test_should_summarize(simple_summarizer):
    """Test should_summarize decision"""
    short_history = [
        {"role": "user", "content": "Q1"},
        {"role": "assistant", "content": "A1"}
    ]

    long_history = [
        {"role": "user", "content": f"Q{i}"}
        for i in range(10)
    ]

    assert simple_summarizer.should_summarize(short_history) is False
    assert simple_summarizer.should_summarize(long_history) is True


def test_adaptive_importance_scoring(adaptive_summarizer):
    """Test that adaptive summarizer scores message importance"""
    messages = [
        {"role": "user", "content": "What is the vacation policy?"},  # Question: high
        {"role": "assistant", "content": "15 days. [source: handbook.pdf]"},  # Citation: high
        {"role": "user", "content": "ok"},  # Short: low
        {"role": "assistant", "content": "Let me know if you need more info."},  # Generic: low
    ]

    scored = adaptive_summarizer._score_importance(messages)

    # Questions and cited answers should score higher
    assert scored[0][1] > 0.7  # User question with ?
    assert scored[1][1] > 0.6  # Answer with citation
    assert scored[2][1] < 0.5  # Short acknowledgment
    assert scored[3][1] < 0.6  # Generic response


def test_adaptive_preserves_important_messages(adaptive_summarizer):
    """Test that important messages are preserved even if old"""
    messages = [
        {"role": "user", "content": "What is the refund policy?"},  # Important: question
        {"role": "assistant", "content": "Refunds processed in 7 days. [source: terms.pdf, page 5]"},  # Important: citation
        {"role": "user", "content": "ok"},  # Not important
        {"role": "assistant", "content": "Anything else?"},  # Not important
        {"role": "user", "content": "thanks"},  # Not important
        {"role": "assistant", "content": "You're welcome!"},  # Not important
        {"role": "user", "content": "What about returns?"},  # Recent + important
    ]

    result = adaptive_summarizer.summarize_history(messages)

    # Should preserve important messages (questions with citations) even if old
    preserved_contents = [msg["content"] for msg in result if msg["role"] != "system"]

    # Check that important question is preserved
    assert any("refund policy" in content for content in preserved_contents)
    # Check that recent question is preserved
    assert any("returns" in content for content in preserved_contents)


def test_deduplication(adaptive_summarizer):
    """Test that duplicate messages are removed"""
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi"},
        {"role": "user", "content": "Hello"},  # Duplicate
        {"role": "assistant", "content": "Hi"},  # Duplicate
    ]

    deduplicated = adaptive_summarizer._deduplicate(messages)

    assert len(deduplicated) == 2
    assert deduplicated[0]["content"] == "Hello"
    assert deduplicated[1]["content"] == "Hi"


def test_summarizer_factory():
    """Test summarizer factory function"""
    from app.services.context_summarizer import create_summarizer

    mock_llm = MockLLMProvider()

    simple = create_summarizer(mock_llm, strategy="simple")
    assert isinstance(simple, ContextSummarizer)
    assert not isinstance(simple, AdaptiveSummarizer)

    adaptive = create_summarizer(mock_llm, strategy="adaptive")
    assert isinstance(adaptive, AdaptiveSummarizer)


def test_summarization_with_empty_history(simple_summarizer):
    """Test summarization handles empty history"""
    messages = []

    result = simple_summarizer.summarize_history(messages)

    assert result == []


def test_preserves_message_order(simple_summarizer):
    """Test that message order is preserved after summarization"""
    messages = [
        {"role": "user", "content": f"Question {i}"}
        for i in range(10)
    ]

    result = simple_summarizer.summarize_history(messages)

    # Recent messages should be in order
    recent_messages = [msg for msg in result if msg["role"] != "system"]

    for i in range(len(recent_messages) - 1):
        # Extract question numbers
        num1 = int(recent_messages[i]["content"].split()[-1])
        num2 = int(recent_messages[i + 1]["content"].split()[-1])
        assert num2 > num1  # Should be in ascending order

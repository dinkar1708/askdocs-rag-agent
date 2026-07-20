"""Test LLM factory"""

import pytest
import os

from app.llm.factory import get_llm_provider
from app.llm.mock_provider import MockLLMProvider
from app.llm.gemini_provider import GeminiProvider


def test_get_mock_provider():
    """Test getting mock provider"""
    provider = get_llm_provider("mock")
    assert isinstance(provider, MockLLMProvider)


def test_get_provider_case_insensitive():
    """Test provider name is case insensitive"""
    provider1 = get_llm_provider("MOCK")
    provider2 = get_llm_provider("Mock")
    provider3 = get_llm_provider("mock")

    assert isinstance(provider1, MockLLMProvider)
    assert isinstance(provider2, MockLLMProvider)
    assert isinstance(provider3, MockLLMProvider)


def test_unsupported_provider():
    """Test error for unsupported provider"""
    with pytest.raises(ValueError) as exc_info:
        get_llm_provider("unsupported_provider")

    assert "Unsupported LLM provider" in str(exc_info.value)


def test_provider_from_env(monkeypatch):
    """Test getting provider from environment variable"""
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    provider = get_llm_provider()
    assert isinstance(provider, MockLLMProvider)

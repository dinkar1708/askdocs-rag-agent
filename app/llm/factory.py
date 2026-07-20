"""LLM provider factory"""

from app.llm.base import BaseLLMProvider
from app.llm.mock_provider import MockLLMProvider
from app.llm.gemini_provider import GeminiProvider
from app.core.config import settings


# Singleton instance (lazy-loaded)
_llm_provider_instance = None


def get_llm_provider(provider_name: str = None) -> BaseLLMProvider:
    """Get LLM provider instance (singleton pattern)

    Args:
        provider_name: Provider name (mock, gemini, etc.)
                      Uses settings.LLM_PROVIDER if not specified

    Returns:
        LLM provider instance

    Raises:
        ValueError: If provider not supported
    """
    global _llm_provider_instance

    # Return existing instance if available
    if _llm_provider_instance is not None:
        return _llm_provider_instance

    provider_name = (provider_name or settings.LLM_PROVIDER).lower()

    if provider_name == "mock":
        _llm_provider_instance = MockLLMProvider()
    elif provider_name == "gemini":
        _llm_provider_instance = GeminiProvider()
    else:
        raise ValueError(
            f"Unsupported LLM provider: {provider_name}. "
            f"Supported: mock, gemini"
        )

    return _llm_provider_instance

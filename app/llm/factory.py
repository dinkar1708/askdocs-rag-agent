"""LLM provider factory"""

from app.llm.base import BaseLLMProvider
from app.llm.mock_provider import MockLLMProvider
from app.llm.gemini_provider import GeminiProvider
from app.core.config import settings


def get_llm_provider(provider_name: str = None) -> BaseLLMProvider:
    """Get LLM provider instance

    Args:
        provider_name: Provider name (mock, gemini, etc.)
                      Uses settings.LLM_PROVIDER if not specified

    Returns:
        LLM provider instance

    Raises:
        ValueError: If provider not supported
    """
    provider_name = (provider_name or settings.LLM_PROVIDER).lower()

    if provider_name == "mock":
        return MockLLMProvider()
    elif provider_name == "gemini":
        return GeminiProvider()
    else:
        raise ValueError(
            f"Unsupported LLM provider: {provider_name}. "
            f"Supported: mock, gemini"
        )


# Singleton instance
llm_provider = get_llm_provider()

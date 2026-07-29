"""LLM provider factory"""

from app.llm.base import BaseLLMProvider
from app.llm.mock_provider import MockLLMProvider
from app.llm.gemini_provider import GeminiProvider
from app.llm.ollama_provider import OllamaProvider
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

    # Get the requested provider name
    requested_provider = (provider_name or settings.LLM_PROVIDER).lower()

    # Validate provider name first
    if requested_provider not in ["mock", "gemini", "ollama"]:
        raise ValueError(
            f"Unsupported LLM provider: {requested_provider}. "
            f"Supported: mock, gemini, ollama"
        )

    # Return existing instance if available and matches requested provider
    if _llm_provider_instance is not None:
        return _llm_provider_instance

    # Create new instance based on provider
    if requested_provider == "mock":
        _llm_provider_instance = MockLLMProvider()
    elif requested_provider == "gemini":
        _llm_provider_instance = GeminiProvider()
    elif requested_provider == "ollama":
        _llm_provider_instance = OllamaProvider()

    return _llm_provider_instance

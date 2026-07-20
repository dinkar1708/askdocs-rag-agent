"""Base LLM provider interface"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers"""

    @abstractmethod
    async def generate(self, system_prompt: str = "", user_prompt: str = "", **kwargs) -> str:
        """Generate text completion from prompt

        Args:
            system_prompt: System instructions
            user_prompt: User's input prompt
            **kwargs: Provider-specific parameters

        Returns:
            Generated text response
        """
        pass

    @abstractmethod
    def generate_with_context(
        self,
        question: str,
        context: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate answer with retrieved context

        Args:
            question: User's question
            context: Retrieved document chunks
            **kwargs: Provider-specific parameters

        Returns:
            Dict with answer, confidence, reasoning
        """
        pass

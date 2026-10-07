"""Base LLM provider interface"""

from abc import ABC, abstractmethod
from typing import Dict, Any, AsyncGenerator


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

    async def generate_stream(
        self,
        system_prompt: str = "",
        user_prompt: str = "",
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate streaming token completion from prompt

        Args:
            system_prompt: System instructions
            user_prompt: User's input prompt
            **kwargs: Provider-specific parameters

        Yields:
            Token or text segments as they arrive
        """
        full_text = await self.generate(system_prompt=system_prompt, user_prompt=user_prompt, **kwargs)
        # Default fallback: stream text token by token / word by word
        words = full_text.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")

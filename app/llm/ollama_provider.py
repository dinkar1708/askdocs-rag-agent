"""Ollama LLM provider for local inference"""

import json
from typing import Dict, Any
import httpx
from app.llm.base import BaseLLMProvider
from app.core.config import settings


class OllamaProvider(BaseLLMProvider):
    """Ollama provider for 100% offline local LLM inference

    Requires:
    - Ollama installed and running (brew install ollama)
    - Model pulled (ollama pull llama3.2)

    Features:
    - Zero cost (no API fees)
    - 100% offline capability
    - Full data privacy
    - Decent quality with llama3.2
    """

    def __init__(self):
        """Initialize Ollama provider"""
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.timeout = 60.0  # Longer timeout for local inference

    async def generate(self, system_prompt: str = "", user_prompt: str = "", **kwargs) -> str:
        """Generate completion using Ollama

        Args:
            system_prompt: System instructions
            user_prompt: User's input prompt
            **kwargs: Additional parameters

        Returns:
            Generated text response
        """
        prompt = f"{system_prompt}\n\n{user_prompt}" if system_prompt else user_prompt

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": kwargs.get("temperature", 0.7),
                        "top_p": kwargs.get("top_p", 0.9),
                    }
                }
            )
            response.raise_for_status()
            result = response.json()
            return result.get("response", "").strip()

    def generate_with_context(
        self,
        question: str,
        context: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate grounded answer with Ollama

        Args:
            question: User's question
            context: Retrieved document chunks
            **kwargs: Additional parameters

        Returns:
            Dict with answer, confidence, reasoning
        """
        # Build RAG prompt
        system_prompt = """You are a precise document Q&A assistant.

CRITICAL RULES:
1. Answer ONLY from the provided context
2. If information is not in context, respond with "NOT_FOUND"
3. Include specific page references in your answer
4. Do not make assumptions or add external knowledge
5. Be concise and direct"""

        user_prompt = f"""Context from documents:
{context}

Question: {question}

Instructions:
- Answer based ONLY on the context above
- Cite page numbers in format [document_name, page X]
- If not found in context, respond with "NOT_FOUND"

Answer:"""

        # Call Ollama synchronously (wrapping async call)
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        answer = loop.run_until_complete(
            self.generate(system_prompt=system_prompt, user_prompt=user_prompt, **kwargs)
        )

        # Parse response
        if "NOT_FOUND" in answer.upper() or len(answer.strip()) < 10:
            return {
                "answer": "NOT_FOUND",
                "confidence": 0.0,
                "reasoning": "Information not found in provided documents",
                "model": f"ollama:{self.model}"
            }

        return {
            "answer": answer,
            "confidence": 0.85,  # Ollama doesn't provide confidence scores
            "reasoning": "Answer generated from document context",
            "model": f"ollama:{self.model}"
        }

"""Google Gemini LLM provider"""

from typing import Dict, Any
import google.generativeai as genai

from app.llm.base import BaseLLMProvider
from app.core.config import settings


class GeminiProvider(BaseLLMProvider):
    """Google Gemini API provider"""

    def __init__(self, api_key: str = None):
        """Initialize Gemini provider

        Args:
            api_key: Gemini API key (uses settings if not provided)
        """
        self.api_key = api_key or settings.GEMINI_API_KEY
        if not self.api_key or self.api_key == "dummy-key-for-testing":
            raise ValueError("Valid GEMINI_API_KEY required")

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text completion

        Args:
            prompt: Input prompt
            **kwargs: Gemini-specific parameters

        Returns:
            Generated text
        """
        response = self.model.generate_content(prompt, **kwargs)
        return response.text

    def generate_with_context(
        self,
        question: str,
        context: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate answer with document context

        Args:
            question: User's question
            context: Retrieved document chunks
            **kwargs: Gemini parameters

        Returns:
            Dict with answer, confidence, reasoning
        """
        # Construct prompt with context
        prompt = f"""You are a helpful assistant that answers questions based on provided documents.

IMPORTANT RULES:
1. Only answer based on the context provided below
2. If the answer is not in the context, respond with exactly "NOT_FOUND"
3. Always cite the source (document and page) for your answer
4. Be concise and direct

CONTEXT:
{context}

QUESTION:
{question}

Provide your answer in the following format:
ANSWER: [your answer]
CONFIDENCE: [0.0 to 1.0]
REASONING: [brief explanation]
"""

        response_text = self.generate(prompt, **kwargs)

        # Parse response
        lines = response_text.strip().split('\n')
        answer = ""
        confidence = 0.5
        reasoning = ""

        for line in lines:
            if line.startswith("ANSWER:"):
                answer = line.replace("ANSWER:", "").strip()
            elif line.startswith("CONFIDENCE:"):
                try:
                    confidence = float(line.replace("CONFIDENCE:", "").strip())
                except:
                    confidence = 0.5
            elif line.startswith("REASONING:"):
                reasoning = line.replace("REASONING:", "").strip()

        return {
            "question": question,
            "answer": answer or response_text,
            "confidence": confidence,
            "reasoning": reasoning,
            "provider": "gemini",
            "raw_response": response_text
        }

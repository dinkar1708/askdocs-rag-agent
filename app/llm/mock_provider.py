"""Mock LLM provider for testing and demos"""

from typing import Dict, Any
from app.llm.base import BaseLLMProvider


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM that returns predefined responses

    Use for:
    - Testing without API calls
    - Demos without API keys
    - Development without internet
    - CI/CD pipelines
    """

    def __init__(self):
        """Initialize mock provider with sample responses"""
        self.call_count = 0

        # Sample responses for different question types
        self.sample_responses = {
            "vacation": {
                "answer": "According to the employee handbook, full-time employees receive 15 days of paid vacation per year. Part-time employees receive prorated vacation based on hours worked.",
                "confidence": 0.95,
                "reasoning": "Found explicit vacation policy in employee handbook",
                "sources": [
                    {"document": "employee_handbook.pdf", "page": 12, "chunk_id": 1},
                    {"document": "employee_handbook.pdf", "page": 13, "chunk_id": 2}
                ]
            },
            "benefits": {
                "answer": "The company offers comprehensive benefits including health insurance, dental coverage, 401k with 4% match, and flexible spending accounts.",
                "confidence": 0.92,
                "reasoning": "Found benefits information in policy documents",
                "sources": [
                    {"document": "benefits_guide.pdf", "page": 3, "chunk_id": 5}
                ]
            },
            "default": {
                "answer": "Based on the provided documents, I found relevant information about your question. The policy states that employees should follow standard procedures.",
                "confidence": 0.75,
                "reasoning": "General information found in documents",
                "sources": [
                    {"document": "sample.pdf", "page": 1, "chunk_id": 1}
                ]
            },
            "not_found": {
                "answer": "NOT_FOUND",
                "confidence": 0.0,
                "reasoning": "No relevant information found in the provided context",
                "sources": []
            }
        }

    async def generate(self, system_prompt: str = "", user_prompt: str = "", **kwargs) -> str:
        """Generate simple text completion

        Args:
            system_prompt: System instructions
            user_prompt: User's input prompt
            **kwargs: Ignored for mock provider

        Returns:
            Mock generated text based on prompt content
        """
        self.call_count += 1

        # Combine prompts for pattern matching
        combined = f"{system_prompt} {user_prompt}".lower()

        if "vacation" in combined or "time off" in combined:
            return "According to the employee handbook [company_policy.pdf - Page 1], full-time employees accrue 15 days of paid vacation per year, starting from their first day of employment."
        elif "benefit" in combined or "insurance" in combined:
            return "The company offers comprehensive benefits [company_policy.pdf - Page 3], including health insurance (80% premium covered), dental, vision, and 401k with 50% match up to 6% of salary."
        elif "work" in combined and ("remote" in combined or "schedule" in combined):
            return "According to the work policy [company_policy.pdf - Page 2], employees may work remotely up to 2 days per week with manager approval. Standard hours are Monday-Friday, 9 AM to 5 PM."
        elif "sick" in combined:
            return "Per company policy [company_policy.pdf - Page 1], employees receive 10 days of sick leave annually. Sick leave does not roll over to the next year."
        else:
            return "Based on the provided context, I can help answer questions about company policies. Please refer to the relevant sections in the documents provided."

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
            **kwargs: Ignored for mock provider

        Returns:
            Dict with answer, confidence, sources
        """
        self.call_count += 1

        # Match question to sample responses
        question_lower = question.lower()

        if "vacation" in question_lower or "time off" in question_lower:
            response_type = "vacation"
        elif "benefit" in question_lower or "insurance" in question_lower:
            response_type = "benefits"
        elif not context or len(context.strip()) < 10:
            response_type = "not_found"
        else:
            response_type = "default"

        response = self.sample_responses[response_type].copy()
        response["question"] = question
        response["provider"] = "mock"
        response["call_count"] = self.call_count

        return response

    def reset_call_count(self):
        """Reset call counter for testing"""
        self.call_count = 0


# Singleton instance for easy testing
mock_llm = MockLLMProvider()

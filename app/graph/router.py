"""
LangGraph Query Router

Routes queries to: answer / clarify / refuse based on:
- Relevance to documents
- Ambiguity detection
- Confidence thresholds
"""

from typing import Dict, List, Literal
from enum import Enum


class QueryIntent(str, Enum):
    """Query classification types"""
    ANSWER = "answer"        # High confidence, relevant to documents
    CLARIFY = "clarify"      # Ambiguous, needs more context
    REFUSE = "refuse"        # Off-topic or low confidence


class QueryRouter:
    """Routes queries based on confidence and relevance"""

    def __init__(
        self,
        high_confidence_threshold: float = 0.5,
        low_confidence_threshold: float = 0.3
    ):
        """
        Initialize router with confidence thresholds

        Args:
            high_confidence_threshold: Minimum score for 'answer' intent
            low_confidence_threshold: Below this triggers 'refuse'
        """
        self.high_threshold = high_confidence_threshold
        self.low_threshold = low_confidence_threshold

    def route(
        self,
        question: str,
        chunks: List[Dict],
        similarity_threshold: float = 0.3
    ) -> Dict:
        """
        Route query to appropriate intent

        Args:
            question: User's question
            chunks: Retrieved document chunks with similarity scores
            similarity_threshold: Minimum similarity for relevance

        Returns:
            Dict with 'intent' and 'reason' keys
        """
        # Check if we have any chunks
        if not chunks:
            return {
                "intent": QueryIntent.REFUSE,
                "reason": "No relevant documents found",
                "confidence": 0.0
            }

        # Get best similarity score
        best_score = max(chunk.get("similarity_score", 0.0) for chunk in chunks)

        # Check for off-topic questions (obvious non-document queries)
        if self._is_off_topic(question):
            return {
                "intent": QueryIntent.REFUSE,
                "reason": "Question is not related to uploaded documents",
                "confidence": best_score
            }

        # High confidence: answer directly
        if best_score >= self.high_threshold:
            return {
                "intent": QueryIntent.ANSWER,
                "reason": "High confidence match found",
                "confidence": best_score
            }

        # Medium confidence: ask for clarification
        elif best_score >= self.low_threshold:
            # Check if question is ambiguous
            if self._is_ambiguous(question):
                return {
                    "intent": QueryIntent.CLARIFY,
                    "reason": "Question is ambiguous, needs clarification",
                    "confidence": best_score
                }
            else:
                return {
                    "intent": QueryIntent.ANSWER,
                    "reason": "Medium confidence match, proceeding with answer",
                    "confidence": best_score
                }

        # Low confidence: refuse to answer
        else:
            return {
                "intent": QueryIntent.REFUSE,
                "reason": "Confidence too low, no good match found",
                "confidence": best_score
            }

    def _is_off_topic(self, question: str) -> bool:
        """
        Detect obviously off-topic questions

        Examples:
        - "What's the weather?"
        - "Tell me a joke"
        - "Who won the game?"
        """
        question_lower = question.lower()

        # Common off-topic patterns
        off_topic_keywords = [
            "weather", "joke", "game", "score", "news",
            "movie", "recipe", "song", "video", "meme",
            "current events", "today's date", "time now"
        ]

        return any(keyword in question_lower for keyword in off_topic_keywords)

    def _is_ambiguous(self, question: str) -> bool:
        """
        Detect ambiguous questions that need clarification

        Examples:
        - "Tell me about it" (no context)
        - "What about the thing?" (vague reference)
        - "How?" (too short)
        """
        question_lower = question.lower().strip()

        # Too short (likely missing context)
        if len(question_lower.split()) <= 2:
            return True

        # Vague pronouns without context
        vague_patterns = [
            "tell me about it",
            "what about that",
            "what about the thing",
            "how does it work",
            "what is it",
            "where is it"
        ]

        return any(pattern in question_lower for pattern in vague_patterns)

    def format_response(
        self,
        intent: str,
        confidence: float,
        reason: str,
        answer: str = None,
        clarification_prompt: str = None
    ) -> Dict:
        """
        Format router output for API response

        Args:
            intent: answer/clarify/refuse
            confidence: Similarity score
            reason: Why this intent was chosen
            answer: Generated answer (for 'answer' intent)
            clarification_prompt: Question for user (for 'clarify' intent)

        Returns:
            Formatted response dict
        """
        response = {
            "intent": intent,
            "confidence": round(confidence, 3),
            "reason": reason
        }

        if intent == QueryIntent.ANSWER and answer:
            response["answer"] = answer
        elif intent == QueryIntent.CLARIFY:
            response["clarification_needed"] = clarification_prompt or \
                "Could you please provide more context or be more specific?"
        elif intent == QueryIntent.REFUSE:
            response["message"] = "not_found - This question cannot be answered from the uploaded documents."

        return response


# Singleton instance
_router_instance = None


def get_query_router() -> QueryRouter:
    """Get singleton router instance"""
    global _router_instance
    if _router_instance is None:
        _router_instance = QueryRouter(
            high_confidence_threshold=0.5,
            low_confidence_threshold=0.3
        )
    return _router_instance

"""Context Summarization for Multi-turn Chat

This module compresses conversation history to fit within LLM context windows
while preserving important information for context resolution.

Instead of dropping old messages, we summarize them to maintain continuity.
"""

from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ContextSummarizer:
    """
    Summarize conversation history to reduce token count while preserving context
    """

    def __init__(self, llm_provider, max_history_turns: int = 10):
        """
        Initialize context summarizer

        Args:
            llm_provider: LLM provider for generating summaries
            max_history_turns: Maximum number of recent turns to keep unsummarized
        """
        self.llm_provider = llm_provider
        self.max_history_turns = max_history_turns

    def summarize_history(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Summarize old conversation history

        Strategy:
        - Keep last N turns unchanged (most relevant context)
        - Summarize older turns into a condensed format
        - Preserve key entities, topics, and decisions

        Args:
            messages: List of message dicts with 'role' and 'content'

        Returns:
            Compressed message history
        """
        if len(messages) <= self.max_history_turns:
            # No summarization needed
            return messages

        # Split into old (to summarize) and recent (keep as-is)
        old_messages = messages[:-self.max_history_turns]
        recent_messages = messages[-self.max_history_turns:]

        # Summarize old messages
        summary = self._create_summary(old_messages)

        # Build compressed history
        compressed_history = [
            {
                "role": "system",
                "content": f"[Previous conversation summary: {summary}]"
            }
        ] + recent_messages

        logger.info(f"Compressed {len(messages)} messages to {len(compressed_history)} (saved ~{len(old_messages)} messages)")

        return compressed_history

    def _create_summary(self, messages: List[Dict[str, str]]) -> str:
        """
        Create a summary of message history using LLM

        Args:
            messages: Messages to summarize

        Returns:
            Concise summary text
        """
        if not messages:
            return ""

        # Format messages for summary
        conversation_text = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in messages
        ])

        # Build summary prompt
        prompt = f"""
Summarize the following conversation history. Focus on:
1. Key topics discussed
2. Important facts or decisions mentioned
3. User's main questions and concerns

Be concise (max 3-4 sentences).

CONVERSATION:
{conversation_text}

SUMMARY:
"""

        try:
            summary = self.llm_provider.complete(prompt).strip()
            return summary
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            # Fallback: Create simple summary
            return f"Previous conversation covered {len(messages)} exchanges about various topics."

    def should_summarize(self, messages: List[Dict[str, str]]) -> bool:
        """
        Determine if history should be summarized

        Args:
            messages: Current message history

        Returns:
            True if summarization would be beneficial
        """
        return len(messages) > self.max_history_turns


class AdaptiveSummarizer(ContextSummarizer):
    """
    Advanced summarizer that adapts based on message importance

    Instead of simple recency-based summarization, this:
    - Identifies important messages (questions, key facts)
    - Preserves important messages even if old
    - Summarizes only less important exchanges
    """

    def __init__(self, llm_provider, max_history_turns: int = 10, importance_threshold: float = 0.7):
        super().__init__(llm_provider, max_history_turns)
        self.importance_threshold = importance_threshold

    def summarize_history(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Adaptive summarization based on message importance

        Args:
            messages: Message history

        Returns:
            Compressed history with important messages preserved
        """
        if len(messages) <= self.max_history_turns:
            return messages

        # Score message importance
        scored_messages = self._score_importance(messages)

        # Keep important messages + recent messages
        important_messages = [
            msg for msg, score in scored_messages
            if score >= self.importance_threshold
        ]

        recent_messages = messages[-self.max_history_turns:]

        # Combine and deduplicate
        preserved_messages = self._deduplicate(important_messages + recent_messages)

        # Summarize the rest
        summarized_messages = [
            msg for msg in messages
            if msg not in preserved_messages
        ]

        if summarized_messages:
            summary = self._create_summary(summarized_messages)
            compressed_history = [
                {
                    "role": "system",
                    "content": f"[Earlier in conversation: {summary}]"
                }
            ] + preserved_messages
        else:
            compressed_history = preserved_messages

        logger.info(f"Adaptive summarization: kept {len(preserved_messages)} important/recent messages, summarized {len(summarized_messages)}")

        return compressed_history

    def _score_importance(self, messages: List[Dict[str, str]]) -> List[tuple]:
        """
        Score each message by importance

        Heuristics:
        - User questions: High importance
        - Messages with citations/sources: High importance
        - Longer messages: Moderate importance
        - Short acknowledgments: Low importance

        Args:
            messages: Messages to score

        Returns:
            List of (message, importance_score) tuples
        """
        scored = []

        for msg in messages:
            score = 0.5  # Base score

            # User questions are important
            if msg["role"] == "user" and "?" in msg["content"]:
                score += 0.3

            # Messages with citations are important
            if msg["role"] == "assistant" and ("sources" in msg or "[" in msg.get("content", "")):
                score += 0.2

            # Longer messages likely contain more info
            word_count = len(msg["content"].split())
            if word_count > 50:
                score += 0.1
            elif word_count < 10:
                score -= 0.2

            # Cap score at 1.0
            score = min(1.0, max(0.0, score))

            scored.append((msg, score))

        return scored

    def _deduplicate(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Remove duplicate messages while preserving order

        Args:
            messages: Messages to deduplicate

        Returns:
            Deduplicated message list
        """
        seen = set()
        deduplicated = []

        for msg in messages:
            # Create a hash of message content for deduplication
            msg_hash = f"{msg['role']}:{msg['content']}"

            if msg_hash not in seen:
                seen.add(msg_hash)
                deduplicated.append(msg)

        return deduplicated


def create_summarizer(llm_provider, strategy: str = "simple", **kwargs) -> ContextSummarizer:
    """
    Factory function to create a context summarizer

    Args:
        llm_provider: LLM provider instance
        strategy: Summarization strategy ("simple" or "adaptive")
        **kwargs: Additional arguments for summarizer

    Returns:
        ContextSummarizer instance
    """
    if strategy == "adaptive":
        return AdaptiveSummarizer(llm_provider, **kwargs)
    else:
        return ContextSummarizer(llm_provider, **kwargs)

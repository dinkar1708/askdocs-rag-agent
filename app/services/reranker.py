"""Reranking service for two-stage retrieval using cross-encoder models"""
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class Reranker:
    """Two-stage retrieval with cross-encoder reranking for better relevance scoring"""

    def __init__(self, model_name: str = 'BAAI/bge-reranker-v2-m3'):
        """
        Initialize the reranker with a cross-encoder model

        Args:
            model_name: HuggingFace model name for the cross-encoder
                       Default: BAAI/bge-reranker-v2-m3 (recommended)
        """
        self.model_name = model_name
        self._model = None  # Lazy loading

    @property
    def model(self):
        """Lazy load the cross-encoder model on first use"""
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder
                logger.info(f"Loading reranker model: {self.model_name}")
                self._model = CrossEncoder(self.model_name)
                logger.info("Reranker model loaded successfully")
            except ImportError as e:
                logger.error("sentence-transformers not installed. Install with: pip install sentence-transformers")
                raise ImportError(
                    "sentence-transformers is required for reranking. "
                    "Install it with: pip install sentence-transformers"
                ) from e
            except Exception as e:
                logger.error(f"Failed to load reranker model: {e}")
                raise RuntimeError(f"Failed to load reranker model {self.model_name}: {e}") from e
        return self._model

    def rerank(
        self,
        query: str,
        chunks: List[Dict],
        top_k: int = 5
    ) -> List[Dict]:
        """
        Rerank chunks by relevance to query using cross-encoder

        Args:
            query: User's question
            chunks: List of candidate chunks from vector search
                   Each chunk should have at least a 'text' field
            top_k: Number of top chunks to return after reranking

        Returns:
            List of top-k chunks sorted by reranking score (descending)
            Each chunk will have additional fields:
            - reranking_score: Cross-encoder relevance score
            - original_similarity: Original vector similarity score (preserved)

        Raises:
            ValueError: If chunks is empty or query is empty
            RuntimeError: If model fails to load or predict
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        if not chunks:
            logger.warning("No chunks provided for reranking")
            return []

        try:
            # Create query-chunk pairs for the cross-encoder
            pairs = [(query, chunk['text']) for chunk in chunks]

            # Score all pairs using the cross-encoder
            logger.debug(f"Reranking {len(pairs)} chunks for query: {query[:50]}...")
            scores = self.model.predict(pairs)

            # Add scores to chunks and preserve original similarity
            for chunk, score in zip(chunks, scores):
                chunk['reranking_score'] = float(score)
                # Preserve original vector similarity score if it exists
                if 'similarity_score' in chunk and 'original_similarity' not in chunk:
                    chunk['original_similarity'] = chunk['similarity_score']

            # Sort by reranking score (descending - higher is better)
            ranked = sorted(chunks, key=lambda x: x['reranking_score'], reverse=True)

            logger.info(f"Reranked {len(chunks)} chunks, returning top {top_k}")

            return ranked[:top_k]

        except Exception as e:
            logger.error(f"Error during reranking: {e}")
            # Fallback: return original chunks if reranking fails
            logger.warning("Falling back to original ranking due to reranking error")
            return chunks[:top_k]


def create_reranker(model_name: Optional[str] = None) -> Reranker:
    """
    Factory function to create a Reranker instance

    Args:
        model_name: Optional model name override

    Returns:
        Reranker instance
    """
    from app.core.config import settings

    model = model_name or getattr(settings, 'RERANKING_MODEL', 'BAAI/bge-reranker-v2-m3')
    return Reranker(model_name=model)

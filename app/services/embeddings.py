"""Embedding generation service"""

from typing import List, Dict
from sentence_transformers import SentenceTransformer

# Load embedding model (384 dimensions)
# This will be cached after first load
_embedding_model = None


def get_embedding_model():
    """Get or load embedding model (singleton pattern)"""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedding_model


def generate_embedding(text: str) -> List[float]:
    """Generate embedding vector for text

    Args:
        text: Input text

    Returns:
        384-dimensional embedding vector
    """
    model = get_embedding_model()
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding.tolist()


def chunk_text(
    text: str,
    page_number: int,
    chunk_size: int = 500,
    overlap: int = 50
) -> List[Dict]:
    """Split text into overlapping chunks

    Args:
        text: Text to chunk
        page_number: Page number this text came from
        chunk_size: Target chunk size in characters
        overlap: Overlap between chunks

    Returns:
        List of chunks with text and page_number
    """
    chunks = []

    # Simple chunking by character count with overlap
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk_text_content = text[start:end]

        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence end
            last_period = chunk_text_content.rfind('.')
            last_newline = chunk_text_content.rfind('\n')
            break_point = max(last_period, last_newline)

            if break_point > chunk_size * 0.5:  # At least 50% through
                end = start + break_point + 1
                chunk_text_content = text[start:end]

        if chunk_text_content.strip():
            chunks.append({
                "text": chunk_text_content.strip(),
                "page_number": page_number
            })

        # Move start position with overlap
        start = end - overlap
        if start >= len(text):
            break

    return chunks

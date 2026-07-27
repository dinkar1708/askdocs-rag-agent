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
    """Split text into overlapping chunks (character-based)

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


def semantic_chunk_text(
    text: str,
    page_number: int,
    use_semantic: bool = True,
    similarity_threshold: float = 0.5,
    min_chunk_size: int = 200,
    max_chunk_size: int = 1000
) -> List[Dict]:
    """
    Chunk text semantically or fall back to character-based.

    If use_semantic=True:
        - Use SemanticChunker to split at topic boundaries
    Else:
        - Use existing character-based chunking

    Args:
        text: Text to chunk
        page_number: Page number this text came from
        use_semantic: Whether to use semantic chunking
        similarity_threshold: Threshold for semantic similarity (0-1)
        min_chunk_size: Minimum chunk size in characters
        max_chunk_size: Maximum chunk size in characters

    Returns:
        List of chunks with text and page_number
    """
    if not use_semantic:
        # Fall back to character-based chunking
        return chunk_text(text, page_number)

    # Import here to avoid circular dependency
    from app.services.semantic_chunker import get_semantic_chunker

    # Get semantic chunker instance
    chunker = get_semantic_chunker(similarity_threshold=similarity_threshold)

    # Perform semantic chunking
    chunk_texts = chunker.chunk_by_similarity(
        text,
        min_chunk_size=min_chunk_size,
        max_chunk_size=max_chunk_size
    )

    # Format chunks with metadata
    chunks = []
    for chunk_text_content in chunk_texts:
        if chunk_text_content.strip():
            chunks.append({
                "text": chunk_text_content.strip(),
                "page_number": page_number
            })

    return chunks

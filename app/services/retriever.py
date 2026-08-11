"""RAG retrieval service for semantic search using pgvector"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
import re
from app.db.models import Chunk, Document
from app.services.embeddings import generate_embedding

logger = logging.getLogger(__name__)

# Regex pattern for validating metadata keys to prevent SQL injection
SAFE_METADATA_KEY_PATTERN = re.compile(r'^[a-zA-Z0-9_]+$')


def retrieve_relevant_chunks(
    query: str,
    db: Session,
    top_k: int = 5,
    similarity_threshold: float = 0.3,
    metadata_filters: Optional[Dict] = None
) -> List[Dict]:
    """
    Retrieve most relevant document chunks for a query using vector similarity

    Args:
        query: User's question
        db: Database session
        top_k: Number of chunks to retrieve (default 5)
        similarity_threshold: Minimum cosine similarity score (0-1, default 0.3)
        metadata_filters: Optional dict to filter documents by metadata (e.g., {'department': 'HR'})

    Returns:
        List of dicts with keys: chunk_id, text, score, document_id, filename, page_number
    """
    # Generate embedding for the query
    query_embedding = generate_embedding(query)

    # Convert embedding to pgvector format
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

    # Build metadata filter conditions
    metadata_conditions = []
    params = {
        "threshold": similarity_threshold,
        "limit": top_k
    }

    if metadata_filters:
        for key, value in metadata_filters.items():
            # SECURITY: Validate metadata key to prevent SQL injection
            # Only allow alphanumeric and underscore characters
            if not SAFE_METADATA_KEY_PATTERN.match(key):
                logger.warning(f"Invalid metadata key rejected: {key}")
                raise ValueError(
                    f"Invalid metadata key '{key}'. Only alphanumeric characters and underscores allowed."
                )

            # Use JSON operator to check if metadata contains the key-value pair
            if isinstance(value, list):
                # For array values, check if any element matches
                metadata_conditions.append(f"d.doc_metadata->>'{key}' = ANY(:filter_{key})")
                params[f"filter_{key}"] = value
            else:
                # For scalar values, do equality check
                metadata_conditions.append(f"d.doc_metadata->>'{key}' = :filter_{key}")
                params[f"filter_{key}"] = str(value)

    # Combine all WHERE conditions
    where_clause = f"WHERE 1 - (c.embedding <=> '{embedding_str}'::vector) >= :threshold"
    if metadata_conditions:
        where_clause += " AND " + " AND ".join(metadata_conditions)

    # Cosine similarity search using pgvector
    # Note: pgvector uses <=> for cosine distance, so we convert to similarity (1 - distance)
    # We use string formatting for the vector since SQLAlchemy parameter binding doesn't work well with custom types
    sql_query = f"""
        SELECT
            c.id as chunk_id,
            c.text,
            c.page_number,
            c.document_id,
            d.filename,
            1 - (c.embedding <=> '{embedding_str}'::vector) as similarity_score
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        {where_clause}
        ORDER BY c.embedding <=> '{embedding_str}'::vector
        LIMIT :limit
    """

    result = db.execute(text(sql_query), params)

    chunks = []
    for row in result:
        chunks.append({
            "chunk_id": row.chunk_id,
            "text": row.text,
            "page_number": row.page_number,
            "document_id": row.document_id,
            "filename": row.filename,
            "similarity_score": float(row.similarity_score)
        })

    return chunks


def format_context_for_llm(chunks: List[Dict]) -> str:
    """
    Format retrieved chunks into context string for LLM

    Args:
        chunks: List of retrieved chunk dicts

    Returns:
        Formatted context string with citations
    """
    if not chunks:
        return "No relevant information found in the documents."

    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        citation = f"[{chunk['filename']} - Page {chunk['page_number']}]"
        context_parts.append(f"{citation}\n{chunk['text']}")

    return "\n\n".join(context_parts)


# Singleton pattern for reranker model loading
_reranker = None


def get_reranker():
    """
    Get or create reranker instance (lazy loading singleton)

    Returns:
        Reranker instance
    """
    global _reranker
    if _reranker is None:
        from app.services.reranker import create_reranker
        _reranker = create_reranker()
    return _reranker


def retrieve_with_reranking(
    query: str,
    db: Session,
    initial_k: int = 30,
    final_k: int = 5,
    similarity_threshold: float = 0.2,
    metadata_filters: Optional[Dict] = None
) -> List[Dict]:
    """
    Two-stage retrieval with reranking for better relevance

    Process:
    1. Stage 1 (Fast): Vector search retrieves initial_k candidate chunks
    2. Stage 2 (Precise): Cross-encoder reranks candidates by relevance
    3. Return top final_k chunks after reranking

    Args:
        query: User's question
        db: Database session
        initial_k: Number of candidates to retrieve in stage 1 (default 30)
        final_k: Number of final results after reranking (default 5)
        similarity_threshold: Minimum cosine similarity for stage 1 (default 0.2)
        metadata_filters: Optional dict to filter documents by metadata

    Returns:
        Top-k reranked chunks with reranking_score and original_similarity fields
    """
    # Stage 1: Fast vector search for candidates
    logger.info(f"Stage 1: Retrieving {initial_k} candidates via vector search")
    candidates = retrieve_relevant_chunks(
        query=query,
        db=db,
        top_k=initial_k,
        similarity_threshold=similarity_threshold,
        metadata_filters=metadata_filters
    )

    if not candidates:
        logger.warning("No candidates found in vector search")
        return []

    logger.info(f"Found {len(candidates)} candidates")

    # Stage 2: Rerank with cross-encoder
    try:
        logger.info(f"Stage 2: Reranking with cross-encoder")
        reranker = get_reranker()
        final_chunks = reranker.rerank(query, candidates, top_k=final_k)
        logger.info(f"Reranking complete, returning {len(final_chunks)} chunks")
        return final_chunks
    except Exception as e:
        # Fallback to original retrieval if reranking fails
        logger.error(f"Reranking failed: {e}, falling back to original retrieval")
        return candidates[:final_k]

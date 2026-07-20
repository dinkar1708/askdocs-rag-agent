"""RAG retrieval service for semantic search using pgvector"""
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.models import Chunk, Document
from app.services.embeddings import generate_embedding


def retrieve_relevant_chunks(
    query: str,
    db: Session,
    top_k: int = 5,
    similarity_threshold: float = 0.3
) -> List[Dict]:
    """
    Retrieve most relevant document chunks for a query using vector similarity

    Args:
        query: User's question
        db: Database session
        top_k: Number of chunks to retrieve (default 5)
        similarity_threshold: Minimum cosine similarity score (0-1, default 0.3)

    Returns:
        List of dicts with keys: chunk_id, text, score, document_id, filename, page_number
    """
    # Generate embedding for the query
    query_embedding = generate_embedding(query)

    # Convert embedding to pgvector format
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

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
        WHERE 1 - (c.embedding <=> '{embedding_str}'::vector) >= :threshold
        ORDER BY c.embedding <=> '{embedding_str}'::vector
        LIMIT :limit
    """

    result = db.execute(
        text(sql_query),
        {
            "threshold": similarity_threshold,
            "limit": top_k
        }
    )

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

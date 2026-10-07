"""Hypothetical Document Embeddings (HyDE) Service

HyDE (Gao et al., 2022) generates a hypothetical answer passage using an LLM
prior to embedding, capturing the document-style vocabulary and latent semantics
to significantly boost zero-shot vector recall on complex questions.
"""

import logging
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
import re

from app.services.embeddings import generate_embedding
from app.llm.factory import get_llm_provider
from app.llm.base import BaseLLMProvider
from app.services.retriever import SAFE_METADATA_KEY_PATTERN

logger = logging.getLogger(__name__)

HYDE_SYSTEM_PROMPT = """You are an expert technical and informational writer.
Given a user question, write a single concise hypothetical passage that directly and authoritatively answers the question as if extracted from an official manual, policy, or textbook.
Do not include conversational greetings, warnings, or meta-commentary. Output strictly the informative passage."""


async def generate_hypothetical_passage(
    query: str,
    llm_provider: Optional[BaseLLMProvider] = None
) -> str:
    """
    Generate a hypothetical answer passage for the user's question using the LLM.
    """
    provider = llm_provider or get_llm_provider()
    user_prompt = f"Question: {query}\n\nHypothetical Authoritative Passage:"

    try:
        passage = await provider.generate(
            system_prompt=HYDE_SYSTEM_PROMPT,
            user_prompt=user_prompt
        )
        if passage and len(passage.strip()) > 10:
            return passage.strip()
    except Exception as e:
        logger.warning(f"Failed to generate HyDE hypothetical passage: {e}")

    # Fall back to original query if LLM generation fails or returns empty
    return query


async def retrieve_with_hyde(
    query: str,
    db: Session,
    top_k: int = 5,
    similarity_threshold: float = 0.25,
    metadata_filters: Optional[Dict] = None,
    llm_provider: Optional[BaseLLMProvider] = None
) -> List[Dict]:
    """
    Retrieve document chunks using Hypothetical Document Embeddings (HyDE).

    Steps:
    1. Generate a hypothetical answer passage using the LLM.
    2. Embed the hypothetical passage into the vector space.
    3. Perform vector search in pgvector using the hypothetical embedding.
    4. Return relevant chunks annotated with hyde metadata.
    """
    hypothetical_passage = await generate_hypothetical_passage(query, llm_provider=llm_provider)
    logger.info(f"HyDE generated hypothetical passage ({len(hypothetical_passage)} chars)")

    # Generate embedding from the hypothetical passage
    hypothetical_embedding = generate_embedding(hypothetical_passage)
    embedding_str = "[" + ",".join(str(x) for x in hypothetical_embedding) + "]"

    # Query vector database
    metadata_conditions = []
    params = {
        "threshold": similarity_threshold,
        "limit": top_k
    }

    if metadata_filters:
        for key, value in metadata_filters.items():
            if not SAFE_METADATA_KEY_PATTERN.match(key):
                raise ValueError(f"Invalid metadata key: {key}")

            if isinstance(value, list):
                placeholders = [f":meta_{key}_{i}" for i in range(len(value))]
                for i, v in enumerate(value):
                    params[f"meta_{key}_{i}"] = str(v)
                metadata_conditions.append(f"d.doc_metadata->>'{key}' IN ({','.join(placeholders)})")
            else:
                params[f"meta_{key}"] = str(value)
                metadata_conditions.append(f"d.doc_metadata->>'{key}' = :meta_{key}")

    where_clause = "WHERE 1 - (c.embedding <=> :embedding) >= :threshold"
    if metadata_conditions:
        where_clause += " AND " + " AND ".join(metadata_conditions)

    query_sql = f"""
        SELECT
            c.id as chunk_id,
            c.text,
            1 - (c.embedding <=> :embedding) as similarity_score,
            c.document_id,
            d.filename,
            c.page_number,
            c.chunk_index
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        {where_clause}
        ORDER BY similarity_score DESC
        LIMIT :limit
    """

    result = db.execute(
        text(query_sql),
        {**params, "embedding": embedding_str}
    )

    chunks = []
    for row in result:
        chunks.append({
            "chunk_id": row.chunk_id,
            "text": row.text,
            "similarity_score": float(row.similarity_score),
            "document_id": row.document_id,
            "filename": row.filename,
            "page_number": row.page_number,
            "chunk_index": getattr(row, "chunk_index", 0),
            "hyde_passage": hypothetical_passage[:200]
        })

    return chunks

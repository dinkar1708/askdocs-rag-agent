"""Hybrid search combining vector similarity and BM25 full-text search

This module implements hybrid retrieval using:
1. Vector similarity search (semantic understanding)
2. BM25 full-text search (exact keyword matching)
3. Reciprocal Rank Fusion (RRF) to merge results

Hybrid search significantly improves retrieval quality for:
- Exact matches: error codes, SKUs, version numbers, proper nouns
- Semantic matches: conceptually similar content
- Combined queries: "Python 3.11 compatibility issues" (version + concept)
"""

from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text, func
import logging

from app.db.models import Chunk, Document
from app.services.embeddings import generate_embedding

logger = logging.getLogger(__name__)


def reciprocal_rank_fusion(
    results_list: List[List[Dict]],
    k: int = 60
) -> List[Dict]:
    """
    Merge multiple ranked lists using Reciprocal Rank Fusion (RRF)

    RRF formula: score = Σ 1/(k + rank) for each result across all lists

    Args:
        results_list: List of ranked result lists (e.g., [vector_results, bm25_results])
        k: RRF constant (default 60, standard in literature)

    Returns:
        Merged and re-ranked results sorted by RRF score
    """
    # Track RRF scores and result data
    rrf_scores: Dict[int, float] = {}  # chunk_id -> score
    chunk_data: Dict[int, Dict] = {}   # chunk_id -> chunk info

    for results in results_list:
        for rank, result in enumerate(results, start=1):
            chunk_id = result["chunk_id"]

            # RRF score contribution from this ranking
            score_contribution = 1.0 / (k + rank)

            # Accumulate scores
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + score_contribution

            # Store chunk data (first occurrence)
            if chunk_id not in chunk_data:
                chunk_data[chunk_id] = result

    # Sort by RRF score (highest first)
    ranked_chunks = sorted(
        rrf_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    # Build final result list with RRF scores
    merged_results = []
    for chunk_id, rrf_score in ranked_chunks:
        result = chunk_data[chunk_id].copy()
        result["rrf_score"] = rrf_score
        merged_results.append(result)

    return merged_results


def bm25_search(
    query: str,
    db: Session,
    top_k: int = 30,
    metadata_filters: Optional[Dict] = None
) -> List[Dict]:
    """
    Full-text search using PostgreSQL's BM25-like ranking (ts_rank)

    Args:
        query: User's search query
        db: Database session
        top_k: Number of results to return
        metadata_filters: Optional dict to filter documents by metadata

    Returns:
        List of chunks ranked by text relevance
    """
    # Build metadata filter conditions (same as vector search)
    metadata_conditions = []
    params = {"limit": top_k}

    if metadata_filters:
        from app.services.retriever import SAFE_METADATA_KEY_PATTERN

        for key, value in metadata_filters.items():
            # Validate key to prevent SQL injection
            if not SAFE_METADATA_KEY_PATTERN.match(key):
                logger.warning(f"Invalid metadata key rejected: {key}")
                raise ValueError(
                    f"Invalid metadata key '{key}'. Only alphanumeric characters and underscores allowed."
                )

            if isinstance(value, list):
                metadata_conditions.append(f"d.doc_metadata->>'{key}' = ANY(:filter_{key})")
                params[f"filter_{key}"] = value
            else:
                metadata_conditions.append(f"d.doc_metadata->>'{key}' = :filter_{key}")
                params[f"filter_{key}"] = str(value)

    # Build WHERE clause
    where_clause = "WHERE c.text_search @@ to_tsquery('english', :query)"
    if metadata_conditions:
        where_clause += " AND " + " AND ".join(metadata_conditions)

    # Prepare query for tsquery (replace spaces with &)
    tsquery = query.replace(" ", " & ")
    params["query"] = tsquery

    # Full-text search with ts_rank
    sql_query = f"""
        SELECT
            c.id as chunk_id,
            c.text,
            c.page_number,
            c.document_id,
            d.filename,
            ts_rank(c.text_search, to_tsquery('english', :query)) as bm25_score
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        {where_clause}
        ORDER BY bm25_score DESC
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
            "bm25_score": float(row.bm25_score)
        })

    logger.info(f"BM25 search found {len(chunks)} results")
    return chunks


def hybrid_search(
    query: str,
    db: Session,
    top_k: int = 5,
    initial_k: int = 30,
    metadata_filters: Optional[Dict] = None
) -> List[Dict]:
    """
    Hybrid search combining vector similarity and BM25 full-text search

    Process:
    1. Retrieve initial_k candidates from vector search
    2. Retrieve initial_k candidates from BM25 search
    3. Merge using Reciprocal Rank Fusion (RRF)
    4. Return top_k final results

    Args:
        query: User's search query
        db: Database session
        top_k: Number of final results to return
        initial_k: Number of candidates to retrieve from each method
        metadata_filters: Optional dict to filter documents by metadata

    Returns:
        Top-k chunks ranked by hybrid RRF score
    """
    logger.info(f"Hybrid search: query='{query}', top_k={top_k}, initial_k={initial_k}")

    # Import here to avoid circular dependency
    from app.services.retriever import retrieve_relevant_chunks

    # 1. Vector similarity search
    logger.info(f"Stage 1: Vector search for {initial_k} candidates")
    vector_results = retrieve_relevant_chunks(
        query=query,
        db=db,
        top_k=initial_k,
        similarity_threshold=0.0,  # No threshold filtering, we want all initial_k
        metadata_filters=metadata_filters
    )

    # 2. BM25 full-text search
    logger.info(f"Stage 2: BM25 search for {initial_k} candidates")
    bm25_results = bm25_search(
        query=query,
        db=db,
        top_k=initial_k,
        metadata_filters=metadata_filters
    )

    # 3. Reciprocal Rank Fusion
    logger.info("Stage 3: Merging with RRF")
    merged_results = reciprocal_rank_fusion([vector_results, bm25_results])

    # 4. Return top-k
    final_results = merged_results[:top_k]
    logger.info(f"Hybrid search complete, returning {len(final_results)} results")

    return final_results


def hybrid_search_with_reranking(
    query: str,
    db: Session,
    top_k: int = 5,
    initial_k: int = 30,
    metadata_filters: Optional[Dict] = None
) -> List[Dict]:
    """
    Three-stage retrieval: Hybrid search + Cross-encoder reranking

    Process:
    1. Hybrid search (vector + BM25 + RRF) for initial_k candidates
    2. Cross-encoder reranking for final top_k results

    Args:
        query: User's search query
        db: Database session
        top_k: Number of final results after reranking
        initial_k: Number of candidates for hybrid search
        metadata_filters: Optional dict to filter documents by metadata

    Returns:
        Top-k reranked chunks
    """
    logger.info(f"Hybrid search with reranking: initial_k={initial_k}, final_k={top_k}")

    # Stage 1 & 2 & 3: Hybrid search (vector + BM25 + RRF)
    candidates = hybrid_search(
        query=query,
        db=db,
        top_k=initial_k,
        initial_k=initial_k,
        metadata_filters=metadata_filters
    )

    if not candidates:
        logger.warning("No candidates found in hybrid search")
        return []

    # Stage 4: Rerank with cross-encoder
    try:
        logger.info(f"Stage 4: Reranking {len(candidates)} candidates")
        from app.services.retriever import get_reranker
        reranker = get_reranker()
        final_chunks = reranker.rerank(query, candidates, top_k=top_k)
        logger.info(f"Reranking complete, returning {len(final_chunks)} chunks")
        return final_chunks
    except Exception as e:
        logger.error(f"Reranking failed: {e}, falling back to hybrid results")
        return candidates[:top_k]

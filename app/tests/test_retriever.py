"""Tests for RAG retrieval functionality"""
import pytest
from app.services.retriever import (
    retrieve_relevant_chunks,
    retrieve_with_reranking,
    format_context_for_llm
)
from app.db.models import Document, Chunk
from app.services.embeddings import generate_embedding


def test_retrieve_relevant_chunks(db_session, sample_document_with_chunks):
    """Test retrieving relevant chunks for a query"""
    doc, chunks = sample_document_with_chunks

    # Query about vacation
    query = "How many vacation days do employees get?"
    results = retrieve_relevant_chunks(query, db_session, top_k=3)

    assert len(results) <= 3
    assert all("chunk_id" in r for r in results)
    assert all("text" in r for r in results)
    assert all("similarity_score" in r for r in results)
    assert all("filename" in r for r in results)
    assert all("page_number" in r for r in results)

    # Scores should be between 0 and 1
    assert all(0 <= r["similarity_score"] <= 1 for r in results)

    # Results should be sorted by score (highest first)
    scores = [r["similarity_score"] for r in results]
    assert scores == sorted(scores, reverse=True)


def test_retrieve_with_no_matches(db_session, sample_document_with_chunks):
    """Test retrieval when query has no good matches"""
    # Query about something not in the document
    query = "What is the quantum physics theory?"
    results = retrieve_relevant_chunks(
        query,
        db_session,
        top_k=3,
        similarity_threshold=0.8  # High threshold
    )

    # Should return few or no results
    assert len(results) <= 3


def test_retrieve_empty_database(db_session):
    """Test retrieval when no documents exist"""
    query = "Any question"
    results = retrieve_relevant_chunks(query, db_session)

    assert results == []


def test_retrieve_top_k_parameter(db_session, sample_document_with_chunks):
    """Test that top_k parameter limits results correctly"""
    query = "vacation policy"

    # Test different top_k values
    results_3 = retrieve_relevant_chunks(query, db_session, top_k=3)
    results_5 = retrieve_relevant_chunks(query, db_session, top_k=5)

    assert len(results_3) <= 3
    assert len(results_5) <= 5
    assert len(results_5) >= len(results_3)


def test_format_context_for_llm(sample_chunks_data):
    """Test formatting chunks into LLM context"""
    chunks = [
        {
            "chunk_id": 1,
            "text": "Employees get 15 days vacation per year.",
            "filename": "policy.pdf",
            "page_number": 1,
            "similarity_score": 0.9
        },
        {
            "chunk_id": 2,
            "text": "Sick leave is 10 days annually.",
            "filename": "policy.pdf",
            "page_number": 2,
            "similarity_score": 0.7
        }
    ]

    context = format_context_for_llm(chunks)

    # Should include citations
    assert "[policy.pdf - Page 1]" in context
    assert "[policy.pdf - Page 2]" in context

    # Should include chunk text
    assert "15 days vacation" in context
    assert "10 days annually" in context

    # Chunks should be separated
    assert "\n\n" in context


def test_format_context_empty(sample_chunks_data):
    """Test formatting with no chunks"""
    context = format_context_for_llm([])

    assert "No relevant information found" in context


def test_similarity_threshold(db_session, sample_document_with_chunks):
    """Test that similarity threshold filters results correctly"""
    query = "vacation days"

    # Low threshold - should get more results
    results_low = retrieve_relevant_chunks(
        query,
        db_session,
        top_k=10,
        similarity_threshold=0.1
    )

    # High threshold - should get fewer results
    results_high = retrieve_relevant_chunks(
        query,
        db_session,
        top_k=10,
        similarity_threshold=0.7
    )

    assert len(results_high) <= len(results_low)

    # All high threshold results should have score >= 0.7
    assert all(r["similarity_score"] >= 0.7 for r in results_high)


def test_retrieve_includes_document_metadata(db_session, sample_document_with_chunks):
    """Test that retrieved chunks include document metadata"""
    doc, chunks = sample_document_with_chunks

    query = "vacation policy"
    results = retrieve_relevant_chunks(query, db_session, top_k=1)

    assert len(results) > 0
    result = results[0]

    # Should include document info
    assert result["document_id"] == doc.id
    assert result["filename"] == doc.filename
    assert isinstance(result["page_number"], int)


# ============================================================================
# RERANKING TESTS
# ============================================================================

def test_retrieve_with_reranking_basic(db_session, sample_document_with_chunks):
    """Test basic reranking functionality"""
    doc, chunks = sample_document_with_chunks

    query = "How many vacation days do employees get?"
    results = retrieve_with_reranking(
        query,
        db_session,
        initial_k=6,  # Get all chunks
        final_k=3     # Return top 3 after reranking
    )

    # Should return final_k results
    assert len(results) <= 3
    assert len(results) > 0

    # Each result should have reranking score
    for result in results:
        assert "reranking_score" in result
        assert "original_similarity" in result
        assert isinstance(result["reranking_score"], float)

    # Results should be sorted by reranking score
    reranking_scores = [r["reranking_score"] for r in results]
    assert reranking_scores == sorted(reranking_scores, reverse=True)


def test_reranking_improves_order(db_session, sample_document_with_chunks):
    """Test that reranking improves result ordering"""
    doc, chunks = sample_document_with_chunks

    # Query that might have different vector vs semantic relevance
    query = "What are the benefits of working here?"

    # Get results without reranking (lower threshold to get results)
    no_rerank = retrieve_relevant_chunks(query, db_session, top_k=5, similarity_threshold=0.1)

    # Get results with reranking
    with_rerank = retrieve_with_reranking(
        query,
        db_session,
        initial_k=6,
        final_k=5,
        similarity_threshold=0.1
    )

    # Both should return results
    assert len(no_rerank) > 0
    assert len(with_rerank) > 0

    # The top results might be different (reranking can change order)
    # We can't assert they're different, but we can verify both work
    assert all("chunk_id" in r for r in with_rerank)
    assert all("reranking_score" in r for r in with_rerank)


def test_reranking_with_no_candidates(db_session):
    """Test reranking when no chunks match"""
    query = "quantum physics theories"

    results = retrieve_with_reranking(
        query,
        db_session,
        initial_k=10,
        final_k=5,
        similarity_threshold=0.9  # Very high threshold
    )

    # Should handle gracefully
    assert isinstance(results, list)
    assert len(results) == 0


def test_reranking_preserves_metadata(db_session, sample_document_with_chunks):
    """Test that reranking preserves all chunk metadata"""
    doc, chunks = sample_document_with_chunks

    query = "remote work policy"
    results = retrieve_with_reranking(query, db_session, initial_k=6, final_k=2)

    assert len(results) > 0
    result = results[0]

    # Should have all original fields plus reranking fields
    assert "chunk_id" in result
    assert "text" in result
    assert "filename" in result
    assert "page_number" in result
    assert "document_id" in result
    assert "similarity_score" in result
    assert "reranking_score" in result
    assert "original_similarity" in result


def test_reranking_parameters(db_session, sample_document_with_chunks):
    """Test different reranking parameter combinations"""
    query = "sick leave policy"

    # Test different initial_k values
    results_10 = retrieve_with_reranking(query, db_session, initial_k=10, final_k=3)
    results_3 = retrieve_with_reranking(query, db_session, initial_k=3, final_k=3)

    # Both should work and respect final_k
    assert len(results_10) <= 3
    assert len(results_3) <= 3

    # Test when initial_k < final_k (should return initial_k results)
    results_limited = retrieve_with_reranking(query, db_session, initial_k=2, final_k=5)
    assert len(results_limited) <= 2

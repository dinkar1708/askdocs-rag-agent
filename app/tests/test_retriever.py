"""Tests for RAG retrieval functionality"""
import pytest
from app.services.retriever import retrieve_relevant_chunks, format_context_for_llm
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

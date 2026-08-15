"""Tests for Citation Verification"""

import pytest
from app.services.citation_verifier import (
    extract_claimed_citations,
    verify_citation_existence,
    CitationVerificationState,
    verify_citations
)


def test_extract_claimed_citations_bracket_format():
    """Test extraction of [doc.pdf, p.5] format"""
    state: CitationVerificationState = {
        "question": "Test",
        "context_chunks": [],
        "generated_answer": "According to [handbook.pdf, p.7], employees get 15 days vacation.",
        "claimed_citations": [],
        "verified_citations": [],
        "flagged_citations": [],
        "verification_status": "unknown"
    }

    result = extract_claimed_citations(state)

    assert len(result["claimed_citations"]) == 1
    assert result["claimed_citations"][0]["document"] == "handbook.pdf"
    assert result["claimed_citations"][0]["page"] == 7


def test_extract_claimed_citations_source_format():
    """Test extraction of (source: doc.pdf, page 5) format"""
    state: CitationVerificationState = {
        "question": "Test",
        "context_chunks": [],
        "generated_answer": "The policy states (source: terms.pdf, page 23) that refunds are processed in 7 days.",
        "claimed_citations": [],
        "verified_citations": [],
        "flagged_citations": [],
        "verification_status": "unknown"
    }

    result = extract_claimed_citations(state)

    assert len(result["claimed_citations"]) == 1
    assert result["claimed_citations"][0]["document"] == "terms.pdf"
    assert result["claimed_citations"][0]["page"] == 23


def test_extract_claimed_citations_plain_format():
    """Test extraction of plain doc.pdf, page 5 format"""
    state: CitationVerificationState = {
        "question": "Test",
        "context_chunks": [],
        "generated_answer": "As stated in handbook.pdf, page 15, remote work is allowed.",
        "claimed_citations": [],
        "verified_citations": [],
        "flagged_citations": [],
        "verification_status": "unknown"
    }

    result = extract_claimed_citations(state)

    assert len(result["claimed_citations"]) == 1
    assert result["claimed_citations"][0]["document"] == "handbook.pdf"
    assert result["claimed_citations"][0]["page"] == 15


def test_extract_multiple_citations():
    """Test extraction of multiple citations"""
    state: CitationVerificationState = {
        "question": "Test",
        "context_chunks": [],
        "generated_answer": "According to [doc1.pdf, p.5] and [doc2.pdf, p.10], the policy is clear.",
        "claimed_citations": [],
        "verified_citations": [],
        "flagged_citations": [],
        "verification_status": "unknown"
    }

    result = extract_claimed_citations(state)

    assert len(result["claimed_citations"]) == 2
    assert result["claimed_citations"][0]["page"] == 5
    assert result["claimed_citations"][1]["page"] == 10


def test_verify_citation_existence_found():
    """Test that existing citations are verified"""
    state: CitationVerificationState = {
        "question": "Test",
        "context_chunks": [
            {
                "chunk_id": 1,
                "filename": "handbook.pdf",
                "page_number": 7,
                "text": "Employees receive 15 days of paid vacation per year.",
                "score": 0.9
            }
        ],
        "generated_answer": "Test",
        "claimed_citations": [
            {
                "document": "handbook.pdf",
                "page": 7,
                "found_in_context": False
            }
        ],
        "verified_citations": [],
        "flagged_citations": [],
        "verification_status": "unknown"
    }

    result = verify_citation_existence(state)

    assert len(result["verified_citations"]) == 1
    assert len(result["flagged_citations"]) == 0
    assert result["verified_citations"][0]["found_in_context"] is True
    assert result["verified_citations"][0]["chunk_id"] == 1


def test_verify_citation_existence_not_found():
    """Test that non-existent citations are flagged"""
    state: CitationVerificationState = {
        "question": "Test",
        "context_chunks": [
            {
                "chunk_id": 1,
                "filename": "handbook.pdf",
                "page_number": 7,
                "text": "Some text",
                "score": 0.9
            }
        ],
        "generated_answer": "Test",
        "claimed_citations": [
            {
                "document": "nonexistent.pdf",
                "page": 99,
                "found_in_context": False
            }
        ],
        "verified_citations": [],
        "flagged_citations": [],
        "verification_status": "unknown"
    }

    result = verify_citation_existence(state)

    assert len(result["verified_citations"]) == 0
    assert len(result["flagged_citations"]) == 1
    assert result["flagged_citations"][0]["found_in_context"] is False


def test_verify_citation_existence_partial():
    """Test partial verification (some found, some not)"""
    state: CitationVerificationState = {
        "question": "Test",
        "context_chunks": [
            {
                "chunk_id": 1,
                "filename": "handbook.pdf",
                "page_number": 7,
                "text": "Valid text",
                "score": 0.9
            }
        ],
        "generated_answer": "Test",
        "claimed_citations": [
            {
                "document": "handbook.pdf",
                "page": 7,
                "found_in_context": False
            },
            {
                "document": "fake.pdf",
                "page": 99,
                "found_in_context": False
            }
        ],
        "verified_citations": [],
        "flagged_citations": [],
        "verification_status": "unknown"
    }

    result = verify_citation_existence(state)

    assert len(result["verified_citations"]) == 1
    assert len(result["flagged_citations"]) == 1


def test_no_citations_claimed():
    """Test answer with no citations"""
    state: CitationVerificationState = {
        "question": "Test",
        "context_chunks": [],
        "generated_answer": "This answer has no citations.",
        "claimed_citations": [],
        "verified_citations": [],
        "flagged_citations": [],
        "verification_status": "unknown"
    }

    result = extract_claimed_citations(state)

    assert len(result["claimed_citations"]) == 0

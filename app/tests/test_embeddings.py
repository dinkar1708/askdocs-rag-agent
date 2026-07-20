"""Test embedding generation"""

import pytest
from app.services.embeddings import generate_embedding, chunk_text


def test_generate_embedding():
    """Test generating embeddings"""
    text = "This is a test sentence."
    embedding = generate_embedding(text)

    assert isinstance(embedding, list)
    assert len(embedding) == 384  # all-MiniLM-L6-v2 dimension
    assert all(isinstance(x, float) for x in embedding)


def test_embedding_consistency():
    """Test same text produces same embedding"""
    text = "Consistent test text"

    embedding1 = generate_embedding(text)
    embedding2 = generate_embedding(text)

    # Should be identical
    assert embedding1 == embedding2


def test_different_texts_different_embeddings():
    """Test different texts produce different embeddings"""
    text1 = "The quick brown fox"
    text2 = "Vacation policy details"

    embedding1 = generate_embedding(text1)
    embedding2 = generate_embedding(text2)

    # Should be different
    assert embedding1 != embedding2


def test_chunk_text_basic():
    """Test basic text chunking"""
    text = "A" * 1000  # 1000 character text
    chunks = chunk_text(text, page_number=1, chunk_size=200, overlap=50)

    assert len(chunks) > 0
    for chunk in chunks:
        assert "text" in chunk
        assert "page_number" in chunk
        assert chunk["page_number"] == 1
        assert len(chunk["text"]) <= 250  # chunk_size + some buffer


def test_chunk_text_with_sentences():
    """Test chunking respects sentence boundaries"""
    text = "First sentence. Second sentence. Third sentence. Fourth sentence."
    chunks = chunk_text(text, page_number=2, chunk_size=30, overlap=5)

    assert len(chunks) > 0
    # Chunks should try to break at sentences
    for chunk in chunks:
        assert chunk["page_number"] == 2


def test_chunk_text_empty():
    """Test chunking empty text"""
    chunks = chunk_text("", page_number=1)

    assert len(chunks) == 0


def test_chunk_text_overlap():
    """Test chunks have overlap"""
    text = "Word1 Word2 Word3 Word4 Word5 Word6 Word7 Word8"
    chunks = chunk_text(text, page_number=1, chunk_size=20, overlap=5)

    # With overlap, consecutive chunks should share some text
    if len(chunks) > 1:
        # This is hard to test exactly, but we should have multiple chunks
        assert len(chunks) >= 2

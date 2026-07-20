"""Test database models"""

import pytest
from datetime import datetime

from app.db.models import Document, Chunk, Session


def test_create_document(db_session):
    """Test creating a document"""
    doc = Document(
        filename="test.pdf",
        page_count=5
    )
    db_session.add(doc)
    db_session.commit()

    assert doc.id is not None
    assert doc.filename == "test.pdf"
    assert doc.page_count == 5
    assert isinstance(doc.uploaded_at, datetime)


def test_create_chunk(db_session):
    """Test creating a chunk linked to document"""
    # Create document first
    doc = Document(filename="test.pdf", page_count=5)
    db_session.add(doc)
    db_session.commit()

    # Create chunk
    chunk = Chunk(
        document_id=doc.id,
        text="This is a test chunk of text.",
        page_number=1,
        embedding=[0.1, 0.2, 0.3] * 128  # 384 dimensions
    )
    db_session.add(chunk)
    db_session.commit()

    assert chunk.id is not None
    assert chunk.document_id == doc.id
    assert chunk.text == "This is a test chunk of text."
    assert chunk.page_number == 1
    assert len(chunk.embedding) == 384


def test_document_chunks_relationship(db_session):
    """Test document-chunks relationship"""
    doc = Document(filename="test.pdf", page_count=5)
    db_session.add(doc)
    db_session.commit()

    # Add multiple chunks
    for i in range(3):
        chunk = Chunk(
            document_id=doc.id,
            text=f"Chunk {i}",
            page_number=i + 1,
            embedding=[0.1] * 384
        )
        db_session.add(chunk)
    db_session.commit()

    # Verify relationship
    assert len(doc.chunks) == 3
    assert doc.chunks[0].text == "Chunk 0"
    assert doc.chunks[2].page_number == 3


def test_cascade_delete(db_session):
    """Test cascade delete - deleting document deletes chunks"""
    doc = Document(filename="test.pdf", page_count=5)
    db_session.add(doc)
    db_session.commit()

    chunk = Chunk(
        document_id=doc.id,
        text="Test chunk",
        page_number=1,
        embedding=[0.1] * 384
    )
    db_session.add(chunk)
    db_session.commit()

    doc_id = doc.id
    chunk_id = chunk.id

    # Delete document
    db_session.delete(doc)
    db_session.commit()

    # Verify chunk was also deleted
    assert db_session.query(Document).filter(Document.id == doc_id).first() is None
    assert db_session.query(Chunk).filter(Chunk.id == chunk_id).first() is None


def test_create_session(db_session):
    """Test creating a chat session"""
    session = Session()
    db_session.add(session)
    db_session.commit()

    assert session.id is not None
    assert isinstance(session.created_at, datetime)
    assert isinstance(session.last_accessed, datetime)

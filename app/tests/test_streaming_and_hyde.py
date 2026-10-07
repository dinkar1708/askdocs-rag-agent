"""Unit tests for HyDE (Hypothetical Document Embeddings) and Real-Time SSE Token Streaming"""

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.models import Document, Chunk, Session as SessionModel, Message
from app.services.hyde import generate_hypothetical_passage, retrieve_with_hyde
from app.services.embeddings import generate_embedding
from app.llm.mock_provider import MockLLMProvider


@pytest.mark.asyncio
async def test_hyde_passage_generation():
    """Test generating hypothetical document passage"""
    mock_provider = MockLLMProvider()
    passage = await generate_hypothetical_passage("What is the refund policy?", llm_provider=mock_provider)
    assert isinstance(passage, str)
    assert len(passage) > 0


@pytest.mark.asyncio
async def test_hyde_retrieval(db_session):
    """Test retrieval with HyDE using pgvector test database"""
    doc = Document(filename="terms_of_service.pdf", page_count=2, doc_metadata={})
    db_session.add(doc)
    db_session.flush()

    emb1 = generate_embedding("Full refund available within 30 days of purchase upon request.")
    chunk1 = Chunk(
        document_id=doc.id,
        text="Full refund available within 30 days of purchase upon request.",
        page_number=1,
        embedding=emb1
    )
    db_session.add(chunk1)
    db_session.commit()

    mock_provider = MockLLMProvider()
    chunks = await retrieve_with_hyde(
        query="How do I get my money back?",
        db=db_session,
        top_k=3,
        similarity_threshold=0.1,
        llm_provider=mock_provider
    )
    assert isinstance(chunks, list)
    assert len(chunks) >= 1
    assert "refund" in chunks[0]["text"].lower()
    assert "hyde_passage" in chunks[0]


def test_ask_stream_endpoint_refuse(client: TestClient, db_session):
    """Test /ask/stream endpoint when question cannot be answered (refusal)"""
    response = client.post(
        "/ask/stream",
        json={"question": "What is the capital of Mars?", "top_k": 3},
        headers={"X-API-Key": settings.API_KEY}
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    body = response.text
    assert "event: route" in body
    assert "event: token" in body
    assert "event: done" in body
    assert "not_found" in body


def test_ask_stream_endpoint_answer_and_session(client: TestClient, db_session, sample_document_with_chunks):
    """Test /ask/stream endpoint streaming tokens and saving to conversation session"""
    # Create session
    session = SessionModel()
    db_session.add(session)
    db_session.commit()

    response = client.post(
        "/ask/stream",
        json={
            "question": "How many vacation days do employees get?",
            "top_k": 3,
            "session_id": session.id,
            "include_sources": True
        },
        headers={"X-API-Key": settings.API_KEY}
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    body = response.text
    assert "event: route" in body
    assert "event: sources" in body
    assert "event: token" in body
    assert "event: done" in body
    assert str(session.id) in body

    # Verify session messages were persisted in database
    messages = db_session.query(Message).filter(Message.session_id == session.id).all()
    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[1].role == "assistant"
    assert messages[1].sources is not None

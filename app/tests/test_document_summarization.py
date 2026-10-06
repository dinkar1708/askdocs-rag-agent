"""Tests for Document Summarization Feature"""

import pytest
from datetime import datetime
from app.db.models import Document, Chunk
from app.schemas.summary import SummaryRequest, SummaryType, BatchSummaryRequest
from app.services.document_summarizer import DocumentSummarizer, get_document_summarizer
from app.llm.mock_provider import MockLLMProvider


@pytest.fixture
def sample_document(db_session):
    """Create a sample document with chunks for testing summarization"""
    doc = Document(
        filename="ai_engineer_gg11.pdf",
        page_count=3,
        uploaded_at=datetime.utcnow(),
        doc_metadata={"department": "Engineering", "grade": "GG11"}
    )
    db_session.add(doc)
    db_session.flush()

    chunks = [
        Chunk(
            document_id=doc.id,
            page_number=1,
            chunk_index=0,
            text="Position: Senior AI Engineer (GG11). Experience: 8+ years software engineering, 4+ years AI/ML leadership.",
            chunk_type="text"
        ),
        Chunk(
            document_id=doc.id,
            page_number=2,
            chunk_index=1,
            text="Responsibilities: Architect scalable LLM applications, lead MLOps pipelines, and mentor junior engineers.",
            chunk_type="text"
        ),
        Chunk(
            document_id=doc.id,
            page_number=3,
            chunk_index=2,
            text="Compensation & Location: Salary range $150,000 - $180,000 per year. Hybrid remote (3 days/week).",
            chunk_type="text"
        ),
    ]
    for c in chunks:
        db_session.add(c)
    db_session.commit()
    db_session.refresh(doc)
    return doc


@pytest.mark.asyncio
async def test_summarize_document_executive(db_session, sample_document):
    """Test generating an executive summary for a document"""
    summarizer = DocumentSummarizer(llm_provider=MockLLMProvider())
    req = SummaryRequest(summary_type="executive", max_length=150)

    response = await summarizer.summarize_document(
        db=db_session,
        document_id=sample_document.id,
        request=req
    )

    assert response.document_id == sample_document.id
    assert response.filename == "ai_engineer_gg11.pdf"
    assert response.summary_type == "executive"
    assert len(response.summary) > 0
    assert response.word_count > 0
    assert response.cached is False
    assert len(response.key_points) > 0
    assert response.key_points[0].page in [1, 2, 3]


@pytest.mark.asyncio
async def test_summarize_document_caching(db_session, sample_document):
    """Test that generated summaries are cached in document metadata"""
    summarizer = DocumentSummarizer(llm_provider=MockLLMProvider())
    req = SummaryRequest(summary_type="executive", max_length=150)

    # 1. First call generates and caches
    resp1 = await summarizer.summarize_document(db=db_session, document_id=sample_document.id, request=req)
    assert resp1.cached is False

    # 2. Second call returns from cache
    resp2 = await summarizer.summarize_document(db=db_session, document_id=sample_document.id, request=req)
    assert resp2.cached is True
    assert resp2.summary == resp1.summary

    # 3. Force regenerate bypasses cache
    req_force = SummaryRequest(summary_type="executive", max_length=150, force_regenerate=True)
    resp3 = await summarizer.summarize_document(db=db_session, document_id=sample_document.id, request=req_force)
    assert resp3.cached is False


@pytest.mark.asyncio
async def test_summarize_document_detailed(db_session, sample_document):
    """Test detailed summary generation with focus areas"""
    summarizer = DocumentSummarizer(llm_provider=MockLLMProvider())
    req = SummaryRequest(
        summary_type="detailed",
        max_length=300,
        focus_areas=["experience", "compensation"]
    )

    response = await summarizer.summarize_document(
        db=db_session,
        document_id=sample_document.id,
        request=req
    )

    assert response.summary_type == "detailed"
    assert len(response.summary) > 0


@pytest.mark.asyncio
async def test_summarize_empty_document(db_session):
    """Test summarizing a document with no chunks"""
    doc = Document(
        filename="empty.pdf",
        page_count=1,
        uploaded_at=datetime.utcnow()
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    summarizer = DocumentSummarizer(llm_provider=MockLLMProvider())
    req = SummaryRequest(summary_type="executive")

    response = await summarizer.summarize_document(
        db=db_session,
        document_id=doc.id,
        request=req
    )

    assert "no readable text" in response.summary.lower()
    assert len(response.key_points) == 0


@pytest.mark.asyncio
async def test_summarize_nonexistent_document(db_session):
    """Test 404/ValueError on missing document ID"""
    summarizer = DocumentSummarizer(llm_provider=MockLLMProvider())
    req = SummaryRequest(summary_type="executive")

    with pytest.raises(ValueError, match="not found"):
        await summarizer.summarize_document(db=db_session, document_id=99999, request=req)


@pytest.mark.asyncio
async def test_summarize_batch(db_session, sample_document):
    """Test batch document summarization"""
    doc2 = Document(filename="second_doc.pdf", page_count=1, uploaded_at=datetime.utcnow())
    db_session.add(doc2)
    db_session.flush()
    chunk2 = Chunk(document_id=doc2.id, page_number=1, chunk_index=0, text="Doc 2 content", chunk_type="text")
    db_session.add(chunk2)
    db_session.commit()

    summarizer = DocumentSummarizer(llm_provider=MockLLMProvider())
    batch_req = BatchSummaryRequest(
        document_ids=[sample_document.id, doc2.id, 88888],
        summary_type="executive"
    )

    batch_resp = await summarizer.summarize_batch(db=db_session, request=batch_req)
    assert batch_resp.total_processed == 2
    assert len(batch_resp.summaries) == 2
    assert 88888 in batch_resp.failed_document_ids


def test_api_summarize_endpoints(client, sample_document):
    """Test FastAPI REST endpoints /documents/{id}/summarize and /documents/{id}/summary"""
    # 1. Generate summary via POST
    post_resp = client.post(
        f"/documents/{sample_document.id}/summarize",
        json={"summary_type": "executive", "max_length": 150}
    )
    assert post_resp.status_code == 200
    data = post_resp.json()
    assert data["document_id"] == sample_document.id
    assert data["cached"] is False
    assert len(data["key_points"]) > 0

    # 2. Retrieve cached summary via GET
    get_resp = client.get(
        f"/documents/{sample_document.id}/summary?summary_type=executive"
    )
    assert get_resp.status_code == 200
    cached_data = get_resp.json()
    assert cached_data["cached"] is True
    assert cached_data["summary"] == data["summary"]

    # 3. GET on missing cache returns 404
    missing_cache_resp = client.get(
        f"/documents/{sample_document.id}/summary?summary_type=detailed"
    )
    assert missing_cache_resp.status_code == 404

    # 4. POST on non-existent document returns 404
    not_found_resp = client.post(
        "/documents/999999/summarize",
        json={"summary_type": "executive"}
    )
    assert not_found_resp.status_code == 404


def test_api_batch_summarize_endpoint(client, sample_document):
    """Test FastAPI batch summary endpoint POST /documents/summarize/batch"""
    resp = client.post(
        "/documents/summarize/batch",
        json={
            "document_ids": [sample_document.id],
            "summary_type": "executive"
        }
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_processed"] == 1
    assert len(data["summaries"]) == 1

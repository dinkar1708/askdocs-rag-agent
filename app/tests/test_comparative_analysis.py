"""Tests for Comparative Analysis Feature (Feature 09)"""

import pytest
from datetime import datetime
from app.db.models import Document, Chunk
from app.schemas.comparison import (
    ComparisonRequest,
    TableComparisonRequest,
    DiffRequest
)
from app.services.document_comparator import DocumentComparator
from app.llm.mock_provider import MockLLMProvider


@pytest.fixture
def comparison_documents(db_session):
    """Create three sample job documents for comparison tests"""
    doc1 = Document(
        filename="job_gg9.pdf",
        page_count=2,
        uploaded_at=datetime.utcnow(),
        doc_metadata={"grade": "GG9", "role": "AI Engineer"}
    )
    doc2 = Document(
        filename="job_gg10.pdf",
        page_count=2,
        uploaded_at=datetime.utcnow(),
        doc_metadata={"grade": "GG10", "role": "AI Engineer"}
    )
    doc3 = Document(
        filename="job_gg11.pdf",
        page_count=3,
        uploaded_at=datetime.utcnow(),
        doc_metadata={"grade": "GG11", "role": "Senior AI Engineer"}
    )
    db_session.add_all([doc1, doc2, doc3])
    db_session.flush()

    chunks = [
        Chunk(
            document_id=doc1.id,
            page_number=1,
            chunk_index=0,
            text="Qualifications: Bachelor's degree in CS. Experience: 3-5 years in software engineering. Skills: Python, SQL, Basic ML. Salary: $90,000 - $120,000.",
            chunk_type="text"
        ),
        Chunk(
            document_id=doc2.id,
            page_number=1,
            chunk_index=0,
            text="Qualifications: Bachelor's or Master's degree. Experience: 5-7 years with 2+ in ML. Skills: Python, TensorFlow, AWS, MLOps. Salary: $120,000 - $150,000.",
            chunk_type="text"
        ),
        Chunk(
            document_id=doc3.id,
            page_number=1,
            chunk_index=0,
            text="Qualifications: Master's or PhD preferred. Experience: 8+ years with 4+ in AI leadership. Skills: Python, PyTorch, AWS, Team Leadership. Salary: $150,000 - $180,000.",
            chunk_type="text"
        ),
    ]
    db_session.add_all(chunks)
    db_session.commit()
    for d in [doc1, doc2, doc3]:
        db_session.refresh(d)

    return [doc1, doc2, doc3]


@pytest.mark.asyncio
async def test_compare_documents_success(db_session, comparison_documents):
    """Test comparing multiple documents side-by-side"""
    comparator = DocumentComparator(db=db_session, llm_provider=MockLLMProvider())
    doc_ids = [doc.id for doc in comparison_documents]
    req = ComparisonRequest(
        document_ids=doc_ids,
        aspects=["experience", "skills", "salary"]
    )

    response = await comparator.compare_documents(req)

    assert response.comparison.aspects == ["experience", "skills", "salary"]
    assert len(response.comparison.documents) == 3
    for d in response.comparison.documents:
        assert d.document_id in doc_ids
        assert "experience" in d.data
        assert "skills" in d.data
        assert "salary" in d.data
    assert len(response.summary) > 0


@pytest.mark.asyncio
async def test_compare_documents_with_question(db_session, comparison_documents):
    """Test comparison with an explicit focus question"""
    comparator = DocumentComparator(db=db_session, llm_provider=MockLLMProvider())
    doc_ids = [comparison_documents[0].id, comparison_documents[1].id]
    req = ComparisonRequest(
        question="Compare experience progression between GG9 and GG10",
        document_ids=doc_ids,
        aspects=["experience"]
    )

    response = await comparator.compare_documents(req)
    assert len(response.comparison.documents) == 2
    assert "experience" in response.comparison.aspects


@pytest.mark.asyncio
async def test_compare_table_markdown(db_session, comparison_documents):
    """Test generating a markdown comparison table"""
    comparator = DocumentComparator(db=db_session, llm_provider=MockLLMProvider())
    doc_ids = [doc.id for doc in comparison_documents]
    req = TableComparisonRequest(
        document_ids=doc_ids,
        aspects=["experience", "salary"]
    )

    response = await comparator.compare_table(req)

    assert "| Aspect |" in response.markdown_table
    assert "Experience" in response.markdown_table
    assert "Salary" in response.markdown_table
    assert comparison_documents[0].filename in response.markdown_table
    assert len(response.documents) == 3


@pytest.mark.asyncio
async def test_compare_diff_two_documents(db_session, comparison_documents):
    """Test fine-grained diff between two documents"""
    comparator = DocumentComparator(db=db_session, llm_provider=MockLLMProvider())
    doc1, doc2 = comparison_documents[0], comparison_documents[1]
    req = DiffRequest(
        document_ids=[doc1.id, doc2.id],
        aspect="experience"
    )

    response = await comparator.compare_diff(req)

    assert response.document_1.document_id == doc1.id
    assert response.document_2.document_id == doc2.id
    assert len(response.document_1.text) > 0
    assert len(response.document_2.text) > 0
    assert len(response.differences) > 0


@pytest.mark.asyncio
async def test_compare_validation_limits(db_session, comparison_documents):
    """Test document validation constraints: min 2, max 5, nonexistent"""
    comparator = DocumentComparator(db=db_session, llm_provider=MockLLMProvider())

    # Less than 2 documents raises ValueError
    req_too_few = ComparisonRequest.model_construct(document_ids=[comparison_documents[0].id], aspects=["salary"])
    with pytest.raises(ValueError, match="At least 2"):
        await comparator.compare_documents(req_too_few)

    # More than 5 documents raises ValueError
    req_too_many = ComparisonRequest.model_construct(document_ids=[1, 2, 3, 4, 5, 6], aspects=["salary"])
    with pytest.raises(ValueError, match="Maximum 5"):
        await comparator.compare_documents(req_too_many)

    # Nonexistent document ID raises ValueError
    with pytest.raises(ValueError, match="not found"):
        await comparator.compare_documents(
            ComparisonRequest(document_ids=[comparison_documents[0].id, 999999], aspects=["salary"])
        )

    # Diff endpoint with != 2 document IDs raises ValueError
    diff_too_many = DiffRequest.model_construct(
        document_ids=[comparison_documents[0].id, comparison_documents[1].id, comparison_documents[2].id],
        aspect="salary"
    )
    with pytest.raises(ValueError, match="exactly two"):
        await comparator.compare_diff(diff_too_many)


def test_api_compare_endpoints(client, comparison_documents):
    """Test REST API endpoints for comparison"""
    doc_ids = [d.id for d in comparison_documents]

    # 1. POST /compare
    resp = client.post(
        "/compare",
        json={
            "document_ids": [doc_ids[0], doc_ids[1]],
            "aspects": ["experience", "salary"]
        }
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "comparison" in data
    assert len(data["comparison"]["documents"]) == 2

    # 2. POST /compare/table
    resp_table = client.post(
        "/compare/table",
        json={
            "document_ids": [doc_ids[0], doc_ids[1]],
            "aspects": ["experience", "salary"]
        }
    )
    assert resp_table.status_code == 200
    data_table = resp_table.json()
    assert "| Aspect |" in data_table["markdown_table"]

    # 3. POST /compare/diff
    resp_diff = client.post(
        "/compare/diff",
        json={
            "document_ids": [doc_ids[0], doc_ids[1]],
            "aspect": "experience"
        }
    )
    assert resp_diff.status_code == 200
    data_diff = resp_diff.json()
    assert data_diff["document_1"]["document_id"] == doc_ids[0]
    assert data_diff["document_2"]["document_id"] == doc_ids[1]

    # 4. POST /compare on nonexistent document returns 404
    resp_404 = client.post(
        "/compare",
        json={
            "document_ids": [doc_ids[0], 999999],
            "aspects": ["salary"]
        }
    )
    assert resp_404.status_code == 404

    # 5. POST /compare with fewer than 2 documents returns 422 (Pydantic min_length validation)
    resp_422 = client.post(
        "/compare",
        json={
            "document_ids": [doc_ids[0]],
            "aspects": ["salary"]
        }
    )
    assert resp_422.status_code == 422

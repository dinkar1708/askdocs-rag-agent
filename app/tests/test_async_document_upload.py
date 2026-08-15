"""Tests for async document upload with LangGraph processing"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import io

from app.db.models import DocumentProcessingJob, Document


def create_test_pdf(text: str = "Test PDF content") -> bytes:
    """Create a simple test PDF in memory"""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.drawString(100, 750, text)
    pdf.showPage()
    pdf.save()

    buffer.seek(0)
    return buffer.getvalue()


def test_async_document_upload_returns_job_id(client: TestClient, db_session: Session):
    """Test that async upload returns job_id immediately"""

    # Create test PDF
    pdf_content = create_test_pdf("Test async upload document")
    pdf_file = io.BytesIO(pdf_content)

    # Upload with async_processing=true
    response = client.post(
        "/documents?async_processing=true",
        files={"file": ("test_async.pdf", pdf_file, "application/pdf")}
    )

    assert response.status_code == 201
    data = response.json()

    # Should return job_id, not document_id
    assert "job_id" in data
    assert "filename" in data
    assert "status" in data
    assert "message" in data
    assert data["status"] == "queued"
    assert data["filename"] == "test_async.pdf"

    # Verify job was created in database
    job = db_session.query(DocumentProcessingJob).filter(
        DocumentProcessingJob.job_id == data["job_id"]
    ).first()

    assert job is not None
    assert job.filename == "test_async.pdf"
    assert job.status == "queued"
    assert job.progress == 0


def test_sync_document_upload_returns_document_id(client: TestClient, db_session: Session):
    """Test that sync upload (default) returns document_id after processing"""

    # Create test PDF
    pdf_content = create_test_pdf("Test sync upload document")
    pdf_file = io.BytesIO(pdf_content)

    # Upload with async_processing=false (default)
    response = client.post(
        "/documents",
        files={"file": ("test_sync.pdf", pdf_file, "application/pdf")}
    )

    assert response.status_code == 201
    data = response.json()

    # Should return document_id, not job_id
    assert "id" in data
    assert "filename" in data
    assert "page_count" in data
    assert "chunk_count" in data
    assert data["filename"] == "test_sync.pdf"

    # Verify document was created in database
    document = db_session.query(Document).filter(Document.id == data["id"]).first()
    assert document is not None
    assert document.filename == "test_sync.pdf"


def test_get_job_status(client: TestClient, db_session: Session):
    """Test getting job status"""

    # Create test PDF
    pdf_content = create_test_pdf("Test job status")
    pdf_file = io.BytesIO(pdf_content)

    # Upload with async processing
    upload_response = client.post(
        "/documents?async_processing=true",
        files={"file": ("test_job_status.pdf", pdf_file, "application/pdf")}
    )

    assert upload_response.status_code == 201
    job_id = upload_response.json()["job_id"]

    # Get job status
    status_response = client.get(f"/documents/jobs/{job_id}")

    assert status_response.status_code == 200
    status_data = status_response.json()

    assert status_data["job_id"] == job_id
    assert status_data["filename"] == "test_job_status.pdf"
    assert status_data["status"] in ["queued", "extracting", "chunking", "embedding", "storing", "complete", "failed"]
    assert "progress" in status_data
    assert "current_stage" in status_data
    assert "created_at" in status_data


def test_get_job_status_not_found(client: TestClient):
    """Test getting status of non-existent job"""

    response = client.get("/documents/jobs/non-existent-job-id")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_list_jobs(client: TestClient, db_session: Session):
    """Test listing all jobs"""

    # Create a couple of jobs
    pdf_content = create_test_pdf("Test list jobs")

    for i in range(3):
        pdf_file = io.BytesIO(pdf_content)
        client.post(
            "/documents?async_processing=true",
            files={"file": (f"test_list_{i}.pdf", pdf_file, "application/pdf")}
        )

    # List jobs
    response = client.get("/documents/jobs/")

    assert response.status_code == 200
    data = response.json()

    assert "jobs" in data
    assert "total" in data
    assert len(data["jobs"]) >= 3  # At least the 3 we just created
    assert data["total"] >= 3


def test_list_jobs_with_status_filter(client: TestClient, db_session: Session):
    """Test listing jobs filtered by status"""

    # Create a job
    pdf_content = create_test_pdf("Test filter jobs")
    pdf_file = io.BytesIO(pdf_content)

    client.post(
        "/documents?async_processing=true",
        files={"file": ("test_filter.pdf", pdf_file, "application/pdf")}
    )

    # List jobs with status=queued
    response = client.get("/documents/jobs/?status=queued")

    assert response.status_code == 200
    data = response.json()

    # All returned jobs should have status=queued
    for job in data["jobs"]:
        assert job["status"] == "queued"


def test_async_upload_with_metadata(client: TestClient, db_session: Session):
    """Test async upload with custom metadata"""

    pdf_content = create_test_pdf("Test async with metadata")
    pdf_file = io.BytesIO(pdf_content)

    metadata = {
        "department": "Engineering",
        "grade": "GG11",
        "type": "job_description"
    }

    response = client.post(
        "/documents?async_processing=true",
        files={"file": ("test_metadata.pdf", pdf_file, "application/pdf")},
        data={"metadata": str(metadata).replace("'", '"')}
    )

    assert response.status_code == 201
    job_id = response.json()["job_id"]

    # Verify metadata was stored in job
    job = db_session.query(DocumentProcessingJob).filter(
        DocumentProcessingJob.job_id == job_id
    ).first()

    assert job.doc_metadata == metadata


def test_duplicate_document_async(client: TestClient, db_session: Session):
    """Test that duplicate documents are rejected even in async mode"""

    pdf_content = create_test_pdf("Test duplicate async")

    # Upload first time (sync mode to complete it)
    pdf_file1 = io.BytesIO(pdf_content)
    response1 = client.post(
        "/documents",
        files={"file": ("test_dup_async.pdf", pdf_file1, "application/pdf")}
    )
    assert response1.status_code == 201

    # Upload second time (async mode)
    pdf_file2 = io.BytesIO(pdf_content)
    response2 = client.post(
        "/documents?async_processing=true",
        files={"file": ("test_dup_async.pdf", pdf_file2, "application/pdf")}
    )

    # Should be rejected immediately (before job creation)
    assert response2.status_code == 409
    assert "already exists" in response2.json()["detail"]

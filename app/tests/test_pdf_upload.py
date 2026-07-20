"""Test PDF upload endpoints"""

import pytest
import io
from PyPDF2 import PdfWriter


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


def test_upload_pdf_success(client, db_session):
    """Test successful PDF upload"""
    # Create a test PDF
    pdf_content = create_test_pdf("This is a test document about vacation policy.")

    # Upload
    response = client.post(
        "/documents/",
        files={"file": ("test.pdf", pdf_content, "application/pdf")}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "test.pdf"
    assert data["page_count"] == 1
    assert data["id"] is not None
    assert data["chunk_count"] > 0


def test_upload_non_pdf_fails(client):
    """Test uploading non-PDF file fails"""
    response = client.post(
        "/documents/",
        files={"file": ("test.txt", b"plain text", "text/plain")}
    )

    assert response.status_code == 400
    assert "PDF" in response.json()["detail"]


def test_list_documents(client, db_session):
    """Test listing documents"""
    # Upload a test document first
    pdf_content = create_test_pdf()
    client.post(
        "/documents/",
        files={"file": ("test1.pdf", pdf_content, "application/pdf")}
    )

    # List documents
    response = client.get("/documents/")

    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert "total" in data
    assert data["total"] >= 1
    assert len(data["documents"]) >= 1


def test_get_document(client, db_session):
    """Test getting a specific document"""
    # Upload a test document
    pdf_content = create_test_pdf()
    upload_response = client.post(
        "/documents/",
        files={"file": ("test.pdf", pdf_content, "application/pdf")}
    )
    doc_id = upload_response.json()["id"]

    # Get the document
    response = client.get(f"/documents/{doc_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == doc_id
    assert data["filename"] == "test.pdf"


def test_get_nonexistent_document(client):
    """Test getting a document that doesn't exist"""
    response = client.get("/documents/99999")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_delete_document(client, db_session):
    """Test deleting a document"""
    # Upload a test document
    pdf_content = create_test_pdf()
    upload_response = client.post(
        "/documents/",
        files={"file": ("test.pdf", pdf_content, "application/pdf")}
    )
    doc_id = upload_response.json()["id"]

    # Delete the document
    response = client.delete(f"/documents/{doc_id}")

    assert response.status_code == 204

    # Verify it's deleted
    get_response = client.get(f"/documents/{doc_id}")
    assert get_response.status_code == 404


def test_delete_nonexistent_document(client):
    """Test deleting a document that doesn't exist"""
    response = client.delete("/documents/99999")

    assert response.status_code == 404

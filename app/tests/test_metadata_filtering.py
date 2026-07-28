"""Tests for Feature 10: Advanced Filters & Metadata"""

import pytest
import json
import io


def create_test_pdf(title: str, text: str) -> bytes:
    """Create a simple test PDF in memory"""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.drawString(100, 750, title)
    pdf.drawString(100, 720, text)
    pdf.showPage()
    pdf.save()

    buffer.seek(0)
    return buffer.getvalue()


def test_upload_document_with_metadata(client, db_session):
    """Test uploading a document with custom metadata"""
    # Create test PDF
    pdf_content = create_test_pdf("Test Document", "This is a test document for metadata.")

    # Create metadata
    metadata = {
        "department": "HR",
        "grade": "9-12",
        "type": "policy",
        "tags": ["employee", "handbook"]
    }

    # Upload document with metadata
    response = client.post(
        "/documents/",
        files={"file": ("test.pdf", pdf_content, "application/pdf")},
        data={"metadata": json.dumps(metadata)}
    )

    assert response.status_code == 201
    data = response.json()

    # Verify metadata is returned
    assert data["doc_metadata"] == metadata
    assert data["filename"] == "test.pdf"
    assert data["chunk_count"] > 0


def test_upload_document_without_metadata(client, db_session):
    """Test uploading a document without metadata (should use empty dict as default)"""
    pdf_content = create_test_pdf("Test Document", "This is a test document.")

    response = client.post(
        "/documents/",
        files={"file": ("test.pdf", pdf_content, "application/pdf")}
    )

    assert response.status_code == 201
    data = response.json()

    # Verify metadata defaults to empty dict
    assert data["doc_metadata"] == {}


def test_upload_document_with_invalid_metadata_json(client, db_session):
    """Test uploading a document with invalid JSON metadata"""
    pdf_content = create_test_pdf("Test Document", "This is a test document.")

    response = client.post(
        "/documents/",
        files={"file": ("test.pdf", pdf_content, "application/pdf")},
        data={"metadata": "not-valid-json"}
    )

    assert response.status_code == 400
    assert "Invalid metadata JSON format" in response.json()["detail"]


def test_update_document_metadata(client, db_session):
    """Test updating document metadata using PATCH endpoint"""
    # First, upload a document
    pdf_content = create_test_pdf("Test Document", "This is a test document.")
    initial_metadata = {"department": "HR"}

    upload_response = client.post(
        "/documents/",
        files={"file": ("test.pdf", pdf_content, "application/pdf")},
        data={"metadata": json.dumps(initial_metadata)}
    )

    assert upload_response.status_code == 201
    doc_id = upload_response.json()["id"]

    # Update metadata
    update_metadata = {
        "grade": "9-12",
        "type": "policy"
    }

    patch_response = client.patch(
        f"/documents/{doc_id}",
        json={"doc_metadata": update_metadata}
    )

    assert patch_response.status_code == 200
    updated_data = patch_response.json()

    # Verify metadata was merged (not replaced)
    expected_metadata = {**initial_metadata, **update_metadata}
    assert updated_data["doc_metadata"] == expected_metadata


def test_list_documents_with_metadata_filter(client, db_session):
    """Test filtering documents by metadata in GET /documents endpoint"""
    # Upload multiple documents with different metadata
    documents = [
        ("hr_policy.pdf", {"department": "HR", "grade": "9-12"}),
        ("it_policy.pdf", {"department": "IT", "grade": "9-12"}),
        ("hr_handbook.pdf", {"department": "HR", "grade": "K-8"}),
    ]

    for filename, metadata in documents:
        pdf_content = create_test_pdf(filename, f"Content for {filename}")
        client.post(
            "/documents/",
            files={"file": (filename, pdf_content, "application/pdf")},
            data={"metadata": json.dumps(metadata)}
        )

    # Filter by department=HR
    response = client.get(
        "/documents/",
        params={"metadata_filters": json.dumps({"department": "HR"})}
    )

    assert response.status_code == 200
    data = response.json()

    # Should return 2 HR documents
    assert data["total"] == 2
    assert all(doc["doc_metadata"]["department"] == "HR" for doc in data["documents"])


def test_list_documents_with_multiple_metadata_filters(client, db_session):
    """Test filtering documents by multiple metadata fields"""
    # Upload documents
    documents = [
        ("hr_high_school.pdf", {"department": "HR", "grade": "9-12"}),
        ("it_high_school.pdf", {"department": "IT", "grade": "9-12"}),
        ("hr_elementary.pdf", {"department": "HR", "grade": "K-8"}),
    ]

    for filename, metadata in documents:
        pdf_content = create_test_pdf(filename, f"Content for {filename}")
        client.post(
            "/documents/",
            files={"file": (filename, pdf_content, "application/pdf")},
            data={"metadata": json.dumps(metadata)}
        )

    # Filter by department=HR AND grade=9-12
    response = client.get(
        "/documents/",
        params={"metadata_filters": json.dumps({"department": "HR", "grade": "9-12"})}
    )

    assert response.status_code == 200
    data = response.json()

    # Should return only 1 document
    assert data["total"] == 1
    assert data["documents"][0]["filename"] == "hr_high_school.pdf"


def test_list_documents_with_invalid_metadata_filter(client, db_session):
    """Test that invalid JSON in metadata_filters returns 400"""
    response = client.get(
        "/documents/",
        params={"metadata_filters": "not-valid-json"}
    )

    assert response.status_code == 400
    assert "Invalid metadata_filters JSON format" in response.json()["detail"]


def test_ask_question_with_metadata_filter(client, db_session):
    """Test filtering chunks by metadata when asking questions"""
    # Upload two documents with different metadata
    hr_content = create_test_pdf("HR Policy", "Vacation policy: 15 days per year for HR employees.")
    it_content = create_test_pdf("IT Policy", "Vacation policy: 20 days per year for IT employees.")

    client.post(
        "/documents/",
        files={"file": ("hr_policy.pdf", hr_content, "application/pdf")},
        data={"metadata": json.dumps({"department": "HR"})}
    )

    client.post(
        "/documents/",
        files={"file": ("it_policy.pdf", it_content, "application/pdf")},
        data={"metadata": json.dumps({"department": "IT"})}
    )

    # Ask question filtered by department=HR
    response = client.post(
        "/ask/",
        json={
            "question": "What is the vacation policy?",
            "metadata_filters": {"department": "HR"},
            "top_k": 5
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Verify answer only includes HR sources
    if data["sources"]:
        assert all("hr_policy.pdf" in source["filename"].lower() for source in data["sources"])
        # Answer should mention 15 days (HR) not 20 days (IT)
        assert "15" in data["answer"] or data["answer"] == "not_found - This question cannot be answered from the uploaded documents."


def test_ask_question_without_metadata_filter(client, db_session):
    """Test that questions without filters search all documents"""
    # Upload documents with metadata
    hr_content = create_test_pdf("HR Policy", "HR vacation policy information.")
    it_content = create_test_pdf("IT Policy", "IT vacation policy information.")

    client.post(
        "/documents/",
        files={"file": ("hr_policy.pdf", hr_content, "application/pdf")},
        data={"metadata": json.dumps({"department": "HR"})}
    )

    client.post(
        "/documents/",
        files={"file": ("it_policy.pdf", it_content, "application/pdf")},
        data={"metadata": json.dumps({"department": "IT"})}
    )

    # Ask question without filter
    response = client.post(
        "/ask/",
        json={
            "question": "What is the vacation policy?",
            "top_k": 10
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Should search both documents
    assert response.status_code == 200


def test_get_document_returns_metadata(client, db_session):
    """Test that GET /documents/{id} returns metadata"""
    # Upload document with metadata
    pdf_content = create_test_pdf("Test Doc", "Content")
    metadata = {"department": "HR", "type": "policy"}

    upload_response = client.post(
        "/documents/",
        files={"file": ("test.pdf", pdf_content, "application/pdf")},
        data={"metadata": json.dumps(metadata)}
    )

    doc_id = upload_response.json()["id"]

    # Get document by ID
    get_response = client.get(f"/documents/{doc_id}")

    assert get_response.status_code == 200
    data = get_response.json()
    assert data["doc_metadata"] == metadata


def test_metadata_persists_across_operations(client, db_session):
    """Test that metadata persists correctly through various operations"""
    # Upload with metadata
    pdf_content = create_test_pdf("Test Doc", "Content")
    initial_metadata = {"department": "HR", "version": "1.0"}

    upload_response = client.post(
        "/documents/",
        files={"file": ("test.pdf", pdf_content, "application/pdf")},
        data={"metadata": json.dumps(initial_metadata)}
    )

    doc_id = upload_response.json()["id"]

    # Update metadata
    client.patch(
        f"/documents/{doc_id}",
        json={"doc_metadata": {"version": "2.0", "reviewed": True}}
    )

    # List all documents
    list_response = client.get("/documents/")
    found_doc = next(doc for doc in list_response.json()["documents"] if doc["id"] == doc_id)

    # Verify merged metadata
    expected = {"department": "HR", "version": "2.0", "reviewed": True}
    assert found_doc["doc_metadata"] == expected

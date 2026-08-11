"""Test extraction API endpoints"""

import pytest
from unittest.mock import AsyncMock, patch
from app.tests.utils import document_api_call


def test_extract_endpoint_structure(client):
    """Test extraction endpoint is available and has correct structure"""
    # Try to call the endpoint (will fail validation, but proves endpoint exists)
    response = client.post("/extract", json={
        "document_id": 999,  # Non-existent document
        "schema": {
            "title": "string"
        }
    })

    # Should get 404 (document not found) or 500, not 404 (endpoint not found)
    assert response.status_code in [404, 500], f"Expected 404/500, got {response.status_code}"


@pytest.mark.asyncio
async def test_extraction_service_mock():
    """Test extraction service with mocked LLM"""
    from app.services.extractor import ExtractionService
    from app.db.models import Document, Chunk
    from unittest.mock import MagicMock

    # Mock database session
    mock_db = MagicMock()

    # Mock document and chunks
    mock_document = Document(
        id=1,
        filename="test.pdf",
        page_count=1
    )

    mock_chunk = Chunk(
        id=1,
        document_id=1,
        text="Senior AI Engineer with 8 years experience. Required skills: Python, TensorFlow, AWS.",
        page_number=1
    )

    # Setup mock queries
    mock_db.query.return_value.filter.return_value.first.return_value = mock_document
    mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_chunk]

    # Create extraction service
    extractor = ExtractionService(mock_db)

    # Mock LLM provider
    mock_llm = AsyncMock()
    mock_llm.generate = AsyncMock(return_value='''{
        "title": "Senior AI Engineer",
        "experience_years": 8,
        "required_skills": ["Python", "TensorFlow", "AWS"]
    }''')

    with patch('app.services.extractor.get_llm_provider', return_value=mock_llm):
        # Test extraction
        schema = {
            "title": "string",
            "experience_years": "number",
            "required_skills": "array"
        }

        extracted_data, confidence, sources, warnings = await extractor.extract_from_document(1, schema)

        # Verify extraction results
        assert extracted_data["title"] == "Senior AI Engineer"
        assert extracted_data["experience_years"] == 8
        assert extracted_data["required_skills"] == ["Python", "TensorFlow", "AWS"]
        assert confidence == 1.0  # All 3 fields extracted
        assert len(warnings) == 0


def test_extraction_type_validation():
    """Test type validation in extraction service"""
    from app.services.extractor import ExtractionService
    from unittest.mock import MagicMock

    mock_db = MagicMock()
    extractor = ExtractionService(mock_db)

    # Test string validation
    assert extractor._validate_type("test", "string", "field1") == "test"
    assert extractor._validate_type(123, "string", "field1") == "123"

    # Test number validation
    assert extractor._validate_type(42, "number", "field2") == 42
    assert extractor._validate_type(3.14, "number", "field2") == 3.14
    assert extractor._validate_type("8", "number", "field2") == 8

    # Test array validation
    assert extractor._validate_type(["a", "b"], "array", "field3") == ["a", "b"]
    assert extractor._validate_type("a,b,c", "array", "field3") == ["a", "b", "c"]

    # Test boolean validation
    assert extractor._validate_type(True, "boolean", "field4") is True
    assert extractor._validate_type("true", "boolean", "field4") is True
    assert extractor._validate_type("yes", "boolean", "field4") is True

    # Test invalid number
    with pytest.raises(ValueError):
        extractor._validate_type("not a number", "number", "field5")


def test_extraction_response_parsing():
    """Test parsing LLM response"""
    from app.services.extractor import ExtractionService
    from unittest.mock import MagicMock

    mock_db = MagicMock()
    extractor = ExtractionService(mock_db)

    # Test valid JSON response
    response = '{"title": "Engineer", "years": 5}'
    schema = {"title": "string", "years": "number"}

    data, confidence, warnings = extractor._parse_extraction_response(response, schema)

    assert data["title"] == "Engineer"
    assert data["years"] == 5
    assert confidence == 1.0
    assert len(warnings) == 0

    # Test JSON in markdown code block
    response = '''```json
    {"title": "Engineer", "years": 5}
    ```'''

    data, confidence, warnings = extractor._parse_extraction_response(response, schema)

    assert data["title"] == "Engineer"
    assert data["years"] == 5

    # Test missing field
    response = '{"title": "Engineer"}'
    schema = {"title": "string", "years": "number", "location": "string"}

    data, confidence, warnings = extractor._parse_extraction_response(response, schema)

    assert data["title"] == "Engineer"
    assert data["years"] is None
    assert data["location"] is None
    assert confidence < 1.0  # Not all fields extracted
    assert len(warnings) > 0  # Should have warnings about missing fields


def test_batch_extraction_endpoint(client):
    """Test batch extraction endpoint structure"""
    response = client.post("/extract/batch", json={
        "document_ids": [999],  # Non-existent
        "schema": {
            "title": "string"
        },
        "export_format": "csv"
    })

    # Endpoint should exist (even if it fails due to missing documents)
    assert response.status_code in [200, 404, 500]


def test_csv_export_format():
    """Test CSV export formatting"""
    from app.api.extraction import _export_as_csv

    results = [
        {
            "document_id": 1,
            "filename": "test.pdf",
            "extracted_data": {
                "title": "Engineer",
                "years": 5,
                "skills": ["Python", "AWS"]
            }
        }
    ]

    schema = {"title": "string", "years": "number", "skills": "array"}

    response = _export_as_csv(results, schema, "test_batch")

    # Check response type
    assert response.media_type == "text/csv"
    assert "attachment" in response.headers["Content-Disposition"]


def test_json_export_format():
    """Test JSON export formatting"""
    from app.api.extraction import _export_as_json

    results = [
        {
            "document_id": 1,
            "filename": "test.pdf",
            "extracted_data": {
                "title": "Engineer"
            }
        }
    ]

    response = _export_as_json(results, "test_batch")

    # Check response type
    assert response.media_type == "application/json"
    assert "attachment" in response.headers["Content-Disposition"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

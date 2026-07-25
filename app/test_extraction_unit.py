"""Unit tests for extraction feature (no dependencies)"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_type_validation():
    """Test type validation logic"""
    from services.extractor import ExtractionService
    from unittest.mock import MagicMock

    mock_db = MagicMock()
    extractor = ExtractionService(mock_db)

    print("Testing Type Validation...")
    print("-" * 60)

    # Test string
    result = extractor._validate_type("hello", "string", "field1")
    assert result == "hello", f"String validation failed: {result}"
    print("✅ String validation: PASS")

    # Test number (int)
    result = extractor._validate_type(42, "number", "field2")
    assert result == 42, f"Number (int) validation failed: {result}"
    print("✅ Number (int) validation: PASS")

    # Test number (float)
    result = extractor._validate_type(3.14, "number", "field3")
    assert result == 3.14, f"Number (float) validation failed: {result}"
    print("✅ Number (float) validation: PASS")

    # Test number from string
    result = extractor._validate_type("8", "number", "field4")
    assert result == 8, f"Number from string validation failed: {result}"
    print("✅ Number from string validation: PASS")

    # Test array
    result = extractor._validate_type(["a", "b", "c"], "array", "field5")
    assert result == ["a", "b", "c"], f"Array validation failed: {result}"
    print("✅ Array validation: PASS")

    # Test array from comma-separated string
    result = extractor._validate_type("Python, AWS, Docker", "array", "field6")
    assert result == ["Python", "AWS", "Docker"], f"Array from string validation failed: {result}"
    print("✅ Array from string validation: PASS")

    # Test boolean
    result = extractor._validate_type(True, "boolean", "field7")
    assert result is True, f"Boolean validation failed: {result}"
    print("✅ Boolean (True) validation: PASS")

    result = extractor._validate_type("yes", "boolean", "field8")
    assert result is True, f"Boolean from 'yes' validation failed: {result}"
    print("✅ Boolean from string validation: PASS")

    # Test object (dict)
    result = extractor._validate_type({"key": "value"}, "object", "field9")
    assert result == {"key": "value"}, f"Object validation failed: {result}"
    print("✅ Object validation: PASS")

    print("\n✅ All type validation tests passed!\n")


def test_response_parsing():
    """Test LLM response parsing"""
    from services.extractor import ExtractionService
    from unittest.mock import MagicMock

    mock_db = MagicMock()
    extractor = ExtractionService(mock_db)

    print("Testing Response Parsing...")
    print("-" * 60)

    # Test 1: Plain JSON response
    response = '{"title": "Senior Engineer", "years": 8, "skills": ["Python", "AWS"]}'
    schema = {"title": "string", "years": "number", "skills": "array"}

    data, confidence, warnings = extractor._parse_extraction_response(response, schema)

    assert data["title"] == "Senior Engineer"
    assert data["years"] == 8
    assert data["skills"] == ["Python", "AWS"]
    assert confidence == 1.0
    print("✅ Plain JSON parsing: PASS")

    # Test 2: JSON in markdown code block
    response = '''```json
{
    "title": "Engineer",
    "years": 5,
    "skills": ["Python"]
}
```'''
    schema = {"title": "string", "years": "number", "skills": "array"}

    data, confidence, warnings = extractor._parse_extraction_response(response, schema)

    assert data["title"] == "Engineer"
    assert data["years"] == 5
    assert data["skills"] == ["Python"]
    print("✅ Markdown JSON parsing: PASS")

    # Test 3: Missing fields
    response = '{"title": "Engineer"}'
    schema = {"title": "string", "years": "number", "location": "string"}

    data, confidence, warnings = extractor._parse_extraction_response(response, schema)

    assert data["title"] == "Engineer"
    assert data["years"] is None
    assert data["location"] is None
    assert confidence < 1.0
    assert len(warnings) > 0
    print("✅ Missing fields handling: PASS")
    print(f"   Confidence: {confidence:.2%}")
    print(f"   Warnings: {len(warnings)}")

    print("\n✅ All response parsing tests passed!\n")


def test_prompt_generation():
    """Test extraction prompt generation"""
    from services.extractor import ExtractionService
    from unittest.mock import MagicMock

    mock_db = MagicMock()
    extractor = ExtractionService(mock_db)

    print("Testing Prompt Generation...")
    print("-" * 60)

    schema = {
        "title": "string",
        "experience_years": "number",
        "required_skills": "array"
    }

    document_text = "Senior AI Engineer with 8 years of experience. Skills: Python, TensorFlow."

    prompt = extractor._build_extraction_prompt(schema, document_text)

    # Verify prompt contains key elements
    assert "title: string" in prompt
    assert "experience_years: number" in prompt
    assert "required_skills: array" in prompt
    assert document_text in prompt
    assert "JSON" in prompt

    print("✅ Prompt generation: PASS")
    print(f"   Prompt length: {len(prompt)} characters")
    print(f"   Contains schema: ✓")
    print(f"   Contains document: ✓")
    print(f"   Contains instructions: ✓")

    print("\n✅ Prompt generation test passed!\n")


def test_schemas():
    """Test pydantic schemas"""
    from schemas.extraction import (
        ExtractionRequest,
        ExtractionResponse,
        BatchExtractionRequest,
        FieldSource
    )

    print("Testing Pydantic Schemas...")
    print("-" * 60)

    # Test ExtractionRequest
    request = ExtractionRequest(
        document_id=1,
        schema={"title": "string", "years": "number"}
    )
    assert request.document_id == 1
    assert request.schema == {"title": "string", "years": "number"}
    print("✅ ExtractionRequest schema: PASS")

    # Test FieldSource
    source = FieldSource(page=1, field="title")
    assert source.page == 1
    assert source.field == "title"
    print("✅ FieldSource schema: PASS")

    # Test ExtractionResponse
    response = ExtractionResponse(
        document_id=1,
        extracted_data={"title": "Engineer"},
        confidence=0.95,
        sources=[FieldSource(page=1, field="title")],
        warnings=[]
    )
    assert response.confidence == 0.95
    assert len(response.sources) == 1
    print("✅ ExtractionResponse schema: PASS")

    # Test BatchExtractionRequest
    batch_request = BatchExtractionRequest(
        document_ids=[1, 2, 3],
        schema={"title": "string"},
        export_format="csv"
    )
    assert len(batch_request.document_ids) == 3
    assert batch_request.export_format == "csv"
    print("✅ BatchExtractionRequest schema: PASS")

    print("\n✅ All schema tests passed!\n")


if __name__ == "__main__":
    print("=" * 60)
    print("EXTRACTION FEATURE - UNIT TESTS")
    print("=" * 60)
    print()

    try:
        test_schemas()
        test_type_validation()
        test_response_parsing()
        test_prompt_generation()

        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print()
        print("Summary:")
        print("  - Schema validation: ✓")
        print("  - Type conversion: ✓")
        print("  - Response parsing: ✓")
        print("  - Prompt generation: ✓")
        print()
        print("Feature 08 is ready for production!")
        print()

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)

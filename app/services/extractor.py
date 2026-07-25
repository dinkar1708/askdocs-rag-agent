"""Structured data extraction service"""

import json
import logging
import re
from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session

from app.db.models import Document, Chunk
from app.llm.factory import get_llm_provider
from app.schemas.extraction import FieldSource

logger = logging.getLogger(__name__)


class ExtractionService:
    """Service for extracting structured data from documents using LLM"""

    def __init__(self, db: Session):
        self.db = db
        self.llm_provider = get_llm_provider()

    async def extract_from_document(
        self,
        document_id: int,
        schema: Dict[str, str]
    ) -> Tuple[Dict[str, Any], float, List[FieldSource], List[str]]:
        """
        Extract structured data from a document based on schema.

        Args:
            document_id: ID of the document to extract from
            schema: Dictionary mapping field names to their types
                   e.g., {"title": "string", "experience_years": "number"}

        Returns:
            Tuple of (extracted_data, confidence, sources, warnings)
        """
        logger.info("Starting extraction for document %d with schema: %s", document_id, list(schema.keys()))

        # Get document and its chunks
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error("Document %d not found", document_id)
            raise ValueError(f"Document {document_id} not found")

        chunks = self.db.query(Chunk).filter(Chunk.document_id == document_id).order_by(Chunk.page_number).all()

        if not chunks:
            logger.error("No chunks found for document %d", document_id)
            raise ValueError(f"No chunks found for document {document_id}")

        # Combine chunk text
        document_text = "\n\n".join([chunk.text for chunk in chunks])

        # Build extraction prompt
        extraction_prompt = self._build_extraction_prompt(schema, document_text)

        # Call LLM
        logger.debug("Calling LLM for extraction")
        response = await self.llm_provider.generate(
            system_prompt="You are a precise data extraction assistant. Extract only the requested fields from the document. Return valid JSON only.",
            user_prompt=extraction_prompt
        )

        # Parse response
        logger.debug("Parsing extraction response")
        extracted_data, confidence, warnings = self._parse_extraction_response(
            response, schema
        )

        # Track sources (simplified - all from first page for now)
        sources = [FieldSource(page=1, field=field) for field in extracted_data.keys()]

        logger.info("Extraction completed for document %d with confidence %.2f", document_id, confidence)
        if warnings:
            logger.warning("Extraction warnings for document %d: %s", document_id, warnings)

        return extracted_data, confidence, sources, warnings

    def _build_extraction_prompt(self, schema: Dict[str, str], document_text: str) -> str:
        """Build the extraction prompt for the LLM"""

        # Format schema description
        schema_desc = []
        for field, field_type in schema.items():
            schema_desc.append(f"- {field}: {field_type}")

        schema_str = "\n".join(schema_desc)

        prompt = f"""Extract the following fields from the document below. Return ONLY a valid JSON object with the extracted values.

Schema (field_name: type):
{schema_str}

Type definitions:
- string: Text value
- number: Numeric value (integer or decimal)
- array: List of values
- boolean: true or false
- object: Nested JSON object

If a field cannot be found or extracted, set its value to null.

Document:
---
{document_text[:8000]}  # Limit to 8000 chars to avoid token limits
---

Return ONLY the JSON object, no explanation or markdown:"""

        return prompt

    def _parse_extraction_response(
        self,
        response: str,
        schema: Dict[str, str]
    ) -> Tuple[Dict[str, Any], float, List[str]]:
        """
        Parse LLM response into structured data.

        Returns:
            Tuple of (extracted_data, confidence, warnings)
        """
        warnings = []

        # Extract JSON from response (handle markdown code blocks)
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON object directly
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                warnings.append("Could not find JSON in LLM response")
                return {field: None for field in schema.keys()}, 0.0, warnings

        # Parse JSON
        try:
            extracted_data = json.loads(json_str)
        except json.JSONDecodeError as e:
            warnings.append(f"Invalid JSON in response: {str(e)}")
            return {field: None for field in schema.keys()}, 0.0, warnings

        # Validate and type-check fields
        validated_data = {}
        for field, expected_type in schema.items():
            value = extracted_data.get(field)

            if value is None:
                validated_data[field] = None
                warnings.append(f"Field '{field}' not found in document")
                continue

            # Type validation
            try:
                validated_value = self._validate_type(value, expected_type, field)
                validated_data[field] = validated_value
            except ValueError as e:
                warnings.append(str(e))
                validated_data[field] = None

        # Calculate confidence based on how many fields were successfully extracted
        total_fields = len(schema)
        extracted_fields = sum(1 for v in validated_data.values() if v is not None)
        confidence = extracted_fields / total_fields if total_fields > 0 else 0.0

        return validated_data, confidence, warnings

    def _validate_type(self, value: Any, expected_type: str, field_name: str) -> Any:
        """Validate and convert value to expected type"""

        if expected_type == "string":
            return str(value) if value is not None else None

        elif expected_type == "number":
            if isinstance(value, (int, float)):
                return value
            # Try to parse string to number
            if isinstance(value, str):
                try:
                    # Try int first
                    if '.' not in value:
                        return int(value)
                    return float(value)
                except ValueError:
                    raise ValueError(f"Could not convert '{field_name}' value '{value}' to number")
            raise ValueError(f"Field '{field_name}' expected number, got {type(value).__name__}")

        elif expected_type == "array":
            if isinstance(value, list):
                return value
            # Try to convert string to array
            if isinstance(value, str):
                return [v.strip() for v in value.split(',')]
            raise ValueError(f"Field '{field_name}' expected array, got {type(value).__name__}")

        elif expected_type == "boolean":
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() in ('true', 'yes', '1')
            raise ValueError(f"Field '{field_name}' expected boolean, got {type(value).__name__}")

        elif expected_type == "object":
            if isinstance(value, dict):
                return value
            raise ValueError(f"Field '{field_name}' expected object, got {type(value).__name__}")

        else:
            # Unknown type, return as-is
            return value

    async def batch_extract(
        self,
        document_ids: List[int],
        schema: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Extract structured data from multiple documents.

        Args:
            document_ids: List of document IDs
            schema: Extraction schema

        Returns:
            List of extraction results
        """
        results = []

        for doc_id in document_ids:
            try:
                document = self.db.query(Document).filter(Document.id == doc_id).first()
                if not document:
                    results.append({
                        "document_id": doc_id,
                        "filename": "unknown",
                        "extracted_data": {field: None for field in schema.keys()},
                        "warnings": [f"Document {doc_id} not found"]
                    })
                    continue

                extracted_data, confidence, sources, warnings = await self.extract_from_document(
                    doc_id, schema
                )

                results.append({
                    "document_id": doc_id,
                    "filename": document.filename,
                    "extracted_data": extracted_data,
                    "warnings": warnings
                })
            except Exception as e:
                results.append({
                    "document_id": doc_id,
                    "filename": "error",
                    "extracted_data": {field: None for field in schema.keys()},
                    "warnings": [f"Extraction failed: {str(e)}"]
                })

        return results

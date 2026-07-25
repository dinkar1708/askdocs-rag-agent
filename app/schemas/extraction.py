"""Extraction schemas for structured data extraction"""

from pydantic import BaseModel
from typing import Dict, Any, List, Optional


class ExtractionSchema(BaseModel):
    """
    Schema defining fields to extract from documents.

    Example:
        {
            "title": "string",
            "experience_years": "number",
            "required_skills": "array",
            "remote_eligible": "boolean"
        }
    """
    pass  # This is a flexible dict, validated as Dict[str, str]


class FieldSource(BaseModel):
    """Source information for an extracted field"""
    page: int
    field: str


class ExtractionRequest(BaseModel):
    """Request for extracting structured data from a document"""
    document_id: int
    schema: Dict[str, str]  # field_name -> type mapping

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": 1,
                "schema": {
                    "title": "string",
                    "experience_years": "number",
                    "required_skills": "array",
                    "location": "string"
                }
            }
        }


class ExtractionResponse(BaseModel):
    """Response containing extracted structured data"""
    document_id: int
    extracted_data: Dict[str, Any]
    confidence: float
    sources: List[FieldSource]
    warnings: List[str] = []

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": 1,
                "extracted_data": {
                    "title": "Senior AI Engineer (GG11)",
                    "experience_years": 8,
                    "required_skills": ["Python", "Machine Learning", "AWS"],
                    "location": "Remote / New York"
                },
                "confidence": 0.92,
                "sources": [
                    {"page": 1, "field": "title"},
                    {"page": 1, "field": "experience_years"},
                    {"page": 2, "field": "required_skills"}
                ],
                "warnings": []
            }
        }


class BatchExtractionRequest(BaseModel):
    """Request for batch extraction from multiple documents"""
    document_ids: List[int]
    schema: Dict[str, str]
    export_format: Optional[str] = "json"  # csv, xlsx, or json

    class Config:
        json_schema_extra = {
            "example": {
                "document_ids": [1, 2, 3],
                "schema": {
                    "title": "string",
                    "experience_years": "number",
                    "required_skills": "array"
                },
                "export_format": "csv"
            }
        }


class BatchExtractionResult(BaseModel):
    """Single document result in batch extraction"""
    document_id: int
    filename: str
    extracted_data: Dict[str, Any]
    warnings: List[str] = []


class BatchExtractionResponse(BaseModel):
    """Response for batch extraction"""
    batch_id: str
    results: List[BatchExtractionResult]
    total: int
    export_url: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "batch_id": "batch_abc123",
                "results": [
                    {
                        "document_id": 1,
                        "filename": "job_gg11.pdf",
                        "extracted_data": {
                            "title": "Senior AI Engineer (GG11)",
                            "experience_years": 8,
                            "required_skills": ["Python", "ML", "AWS"]
                        },
                        "warnings": []
                    }
                ],
                "total": 1,
                "export_url": "/extract/batch/export/batch_abc123.csv"
            }
        }

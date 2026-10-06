"""Comparative Analysis schemas"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class ComparisonRequest(BaseModel):
    """Request schema for comparing multiple documents"""
    question: Optional[str] = Field(
        default=None,
        description="Optional comparative question (e.g. 'Compare experience requirements')"
    )
    document_ids: List[int] = Field(
        ...,
        min_length=2,
        max_length=5,
        description="List of document IDs to compare (2 to 5 documents)"
    )
    aspects: List[str] = Field(
        ...,
        min_length=1,
        description="List of aspects/fields to compare across documents (e.g. ['experience', 'skills'])"
    )


class DocumentAspectData(BaseModel):
    """Aspect data extracted for a single document"""
    document_id: int = Field(..., description="Document ID")
    filename: str = Field(..., description="Document filename")
    data: Dict[str, Any] = Field(default_factory=dict, description="Extracted values for each aspect")


class ComparisonData(BaseModel):
    """Structured side-by-side comparison dataset"""
    aspects: List[str] = Field(..., description="Aspects compared")
    documents: List[DocumentAspectData] = Field(..., description="Extracted aspect data per document")


class ComparisonResponse(BaseModel):
    """Response schema for document comparison"""
    comparison: ComparisonData = Field(..., description="Side-by-side extracted data")
    differences: Dict[str, Any] = Field(
        default_factory=dict,
        description="Identified differences, commonalities, and trends per aspect"
    )
    summary: str = Field(..., description="High-level narrative synthesis of the comparison")


class TableComparisonRequest(BaseModel):
    """Request schema for generating a Markdown comparison table"""
    document_ids: List[int] = Field(
        ...,
        min_length=2,
        max_length=5,
        description="List of document IDs to compare"
    )
    aspects: List[str] = Field(
        ...,
        min_length=1,
        description="Aspects to include as rows in the comparison table"
    )


class TableComparisonResponse(BaseModel):
    """Response schema for Markdown table comparison"""
    markdown_table: str = Field(..., description="Formatted GitHub Markdown table")
    aspects: List[str] = Field(..., description="Aspects included in the table")
    documents: List[DocumentAspectData] = Field(..., description="Underlying document aspect data")


class DiffRequest(BaseModel):
    """Request schema for comparing two versions of a document on a single aspect"""
    document_ids: List[int] = Field(
        ...,
        min_length=2,
        max_length=2,
        description="Exactly two document IDs to diff"
    )
    aspect: str = Field(..., description="Specific aspect or section to diff (e.g. 'benefits', 'vacation')")


class DiffFieldChange(BaseModel):
    """Specific field difference between two documents"""
    field: str = Field(..., description="Name of changed property/field")
    doc_1_value: Any = Field(..., description="Value in first document")
    doc_2_value: Any = Field(..., description="Value in second document")
    change: Optional[str] = Field(None, description="Description or magnitude of change (e.g. '+3 days')")


class DocumentSnippet(BaseModel):
    """Document context snippet for diff comparison"""
    document_id: int = Field(..., description="Document ID")
    filename: str = Field(..., description="Document filename")
    text: str = Field(..., description="Extracted context text for the aspect")


class DiffResponse(BaseModel):
    """Response schema for fine-grained diff between two documents"""
    document_1: DocumentSnippet = Field(..., description="Context extracted from first document")
    document_2: DocumentSnippet = Field(..., description="Context extracted from second document")
    differences: List[DiffFieldChange] = Field(
        default_factory=list,
        description="List of specific field changes"
    )
    summary: Optional[str] = Field(None, description="Optional brief diff summary")

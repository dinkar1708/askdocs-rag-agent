"""Document schemas"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Dict, Any, Optional


class DocumentResponse(BaseModel):
    """Document response schema"""
    id: int
    filename: str
    page_count: int
    uploaded_at: datetime
    chunk_count: int
    doc_metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class DocumentMetadataUpdate(BaseModel):
    """Schema for updating document metadata"""
    doc_metadata: Dict[str, Any] = Field(..., description="Metadata fields to update or add")


class DocumentListResponse(BaseModel):
    """List of documents with pagination"""
    documents: List[DocumentResponse]
    total: int
    skip: int
    limit: int

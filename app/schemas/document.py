"""Document schemas"""

from pydantic import BaseModel
from datetime import datetime
from typing import List


class DocumentResponse(BaseModel):
    """Document response schema"""
    id: int
    filename: str
    page_count: int
    uploaded_at: datetime
    chunk_count: int

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """List of documents with pagination"""
    documents: List[DocumentResponse]
    total: int
    skip: int
    limit: int

"""Pydantic schemas for document processing jobs"""

from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class JobResponse(BaseModel):
    """Response for job status"""
    job_id: str
    filename: str
    status: str  # queued, extracting, chunking, embedding, storing, complete, failed
    progress: int  # 0-100
    current_stage: Optional[str] = None
    error_message: Optional[str] = None
    result_document_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JobCreateResponse(BaseModel):
    """Response after initiating document upload job"""
    job_id: str
    filename: str
    status: str
    message: str


class JobListResponse(BaseModel):
    """Response for listing jobs"""
    jobs: list[JobResponse]
    total: int

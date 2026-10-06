"""Document summarization schemas"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum


class SummaryType(str, Enum):
    """Supported summary types"""
    EXECUTIVE = "executive"
    DETAILED = "detailed"
    KEY_POINTS = "key_points"
    SECTION_SUMMARIES = "section_summaries"


class KeyPoint(BaseModel):
    """A key takeaway point with page citation"""
    point: str = Field(..., description="Key point statement")
    page: Optional[int] = Field(None, description="Page number reference")


class SectionSummary(BaseModel):
    """Summary of a specific document section"""
    section: str = Field(..., description="Section or topic name")
    summary: str = Field(..., description="Summary of the section")
    pages: List[int] = Field(default_factory=list, description="Pages covering this section")


class SummaryRequest(BaseModel):
    """Request schema for generating document summaries"""
    summary_type: str = Field(
        default="executive",
        description="Type of summary: executive, detailed, key_points, section_summaries"
    )
    max_length: Optional[int] = Field(
        default=200,
        description="Target maximum word count for summary"
    )
    focus_areas: Optional[List[str]] = Field(
        default=None,
        description="Optional list of specific topics/areas to focus on"
    )
    force_regenerate: bool = Field(
        default=False,
        description="If True, bypass cached summary and regenerate"
    )


class SummaryResponse(BaseModel):
    """Response schema for document summaries"""
    document_id: int = Field(..., description="ID of summarized document")
    filename: str = Field(..., description="Document filename")
    summary: str = Field(..., description="Generated summary text")
    summary_type: str = Field(..., description="Summary type used")
    word_count: int = Field(..., description="Word count of generated summary")
    key_points: List[KeyPoint] = Field(
        default_factory=list,
        description="Extracted key bullet points with page citations"
    )
    sections: Optional[List[SectionSummary]] = Field(
        default=None,
        description="Section-by-section breakdown (for section_summaries type)"
    )
    cached: bool = Field(
        default=False,
        description="Whether this summary was served from cache"
    )
    generated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when summary was generated"
    )


class BatchSummaryRequest(BaseModel):
    """Request schema for batch document summarization"""
    document_ids: List[int] = Field(..., min_length=1, description="List of document IDs to summarize")
    summary_type: str = Field(default="executive", description="Summary type to generate for all documents")
    max_length: Optional[int] = Field(default=200, description="Target maximum words per summary")
    focus_areas: Optional[List[str]] = Field(default=None, description="Optional focus areas")
    force_regenerate: bool = Field(default=False, description="Whether to force regeneration")


class BatchSummaryResponse(BaseModel):
    """Response schema for batch summarization"""
    summaries: List[SummaryResponse] = Field(default_factory=list)
    total_processed: int = Field(...)
    failed_document_ids: List[int] = Field(default_factory=list)

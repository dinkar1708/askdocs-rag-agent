"""Pydantic schemas for query/answer operations"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class QuestionRequest(BaseModel):
    """Request schema for asking a question"""
    question: str = Field(..., min_length=1, max_length=1000, description="User's question")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of chunks to retrieve")
    include_sources: bool = Field(default=True, description="Include source citations in response")


class SourceCitation(BaseModel):
    """Source citation for an answer"""
    chunk_id: int
    filename: str
    page_number: int
    similarity_score: float
    text_excerpt: str = Field(..., description="First 200 chars of the chunk")


class AnswerResponse(BaseModel):
    """Response schema for question answers"""
    question: str
    answer: str
    sources: List[SourceCitation]
    timestamp: datetime
    model_used: str = Field(..., description="LLM provider used (mock/gemini)")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Router metadata (intent, confidence, reason)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "question": "What is the vacation policy?",
                "answer": "Full-time employees accrue 15 days of paid vacation per year...",
                "sources": [
                    {
                        "chunk_id": 1,
                        "filename": "company_policy.pdf",
                        "page_number": 1,
                        "similarity_score": 0.87,
                        "text_excerpt": "Paid Time Off (PTO): Full-time employees accrue 15 days..."
                    }
                ],
                "timestamp": "2024-01-15T10:30:00",
                "model_used": "mock",
                "metadata": {
                    "intent": "answer",
                    "confidence": 0.87,
                    "reason": "High confidence match found"
                }
            }
        }

"""Pydantic schemas for session management"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class MessageCreate(BaseModel):
    """Schema for creating a message"""
    role: str  # 'user' or 'assistant'
    content: str
    sources: Optional[List[dict]] = None


class MessageResponse(BaseModel):
    """Schema for message response"""
    id: int
    session_id: int
    role: str
    content: str
    sources: Optional[List[dict]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SessionCreate(BaseModel):
    """Schema for creating a session"""
    pass  # No required fields, sessions are created empty


class SessionResponse(BaseModel):
    """Schema for session response"""
    id: int
    created_at: datetime
    last_accessed: datetime
    message_count: int

    class Config:
        from_attributes = True


class SessionWithMessages(BaseModel):
    """Schema for session with full conversation history"""
    id: int
    created_at: datetime
    last_accessed: datetime
    messages: List[MessageResponse]

    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    """Schema for listing sessions"""
    sessions: List[SessionResponse]
    total: int
    skip: int
    limit: int

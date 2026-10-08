"""Pydantic schemas for audit logging and compliance"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class AuditLogResponse(BaseModel):
    """Schema for single audit log record"""
    id: int
    timestamp: datetime
    user_id: Optional[int] = None
    ip_address: Optional[str] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """Schema for paginated audit log results"""
    logs: List[AuditLogResponse]
    total: int
    skip: int
    limit: int


class AuditSummaryResponse(BaseModel):
    """Schema for aggregated security audit statistics"""
    total_events: int
    events_by_action: Dict[str, int]
    events_by_resource: Dict[str, int]
    unique_users: int
    since: datetime

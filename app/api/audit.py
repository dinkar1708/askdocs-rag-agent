"""API endpoints for Security Audit Logs"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import require_role
from app.db.database import get_db
from app.schemas.audit import AuditLogListResponse, AuditSummaryResponse
from app.services.audit import get_audit_logs, get_audit_summary

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(require_role("admin"))]
)


@router.get("/logs", response_model=AuditLogListResponse)
async def list_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    action: Optional[str] = Query(None, description="Filter by action name (e.g. USER_LOGIN)"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type (e.g. document)"),
    start_time: Optional[datetime] = Query(None, description="Filter events after this ISO timestamp"),
    end_time: Optional[datetime] = Query(None, description="Filter events before this ISO timestamp"),
    db: Session = Depends(get_db)
):
    """
    Retrieve audit logs (Admin only).
    Supports filtering by action, user ID, resource type, and date range.
    """
    logs, total = get_audit_logs(
        db=db,
        skip=skip,
        limit=limit,
        action=action,
        user_id=user_id,
        resource_type=resource_type,
        start_time=start_time,
        end_time=end_time
    )

    return AuditLogListResponse(
        logs=logs,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/summary", response_model=AuditSummaryResponse)
async def audit_summary(
    days: int = Query(7, ge=1, le=90, description="Number of past days to aggregate"),
    db: Session = Depends(get_db)
):
    """
    Get aggregated audit statistics and security activity metrics (Admin only).
    """
    summary = get_audit_summary(db=db, days=days)
    return AuditSummaryResponse(**summary)

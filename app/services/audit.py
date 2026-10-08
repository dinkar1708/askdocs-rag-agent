"""Audit logging service for security compliance and tracking"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.models import AuditLog

logger = logging.getLogger(__name__)

SENSITIVE_KEYS = {"password", "token", "secret", "api_key", "authorization", "hashed_password"}


def _sanitize_details(details: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Sanitize sensitive keys from details dictionary before persisting to DB"""
    if not details:
        return {}

    sanitized = {}
    for key, value in details.items():
        if any(sensitive in key.lower() for sensitive in SENSITIVE_KEYS):
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, dict):
            sanitized[key] = _sanitize_details(value)
        else:
            sanitized[key] = value
    return sanitized


def log_audit_event(
    db: Session,
    action: str,
    user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> Optional[AuditLog]:
    """
    Record a security audit log event.
    Non-blocking / fault-tolerant: failure to write an audit log does not crash the calling request.
    """
    try:
        sanitized_details = _sanitize_details(details)
        audit_entry = AuditLog(
            action=action.upper(),
            user_id=user_id,
            ip_address=ip_address,
            resource_type=resource_type.lower() if resource_type else None,
            resource_id=str(resource_id) if resource_id is not None else None,
            details=sanitized_details,
            timestamp=datetime.utcnow()
        )
        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)
        return audit_entry
    except Exception as e:
        logger.error(f"Failed to record audit log: {e}", exc_info=True)
        try:
            db.rollback()
        except Exception:
            pass
        return None


def get_audit_logs(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    action: Optional[str] = None,
    user_id: Optional[int] = None,
    resource_type: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> Tuple[List[AuditLog], int]:
    """Retrieve filtered audit logs with pagination"""
    query = db.query(AuditLog)

    if action:
        query = query.filter(AuditLog.action == action.upper())
    if user_id is not None:
        query = query.filter(AuditLog.user_id == user_id)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type.lower())
    if start_time:
        query = query.filter(AuditLog.timestamp >= start_time)
    if end_time:
        query = query.filter(AuditLog.timestamp <= end_time)

    total = query.count()
    logs = query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
    return logs, total


def get_audit_summary(
    db: Session,
    days: int = 7
) -> Dict[str, Any]:
    """Get aggregated metrics and event counts for the security audit dashboard"""
    since = datetime.utcnow() - timedelta(days=days)
    base_query = db.query(AuditLog).filter(AuditLog.timestamp >= since)

    total_events = base_query.count()

    # Events by action
    action_counts = (
        db.query(AuditLog.action, func.count(AuditLog.id))
        .filter(AuditLog.timestamp >= since)
        .group_by(AuditLog.action)
        .all()
    )
    events_by_action = {action: count for action, count in action_counts}

    # Events by resource
    resource_counts = (
        db.query(AuditLog.resource_type, func.count(AuditLog.id))
        .filter(AuditLog.timestamp >= since, AuditLog.resource_type.isnot(None))
        .group_by(AuditLog.resource_type)
        .all()
    )
    events_by_resource = {resource: count for resource, count in resource_counts if resource}

    # Unique users
    unique_users = (
        db.query(func.count(func.distinct(AuditLog.user_id)))
        .filter(AuditLog.timestamp >= since, AuditLog.user_id.isnot(None))
        .scalar() or 0
    )

    return {
        "total_events": total_events,
        "events_by_action": events_by_action,
        "events_by_resource": events_by_resource,
        "unique_users": unique_users,
        "since": since,
    }

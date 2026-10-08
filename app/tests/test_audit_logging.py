"""Unit tests for Security Audit Logging (OWASP A09 Logging & Monitoring)"""

from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import User, AuditLog
from app.services.audit import log_audit_event, get_audit_logs, get_audit_summary, _sanitize_details
from app.core.security import hash_password, create_access_token


def test_sanitize_details():
    """Verify passwords and API keys are redacted from audit details"""
    raw_details = {
        "username": "alice",
        "password": "SecretPassword123!",
        "api_key": "sk_test_12345",
        "nested": {
            "token": "bearer_xyz",
            "normal_field": "visible_info"
        }
    }
    sanitized = _sanitize_details(raw_details)
    assert sanitized["username"] == "alice"
    assert sanitized["password"] == "[REDACTED]"
    assert sanitized["api_key"] == "[REDACTED]"
    assert sanitized["nested"]["token"] == "[REDACTED]"
    assert sanitized["nested"]["normal_field"] == "visible_info"


def test_log_audit_event_record(db_session: Session):
    """Test recording an audit log entry in the database"""
    user = User(
        email="audited@example.com",
        hashed_password=hash_password("Pass12345!"),
        role="user",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()

    entry = log_audit_event(
        db=db_session,
        action="DOCUMENT_UPLOAD",
        user_id=user.id,
        ip_address="192.168.1.100",
        resource_type="document",
        resource_id="42",
        details={"filename": "q3_report.pdf", "size_bytes": 10240}
    )

    assert entry is not None
    assert entry.id is not None
    assert entry.action == "DOCUMENT_UPLOAD"
    assert entry.user_id == user.id
    assert entry.ip_address == "192.168.1.100"
    assert entry.resource_type == "document"
    assert entry.resource_id == "42"
    assert entry.details["filename"] == "q3_report.pdf"


def test_get_audit_logs_query(db_session: Session):
    """Test querying and filtering audit logs"""
    user = User(
        email="query_test_user@example.com",
        hashed_password=hash_password("Pass12345!"),
        role="user",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()

    for i in range(5):
        log_audit_event(
            db=db_session,
            action="QUERY_ASK" if i % 2 == 0 else "DOCUMENT_VIEW",
            user_id=user.id,
            resource_type="query",
            details={"index": i}
        )

    logs, total = get_audit_logs(db=db_session, action="QUERY_ASK", limit=10)
    assert total == 3
    assert len(logs) == 3
    assert all(l.action == "QUERY_ASK" for l in logs)


def test_get_audit_summary_metrics(db_session: Session):
    """Test generating audit summary metrics"""
    u1 = User(email="user1_metric@example.com", hashed_password=hash_password("Pass12345!"), role="user")
    u2 = User(email="user2_metric@example.com", hashed_password=hash_password("Pass12345!"), role="user")
    db_session.add_all([u1, u2])
    db_session.commit()

    log_audit_event(db=db_session, action="USER_LOGIN", user_id=u1.id, resource_type="user")
    log_audit_event(db=db_session, action="USER_LOGIN", user_id=u2.id, resource_type="user")
    log_audit_event(db=db_session, action="DOCUMENT_UPLOAD", user_id=u1.id, resource_type="document")

    summary = get_audit_summary(db=db_session, days=7)
    assert summary["total_events"] == 3
    assert summary["events_by_action"]["USER_LOGIN"] == 2
    assert summary["events_by_action"]["DOCUMENT_UPLOAD"] == 1
    assert summary["events_by_resource"]["user"] == 2
    assert summary["events_by_resource"]["document"] == 1
    assert summary["unique_users"] == 2


def test_api_audit_endpoints_rbac(client: TestClient, db_session: Session):
    """Test RBAC on /audit/logs and /audit/summary endpoints"""
    # Create admin user
    admin = User(
        email="audit_admin@example.com",
        hashed_password=hash_password("AdminPass123!"),
        role="admin",
        is_active=True
    )
    # Create normal user
    regular = User(
        email="audit_user@example.com",
        hashed_password=hash_password("UserPass123!"),
        role="user",
        is_active=True
    )
    db_session.add_all([admin, regular])
    db_session.commit()

    admin_token = create_access_token({"sub": admin.email, "user_id": admin.id, "role": "admin"})
    user_token = create_access_token({"sub": regular.email, "user_id": regular.id, "role": "user"})

    # Admin access -> 200 OK
    res_admin = client.get("/audit/logs", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_admin.status_code == 200
    assert "logs" in res_admin.json()

    res_summary_admin = client.get("/audit/summary", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_summary_admin.status_code == 200
    assert "total_events" in res_summary_admin.json()

    # Regular user access -> 403 Forbidden
    res_user = client.get("/audit/logs", headers={"Authorization": f"Bearer {user_token}"})
    assert res_user.status_code == 403

    res_summary_user = client.get("/audit/summary", headers={"Authorization": f"Bearer {user_token}"})
    assert res_summary_user.status_code == 403


def test_auth_actions_produce_audit_logs(client: TestClient, db_session: Session):
    """Test that auth actions trigger audit log records automatically"""
    # 1. Register
    reg_res = client.post("/auth/register", json={
        "email": "audited_flow@example.com",
        "password": "Password123!",
        "full_name": "Audited User"
    })
    assert reg_res.status_code == 201

    # Verify registration logged
    reg_logs, count = get_audit_logs(db=db_session, action="USER_REGISTER")
    assert count >= 1
    assert any(l.details.get("email") == "audited_flow@example.com" for l in reg_logs)

    # 2. Failed login
    fail_res = client.post("/auth/login", json={
        "email": "audited_flow@example.com",
        "password": "WrongPassword!"
    })
    assert fail_res.status_code == 401

    # Verify failure logged
    fail_logs, fail_count = get_audit_logs(db=db_session, action="AUTH_FAILURE")
    assert fail_count >= 1

    # 3. Successful login
    ok_res = client.post("/auth/login", json={
        "email": "audited_flow@example.com",
        "password": "Password123!"
    })
    assert ok_res.status_code == 200

    # Verify login logged
    login_logs, login_count = get_audit_logs(db=db_session, action="USER_LOGIN")
    assert login_count >= 1

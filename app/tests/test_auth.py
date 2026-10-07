"""Unit and integration tests for Authentication & Authorization (Feature 12)"""

from datetime import timedelta
import pytest
from fastapi.testclient import TestClient

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)
from app.db.models import User, Session as SessionModel
from app.core.config import settings


def test_password_hashing_and_verification():
    """Verify PBKDF2 password hashing and verification works securely"""
    password = "SuperSecretPassword123!"
    hashed = hash_password(password)

    assert hashed.startswith("pbkdf2_sha256$")
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False
    assert verify_password(password, "invalid_hash_string") is False


def test_jwt_token_creation_and_validation():
    """Verify JWT access token creation and decoding"""
    data = {"sub": "user@example.com", "user_id": 42, "role": "user"}
    token = create_access_token(data, expires_delta=timedelta(minutes=15))

    payload = decode_access_token(token)
    assert payload["sub"] == "user@example.com"
    assert payload["user_id"] == 42
    assert payload["role"] == "user"
    assert "exp" in payload

    # Test expired token
    expired_token = create_access_token(data, expires_delta=timedelta(seconds=-10))
    with pytest.raises(ValueError, match="Token has expired"):
        decode_access_token(expired_token)

    # Test tampered token
    tampered_token = token[:-5] + "aaaaa"
    with pytest.raises(ValueError, match="Invalid token signature"):
        decode_access_token(tampered_token)

    # Test malformed token
    with pytest.raises(ValueError, match="Invalid token format"):
        decode_access_token("not.a.valid.token.parts")


def test_user_registration(client: TestClient, db_session):
    """Test user registration endpoint"""
    response = client.post("/auth/register", json={
        "email": "alice@example.com",
        "password": "Password123!",
        "full_name": "Alice Smith",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "alice@example.com"
    assert data["full_name"] == "Alice Smith"
    assert data["is_active"] is True
    assert "hashed_password" not in data


def test_user_registration_duplicate_email(client: TestClient, db_session):
    """Test duplicate registration returns 400 Bad Request"""
    client.post("/auth/register", json={
        "email": "duplicate@example.com",
        "password": "Password123!",
        "full_name": "First User",
    })

    response = client.post("/auth/register", json={
        "email": "duplicate@example.com",
        "password": "Password123!",
        "full_name": "Second User",
    })
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_user_login_success(client: TestClient, db_session):
    """Test login with valid credentials returns JWT token"""
    client.post("/auth/register", json={
        "email": "bob@example.com",
        "password": "SecretPassword123!",
        "full_name": "Bob Jones",
    })

    response = client.post("/auth/login", json={
        "email": "bob@example.com",
        "password": "SecretPassword123!",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "bob@example.com"


def test_user_login_invalid_password(client: TestClient, db_session):
    """Test login with wrong password returns 401"""
    client.post("/auth/register", json={
        "email": "charlie@example.com",
        "password": "CorrectPassword123!",
    })

    response = client.post("/auth/login", json={
        "email": "charlie@example.com",
        "password": "WrongPassword123!",
    })
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_user_login_inactive(client: TestClient, db_session):
    """Test inactive account cannot log in"""
    user = User(
        email="inactive@example.com",
        hashed_password=hash_password("Password123!"),
        full_name="Inactive User",
        role="user",
        is_active=False,
    )
    db_session.add(user)
    db_session.commit()

    response = client.post("/auth/login", json={
        "email": "inactive@example.com",
        "password": "Password123!",
    })
    assert response.status_code == 403
    assert "deactivated" in response.json()["detail"]


def test_get_current_user_profile(client: TestClient, db_session):
    """Test GET /auth/me returns current user profile with valid token"""
    reg_res = client.post("/auth/register", json={
        "email": "profile@example.com",
        "password": "Password123!",
        "full_name": "Profile User",
    })
    login_res = client.post("/auth/login", json={
        "email": "profile@example.com",
        "password": "Password123!",
    })
    token = login_res.json()["access_token"]

    # Authorized call
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "profile@example.com"

    # Unauthorized call (no token)
    unauth_response = client.get("/auth/me")
    assert unauth_response.status_code == 401


def test_change_password(client: TestClient, db_session):
    """Test changing user password"""
    client.post("/auth/register", json={
        "email": "changer@example.com",
        "password": "OldPassword123!",
    })
    login_res = client.post("/auth/login", json={
        "email": "changer@example.com",
        "password": "OldPassword123!",
    })
    token = login_res.json()["access_token"]

    # Incorrect old password
    fail_res = client.post(
        "/auth/change-password",
        json={"old_password": "WrongOldPassword!", "new_password": "BrandNewPassword123!"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert fail_res.status_code == 400

    # Correct old password
    ok_res = client.post(
        "/auth/change-password",
        json={"old_password": "OldPassword123!", "new_password": "BrandNewPassword123!"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert ok_res.status_code == 200

    # New login works with new password
    new_login = client.post("/auth/login", json={
        "email": "changer@example.com",
        "password": "BrandNewPassword123!",
    })
    assert new_login.status_code == 200


def test_admin_list_users_rbac(client: TestClient, db_session):
    """Test RBAC on admin users list endpoint"""
    # First user registered becomes admin
    admin_reg = client.post("/auth/register", json={
        "email": "admin@example.com",
        "password": "AdminPassword123!",
        "role": "admin",
    })
    admin_token = client.post("/auth/login", json={
        "email": "admin@example.com",
        "password": "AdminPassword123!",
    }).json()["access_token"]

    # Second user is standard 'user'
    user_reg = client.post("/auth/register", json={
        "email": "regular@example.com",
        "password": "RegularPassword123!",
        "role": "user",
    })
    user_token = client.post("/auth/login", json={
        "email": "regular@example.com",
        "password": "RegularPassword123!",
    }).json()["access_token"]

    # Admin accesses /auth/users -> 200 OK
    admin_view = client.get("/auth/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert admin_view.status_code == 200
    assert admin_view.json()["total"] >= 2

    # Regular user accesses /auth/users -> 403 Forbidden
    user_view = client.get("/auth/users", headers={"Authorization": f"Bearer {user_token}"})
    assert user_view.status_code == 403


def test_session_user_linking_and_isolation(client: TestClient, db_session):
    """Test sessions linked to authenticated users and permissions"""
    client.post("/auth/register", json={
        "email": "user1@example.com",
        "password": "Password123!",
    })
    token1 = client.post("/auth/login", json={
        "email": "user1@example.com",
        "password": "Password123!",
    }).json()["access_token"]

    client.post("/auth/register", json={
        "email": "user2@example.com",
        "password": "Password123!",
    })
    token2 = client.post("/auth/login", json={
        "email": "user2@example.com",
        "password": "Password123!",
    }).json()["access_token"]

    # User 1 creates a session
    s1_res = client.post(
        "/sessions/",
        json={},
        headers={"Authorization": f"Bearer {token1}", "X-API-Key": settings.API_KEY},
    )
    assert s1_res.status_code == 201
    s1_id = s1_res.json()["id"]
    assert s1_res.json()["user_id"] is not None

    # User 1 can view session 1
    view_ok = client.get(
        f"/sessions/{s1_id}",
        headers={"Authorization": f"Bearer {token1}", "X-API-Key": settings.API_KEY},
    )
    assert view_ok.status_code == 200

    # User 2 attempts to view User 1's private session -> 403 Forbidden
    view_forbidden = client.get(
        f"/sessions/{s1_id}",
        headers={"Authorization": f"Bearer {token2}", "X-API-Key": settings.API_KEY},
    )
    assert view_forbidden.status_code == 403

    # Anonymous user can create and view anonymous session
    anon_res = client.post(
        "/sessions/",
        json={},
        headers={"X-API-Key": settings.API_KEY},
    )
    assert anon_res.status_code == 201
    assert anon_res.json()["user_id"] is None

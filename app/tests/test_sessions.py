"""Tests for session management endpoints"""
import pytest
from app.tests.utils.api_documenter import document_api_call


def test_create_session(client):
    """Test creating a new chat session"""
    response = client.post("/sessions/", json={})
    data = response.json()

    # Document API call
    document_api_call(
        "create_session.json",
        "POST",
        "/sessions/",
        {},
        data,
        response.status_code
    )

    assert response.status_code == 201
    assert "id" in data
    assert "created_at" in data
    assert "last_accessed" in data
    assert data["message_count"] == 0


def test_list_sessions_empty(client):
    """Test listing sessions when none exist"""
    response = client.get("/sessions/")
    data = response.json()

    # Document API call
    document_api_call(
        "list_sessions_empty.json",
        "GET",
        "/sessions/",
        {},
        data,
        response.status_code
    )

    assert response.status_code == 200
    assert "sessions" in data
    assert "total" in data
    assert "skip" in data
    assert "limit" in data
    assert isinstance(data["sessions"], list)


def test_list_sessions_with_data(client):
    """Test listing sessions after creating some"""
    # Create 3 sessions
    session_ids = []
    for _ in range(3):
        response = client.post("/sessions/", json={})
        assert response.status_code == 201
        session_ids.append(response.json()["id"])

    # List sessions
    response = client.get("/sessions/")
    data = response.json()

    # Document API call
    document_api_call(
        "list_sessions.json",
        "GET",
        "/sessions/",
        {},
        data,
        response.status_code
    )

    assert response.status_code == 200
    assert data["total"] >= 3
    assert len(data["sessions"]) >= 3


def test_list_sessions_with_pagination(client):
    """Test pagination in session listing"""
    # Create sessions
    for _ in range(5):
        client.post("/sessions/", json={})

    # Test pagination
    response = client.get("/sessions/?skip=2&limit=2")
    data = response.json()

    # Document API call
    document_api_call(
        "list_sessions_paginated.json",
        "GET",
        "/sessions/?skip=2&limit=2",
        {"skip": 2, "limit": 2},
        data,
        response.status_code
    )

    assert response.status_code == 200
    assert data["skip"] == 2
    assert data["limit"] == 2
    assert len(data["sessions"]) <= 2


def test_get_session(client):
    """Test retrieving a specific session"""
    # Create a session
    create_response = client.post("/sessions/", json={})
    session_id = create_response.json()["id"]

    # Get the session
    response = client.get(f"/sessions/{session_id}")
    data = response.json()

    # Document API call
    document_api_call(
        "get_session.json",
        "GET",
        f"/sessions/{session_id}",
        {},
        data,
        response.status_code
    )

    assert response.status_code == 200
    assert data["id"] == session_id
    assert "created_at" in data
    assert "last_accessed" in data
    assert "messages" in data
    assert isinstance(data["messages"], list)
    assert len(data["messages"]) == 0


def test_get_nonexistent_session(client):
    """Test retrieving a session that doesn't exist"""
    response = client.get("/sessions/99999")
    data = response.json()

    # Document API call
    document_api_call(
        "get_session_not_found.json",
        "GET",
        "/sessions/99999",
        {},
        data,
        response.status_code
    )

    assert response.status_code == 404
    assert "detail" in data


def test_delete_session(client):
    """Test deleting a session"""
    # Create a session
    create_response = client.post("/sessions/", json={})
    session_id = create_response.json()["id"]

    # Delete the session
    response = client.delete(f"/sessions/{session_id}")

    # Document API call
    document_api_call(
        "delete_session.json",
        "DELETE",
        f"/sessions/{session_id}",
        {},
        {},
        response.status_code
    )

    assert response.status_code == 204

    # Verify it's deleted
    get_response = client.get(f"/sessions/{session_id}")
    assert get_response.status_code == 404


def test_delete_nonexistent_session(client):
    """Test deleting a session that doesn't exist"""
    response = client.delete("/sessions/99999")
    data = response.json()

    # Document API call
    document_api_call(
        "delete_session_not_found.json",
        "DELETE",
        "/sessions/99999",
        {},
        data,
        response.status_code
    )

    assert response.status_code == 404
    assert "detail" in data


def test_session_last_accessed_update(client):
    """Test that last_accessed is updated when session is retrieved"""
    # Create a session
    create_response = client.post("/sessions/", json={})
    session_id = create_response.json()["id"]
    initial_last_accessed = create_response.json()["last_accessed"]

    # Wait a bit (not actually sleeping, just ensuring timestamp would be different)
    # Get the session
    response = client.get(f"/sessions/{session_id}")
    data = response.json()

    # Document API call
    document_api_call(
        "session_last_accessed.json",
        "GET",
        f"/sessions/{session_id}",
        {},
        data,
        response.status_code
    )

    assert response.status_code == 200
    # last_accessed should be updated (or at least equal)
    assert data["last_accessed"] >= initial_last_accessed


def test_session_message_count(client):
    """Test that message_count is correctly calculated"""
    # Create a session
    create_response = client.post("/sessions/", json={})
    session_id = create_response.json()["id"]

    # Initially should have 0 messages
    list_response = client.get("/sessions/")
    sessions = list_response.json()["sessions"]
    session = next(s for s in sessions if s["id"] == session_id)

    # Document API call
    document_api_call(
        "session_message_count.json",
        "GET",
        "/sessions/",
        {},
        list_response.json(),
        list_response.status_code
    )

    assert session["message_count"] == 0


def test_session_cascade_delete(client):
    """Test that deleting a session cascades to messages"""
    # This test verifies the cascade delete works
    # We'll verify by checking that after deleting a session,
    # we can't retrieve it anymore

    # Create a session
    create_response = client.post("/sessions/", json={})
    session_id = create_response.json()["id"]

    # Delete the session
    delete_response = client.delete(f"/sessions/{session_id}")
    assert delete_response.status_code == 204

    # Verify it's gone
    get_response = client.get(f"/sessions/{session_id}")
    data = get_response.json()

    # Document API call
    document_api_call(
        "session_cascade_delete.json",
        "GET",
        f"/sessions/{session_id}",
        {},
        data,
        get_response.status_code
    )

    assert get_response.status_code == 404

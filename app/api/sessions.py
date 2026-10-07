"""API endpoints for session management"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.database import get_db
from app.db.models import Session as SessionModel, Message, User
from app.schemas.session import (
    SessionCreate,
    SessionResponse,
    SessionWithMessages,
    SessionListResponse,
)
from app.core.auth import verify_api_key, get_optional_current_user

router = APIRouter(
    prefix="/sessions",
    tags=["sessions"],
    dependencies=[Depends(verify_api_key)],
)


@router.post("/", response_model=SessionResponse, status_code=201)
async def create_session(
    session_data: SessionCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """
    Create a new chat session.

    Sessions are used for multi-turn conversations with context.
    If an authenticated user token is provided, the session is linked to the user.
    """
    user_id = current_user.id if current_user else None
    session = SessionModel(user_id=user_id)
    db.add(session)
    db.commit()
    db.refresh(session)

    return SessionResponse(
        id=session.id,
        user_id=session.user_id,
        created_at=session.created_at,
        last_accessed=session.last_accessed,
        message_count=0,
    )


@router.get("/", response_model=SessionListResponse)
async def list_sessions(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """List chat sessions. Scoped to the user if authenticated (unless admin)."""
    query = db.query(SessionModel)
    if current_user and current_user.role != "admin":
        query = query.filter((SessionModel.user_id == current_user.id) | (SessionModel.user_id.is_(None)))

    sessions = query.offset(skip).limit(limit).all()
    total = query.count()

    session_responses = []
    for session in sessions:
        message_count = db.query(Message).filter(Message.session_id == session.id).count()
        session_responses.append(SessionResponse(
            id=session.id,
            user_id=session.user_id,
            created_at=session.created_at,
            last_accessed=session.last_accessed,
            message_count=message_count,
        ))

    return SessionListResponse(
        sessions=session_responses,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{session_id}", response_model=SessionWithMessages)
async def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """Get a specific session with full conversation history"""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id and current_user:
        if current_user.role != "admin" and session.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this session",
            )

    # Update last_accessed
    session.last_accessed = datetime.utcnow()
    db.commit()

    return SessionWithMessages(
        id=session.id,
        user_id=session.user_id,
        created_at=session.created_at,
        last_accessed=session.last_accessed,
        messages=session.messages,
    )


@router.delete("/{session_id}", status_code=204)
async def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """Delete a chat session"""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id and current_user:
        if current_user.role != "admin" and session.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this session",
            )

    db.delete(session)
    db.commit()

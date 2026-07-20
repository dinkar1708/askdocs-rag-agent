"""API endpoints for session management"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.database import get_db
from app.db.models import Session as SessionModel, Message
from app.schemas.session import (
    SessionCreate,
    SessionResponse,
    SessionWithMessages,
    SessionListResponse
)

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/", response_model=SessionResponse, status_code=201)
async def create_session(
    session_data: SessionCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new chat session

    Sessions are used for multi-turn conversations with context.
    """
    session = SessionModel()
    db.add(session)
    db.commit()
    db.refresh(session)

    return SessionResponse(
        id=session.id,
        created_at=session.created_at,
        last_accessed=session.last_accessed,
        message_count=0
    )


@router.get("/", response_model=SessionListResponse)
async def list_sessions(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """List all chat sessions"""
    sessions = db.query(SessionModel).offset(skip).limit(limit).all()
    total = db.query(SessionModel).count()

    session_responses = []
    for session in sessions:
        message_count = db.query(Message).filter(Message.session_id == session.id).count()
        session_responses.append(SessionResponse(
            id=session.id,
            created_at=session.created_at,
            last_accessed=session.last_accessed,
            message_count=message_count
        ))

    return SessionListResponse(
        sessions=session_responses,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{session_id}", response_model=SessionWithMessages)
async def get_session(
    session_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific session with full conversation history"""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Update last_accessed
    session.last_accessed = datetime.utcnow()
    db.commit()

    return SessionWithMessages(
        id=session.id,
        created_at=session.created_at,
        last_accessed=session.last_accessed,
        messages=session.messages
    )


@router.delete("/{session_id}", status_code=204)
async def delete_session(
    session_id: int,
    db: Session = Depends(get_db)
):
    """Delete a chat session"""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    db.delete(session)
    db.commit()

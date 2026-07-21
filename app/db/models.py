"""SQLAlchemy database models"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from app.db.database import Base


class Document(Base):
    """Uploaded document"""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    page_count = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to chunks
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")


class Chunk(Base):
    """Text chunk with embedding from a document"""

    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    text = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=False)
    embedding = Column(Vector(384))  # sentence-transformers/all-MiniLM-L6-v2
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to document
    document = relationship("Document", back_populates="chunks")


class Session(Base):
    """Chat session for multi-turn conversations"""

    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to messages
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")


class Message(Base):
    """Individual message in a chat session"""

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    role = Column(String(50), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    sources = Column(JSON, nullable=True)  # Source citations for assistant messages
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to session
    session = relationship("Session", back_populates="messages")

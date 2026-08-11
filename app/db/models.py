"""SQLAlchemy database models"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.types import TypeDecorator
from pgvector.sqlalchemy import Vector

from app.db.database import Base


class TSVector(TypeDecorator):
    """Custom TSVECTOR type that falls back to Text for non-PostgreSQL databases"""
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(TSVECTOR())
        else:
            # Use Text for SQLite and other databases
            return dialect.type_descriptor(Text())


class Document(Base):
    """Uploaded document"""

    __tablename__ = "documents"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    page_count = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    doc_metadata = Column(JSON, default={}, nullable=False)  # Custom metadata (department, grade, type, tags, etc.)
    content_hash = Column(String(64), unique=True, nullable=True)  # SHA-256 hash for duplicate detection

    # Relationship to chunks
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")


class Chunk(Base):
    """Text chunk with embedding from a document"""

    __tablename__ = "chunks"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    text = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=False)
    chunk_index = Column(Integer, nullable=False, default=0)  # Position within document for ordering
    embedding = Column(Vector(384))  # sentence-transformers/all-MiniLM-L6-v2
    chunk_type = Column(String(50), default='text')  # 'text' or 'table'
    chunk_metadata = Column(JSON, nullable=True)  # Additional metadata (headers, bbox, etc.)
    text_search = Column(TSVector, nullable=True)  # Full-text search vector for hybrid search (BM25, PostgreSQL only)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to document
    document = relationship("Document", back_populates="chunks")


class Session(Base):
    """Chat session for multi-turn conversations"""

    __tablename__ = "sessions"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to messages
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")


class Message(Base):
    """Individual message in a chat session"""

    __tablename__ = "messages"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    role = Column(String(50), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    sources = Column(JSON, nullable=True)  # Source citations for assistant messages
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to session
    session = relationship("Session", back_populates="messages")

"""Pytest configuration and fixtures"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.database import Base, get_db
from app.llm.mock_provider import MockLLMProvider


# Test database (in-memory SQLite)
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create test database session"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create test client"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def mock_llm():
    """Create mock LLM provider"""
    llm = MockLLMProvider()
    yield llm
    llm.reset_call_count()


@pytest.fixture(scope="session")
def sample_pdf_path():
    """Path to sample PDF for testing"""
    return "tests/fixtures/sample.pdf"


@pytest.fixture(scope="function")
def sample_document_with_chunks(db_session):
    """Create a sample document with embedded chunks for testing"""
    from app.db.models import Document, Chunk
    from app.services.embeddings import generate_embedding

    # Create document
    doc = Document(
        filename="company_policy.pdf",
        page_count=4
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    # Sample text chunks about company policies
    chunk_texts = [
        "Paid Time Off (PTO): Full-time employees accrue 15 days of paid vacation per year, starting from their first day of employment.",
        "Sick Leave: Employees receive 10 days of sick leave annually. Sick leave does not roll over to the next year.",
        "Standard Hours: Our standard work week is Monday through Friday, 9:00 AM to 5:00 PM, with a one-hour lunch break.",
        "Remote Work Policy: Employees may work remotely up to 2 days per week with manager approval.",
        "Health Insurance: The company provides comprehensive health insurance coverage including medical, dental, and vision.",
        "401(k) Retirement Plan: Employees are eligible to participate after 90 days of employment. Company matches 50% up to 6%.",
    ]

    chunks = []
    for i, text in enumerate(chunk_texts):
        embedding = generate_embedding(text)
        chunk = Chunk(
            document_id=doc.id,
            text=text,
            page_number=(i // 2) + 1,  # Distribute across pages
            embedding=embedding
        )
        db_session.add(chunk)
        chunks.append(chunk)

    db_session.commit()
    for chunk in chunks:
        db_session.refresh(chunk)

    return doc, chunks


@pytest.fixture(scope="function")
def sample_chunks_data():
    """Sample chunk data (dict format) for testing formatters"""
    return [
        {
            "chunk_id": 1,
            "text": "Sample text from document.",
            "filename": "test.pdf",
            "page_number": 1,
            "similarity_score": 0.85
        }
    ]

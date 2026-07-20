"""Quick test script to verify model definitions"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from db.models import Document, Chunk, Session
from db.database import Base
from datetime import datetime

def test_model_definitions():
    """Verify all models are properly defined"""

    # Test Document model
    print("Testing Document model...")
    assert hasattr(Document, '__tablename__')
    assert Document.__tablename__ == 'documents'
    assert hasattr(Document, 'id')
    assert hasattr(Document, 'filename')
    assert hasattr(Document, 'page_count')
    assert hasattr(Document, 'uploaded_at')
    assert hasattr(Document, 'chunks')
    print("✓ Document model OK")

    # Test Chunk model
    print("Testing Chunk model...")
    assert hasattr(Chunk, '__tablename__')
    assert Chunk.__tablename__ == 'chunks'
    assert hasattr(Chunk, 'id')
    assert hasattr(Chunk, 'document_id')
    assert hasattr(Chunk, 'text')
    assert hasattr(Chunk, 'page_number')
    assert hasattr(Chunk, 'embedding')
    assert hasattr(Chunk, 'created_at')
    assert hasattr(Chunk, 'document')
    print("✓ Chunk model OK")

    # Test Session model
    print("Testing Session model...")
    assert hasattr(Session, '__tablename__')
    assert Session.__tablename__ == 'sessions'
    assert hasattr(Session, 'id')
    assert hasattr(Session, 'created_at')
    assert hasattr(Session, 'last_accessed')
    print("✓ Session model OK")

    # Test metadata
    print("\nTesting Base metadata...")
    tables = Base.metadata.tables
    assert 'documents' in tables
    assert 'chunks' in tables
    assert 'sessions' in tables
    print(f"✓ Found {len(tables)} tables: {list(tables.keys())}")

    print("\n✓ All model tests passed!")

if __name__ == "__main__":
    test_model_definitions()

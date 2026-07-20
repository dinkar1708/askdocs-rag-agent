"""Initialize database tables"""
from app.db.database import engine, Base
from app.db.models import Document, Chunk, Session, Message

def init_db():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")

if __name__ == "__main__":
    init_db()

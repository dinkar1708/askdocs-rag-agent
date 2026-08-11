"""add_performance_indexes

Revision ID: def456789012
Revises: cad33b9890b0
Create Date: 2026-08-11 10:00:00.000000

Adds performance-critical indexes:
- HNSW vector index on chunks.embedding for fast similarity search
- Index on chunks.document_id for FK joins
- GIN index on documents.doc_metadata for JSON queries
- tsvector column and GIN index on chunks for hybrid search (BM25)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'def456789012'
down_revision: Union[str, None] = 'cad33b9890b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add performance indexes"""

    # Enable pgvector extension if not already enabled
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # 1. Add HNSW vector index on chunks.embedding for cosine similarity
    # HNSW is much faster than sequential scan for large datasets
    # Using vector_cosine_ops for cosine distance operator (<=>)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw
        ON chunks
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)

    # 2. Add index on chunks.document_id (foreign key used in every join)
    op.create_index(
        'idx_chunks_document_id',
        'chunks',
        ['document_id'],
        unique=False
    )

    # 3. Add GIN index on documents.doc_metadata for fast JSON queries
    # Speeds up metadata filters like: WHERE doc_metadata->>'department' = 'HR'
    # Note: Cast JSON to JSONB for GIN index compatibility
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_documents_metadata_gin
        ON documents
        USING gin ((doc_metadata::jsonb))
    """)

    # 4. Add tsvector column for full-text search (hybrid search)
    # This enables BM25-style keyword search alongside vector similarity
    op.add_column(
        'chunks',
        sa.Column('text_search', postgresql.TSVECTOR, nullable=True)
    )

    # 5. Populate tsvector column with existing data
    op.execute("""
        UPDATE chunks
        SET text_search = to_tsvector('english', text)
        WHERE text_search IS NULL
    """)

    # 6. Create GIN index on tsvector for fast full-text search
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_chunks_text_search_gin
        ON chunks
        USING gin (text_search)
    """)

    # 7. Create trigger to auto-update tsvector on INSERT/UPDATE
    # This keeps the search index in sync automatically
    op.execute("""
        CREATE OR REPLACE FUNCTION chunks_text_search_trigger() RETURNS trigger AS $$
        begin
            new.text_search := to_tsvector('english', new.text);
            return new;
        end
        $$ LANGUAGE plpgsql
    """)

    op.execute("""
        CREATE TRIGGER tsvector_update_trigger
        BEFORE INSERT OR UPDATE ON chunks
        FOR EACH ROW
        EXECUTE FUNCTION chunks_text_search_trigger()
    """)


def downgrade() -> None:
    """Remove performance indexes"""

    # Drop trigger and function
    op.execute("DROP TRIGGER IF EXISTS tsvector_update_trigger ON chunks")
    op.execute("DROP FUNCTION IF EXISTS chunks_text_search_trigger()")

    # Drop indexes
    op.execute("DROP INDEX IF EXISTS idx_chunks_text_search_gin")
    op.execute("DROP INDEX IF EXISTS idx_documents_metadata_gin")
    op.drop_index('idx_chunks_document_id', table_name='chunks')
    op.execute("DROP INDEX IF EXISTS idx_chunks_embedding_hnsw")

    # Drop tsvector column
    op.drop_column('chunks', 'text_search')

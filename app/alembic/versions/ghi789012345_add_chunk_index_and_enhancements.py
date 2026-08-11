"""add_chunk_index_and_enhancements

Revision ID: ghi789012345
Revises: def456789012
Create Date: 2026-08-11 13:00:00.000000

Adds:
- chunk_index column for ordering and neighbor expansion
- content_hash column for duplicate detection
- ON DELETE CASCADE for foreign keys
- File size validation (handled in application code)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'ghi789012345'
down_revision: Union[str, None] = 'def456789012'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add enhancements"""

    # 1. Add chunk_index column for ordering chunks within a document
    # This enables:
    # - Reconstructing documents in original order
    # - Neighbor expansion (fetching adjacent chunks for context)
    op.add_column(
        'chunks',
        sa.Column('chunk_index', sa.Integer(), nullable=True)
    )

    # Populate chunk_index for existing chunks (ordered by id)
    op.execute("""
        UPDATE chunks
        SET chunk_index = subquery.row_num - 1
        FROM (
            SELECT id, ROW_NUMBER() OVER (PARTITION BY document_id ORDER BY id) as row_num
            FROM chunks
        ) as subquery
        WHERE chunks.id = subquery.id
    """)

    # Make chunk_index non-nullable after population
    op.alter_column('chunks', 'chunk_index', nullable=False)

    # Add index on (document_id, chunk_index) for efficient ordering
    op.create_index(
        'idx_chunks_document_chunk_order',
        'chunks',
        ['document_id', 'chunk_index'],
        unique=False
    )

    # 2. Add content_hash column for duplicate detection
    op.add_column(
        'documents',
        sa.Column('content_hash', sa.String(64), nullable=True)  # SHA-256 hash
    )

    # Add unique index on content_hash to prevent duplicates
    op.create_index(
        'idx_documents_content_hash',
        'documents',
        ['content_hash'],
        unique=True
    )

    # 3. Add ON DELETE CASCADE to foreign key constraints
    # This ensures that when a document is deleted, all its chunks are deleted automatically

    # Drop existing foreign key
    op.drop_constraint('chunks_document_id_fkey', 'chunks', type_='foreignkey')

    # Recreate with ON DELETE CASCADE
    op.create_foreign_key(
        'chunks_document_id_fkey',
        'chunks',
        'documents',
        ['document_id'],
        ['id'],
        ondelete='CASCADE'
    )

    # Similarly for messages -> sessions
    op.drop_constraint('messages_session_id_fkey', 'messages', type_='foreignkey')
    op.create_foreign_key(
        'messages_session_id_fkey',
        'messages',
        'sessions',
        ['session_id'],
        ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    """Remove enhancements"""

    # Remove foreign key constraints
    op.drop_constraint('messages_session_id_fkey', 'messages', type_='foreignkey')
    op.create_foreign_key(
        'messages_session_id_fkey',
        'messages',
        'sessions',
        ['session_id'],
        ['id']
    )

    op.drop_constraint('chunks_document_id_fkey', 'chunks', type_='foreignkey')
    op.create_foreign_key(
        'chunks_document_id_fkey',
        'chunks',
        'documents',
        ['document_id'],
        ['id']
    )

    # Remove indexes
    op.drop_index('idx_documents_content_hash', table_name='documents')
    op.drop_index('idx_chunks_document_chunk_order', table_name='chunks')

    # Remove columns
    op.drop_column('documents', 'content_hash')
    op.drop_column('chunks', 'chunk_index')

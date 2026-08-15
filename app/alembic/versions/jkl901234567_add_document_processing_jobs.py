"""Add document processing jobs table for LangGraph async ingestion

Revision ID: jkl901234567
Revises: def456789012
Create Date: 2026-08-11

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'jkl901234567'
down_revision = 'ghi789012345'
branch_labels = None
depends_on = None


def upgrade():
    """Create document_processing_jobs table for background async processing"""

    op.create_table(
        'document_processing_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.String(36), nullable=False, index=True),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('content_hash', sa.String(64), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='queued'),
        sa.Column('progress', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('current_stage', sa.String(100), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('doc_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('result_document_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('job_id', name='uq_document_processing_jobs_job_id'),
        sa.ForeignKeyConstraint(['result_document_id'], ['documents.id'], ondelete='SET NULL')
    )

    # Create indexes for efficient job lookups
    op.create_index('idx_jobs_status', 'document_processing_jobs', ['status'])
    op.create_index('idx_jobs_created_at', 'document_processing_jobs', ['created_at'])


def downgrade():
    """Drop document_processing_jobs table"""

    op.drop_index('idx_jobs_created_at', table_name='document_processing_jobs')
    op.drop_index('idx_jobs_status', table_name='document_processing_jobs')
    op.drop_table('document_processing_jobs')

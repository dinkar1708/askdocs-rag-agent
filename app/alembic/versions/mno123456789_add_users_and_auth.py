"""Add users table and user_id foreign keys to sessions and documents

Revision ID: mno123456789
Revises: jkl901234567
Create Date: 2026-10-07

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'mno123456789'
down_revision = 'jkl901234567'
branch_labels = None
depends_on = None


def upgrade():
    """Create users table and add user_id foreign keys"""
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('role', sa.String(50), nullable=False, server_default='user'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='uq_users_email'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_id', 'users', ['id'], unique=False)

    # Add user_id column to sessions
    op.add_column('sessions', sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_sessions_user_id_users',
        'sessions',
        'users',
        ['user_id'],
        ['id'],
        ondelete='SET NULL'
    )

    # Add user_id column to documents
    op.add_column('documents', sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_documents_user_id_users',
        'documents',
        'users',
        ['user_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade():
    """Drop user_id foreign keys and users table"""
    op.drop_constraint('fk_documents_user_id_users', 'documents', type_='foreignkey')
    op.drop_column('documents', 'user_id')

    op.drop_constraint('fk_sessions_user_id_users', 'sessions', type_='foreignkey')
    op.drop_column('sessions', 'user_id')

    op.drop_index('ix_users_id', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')

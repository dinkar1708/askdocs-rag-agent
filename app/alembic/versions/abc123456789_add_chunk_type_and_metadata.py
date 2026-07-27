"""add_chunk_type_and_metadata

Revision ID: abc123456789
Revises: 611ace04d728
Create Date: 2026-07-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'abc123456789'
down_revision: Union[str, None] = '611ace04d728'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add chunk_type column with default 'text'
    op.add_column('chunks', sa.Column('chunk_type', sa.String(length=50), nullable=True))

    # Set default value for existing rows
    op.execute("UPDATE chunks SET chunk_type = 'text' WHERE chunk_type IS NULL")

    # Add chunk_metadata column for storing table headers, bbox, etc.
    op.add_column('chunks', sa.Column('chunk_metadata', sa.JSON(), nullable=True))


def downgrade() -> None:
    # Remove chunk_metadata column
    op.drop_column('chunks', 'chunk_metadata')

    # Remove chunk_type column
    op.drop_column('chunks', 'chunk_type')

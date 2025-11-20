"""add ai processing columns

Revision ID: 0b4c93b0a665
Revises: 5f128176a40b
Create Date: 2025-11-16 18:48:37.956579

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0b4c93b0a665'
down_revision: Union[str, Sequence[str], None] = '5f128176a40b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add only indexes (all columns already exist in initial schema)."""
    # All AI columns already exist in initial schema for both tables
    # Add only indexes
    op.create_index('idx_acte_ai_status', 'acte_legislative', ['ai_status'], schema='legislatie')
    op.create_index('idx_acte_export_status', 'acte_legislative', ['export_status'], schema='legislatie')
    op.create_index('idx_articole_ai_status', 'articole', ['ai_status'], schema='legislatie')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_articole_ai_status', table_name='articole', schema='legislatie')
    op.drop_index('idx_acte_export_status', table_name='acte_legislative', schema='legislatie')
    op.drop_index('idx_acte_ai_status', table_name='acte_legislative', schema='legislatie')

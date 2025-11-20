"""add ai processing columns

Revision ID: 0b4c93b0a665
Revises: 5417c175c050
Create Date: 2025-11-20 16:00:57.434212

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0b4c93b0a665'
down_revision: Union[str, Sequence[str], None] = '5417c175c050'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add AI processing columns to acte_legislative
    op.add_column('acte_legislative', 
                  sa.Column('ai_status', sa.String(20), nullable=True),
                  schema='legislatie')
    op.add_column('acte_legislative',
                  sa.Column('ai_processed_at', sa.DateTime(timezone=True), nullable=True),
                  schema='legislatie')
    op.add_column('acte_legislative',
                  sa.Column('ai_error', sa.Text(), nullable=True),
                  schema='legislatie')
    op.add_column('acte_legislative',
                  sa.Column('metadate', sa.Text(), nullable=True),
                  schema='legislatie')
    op.add_column('acte_legislative',
                  sa.Column('export_status', sa.String(20), nullable=True),
                  schema='legislatie')
    op.add_column('acte_legislative',
                  sa.Column('issue_monitoring_id', sa.Integer(), nullable=True),
                  schema='legislatie')

    # Add AI processing columns to articole
    op.add_column('articole',
                  sa.Column('ai_status', sa.String(20), nullable=True),
                  schema='legislatie')
    op.add_column('articole',
                  sa.Column('ai_processed_at', sa.DateTime(timezone=True), nullable=True),
                  schema='legislatie')
    op.add_column('articole',
                  sa.Column('ai_error', sa.Text(), nullable=True),
                  schema='legislatie')
    op.add_column('articole',
                  sa.Column('metadate', sa.Text(), nullable=True),
                  schema='legislatie')
    op.add_column('articole',
                  sa.Column('issue_monitoring_id', sa.Integer(), nullable=True),
                  schema='legislatie')

    # Create indexes
    op.create_index('idx_acte_ai_status', 'acte_legislative', ['ai_status'], schema='legislatie')
    op.create_index('idx_acte_export_status', 'acte_legislative', ['export_status'], schema='legislatie')
    op.create_index('idx_articole_ai_status', 'articole', ['ai_status'], schema='legislatie')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_articole_ai_status', table_name='articole', schema='legislatie')
    op.drop_index('idx_acte_export_status', table_name='acte_legislative', schema='legislatie')
    op.drop_index('idx_acte_ai_status', table_name='acte_legislative', schema='legislatie')

    op.drop_column('articole', 'issue_monitoring_id', schema='legislatie')
    op.drop_column('articole', 'metadate', schema='legislatie')
    op.drop_column('articole', 'ai_error', schema='legislatie')
    op.drop_column('articole', 'ai_processed_at', schema='legislatie')
    op.drop_column('articole', 'ai_status', schema='legislatie')

    op.drop_column('acte_legislative', 'issue_monitoring_id', schema='legislatie')
    op.drop_column('acte_legislative', 'export_status', schema='legislatie')
    op.drop_column('acte_legislative', 'metadate', schema='legislatie')
    op.drop_column('acte_legislative', 'ai_error', schema='legislatie')
    op.drop_column('acte_legislative', 'ai_processed_at', schema='legislatie')
    op.drop_column('acte_legislative', 'ai_status', schema='legislatie')

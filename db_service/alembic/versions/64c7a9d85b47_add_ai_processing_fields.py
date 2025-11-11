"""add ai processing fields

Revision ID: 64c7a9d85b47
Revises: b862bd50316b
Create Date: 2025-11-11 23:59:44.654997

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '64c7a9d85b47'
down_revision: Union[str, Sequence[str], None] = 'b862bd50316b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add AI processing fields to acte_legislative and articole tables."""
    # Add AI fields to acte_legislative
    op.add_column('acte_legislative', 
        sa.Column('ai_status', sa.String(length=50), nullable=True),
        schema='legislatie'
    )
    op.add_column('acte_legislative',
        sa.Column('ai_processed_at', sa.DateTime(), nullable=True),
        schema='legislatie'
    )
    op.add_column('acte_legislative',
        sa.Column('ai_error', sa.Text(), nullable=True),
        schema='legislatie'
    )
    
    # Add export fields to acte_legislative
    op.add_column('acte_legislative',
        sa.Column('metadate', sa.JSON(), nullable=True),
        schema='legislatie'
    )
    op.add_column('acte_legislative',
        sa.Column('export_status', sa.String(length=50), nullable=True),
        schema='legislatie'
    )
    op.add_column('acte_legislative',
        sa.Column('export_at', sa.DateTime(), nullable=True),
        schema='legislatie'
    )
    op.add_column('acte_legislative',
        sa.Column('export_error', sa.Text(), nullable=True),
        schema='legislatie'
    )
    op.add_column('acte_legislative',
        sa.Column('issue_monitoring_id', sa.Integer(), nullable=True),
        schema='legislatie'
    )
    # Note: versiune already exists from add_change_tracking migration
    
    # Add AI fields to articole
    op.add_column('articole',
        sa.Column('ai_status', sa.String(length=50), nullable=True),
        schema='legislatie'
    )
    op.add_column('articole',
        sa.Column('ai_processed_at', sa.DateTime(), nullable=True),
        schema='legislatie'
    )
    op.add_column('articole',
        sa.Column('ai_error', sa.Text(), nullable=True),
        schema='legislatie'
    )
    # Note: versiune already exists from add_change_tracking migration
    
    # Create indexes on AI status fields
    op.create_index('ix_acte_legislative_ai_status', 'acte_legislative', ['ai_status'], schema='legislatie')
    op.create_index('ix_articole_ai_status', 'articole', ['ai_status'], schema='legislatie')


def downgrade() -> None:
    """Remove AI processing fields."""
    # Drop indexes
    op.drop_index('ix_articole_ai_status', table_name='articole', schema='legislatie')
    op.drop_index('ix_acte_legislative_ai_status', table_name='acte_legislative', schema='legislatie')
    
    # Drop columns from articole (skip versiune - owned by add_change_tracking)
    op.drop_column('articole', 'ai_error', schema='legislatie')
    op.drop_column('articole', 'ai_processed_at', schema='legislatie')
    op.drop_column('articole', 'ai_status', schema='legislatie')
    
    # Drop columns from acte_legislative (skip versiune - owned by add_change_tracking)
    op.drop_column('acte_legislative', 'issue_monitoring_id', schema='legislatie')
    op.drop_column('acte_legislative', 'export_error', schema='legislatie')
    op.drop_column('acte_legislative', 'export_at', schema='legislatie')
    op.drop_column('acte_legislative', 'export_status', schema='legislatie')
    op.drop_column('acte_legislative', 'metadate', schema='legislatie')
    op.drop_column('acte_legislative', 'ai_error', schema='legislatie')
    op.drop_column('acte_legislative', 'ai_processed_at', schema='legislatie')
    op.drop_column('acte_legislative', 'ai_status', schema='legislatie')

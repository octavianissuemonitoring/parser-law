"""add relevance_score to junction tables

Revision ID: cf5de01d0b10
Revises: 1007e30b0c57
Create Date: 2025-11-20 22:30:20.977153

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cf5de01d0b10'
down_revision: Union[str, Sequence[str], None] = '1007e30b0c57'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add relevance_score column to junction tables."""
    from sqlalchemy import inspect
    from alembic import context
    
    conn = context.get_bind()
    inspector = inspect(conn)
    
    # Get list of tables in legislatie schema
    tables = inspector.get_table_names(schema='legislatie')
    
    # Add relevance_score to each junction table if it exists
    if 'articole_issues' in tables:
        op.add_column(
            'articole_issues',
            sa.Column('relevance_score', sa.Float(), nullable=True),
            schema='legislatie'
        )
    
    if 'acte_issues' in tables:
        op.add_column(
            'acte_issues',
            sa.Column('relevance_score', sa.Float(), nullable=True),
            schema='legislatie'
        )
    
    if 'structure_issues' in tables:
        op.add_column(
            'structure_issues',
            sa.Column('relevance_score', sa.Float(), nullable=True),
            schema='legislatie'
        )
    
    if 'domenii_issues' in tables:
        op.add_column(
            'domenii_issues',
            sa.Column('relevance_score', sa.Float(), nullable=True),
            schema='legislatie'
        )


def downgrade() -> None:
    """Remove relevance_score column from junction tables."""
    from sqlalchemy import inspect
    from alembic import context
    
    conn = context.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names(schema='legislatie')
    
    if 'domenii_issues' in tables:
        op.drop_column('domenii_issues', 'relevance_score', schema='legislatie')
    if 'structure_issues' in tables:
        op.drop_column('structure_issues', 'relevance_score', schema='legislatie')
    if 'acte_issues' in tables:
        op.drop_column('acte_issues', 'relevance_score', schema='legislatie')
    if 'articole_issues' in tables:
        op.drop_column('articole_issues', 'relevance_score', schema='legislatie')

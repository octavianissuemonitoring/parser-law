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
    """Add relevance_score column to all junction tables."""
    # Add relevance_score to articole_issues
    op.add_column(
        'articole_issues',
        sa.Column('relevance_score', sa.Float(), nullable=True),
        schema='legislatie'
    )
    
    # Add relevance_score to acte_issues
    op.add_column(
        'acte_issues',
        sa.Column('relevance_score', sa.Float(), nullable=True),
        schema='legislatie'
    )
    
    # Add relevance_score to structure_issues
    op.add_column(
        'structure_issues',
        sa.Column('relevance_score', sa.Float(), nullable=True),
        schema='legislatie'
    )
    
    # Add relevance_score to domenii_issues
    op.add_column(
        'domenii_issues',
        sa.Column('relevance_score', sa.Float(), nullable=True),
        schema='legislatie'
    )


def downgrade() -> None:
    """Remove relevance_score column from junction tables."""
    op.drop_column('domenii_issues', 'relevance_score', schema='legislatie')
    op.drop_column('structure_issues', 'relevance_score', schema='legislatie')
    op.drop_column('acte_issues', 'relevance_score', schema='legislatie')
    op.drop_column('articole_issues', 'relevance_score', schema='legislatie')

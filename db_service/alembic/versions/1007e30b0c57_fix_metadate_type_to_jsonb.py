"""fix_metadate_type_to_jsonb

Revision ID: 1007e30b0c57
Revises: 0b4c93b0a665
Create Date: 2025-11-20 20:47:50.184343

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1007e30b0c57'
down_revision: Union[str, Sequence[str], None] = '0b4c93b0a665'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Convert metadate column from TEXT to JSONB."""
    # Convert acte_legislative.metadate from TEXT to JSONB
    op.execute("""
        ALTER TABLE legislatie.acte_legislative 
        ALTER COLUMN metadate TYPE jsonb USING metadate::jsonb
    """)
    
    # Convert articole.metadate from TEXT to JSONB
    op.execute("""
        ALTER TABLE legislatie.articole 
        ALTER COLUMN metadate TYPE jsonb USING metadate::jsonb
    """)


def downgrade() -> None:
    """Revert metadate column from JSONB to TEXT."""
    # Revert acte_legislative.metadate to TEXT
    op.execute("""
        ALTER TABLE legislatie.acte_legislative 
        ALTER COLUMN metadate TYPE text USING metadate::text
    """)
    
    # Revert articole.metadate to TEXT
    op.execute("""
        ALTER TABLE legislatie.articole 
        ALTER COLUMN metadate TYPE text USING metadate::text
    """)

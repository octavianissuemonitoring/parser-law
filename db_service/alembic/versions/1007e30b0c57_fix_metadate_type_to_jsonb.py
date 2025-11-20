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
    """NO-OP: metadate should remain TEXT type to match model definitions."""
    # Models define metadate as Text (SQLAlchemy), not JSONB
    # Keeping this migration as NO-OP for history
    pass


def downgrade() -> None:
    """Revert metadate column from JSONB to TEXT."""
    # Revert acte_legislative.metadate to TEXT
    op.execute("""
        ALTER TABLE legislatie.acte_legislative 
        ALTER COLUMN metadate TYPE text USING metadate::text
    """)


def downgrade() -> None:
    """NO-OP: nothing to revert."""
    pass

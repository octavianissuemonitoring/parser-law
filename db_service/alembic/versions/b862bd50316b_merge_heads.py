"""merge heads

Revision ID: b862bd50316b
Revises: add_change_tracking, create_linkuri_legislatie
Create Date: 2025-11-11 23:57:23.930711

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b862bd50316b'
down_revision: Union[str, Sequence[str], None] = ('add_change_tracking', 'create_linkuri_legislatie')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

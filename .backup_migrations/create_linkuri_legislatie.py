"""Create linkuri_legislatie table

Revision ID: create_linkuri_legislatie
Revises: 
Create Date: 2024-11-10 18:15:00
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'create_linkuri_legislatie'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create linkuri_legislatie table."""
    op.create_table(
        'linkuri_legislatie',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(500), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending_scraping'),
        sa.Column('acte_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.String(1000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_scraped_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('url'),
        schema='legislatie'
    )
    op.create_index('ix_legislatie_linkuri_legislatie_id', 'linkuri_legislatie', ['id'], unique=False, schema='legislatie')
    op.create_index('ix_legislatie_linkuri_legislatie_url', 'linkuri_legislatie', ['url'], unique=True, schema='legislatie')


def downgrade() -> None:
    """Drop linkuri_legislatie table."""
    op.drop_index('ix_legislatie_linkuri_legislatie_url', table_name='linkuri_legislatie', schema='legislatie')
    op.drop_index('ix_legislatie_linkuri_legislatie_id', table_name='linkuri_legislatie', schema='legislatie')
    op.drop_table('linkuri_legislatie', schema='legislatie')

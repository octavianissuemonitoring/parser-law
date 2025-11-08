"""Create acte_legislative and articole tables

Revision ID: 7ad62c5ec0a8
Revises: 
Create Date: 2025-11-07 21:06:42.977108

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7ad62c5ec0a8'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create schema if not exists
    op.execute("CREATE SCHEMA IF NOT EXISTS legislatie")
    op.execute("SET search_path TO legislatie, public")
    
    # Enable PostgreSQL extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")
    
    # Create acte_legislative table
    op.create_table(
        'acte_legislative',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('tip_act', sa.String(length=50), nullable=False),
        sa.Column('nr_act', sa.String(length=50), nullable=True),
        sa.Column('data_act', sa.Date(), nullable=True),
        sa.Column('an_act', sa.Integer(), nullable=True),
        sa.Column('titlu_act', sa.Text(), nullable=False),
        sa.Column('emitent_act', sa.String(length=255), nullable=True),
        sa.Column('mof_nr', sa.String(length=50), nullable=True),
        sa.Column('mof_data', sa.Date(), nullable=True),
        sa.Column('mof_an', sa.Integer(), nullable=True),
        sa.Column('url_legislatie', sa.String(length=500), nullable=False),
        sa.Column('html_content', sa.Text(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema='legislatie'
    )
    
    # Create indexes on acte_legislative
    op.create_index('ix_acte_legislative_tip_act', 'acte_legislative', ['tip_act'], schema='legislatie')
    op.create_index('ix_acte_legislative_an_act', 'acte_legislative', ['an_act'], schema='legislatie')
    op.create_index('ix_acte_legislative_mof_an', 'acte_legislative', ['mof_an'], schema='legislatie')
    
    # Create articole table
    op.create_table(
        'articole',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('act_id', sa.Integer(), nullable=False),
        sa.Column('ordine', sa.Integer(), nullable=False),
        sa.Column('titlu', sa.String(length=500), nullable=True),
        sa.Column('capitol', sa.String(length=500), nullable=True),
        sa.Column('sectiune', sa.String(length=500), nullable=True),
        sa.Column('subsectiune', sa.String(length=500), nullable=True),
        sa.Column('articol_nr', sa.String(length=50), nullable=True),
        sa.Column('alineat', sa.String(length=50), nullable=True),
        sa.Column('litera', sa.String(length=10), nullable=True),
        sa.Column('continut', sa.Text(), nullable=False),
        sa.Column('tip_continut', sa.String(length=50), nullable=False),
        sa.Column('nivel', sa.Integer(), nullable=False),
        sa.Column('path_complet', sa.String(length=1000), nullable=True),
        sa.Column('issue', sa.String(length=100), nullable=True),
        sa.Column('explicatie', sa.Text(), nullable=True),
        sa.Column('confidence_label', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['act_id'], ['legislatie.acte_legislative.id'], ondelete='CASCADE'),
        schema='legislatie'
    )
    
    # Create indexes on articole
    op.create_index('ix_articole_act_id', 'articole', ['act_id'], schema='legislatie')
    op.create_index('ix_articole_act_id_ordine', 'articole', ['act_id', 'ordine'], schema='legislatie')
    op.create_index('ix_articole_act_id_articol_nr', 'articole', ['act_id', 'articol_nr'], schema='legislatie')
    
    # Create update trigger for updated_at columns
    op.execute("""
        CREATE OR REPLACE FUNCTION legislatie.update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    op.execute("""
        CREATE TRIGGER update_acte_legislative_updated_at BEFORE UPDATE ON legislatie.acte_legislative
        FOR EACH ROW EXECUTE FUNCTION legislatie.update_updated_at_column();
    """)
    
    op.execute("""
        CREATE TRIGGER update_articole_updated_at BEFORE UPDATE ON legislatie.articole
        FOR EACH ROW EXECUTE FUNCTION legislatie.update_updated_at_column();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS update_articole_updated_at ON legislatie.articole")
    op.execute("DROP TRIGGER IF EXISTS update_acte_legislative_updated_at ON legislatie.acte_legislative")
    op.execute("DROP FUNCTION IF EXISTS legislatie.update_updated_at_column()")
    
    # Drop indexes
    op.drop_index('ix_articole_act_id_articol_nr', table_name='articole', schema='legislatie')
    op.drop_index('ix_articole_act_id_ordine', table_name='articole', schema='legislatie')
    op.drop_index('ix_articole_act_id', table_name='articole', schema='legislatie')
    op.drop_index('ix_acte_legislative_mof_an', table_name='acte_legislative', schema='legislatie')
    op.drop_index('ix_acte_legislative_an_act', table_name='acte_legislative', schema='legislatie')
    op.drop_index('ix_acte_legislative_tip_act', table_name='acte_legislative', schema='legislatie')
    
    # Drop tables
    op.drop_table('articole', schema='legislatie')
    op.drop_table('acte_legislative', schema='legislatie')
    
    # Drop schema
    op.execute("DROP SCHEMA IF EXISTS legislatie CASCADE")

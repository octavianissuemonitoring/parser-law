"""Add article change tracking

Revision ID: add_change_tracking
Revises: 7ad62c5ec0a8
Create Date: 2025-11-07 23:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_change_tracking'
down_revision = '7ad62c5ec0a8'
branch_labels = None
depends_on = None


def upgrade():
    """
    Adaugă tracking pentru modificări la nivel de articol.
    Permite detectarea articolelor noi/modificate/șterse pentru re-etichetare LLM.
    """
    
    # Add versioning to acte_legislative
    op.add_column(
        'acte_legislative',
        sa.Column('versiune', sa.Integer(), nullable=False, server_default='1'),
        schema='legislatie'
    )
    
    # Create table for tracking act modifications
    op.create_table(
        'acte_modificari',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('act_id', sa.Integer(), nullable=False),
        sa.Column('versiune', sa.Integer(), nullable=False),
        sa.Column('data_modificare', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('tip_modificare', sa.String(50), nullable=False, comment='initial, update_full, update_partial'),
        sa.Column('sursa_modificare', sa.String(500), nullable=True, comment='URL or source of modification'),
        sa.Column('modificat_de', sa.String(100), nullable=True, comment='User or system identifier'),
        
        # Statistics
        sa.Column('articole_noi', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('articole_modificate', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('articole_sterse', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_articole', sa.Integer(), nullable=False, server_default='0'),
        
        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['act_id'], ['legislatie.acte_legislative.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('act_id', 'versiune', name='uq_act_versiune'),
        schema='legislatie'
    )
    
    # Indexes for performance
    op.create_index('idx_modificari_act_versiune', 'acte_modificari', ['act_id', 'versiune'], schema='legislatie')
    op.create_index('idx_modificari_data', 'acte_modificari', ['data_modificare'], schema='legislatie')
    
    # Create table for article-level changes (GRANULAR TRACKING)
    op.create_table(
        'articole_modificari',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('modificare_id', sa.Integer(), nullable=False, comment='Reference to acte_modificari'),
        sa.Column('articol_id', sa.Integer(), nullable=True, comment='Current article ID (NULL if deleted)'),
        
        # Article identification
        sa.Column('articol_nr', sa.String(20), nullable=True),
        sa.Column('articol_label', sa.String(50), nullable=True),
        sa.Column('ordine', sa.Integer(), nullable=True),
        
        # Change type
        sa.Column('tip_schimbare', sa.String(20), nullable=False, comment='added, modified, deleted, unchanged'),
        
        # Old values (pentru modified și deleted)
        sa.Column('text_vechi', sa.Text(), nullable=True),
        sa.Column('issue_vechi', sa.Text(), nullable=True),
        sa.Column('explicatie_veche', sa.Text(), nullable=True),
        
        # New values (pentru added și modified)
        sa.Column('text_nou', sa.Text(), nullable=True),
        
        # Re-labeling status
        sa.Column('necesita_reetichetare', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('reetichetat', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('reetichetat_la', sa.DateTime(timezone=True), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['modificare_id'], ['legislatie.acte_modificari.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['articol_id'], ['legislatie.articole.id'], ondelete='SET NULL'),
        schema='legislatie'
    )
    
    # Indexes for querying pending re-labeling
    op.create_index('idx_art_mod_modificare', 'articole_modificari', ['modificare_id'], schema='legislatie')
    op.create_index('idx_art_mod_articol', 'articole_modificari', ['articol_id'], schema='legislatie')
    op.create_index('idx_art_mod_reetichetare', 'articole_modificari', ['necesita_reetichetare', 'reetichetat'], schema='legislatie')
    op.create_index('idx_art_mod_tip', 'articole_modificari', ['tip_schimbare'], schema='legislatie')


def downgrade():
    """Remove article change tracking tables."""
    op.drop_index('idx_art_mod_tip', table_name='articole_modificari', schema='legislatie')
    op.drop_index('idx_art_mod_reetichetare', table_name='articole_modificari', schema='legislatie')
    op.drop_index('idx_art_mod_articol', table_name='articole_modificari', schema='legislatie')
    op.drop_index('idx_art_mod_modificare', table_name='articole_modificari', schema='legislatie')
    op.drop_table('articole_modificari', schema='legislatie')
    
    op.drop_index('idx_modificari_data', table_name='acte_modificari', schema='legislatie')
    op.drop_index('idx_modificari_act_versiune', table_name='acte_modificari', schema='legislatie')
    op.drop_table('acte_modificari', schema='legislatie')
    
    op.drop_column('acte_legislative', 'versiune', schema='legislatie')

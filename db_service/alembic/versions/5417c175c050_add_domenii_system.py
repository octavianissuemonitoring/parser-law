"""add domenii system

Revision ID: 5417c175c050
Revises: aa4552000831
Create Date: 2025-11-20 15:59:14.813818

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5417c175c050'
down_revision: Union[str, Sequence[str], None] = 'aa4552000831'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create domenii table
    op.create_table(
        'domenii',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nume', sa.String(100), nullable=False),
        sa.Column('descriere', sa.Text(), nullable=True),
        sa.Column('cod', sa.String(50), nullable=False),
        sa.Column('activ', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cod', name='uq_domeniu_cod'),
        schema='legislatie'
    )
    op.create_index('idx_domenii_cod', 'domenii', ['cod'], schema='legislatie')
    op.create_index('idx_domenii_activ', 'domenii', ['activ'], schema='legislatie')

    # Seed domenii
    op.execute("""
        INSERT INTO legislatie.domenii (nume, cod, descriere, activ) VALUES
        ('Produse Farmaceutice', 'FARMA', 'Legislație privind produsele farmaceutice, medicamente, autorizații de comercializare', true),
        ('Dispozitive Medicale', 'DISP_MED', 'Legislație privind dispozitivele medicale, echipamente medicale, certificări', true),
        ('Produse din Tutun', 'TUTUN', 'Legislație privind produsele din tutun, produse conexe, reglementări speciale', true),
        ('Protecția Consumatorului', 'PROT_CONS', 'Legislație privind drepturile consumatorilor, garanții, reclamații', true),
        ('Sănătate Publică', 'SANATATE', 'Legislație privind sănătatea publică, prevenție, sistem de sănătate', true),
        ('Protecția Mediului', 'MEDIU', 'Legislație privind protecția mediului, gestionarea deșeurilor, poluare', true)
    """)

    # Create acte_domenii junction table
    op.create_table(
        'acte_domenii',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('act_id', sa.Integer(), nullable=False),
        sa.Column('domeniu_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['act_id'], ['legislatie.acte_legislative.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['domeniu_id'], ['legislatie.domenii.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('act_id', 'domeniu_id', name='uq_act_domeniu'),
        schema='legislatie'
    )
    op.create_index('idx_acte_domenii_act', 'acte_domenii', ['act_id'], schema='legislatie')
    op.create_index('idx_acte_domenii_domeniu', 'acte_domenii', ['domeniu_id'], schema='legislatie')

    # Create articole_domenii junction table
    op.create_table(
        'articole_domenii',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('articol_id', sa.Integer(), nullable=False),
        sa.Column('domeniu_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['articol_id'], ['legislatie.articole.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['domeniu_id'], ['legislatie.domenii.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('articol_id', 'domeniu_id', name='uq_articol_domeniu'),
        schema='legislatie'
    )
    op.create_index('idx_articole_domenii_articol', 'articole_domenii', ['articol_id'], schema='legislatie')
    op.create_index('idx_articole_domenii_domeniu', 'articole_domenii', ['domeniu_id'], schema='legislatie')

    # Create function for domain inheritance
    op.execute("""
        CREATE OR REPLACE FUNCTION legislatie.get_articol_domenii(p_articol_id INTEGER)
        RETURNS TABLE (domeniu_id INTEGER, nume VARCHAR, cod VARCHAR) AS $$
        BEGIN
            RETURN QUERY
            SELECT DISTINCT d.id, d.nume, d.cod
            FROM legislatie.domenii d
            WHERE d.id IN (
                -- Direct article domains
                SELECT ad.domeniu_id 
                FROM legislatie.articole_domenii ad 
                WHERE ad.articol_id = p_articol_id
                
                UNION
                
                -- Inherited from act if no direct domains
                SELECT acd.domeniu_id
                FROM legislatie.articole a
                JOIN legislatie.acte_domenii acd ON acd.act_id = a.act_id
                WHERE a.id = p_articol_id
                AND NOT EXISTS (
                    SELECT 1 FROM legislatie.articole_domenii ad2 
                    WHERE ad2.articol_id = p_articol_id
                )
            )
            AND d.activ = true;
        END;
        $$ LANGUAGE plpgsql STABLE;
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP FUNCTION IF EXISTS legislatie.get_articol_domenii(INTEGER)")
    
    op.drop_index('idx_articole_domenii_domeniu', table_name='articole_domenii', schema='legislatie')
    op.drop_index('idx_articole_domenii_articol', table_name='articole_domenii', schema='legislatie')
    op.drop_table('articole_domenii', schema='legislatie')
    
    op.drop_index('idx_acte_domenii_domeniu', table_name='acte_domenii', schema='legislatie')
    op.drop_index('idx_acte_domenii_act', table_name='acte_domenii', schema='legislatie')
    op.drop_table('acte_domenii', schema='legislatie')
    
    op.drop_index('idx_domenii_activ', table_name='domenii', schema='legislatie')
    op.drop_index('idx_domenii_cod', table_name='domenii', schema='legislatie')
    op.drop_table('domenii', schema='legislatie')

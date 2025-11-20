"""add issues system and junction tables

Revision ID: 5f128176a40b
Revises: aa4552000831
Create Date: 2025-11-20 15:58:27.782638

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5f128176a40b'
down_revision: Union[str, Sequence[str], None] = 'aa4552000831'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create junction tables with domeniu_id
    op.create_table(
        'articole_issues',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('articol_id', sa.Integer(), nullable=False),
        sa.Column('issue_id', sa.Integer(), nullable=False),
        sa.Column('domeniu_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['articol_id'], ['legislatie.articole.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['domeniu_id'], ['legislatie.domenii.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('articol_id', 'issue_id', 'domeniu_id', name='uq_articol_issue_domeniu'),
        schema='legislatie'
    )
    op.create_index('idx_articole_issues_articol', 'articole_issues', ['articol_id'], schema='legislatie')
    op.create_index('idx_articole_issues_issue', 'articole_issues', ['issue_id'], schema='legislatie')
    op.create_index('idx_articole_issues_domeniu', 'articole_issues', ['domeniu_id'], schema='legislatie')

    op.create_table(
        'acte_issues',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('act_id', sa.Integer(), nullable=False),
        sa.Column('issue_id', sa.Integer(), nullable=False),
        sa.Column('domeniu_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['act_id'], ['legislatie.acte_legislative.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['domeniu_id'], ['legislatie.domenii.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('act_id', 'issue_id', 'domeniu_id', name='uq_act_issue_domeniu'),
        schema='legislatie'
    )
    op.create_index('idx_acte_issues_act', 'acte_issues', ['act_id'], schema='legislatie')
    op.create_index('idx_acte_issues_issue', 'acte_issues', ['issue_id'], schema='legislatie')
    op.create_index('idx_acte_issues_domeniu', 'acte_issues', ['domeniu_id'], schema='legislatie')

    op.create_table(
        'anexe_issues',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('anexa_id', sa.Integer(), nullable=False),
        sa.Column('issue_id', sa.Integer(), nullable=False),
        sa.Column('domeniu_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['anexa_id'], ['legislatie.anexe.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['domeniu_id'], ['legislatie.domenii.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('anexa_id', 'issue_id', 'domeniu_id', name='uq_anexa_issue_domeniu'),
        schema='legislatie'
    )
    op.create_index('idx_anexe_issues_anexa', 'anexe_issues', ['anexa_id'], schema='legislatie')
    op.create_index('idx_anexe_issues_issue', 'anexe_issues', ['issue_id'], schema='legislatie')
    op.create_index('idx_anexe_issues_domeniu', 'anexe_issues', ['domeniu_id'], schema='legislatie')

    op.create_table(
        'structure_issues',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('act_id', sa.Integer(), nullable=False),
        sa.Column('issue_id', sa.Integer(), nullable=False),
        sa.Column('domeniu_id', sa.Integer(), nullable=False),
        sa.Column('titlu_nr', sa.String(50), nullable=True),
        sa.Column('capitol_nr', sa.String(50), nullable=True),
        sa.Column('sectiune_nr', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['act_id'], ['legislatie.acte_legislative.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['domeniu_id'], ['legislatie.domenii.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('act_id', 'issue_id', 'domeniu_id', 'titlu_nr', 'capitol_nr', 'sectiune_nr', 
                           name='uq_structure_issue_domeniu'),
        schema='legislatie'
    )
    op.create_index('idx_structure_issues_act', 'structure_issues', ['act_id'], schema='legislatie')
    op.create_index('idx_structure_issues_issue', 'structure_issues', ['issue_id'], schema='legislatie')
    op.create_index('idx_structure_issues_domeniu', 'structure_issues', ['domeniu_id'], schema='legislatie')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_structure_issues_domeniu', table_name='structure_issues', schema='legislatie')
    op.drop_index('idx_structure_issues_issue', table_name='structure_issues', schema='legislatie')
    op.drop_index('idx_structure_issues_act', table_name='structure_issues', schema='legislatie')
    op.drop_table('structure_issues', schema='legislatie')
    
    op.drop_index('idx_anexe_issues_domeniu', table_name='anexe_issues', schema='legislatie')
    op.drop_index('idx_anexe_issues_issue', table_name='anexe_issues', schema='legislatie')
    op.drop_index('idx_anexe_issues_anexa', table_name='anexe_issues', schema='legislatie')
    op.drop_table('anexe_issues', schema='legislatie')
    
    op.drop_index('idx_acte_issues_domeniu', table_name='acte_issues', schema='legislatie')
    op.drop_index('idx_acte_issues_issue', table_name='acte_issues', schema='legislatie')
    op.drop_index('idx_acte_issues_act', table_name='acte_issues', schema='legislatie')
    op.drop_table('acte_issues', schema='legislatie')
    
    op.drop_index('idx_articole_issues_domeniu', table_name='articole_issues', schema='legislatie')
    op.drop_index('idx_articole_issues_issue', table_name='articole_issues', schema='legislatie')
    op.drop_index('idx_articole_issues_articol', table_name='articole_issues', schema='legislatie')
    op.drop_table('articole_issues', schema='legislatie')

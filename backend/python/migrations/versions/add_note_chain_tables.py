"""add note chain tables

Revision ID: a1b2c3d4e5f6
Revises: eb010a6ed5ad
Create Date: 2026-02-19 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'eb010a6ed5ad'
branch_labels = None
depends_on = None


def upgrade():
    # Create note_chains table
    op.create_table(
        'note_chains',
        sa.Column('note_chain_id', sa.Uuid(), nullable=False),
        sa.Column('read_permission', sa.VARCHAR(length=50), nullable=False, server_default='Admin'),
        sa.Column('write_permission', sa.VARCHAR(length=50), nullable=False, server_default='Admin'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('note_chain_id'),
    )

    # Create notes table
    op.create_table(
        'notes',
        sa.Column('note_id', sa.Uuid(), nullable=False),
        sa.Column('note_chain_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column('message', sa.VARCHAR(length=2000), nullable=False),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['note_chain_id'], ['note_chains.note_chain_id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id']),
        sa.PrimaryKeyConstraint('note_id'),
    )

    # Create note_chain_reads table
    op.create_table(
        'note_chain_reads',
        sa.Column('note_chain_read_id', sa.Uuid(), nullable=False),
        sa.Column('note_chain_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('last_read_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['note_chain_id'], ['note_chains.note_chain_id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id']),
        sa.PrimaryKeyConstraint('note_chain_read_id'),
        sa.UniqueConstraint('note_chain_id', 'user_id', name='uq_note_chain_reads_chain_user'),
    )

    # Add note_chain_id FK to locations
    op.add_column('locations', sa.Column('note_chain_id', sa.Uuid(), nullable=True))
    op.create_foreign_key(
        'fk_locations_note_chain_id',
        'locations', 'note_chains',
        ['note_chain_id'], ['note_chain_id'],
    )

    # Add note_chain_id FK to routes
    op.add_column('routes', sa.Column('note_chain_id', sa.Uuid(), nullable=True))
    op.create_foreign_key(
        'fk_routes_note_chain_id',
        'routes', 'note_chains',
        ['note_chain_id'], ['note_chain_id'],
    )



def downgrade():
    op.drop_constraint('fk_routes_note_chain_id', 'routes', type_='foreignkey')
    op.drop_column('routes', 'note_chain_id')

    op.drop_constraint('fk_locations_note_chain_id', 'locations', type_='foreignkey')
    op.drop_column('locations', 'note_chain_id')

    # Drop new tables (reverse order of creation)
    op.drop_table('note_chain_reads')
    op.drop_table('notes')
    op.drop_table('note_chains')

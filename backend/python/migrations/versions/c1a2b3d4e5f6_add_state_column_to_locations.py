"""add state column to locations

Revision ID: c1a2b3d4e5f6
Revises: 88d4ec63dfb5
Create Date: 2026-03-24 23:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c1a2b3d4e5f6'
down_revision = '88d4ec63dfb5'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('locations', sa.Column('state', sa.String(), nullable=False, server_default='ACTIVE'))


def downgrade():
    op.drop_column('locations', 'state')

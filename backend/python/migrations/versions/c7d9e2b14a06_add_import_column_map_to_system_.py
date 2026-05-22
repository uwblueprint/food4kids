"""Add import_column_map to system_settings

Revision ID: c7d9e2b14a06
Revises: d3f1a2b4c5e6
Create Date: 2026-05-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c7d9e2b14a06'
down_revision = 'd3f1a2b4c5e6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'system_settings',
        sa.Column('import_column_map', sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('system_settings', 'import_column_map')

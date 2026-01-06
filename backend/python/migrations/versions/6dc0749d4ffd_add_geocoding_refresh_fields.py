"""Add geocoding refresh fields

Revision ID: 6dc0749d4ffd
Revises: 6e14b59510ce4d28a7af0b0f3f4d3385
Create Date: 2025-11-28 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '6dc0749d4ffd'
down_revision = '6e14b59510ce4d28a7af0b0f3f4d3385'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('locations', sa.Column('geocoded_at', sa.DateTime(), nullable=True))
    op.add_column('admin_info', sa.Column('route_archive_after', sa.Integer(), nullable=False, server_default='30'))
    op.alter_column('admin_info', 'route_archive_after', nullable=False)


def downgrade() -> None:
    op.drop_column('admin_info', 'route_archive_after')
    op.drop_column('locations', 'geocoded_at')

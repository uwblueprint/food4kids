"""add route groups table

Revision ID: 3343a7a49425
Revises: 001_initial_schema
Create Date: 2025-10-12 20:02:25.707299

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '3343a7a49425'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'route_groups',
        sa.Column('route_group_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('notes', sa.String(length=1000), nullable=False),
        sa.Column('drive_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('route_group_id')
    )


def downgrade():
    op.drop_table('route_groups')

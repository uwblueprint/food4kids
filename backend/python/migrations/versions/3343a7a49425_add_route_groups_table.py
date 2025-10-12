"""add route groups table

Revision ID: 3343a7a49425
Revises: 001_initial_schema
Create Date: 2025-10-12 20:02:25.707299

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from uuid import uuid4
from datetime import datetime, timezone

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
        sa.Column('notes', sa.Text(), nullable=False),
        sa.Column('num_routes', sa.Integer(), nullable=False),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('route_group_id')
    )

    # Seed data
    route_groups_table = sa.table(
        'route_groups',
        sa.column('route_group_id', postgresql.UUID),
        sa.column('name', sa.String),
        sa.column('notes', sa.Text),
        sa.column('num_routes', sa.Integer),
        sa.column('date', sa.DateTime),
    )

    op.bulk_insert(route_groups_table, [
        {
            'route_group_id': uuid4(),
            'name': 'Downtown Route',
            'notes': 'Main downtown delivery route',
            'num_routes': 5,
            'date': datetime(2025, 10, 15, 10, 0, 0, tzinfo=timezone.utc),
        },
        {
            'route_group_id': uuid4(),
            'name': 'North Side Route',
            'notes': 'Northern suburbs delivery',
            'num_routes': 3,
            'date': datetime(2025, 10, 16, 10, 0, 0, tzinfo=timezone.utc),
        },
        {
            'route_group_id': uuid4(),
            'name': 'East Side Route',
            'notes': 'Eastern area deliveries',
            'num_routes': 4,
            'date': datetime(2025, 10, 17, 10, 0, 0, tzinfo=timezone.utc),
        },
    ])


def downgrade():
    op.drop_table('route_groups')

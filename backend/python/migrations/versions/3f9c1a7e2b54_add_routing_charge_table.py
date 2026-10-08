"""Add routing_charge table for paid routing requests

Revision ID: 3f9c1a7e2b54
Revises: e7b21f4a9c53
Create Date: 2026-10-06 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3f9c1a7e2b54"
down_revision = "e7b21f4a9c53"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "routing_charge",
        sa.Column("routing_charge_id", sa.Uuid(), nullable=False),
        sa.Column("tier", sa.String(length=32), nullable=False),
        sa.Column("shipments", sa.Integer(), nullable=False),
        sa.Column("estimated_cost_usd", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("routing_charge_id"),
    )


def downgrade() -> None:
    op.drop_table("routing_charge")

"""Add api_usage table for per-SKU quota tracking

Revision ID: 5d64c664475d
Revises: b8e3f1a70c92
Create Date: 2026-08-21 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "5d64c664475d"
down_revision = "b8e3f1a70c92"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "api_usage",
        sa.Column("api_usage_id", sa.Uuid(), nullable=False),
        sa.Column("sku", sa.String(length=64), nullable=False),
        sa.Column("billing_month", sa.String(length=6), nullable=False),
        sa.Column(
            "units_used", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("api_usage_id"),
        # Load-bearing, not just hygiene: the service upserts against this
        # constraint so concurrent jobs can't both read the same count and
        # each conclude there is room.
        sa.UniqueConstraint("sku", "billing_month", name="uq_api_usage_sku_month"),
        sa.CheckConstraint("units_used >= 0", name="ck_api_usage_units_nonnegative"),
    )


def downgrade() -> None:
    op.drop_table("api_usage")

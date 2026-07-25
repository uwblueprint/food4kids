"""driver mileage becomes derived; monthly totals table -> adjustments

Driver mileage is now computed from routes: SUM(routes.length) over frozen
routes (those with a RouteSnapshot) grouped by driver and drive_date month,
plus signed manual adjustments. The old driver_history monthly-totals table
is replaced by driver_mileage_adjustments, which holds only what routes
can't express: admin corrections and pre-app history.

No backfill: there is no production deployment, so legacy driver_history
rows are dropped rather than reconciled into adjustments.

Revision ID: b3d4a1c2e5f6
Revises: d7e8f9a0b1c2
Create Date: 2026-07-12
"""

import sqlalchemy as sa
from alembic import op

revision = "b3d4a1c2e5f6"
down_revision = "d7e8f9a0b1c2"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "driver_mileage_adjustments",
        sa.Column("adjustment_id", sa.UUID(), primary_key=True),
        sa.Column(
            "driver_id",
            sa.UUID(),
            sa.ForeignKey("drivers.driver_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("drive_date", sa.Date(), nullable=False),
        sa.Column("km", sa.Float(), nullable=False),
        sa.Column("note", sa.String(length=1000), nullable=False),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )
    op.create_index(
        "ix_driver_mileage_adjustments_driver_id",
        "driver_mileage_adjustments",
        ["driver_id"],
    )
    op.create_index(
        "ix_driver_mileage_adjustments_drive_date",
        "driver_mileage_adjustments",
        ["drive_date"],
    )

    op.drop_table("driver_history")


def downgrade():
    op.create_table(
        "driver_history",
        sa.Column("driver_history_id", sa.Integer(), primary_key=True),
        sa.Column(
            "driver_id",
            sa.UUID(),
            sa.ForeignKey("drivers.driver_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("km", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
        sa.UniqueConstraint("driver_id", "year", "month"),
    )
    op.create_index("ix_driver_history_driver_id", "driver_history", ["driver_id"])

    op.drop_table("driver_mileage_adjustments")

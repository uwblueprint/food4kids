"""driver mileage becomes derived; drop the monthly totals table

Driver mileage is now computed from routes: SUM(routes.length) over frozen
routes (those with a RouteSnapshot) grouped by driver and drive_date month.
Nothing is stored, so the driver_history monthly-totals table goes away.

No backfill: there is no production deployment, so legacy driver_history
rows are simply dropped.

Revision ID: b3d4a1c2e5f6
Revises: 58e90e6bdd92
Create Date: 2026-07-12
"""

import sqlalchemy as sa
from alembic import op

revision = "b3d4a1c2e5f6"
down_revision = "58e90e6bdd92"
branch_labels = None
depends_on = None


def upgrade():
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

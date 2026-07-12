"""driver mileage becomes derived; monthly totals table -> adjustments

Driver mileage is now computed from routes: SUM(routes.length) over frozen
routes (those with a RouteSnapshot) grouped by driver and drive_date month,
plus signed manual adjustments. The old driver_history monthly-totals table
is replaced by driver_mileage_adjustments, which holds only what routes
can't express: admin corrections and pre-app history.

Backfill strategy: for every (driver, year, month) bucket, materialize ONE
adjustment = legacy monthly total - what frozen routes already account for
in that bucket. Every legacy monthly total (and therefore every lifetime
total) is preserved EXACTLY, including totals that came from manual admin
edits. FULL OUTER JOIN covers buckets that exist on only one side — legacy
is the source of truth for totals, since admins may have corrected it.

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
            sa.ForeignKey("drivers.driver_id", ondelete="SET NULL"),
            nullable=True,
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

    # Reconcile every legacy (driver, year, month) total against what the
    # frozen routes in that bucket already derive to.
    op.execute(
        """
        INSERT INTO driver_mileage_adjustments
            (adjustment_id, driver_id, drive_date, km, note,
             created_at, updated_at)
        SELECT gen_random_uuid(), d.driver_id,
               make_date(d.year, d.month, 1), d.diff,
               'Migration reconciliation: preserves the pre-derived monthly '
               'total for this driver exactly (difference between the legacy '
               'total and what their frozen routes in this month sum to).',
               (now() AT TIME ZONE 'America/New_York'),
               (now() AT TIME ZONE 'America/New_York')
        FROM (
            SELECT COALESCE(l.driver_id, r.driver_id) AS driver_id,
                   COALESCE(l.year, r.year) AS year,
                   COALESCE(l.month, r.month) AS month,
                   COALESCE(l.km, 0) - COALESCE(r.total, 0) AS diff
            FROM driver_history l
            FULL OUTER JOIN (
                SELECT rt.driver_id,
                       EXTRACT(YEAR FROM rg.drive_date)::int AS year,
                       EXTRACT(MONTH FROM rg.drive_date)::int AS month,
                       SUM(rt.length) AS total
                FROM route_snapshots rs
                JOIN routes rt ON rt.route_id = rs.route_id
                JOIN route_groups rg
                  ON rg.route_group_id = rt.route_group_id
                WHERE rt.driver_id IS NOT NULL
                GROUP BY rt.driver_id, 2, 3
            ) r ON r.driver_id = l.driver_id
               AND r.year = l.year
               AND r.month = l.month
        ) d
        WHERE ABS(d.diff) > 0.0001
        """
    )

    op.drop_table("driver_history")


def downgrade():
    # Best-effort: rebuild the monthly-totals table from the derived model
    # (frozen-route sums + adjustments).
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

    op.execute(
        """
        INSERT INTO driver_history
            (driver_id, year, month, km, created_at, updated_at)
        SELECT driver_id, year, month, SUM(km),
               (now() AT TIME ZONE 'America/New_York'),
               (now() AT TIME ZONE 'America/New_York')
        FROM (
            SELECT rt.driver_id,
                   EXTRACT(YEAR FROM rg.drive_date)::int AS year,
                   EXTRACT(MONTH FROM rg.drive_date)::int AS month,
                   rt.length AS km
            FROM route_snapshots rs
            JOIN routes rt ON rt.route_id = rs.route_id
            JOIN route_groups rg ON rg.route_group_id = rt.route_group_id
            WHERE rt.driver_id IS NOT NULL
            UNION ALL
            SELECT driver_id,
                   EXTRACT(YEAR FROM drive_date)::int,
                   EXTRACT(MONTH FROM drive_date)::int,
                   km
            FROM driver_mileage_adjustments
            WHERE driver_id IS NOT NULL
        ) combined
        GROUP BY driver_id, year, month
        """
    )

    op.drop_table("driver_mileage_adjustments")

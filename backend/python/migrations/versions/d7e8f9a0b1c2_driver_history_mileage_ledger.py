"""driver history as an append-only mileage ledger

Replaces the monthly-totals driver_history table with a ledger: one row per
mileage event (AUTO delivery credit, REASSIGNMENT compensation, or
MANUAL_ADJUSTMENT). Totals become SUM(km) aggregates bucketed by drive_date.

Also adds route_snapshots.length_km (the credited-at-freeze length that
reconciliation hooks diff against).

Backfill strategy:
1. AUTO entries reconstructed from frozen driven routes
   (km = routes.length, drive_date = route_groups.drive_date).
2. Per (driver, year, month) bucket, any difference between the legacy
   monthly total and the backfilled AUTO sum is materialized as a single
   MANUAL_ADJUSTMENT entry — so every legacy monthly total (and therefore
   every lifetime total) is preserved EXACTLY, including totals that came
   from manual admin edits.

Revision ID: d7e8f9a0b1c2
Revises: f9a8b7c6d5e4
Create Date: 2026-07-10
"""

import sqlalchemy as sa
from alembic import op

revision = "d7e8f9a0b1c2"
down_revision = "f9a8b7c6d5e4"
branch_labels = None
depends_on = None


def upgrade():
    # ------------------------------------------------------------------
    # 1. route_snapshots.length_km — backfill from the live route length
    #    (best available value; historical edits since freeze are unknowable).
    # ------------------------------------------------------------------
    op.add_column("route_snapshots", sa.Column("length_km", sa.Float(), nullable=True))
    op.execute(
        """
        UPDATE route_snapshots rs
        SET length_km = r.length
        FROM routes r
        WHERE r.route_id = rs.route_id
        """
    )
    op.alter_column("route_snapshots", "length_km", nullable=False)

    # ------------------------------------------------------------------
    # 2. Create the ledger under a temporary name. (Renaming the legacy
    #    table aside instead would carry its index/constraint names with
    #    it and collide with the new table's.) Indexes come at the end,
    #    after the legacy table and its identically-named indexes drop.
    # ------------------------------------------------------------------
    op.create_table(
        "driver_history_new",
        sa.Column("driver_history_id", sa.UUID(), primary_key=True),
        sa.Column(
            "driver_id",
            sa.UUID(),
            sa.ForeignKey("drivers.driver_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "route_id",
            sa.UUID(),
            sa.ForeignKey("routes.route_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("drive_date", sa.Date(), nullable=False),
        sa.Column("km", sa.Float(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("note", sa.String(length=1000), nullable=False),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )

    # ------------------------------------------------------------------
    # 3. Backfill AUTO entries from frozen driven routes.
    # ------------------------------------------------------------------
    op.execute(
        """
        INSERT INTO driver_history_new
            (driver_history_id, driver_id, route_id, drive_date, km, kind,
             note, created_at, updated_at)
        SELECT gen_random_uuid(), r.driver_id, r.route_id,
               rg.drive_date::date, r.length, 'auto', '',
               (now() AT TIME ZONE 'America/New_York'),
               (now() AT TIME ZONE 'America/New_York')
        FROM route_snapshots rs
        JOIN routes r ON r.route_id = rs.route_id
        JOIN route_groups rg ON rg.route_group_id = r.route_group_id
        WHERE r.driver_id IS NOT NULL
        """
    )

    # ------------------------------------------------------------------
    # 4. Reconcile: preserve every legacy (driver, year, month) total
    #    exactly. FULL OUTER JOIN so buckets that exist on only one side
    #    (e.g. a frozen route the legacy job never counted) still net out
    #    to the legacy value — legacy is the source of truth for totals,
    #    since admins may have manually corrected it.
    # ------------------------------------------------------------------
    op.execute(
        """
        INSERT INTO driver_history_new
            (driver_history_id, driver_id, route_id, drive_date, km, kind,
             note, created_at, updated_at)
        SELECT gen_random_uuid(), d.driver_id, NULL,
               make_date(d.year, d.month, 1), d.diff, 'manual_adjustment',
               'Migration reconciliation: preserves the pre-ledger monthly '
               'total for this driver exactly (difference between the legacy '
               'total and the backfilled per-route credits).',
               (now() AT TIME ZONE 'America/New_York'),
               (now() AT TIME ZONE 'America/New_York')
        FROM (
            SELECT COALESCE(l.driver_id, b.driver_id) AS driver_id,
                   COALESCE(l.year, b.year) AS year,
                   COALESCE(l.month, b.month) AS month,
                   COALESCE(l.km, 0) - COALESCE(b.total, 0) AS diff
            FROM driver_history l
            FULL OUTER JOIN (
                SELECT driver_id,
                       EXTRACT(YEAR FROM drive_date)::int AS year,
                       EXTRACT(MONTH FROM drive_date)::int AS month,
                       SUM(km) AS total
                FROM driver_history_new
                WHERE kind = 'auto'
                GROUP BY driver_id, 2, 3
            ) b ON b.driver_id = l.driver_id
               AND b.year = l.year
               AND b.month = l.month
        ) d
        WHERE ABS(d.diff) > 0.0001
        """
    )

    # ------------------------------------------------------------------
    # 5. Swap: drop the legacy table, promote the ledger to its name, and
    #    normalize the auto-generated constraint names.
    # ------------------------------------------------------------------
    op.drop_table("driver_history")
    op.execute("ALTER TABLE driver_history_new RENAME TO driver_history")
    op.execute("ALTER INDEX driver_history_new_pkey RENAME TO driver_history_pkey")
    op.execute(
        "ALTER TABLE driver_history RENAME CONSTRAINT "
        "driver_history_new_driver_id_fkey TO driver_history_driver_id_fkey"
    )
    op.execute(
        "ALTER TABLE driver_history RENAME CONSTRAINT "
        "driver_history_new_route_id_fkey TO driver_history_route_id_fkey"
    )

    op.create_index("ix_driver_history_driver_id", "driver_history", ["driver_id"])
    op.create_index("ix_driver_history_route_id", "driver_history", ["route_id"])
    op.create_index("ix_driver_history_drive_date", "driver_history", ["drive_date"])
    # Structural no-double-count guard: at most one AUTO credit per route.
    op.create_index(
        "uq_driver_history_auto_per_route",
        "driver_history",
        ["route_id"],
        unique=True,
        postgresql_where=sa.text("kind = 'auto'"),
    )


def downgrade():
    # Best-effort: rebuild the monthly-totals shape by aggregating the
    # ledger. Same temp-name dance as upgrade (index names are global).
    op.create_table(
        "driver_history_old",
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

    op.execute(
        """
        INSERT INTO driver_history_old
            (driver_id, year, month, km, created_at, updated_at)
        SELECT driver_id,
               EXTRACT(YEAR FROM drive_date)::int,
               EXTRACT(MONTH FROM drive_date)::int,
               SUM(km),
               (now() AT TIME ZONE 'America/New_York'),
               (now() AT TIME ZONE 'America/New_York')
        FROM driver_history
        WHERE driver_id IS NOT NULL
        GROUP BY driver_id, 2, 3
        """
    )

    op.drop_table("driver_history")
    op.execute("ALTER TABLE driver_history_old RENAME TO driver_history")
    op.execute("ALTER INDEX driver_history_old_pkey RENAME TO driver_history_pkey")
    op.execute(
        "ALTER TABLE driver_history RENAME CONSTRAINT "
        "driver_history_old_driver_id_fkey TO driver_history_driver_id_fkey"
    )
    op.create_index("ix_driver_history_driver_id", "driver_history", ["driver_id"])
    op.drop_column("route_snapshots", "length_km")

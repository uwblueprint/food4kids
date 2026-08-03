"""An assigned route must have a start time

Adds a CHECK constraint enforcing that routes.driver_id can only be set when
routes.start_time is also set. An assigned route is a scheduled route -- the
driver has to be told when to show up -- and the reminder email had been
papering over the gap with a "TBD" placeholder.

Unassigned routes are left alone: a route can legitimately exist before it is
scheduled, so the constraint only bites once a driver is attached.

Revision ID: a4c81f2d9b37
Revises: c9a1e5f30b74
Create Date: 2026-07-28 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a4c81f2d9b37"
down_revision = "c9a1e5f30b74"
branch_labels = None
depends_on = None

CONSTRAINT_NAME = "ck_routes_assigned_route_has_start_time"

# Matches the seed generator's standard start; only ever applied to rows that
# are already violating the invariant.
FALLBACK_START_TIME = "08:00:00"


def upgrade():
    # Existing databases are development/seed data only -- there is no
    # production deployment -- and the old seed generator assigned drivers
    # without ever setting a start time. Give those rows the standard start
    # rather than failing the migration and forcing a re-seed.
    connection = op.get_bind()
    backfilled = connection.execute(
        sa.text(
            "UPDATE routes SET start_time = :fallback "
            "WHERE driver_id IS NOT NULL AND start_time IS NULL"
        ),
        {"fallback": FALLBACK_START_TIME},
    ).rowcount
    if backfilled:
        print(
            f"assigned-route start_time backfill: set {backfilled} row(s) "
            f"to {FALLBACK_START_TIME}"
        )

    op.create_check_constraint(
        CONSTRAINT_NAME,
        "routes",
        "driver_id IS NULL OR start_time IS NOT NULL",
    )


def downgrade():
    op.drop_constraint(CONSTRAINT_NAME, "routes", type_="check")

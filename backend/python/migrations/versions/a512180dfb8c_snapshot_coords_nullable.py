"""snapshot coords nullable

Locations carry nullable latitude/longitude (a location may not be geocoded
yet), but the frozen route-stop snapshot required both — so freezing a route
that contained an ungeocoded stop failed on the NOT NULL constraint. Make the
snapshot coordinates nullable to mirror Location; reads already COALESCE the
snapshot over the live location, so a null snapshot coordinate falls back to
the live one.

Revision ID: a512180dfb8c
Revises: b8e3f1a70c92
Create Date: 2026-09-27 23:35:52.545838

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a512180dfb8c"
down_revision = "b8e3f1a70c92"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "route_stop_snapshots",
        "latitude",
        existing_type=sa.Float(),
        nullable=True,
    )
    op.alter_column(
        "route_stop_snapshots",
        "longitude",
        existing_type=sa.Float(),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "route_stop_snapshots",
        "longitude",
        existing_type=sa.Float(),
        nullable=False,
    )
    op.alter_column(
        "route_stop_snapshots",
        "latitude",
        existing_type=sa.Float(),
        nullable=False,
    )

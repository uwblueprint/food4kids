"""Require location_group_id on locations (make non-nullable)

Every location must belong to a delivery group: route generation operates per
location group, and the import flags MISSING_DELIVERY_GROUP. Enforce it at the
schema level.

Revision ID: f3b1c9a2d4e7
Revises: c7d9e2b14a06
Create Date: 2026-05-26 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f3b1c9a2d4e7"
down_revision = "c7d9e2b14a06"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop any locations that never got a delivery group before enforcing the
    # constraint. Safe here because this is a dev-only database with no
    # production data to preserve.
    op.execute("DELETE FROM locations WHERE location_group_id IS NULL")
    op.alter_column(
        "locations",
        "location_group_id",
        existing_type=sa.Uuid(),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "locations",
        "location_group_id",
        existing_type=sa.Uuid(),
        nullable=True,
    )

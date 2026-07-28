"""Drop the stored delivery_type from route_groups

A group's delivery type is a property of the stops it serves — it is whatever
its locations are — so reads always derived it from those locations, and the
column added in b8e2a4c6d9f1 only ever acted as a fallback for a group with no
stops yet. The one way to set it (the Add Route Group dialog) was never built,
so nothing writes the column and the fallback can never fire. Two sources for
one value, one of which is always NULL, is worse than deriving it in one place.

Groups with no stops now report delivery_type: null rather than a value nobody
could have entered.

Revision ID: c1f4a80b7e35
Revises: c9a1e5f30b74
Create Date: 2026-07-28 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c1f4a80b7e35"
down_revision = "c9a1e5f30b74"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("route_groups", "delivery_type")


def downgrade() -> None:
    op.add_column(
        "route_groups",
        sa.Column("delivery_type", sa.String(length=100), nullable=True),
    )

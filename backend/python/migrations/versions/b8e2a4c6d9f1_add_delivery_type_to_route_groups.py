"""Add delivery_type to route_groups

Route groups created by hand (ahead of route generation) carry the delivery
type chosen in the Add Route Group dialog. Groups that already have routes
keep deriving their delivery type from their stops' locations; this stored
value is only the fallback for empty groups.

Revision ID: b8e2a4c6d9f1
Revises: a7f3c1e94b28
Create Date: 2026-07-13 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b8e2a4c6d9f1"
down_revision = "a7f3c1e94b28"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "route_groups",
        sa.Column("delivery_type", sa.String(length=100), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("route_groups", "delivery_type")

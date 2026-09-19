"""Drop system_settings.default_cap

``default_cap`` was a maximum number of stops per route. It was never read by
any service — the only capacity that governs a route is boxes, configured as
``system_settings.boxes_per_car``. The stop cap is removed rather than kept
unused so there is exactly one way to express a driver's limit.

Revision ID: a1c2e3f4b5d6
Revises: 188db1e0eeae
Create Date: 2026-08-05 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a1c2e3f4b5d6"
down_revision = "188db1e0eeae"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("system_settings", "default_cap")


def downgrade() -> None:
    # Restored as nullable with no backfill: the dropped values had no reader,
    # so there is nothing meaningful to reconstruct.
    op.add_column(
        "system_settings",
        sa.Column("default_cap", sa.Integer(), autoincrement=False, nullable=True),
    )

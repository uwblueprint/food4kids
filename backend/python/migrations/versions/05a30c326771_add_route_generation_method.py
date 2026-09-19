"""Add route_generation_method to system settings

Revision ID: 05a30c326771
Revises: 5d64c664475d
Create Date: 2026-08-21 11:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "05a30c326771"
down_revision = "5d64c664475d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "system_settings",
        sa.Column(
            "route_generation_method",
            sa.String(length=32),
            nullable=False,
            server_default="auto",
        ),
    )


def downgrade() -> None:
    op.drop_column("system_settings", "route_generation_method")

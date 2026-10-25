"""Add f4k_wr_twitter to system_settings

The Contact Information tab lists Twitter alongside the other org links.
Nullable like every other social link; the org may not have one.

Revision ID: d41b6c9f2a73
Revises: 3f9c1a7e2b54
Create Date: 2026-10-12 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d41b6c9f2a73"
down_revision = "3f9c1a7e2b54"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "system_settings",
        sa.Column("f4k_wr_twitter", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("system_settings", "f4k_wr_twitter")

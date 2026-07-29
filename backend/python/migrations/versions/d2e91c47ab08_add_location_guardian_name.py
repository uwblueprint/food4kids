"""Add guardian_name to locations

The Apricot import maps a Guardian Name column separately from School Name /
Last Name, so a Family location carries both. Nullable with no backfill:
School rows have no guardian, and rows imported before this column existed
have nothing to derive one from.

Revision ID: d2e91c47ab08
Revises: c1f4a80b7e35
Create Date: 2026-07-29 17:10:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d2e91c47ab08"
down_revision = "c1f4a80b7e35"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "locations",
        sa.Column("guardian_name", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("locations", "guardian_name")

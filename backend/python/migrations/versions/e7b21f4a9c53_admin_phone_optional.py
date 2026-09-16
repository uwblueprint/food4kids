"""Make admin_info.admin_phone optional.

An admin bootstrapped by ``python -m app.create_admin`` may have no number on
file, and a NOT NULL column forces the operator to invent a placeholder. The
driver profile columns went nullable in c3a5e7f9b1d2 for the same reason; this
is the admin half.

Revision ID: e7b21f4a9c53
Revises: c3a5e7f9b1d2
"""

import sqlalchemy as sa
from alembic import op

revision = "e7b21f4a9c53"
down_revision = "c3a5e7f9b1d2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "admin_info",
        "admin_phone",
        existing_type=sa.String(length=100),
        nullable=True,
    )


def downgrade() -> None:
    # NOT NULL cannot come back while rows hold NULL. Empty string is the only
    # value that satisfies the constraint without fabricating a phone number;
    # the upgrade path reads '' as "no number" anyway.
    op.execute("UPDATE admin_info SET admin_phone = '' WHERE admin_phone IS NULL")
    op.alter_column(
        "admin_info",
        "admin_phone",
        existing_type=sa.String(length=100),
        nullable=False,
    )

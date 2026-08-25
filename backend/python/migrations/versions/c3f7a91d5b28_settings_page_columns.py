"""Add the system_settings columns the Settings page needs

The Settings design surfaces org configuration that had no storage behind it.
This adds every column that gap required, as one migration:

* ``announcement_emails_to_admins`` / ``announcement_emails_to_drivers`` --
  system-wide audience filters for announcement emails, each ANDed with the
  per-announcement send choice made on the announcements board. Both default
  to true, so applying this leaves current behaviour unchanged: drivers keep
  receiving announcement emails exactly as before.
* ``f4k_wr_twitter`` -- the Contact Information tab lists Twitter alongside the
  other org links. Nullable like every other social link; the org may not have
  one.

Revision ID: c3f7a91d5b28
Revises: b8e3f1a70c92
Create Date: 2026-08-24 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c3f7a91d5b28"
down_revision = "b8e3f1a70c92"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "system_settings",
        sa.Column(
            "announcement_emails_to_admins",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )
    op.add_column(
        "system_settings",
        sa.Column(
            "announcement_emails_to_drivers",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )
    op.add_column(
        "system_settings",
        sa.Column("f4k_wr_twitter", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("system_settings", "f4k_wr_twitter")
    op.drop_column("system_settings", "announcement_emails_to_drivers")
    op.drop_column("system_settings", "announcement_emails_to_admins")

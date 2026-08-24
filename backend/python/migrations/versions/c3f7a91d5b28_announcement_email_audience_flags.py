"""Add announcement email audience flags to system_settings

Announcement emails are gated by two system-wide audience filters, each ANDed
with the per-announcement send choice made on the announcements board. Both
default to true so applying this migration leaves current behaviour unchanged:
drivers keep receiving announcement emails exactly as before.

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


def downgrade() -> None:
    op.drop_column("system_settings", "announcement_emails_to_drivers")
    op.drop_column("system_settings", "announcement_emails_to_admins")

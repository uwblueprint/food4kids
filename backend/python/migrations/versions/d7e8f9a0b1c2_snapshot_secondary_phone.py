"""Capture both phone numbers in route stop snapshots

Locations carry phone_primary + phone_secondary, but the frozen stop snapshot
only stored a single phone_number (populated from phone_primary), silently
dropping the secondary number from the historical record. Rename the column to
phone_primary and add a nullable phone_secondary so the snapshot mirrors
Location field-for-field.

Revision ID: d7e8f9a0b1c2
Revises: b7c1d2e3f4a5
Create Date: 2026-07-09 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d7e8f9a0b1c2"
down_revision = "b7c1d2e3f4a5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "route_stop_snapshots",
        "phone_number",
        new_column_name="phone_primary",
        existing_type=sa.String(),
        existing_nullable=False,
    )
    op.add_column(
        "route_stop_snapshots",
        sa.Column("phone_secondary", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("route_stop_snapshots", "phone_secondary")
    op.alter_column(
        "route_stop_snapshots",
        "phone_primary",
        new_column_name="phone_number",
        existing_type=sa.String(),
        existing_nullable=False,
    )

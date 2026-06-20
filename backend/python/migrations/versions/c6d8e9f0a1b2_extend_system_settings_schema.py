"""Extend system_settings schema for global settings and reminders

Revision ID: c6d8e9f0a1b2
Revises: f4krp149
Create Date: 2026-06-15 20:30:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c6d8e9f0a1b2"
down_revision = "f4krp149"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "system_settings",
        sa.Column(
            "boxes_per_car",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("10"),
        ),
    )
    op.add_column(
        "system_settings",
        sa.Column(
            "dropoff_minutes",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("3"),
        ),
    )
    op.add_column(
        "system_settings",
        sa.Column(
            "children_per_box",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("2"),
        ),
    )
    op.add_column(
        "system_settings",
        sa.Column("contact_name", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "system_settings",
        sa.Column("contact_phone", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "system_settings",
        sa.Column("f4k_wr_instagram", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "system_settings",
        sa.Column("f4k_wr_facebook", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "system_settings",
        sa.Column("f4k_wr_email", sa.String(length=254), nullable=True),
    )
    op.add_column(
        "system_settings",
        sa.Column("f4k_wr_website", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "system_settings",
        sa.Column("f4k_wr_address", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "system_settings",
        sa.Column(
            "email_reminders",
            sa.JSON(),
            nullable=False,
            server_default=sa.text(
                """'[{"days_before": 1, "time": "09:00:00"}]'::json"""
            ),
        ),
    )


def downgrade() -> None:
    op.drop_column("system_settings", "email_reminders")
    op.drop_column("system_settings", "f4k_wr_address")
    op.drop_column("system_settings", "f4k_wr_website")
    op.drop_column("system_settings", "f4k_wr_email")
    op.drop_column("system_settings", "f4k_wr_facebook")
    op.drop_column("system_settings", "f4k_wr_instagram")
    op.drop_column("system_settings", "contact_phone")
    op.drop_column("system_settings", "contact_name")
    op.drop_column("system_settings", "children_per_box")
    op.drop_column("system_settings", "dropoff_minutes")
    op.drop_column("system_settings", "boxes_per_car")

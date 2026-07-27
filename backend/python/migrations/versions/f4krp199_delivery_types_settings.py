"""Add delivery types to system settings

Revision ID: f4krp199
Revises: b7c1d2e3f4a5
Create Date: 2026-06-29 20:30:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f4krp199"
down_revision = "b7c1d2e3f4a5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "system_settings",
        sa.Column(
            "delivery_types",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("""'["School", "Family"]'::json"""),
        ),
    )


def downgrade() -> None:
    op.drop_column("system_settings", "delivery_types")

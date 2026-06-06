"""rename school_name and add location delivery type

Revision ID: e4f6a7b8c9d0
Revises: d12a38cacf7c
Create Date: 2026-06-06 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e4f6a7b8c9d0"
down_revision = "d12a38cacf7c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("locations", "school_name", new_column_name="name")
    op.add_column(
        "locations",
        sa.Column("delivery_type", sa.String(), server_default="Family", nullable=True),
    )
    op.execute(
        """
        UPDATE locations
        SET delivery_type = 'School'
        WHERE name IS NOT NULL AND btrim(name) != ''
        """
    )
    op.execute(
        """
        UPDATE locations
        SET name = contact_name
        WHERE name IS NULL OR btrim(name) = ''
        """
    )
    op.alter_column(
        "locations",
        "name",
        existing_type=sa.String(),
        nullable=False,
    )
    op.alter_column(
        "locations",
        "delivery_type",
        existing_type=sa.String(),
        nullable=False,
    )


def downgrade() -> None:
    op.drop_column("locations", "delivery_type")
    op.alter_column(
        "locations",
        "name",
        existing_type=sa.String(),
        nullable=True,
        new_column_name="school_name",
    )

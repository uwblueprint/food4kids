"""Driver and location schema changes

Revision ID: f4krp149
Revises: c4d5e6f7a8b9
Create Date: 2026-06-14 22:10:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f4krp149"
down_revision = "c4d5e6f7a8b9"
branch_labels = None
depends_on = None


DEFAULT_AVAILABILITY = "[false, false, false, false, false, false, false]"


def upgrade() -> None:
    op.add_column("users", sa.Column("first_name", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("last_name", sa.String(length=255), nullable=True))
    op.execute(
        """
        UPDATE users
        SET
            first_name = CASE
                WHEN position(' ' in btrim(name)) = 0 THEN btrim(name)
                ELSE regexp_replace(btrim(name), '\\s+\\S+$', '')
            END,
            last_name = CASE
                WHEN position(' ' in btrim(name)) = 0 THEN btrim(name)
                ELSE regexp_replace(btrim(name), '^.*\\s+', '')
            END
        """
    )
    op.alter_column("users", "first_name", existing_type=sa.String(), nullable=False)
    op.alter_column("users", "last_name", existing_type=sa.String(), nullable=False)
    op.drop_column("users", "name")

    op.add_column(
        "drivers", sa.Column("partner_driver_name", sa.String(length=255), nullable=True)
    )
    op.add_column(
        "drivers",
        sa.Column(
            "availability",
            sa.JSON(),
            nullable=False,
            server_default=sa.text(f"'{DEFAULT_AVAILABILITY}'::json"),
        ),
    )
    op.alter_column("drivers", "availability", server_default=None)

    op.add_column(
        "locations", sa.Column("phone_primary", sa.String(), nullable=True)
    )
    op.add_column(
        "locations", sa.Column("phone_secondary", sa.String(), nullable=True)
    )
    op.execute("UPDATE locations SET phone_primary = phone_number")
    op.alter_column(
        "locations", "phone_primary", existing_type=sa.String(), nullable=False
    )
    op.drop_column("locations", "phone_number")


def downgrade() -> None:
    op.add_column("locations", sa.Column("phone_number", sa.String(), nullable=True))
    op.execute("UPDATE locations SET phone_number = phone_primary")
    op.alter_column(
        "locations", "phone_number", existing_type=sa.String(), nullable=False
    )
    op.drop_column("locations", "phone_secondary")
    op.drop_column("locations", "phone_primary")

    op.drop_column("drivers", "availability")
    op.drop_column("drivers", "partner_driver_name")

    op.add_column("users", sa.Column("name", sa.String(length=255), nullable=True))
    op.execute("UPDATE users SET name = first_name || ' ' || last_name")
    op.alter_column("users", "name", existing_type=sa.String(), nullable=False)
    op.drop_column("users", "last_name")
    op.drop_column("users", "first_name")

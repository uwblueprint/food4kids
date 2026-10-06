"""Support the admin driver-management profile fields.

Revision ID: c3a5e7f9b1d2
Revises: b8e3f1a70c92
"""

import sqlalchemy as sa
from alembic import op

revision = "c3a5e7f9b1d2"
down_revision = "b8e3f1a70c92"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The product only schedules Monday-Friday. Preserve the weekday portion
    # of existing seven-slot values and normalize malformed legacy rows.
    op.execute(
        """
        UPDATE drivers
        SET availability = CASE
            WHEN json_array_length(availability) >= 5
                THEN json_build_array(
                    availability -> 0, availability -> 1, availability -> 2,
                    availability -> 3, availability -> 4
                )
            ELSE '[false, false, false, false, false]'::json
        END
        """
    )
    for column, column_type in (
        ("phone", sa.String(length=32)),
        ("address", sa.String(length=255)),
        ("license_plate", sa.String(length=20)),
        ("car_make_model", sa.String(length=255)),
    ):
        op.alter_column("drivers", column, existing_type=column_type, nullable=True)


def downgrade() -> None:
    op.execute(
        """
        UPDATE drivers
        SET availability = json_build_array(
                availability -> 0, availability -> 1, availability -> 2,
                availability -> 3, availability -> 4, false, false
            ),
            phone = COALESCE(phone, ''),
            address = COALESCE(address, ''),
            license_plate = COALESCE(license_plate, ''),
            car_make_model = COALESCE(car_make_model, '')
        """
    )
    for column, column_type in (
        ("phone", sa.String(length=32)),
        ("address", sa.String(length=255)),
        ("license_plate", sa.String(length=20)),
        ("car_make_model", sa.String(length=255)),
    ):
        op.alter_column("drivers", column, existing_type=column_type, nullable=False)

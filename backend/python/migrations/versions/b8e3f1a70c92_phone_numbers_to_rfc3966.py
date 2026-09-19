"""Store phone numbers as RFC 3966 so extensions survive

E.164 has no extension field: ``(519) 576-3443 Ext. 1`` parsed fine and came
back out as ``+15195763443``, dropping the extension with nothing raised. The
F4K office number has one, and school locations routinely do, so this rewrites
every stored phone to RFC 3966 (``tel:+1-519-576-3443;ext=1``).

``drivers.phone`` also widens from 20 to 32 characters — the RFC 3966 form runs
to 31 with the longest extension we accept.

A value that cannot be parsed aborts the migration with the full list of
offenders rather than being skipped: those rows got in through the driver-update
path that used to bypass normalization, and each one needs a human to decide
what the number was meant to be.

Revision ID: b8e3f1a70c92
Revises: a1c4e97b20df
Create Date: 2026-08-15

"""

import phonenumbers
import sqlalchemy as sa
from alembic import op

revision = "b8e3f1a70c92"
down_revision = "a1c4e97b20df"
branch_labels = None
depends_on = None

# (table, primary key column, phone columns)
PHONE_COLUMNS = [
    ("drivers", "driver_id", ["phone"]),
    ("admin_info", "admin_id", ["admin_phone"]),
    ("system_settings", "system_settings_id", ["contact_phone"]),
    ("locations", "location_id", ["phone_primary", "phone_secondary"]),
    ("route_stop_snapshots", "route_stop_id", ["phone_primary", "phone_secondary"]),
]


def _reformat(value: str, fmt: int) -> str:
    parsed = phonenumbers.parse(value, "CA")
    if not phonenumbers.is_valid_number(parsed):
        raise ValueError("not a valid number")
    return phonenumbers.format_number(parsed, fmt)


def _rewrite(fmt: int) -> None:
    """Rewrite every stored phone into ``fmt``, aborting on unparseable data."""
    conn = op.get_bind()
    failures: list[str] = []

    for table, pk, columns in PHONE_COLUMNS:
        for column in columns:
            rows = conn.execute(
                sa.text(
                    f"SELECT {pk}, {column} FROM {table} WHERE {column} IS NOT NULL"
                )
            ).fetchall()
            for row_id, value in rows:
                try:
                    converted = _reformat(value, fmt)
                except (phonenumbers.NumberParseException, ValueError):
                    failures.append(f"{table}.{column} {row_id}: {value!r}")
                    continue
                if converted != value:
                    conn.execute(
                        sa.text(
                            f"UPDATE {table} SET {column} = :v WHERE {pk} = :id"
                        ),
                        {"v": converted, "id": row_id},
                    )

    if failures:
        raise RuntimeError(
            "Cannot normalize these phone numbers; fix them by hand, then "
            "re-run:\n  " + "\n  ".join(failures)
        )


def upgrade() -> None:
    # Widen first: an extension pushes a driver's number past the old 20.
    op.alter_column(
        "drivers",
        "phone",
        existing_type=sa.String(length=20),
        type_=sa.String(length=32),
        existing_nullable=False,
    )
    _rewrite(phonenumbers.PhoneNumberFormat.RFC3966)


def downgrade() -> None:
    # Lossy by nature — E.164 has nowhere to put an extension.
    _rewrite(phonenumbers.PhoneNumberFormat.E164)
    op.alter_column(
        "drivers",
        "phone",
        existing_type=sa.String(length=32),
        type_=sa.String(length=20),
        existing_nullable=False,
    )

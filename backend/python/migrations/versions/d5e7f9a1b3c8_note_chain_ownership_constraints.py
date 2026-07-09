"""Note chain ownership: unique constraints + driver note chains

Revision ID: d5e7f9a1b3c8
Revises: b7c1d2e3f4a5
Create Date: 2026-07-08 00:00:00.000000

A note chain belongs to at most one owner (one-to-one). The owning tables are
`locations`, `routes`, and now `drivers`:

 - Add a `note_chain_id` FK to `drivers` (like locations/routes), and backfill
   an admin-only note chain for every existing driver so admins can leave notes
   about a driver that the driver themselves cannot read or write.
 - Enforce the one-to-one invariant with a unique constraint on the
   `note_chain_id` column of all three tables.

note_chain_id is nullable, and Postgres treats NULLs as distinct, so rows
without a chain remain unconstrained. (`notes` and `note_chain_reads` reference
a chain from the many side and are intentionally left non-unique.)
"""

from uuid import uuid4

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d5e7f9a1b3c8"
down_revision = "b7c1d2e3f4a5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drivers gain a note chain, matching locations and routes.
    op.add_column("drivers", sa.Column("note_chain_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_drivers_note_chain_id",
        "drivers",
        "note_chains",
        ["note_chain_id"],
        ["note_chain_id"],
        ondelete="SET NULL",
    )

    # Backfill: give every existing driver an admin-only note chain so the
    # feature works for the current roster (drivers, unlike locations, are not
    # refreshed via an import that would create chains). read/write default to
    # 'Admin' on note_chains, so drivers can't see or edit these notes.
    conn = op.get_bind()
    driver_ids = conn.execute(
        sa.text("SELECT driver_id FROM drivers WHERE note_chain_id IS NULL")
    ).fetchall()
    for (driver_id,) in driver_ids:
        chain_id = uuid4()
        conn.execute(
            sa.text(
                "INSERT INTO note_chains "
                "(note_chain_id, read_permission, write_permission) "
                "VALUES (:cid, 'Admin', 'Admin')"
            ),
            {"cid": str(chain_id)},
        )
        conn.execute(
            sa.text("UPDATE drivers SET note_chain_id = :cid WHERE driver_id = :did"),
            {"cid": str(chain_id), "did": str(driver_id)},
        )

    # One-to-one uniqueness on every owning table.
    op.create_unique_constraint(
        "uq_drivers_note_chain_id", "drivers", ["note_chain_id"]
    )
    op.create_unique_constraint(
        "uq_locations_note_chain_id", "locations", ["note_chain_id"]
    )
    op.create_unique_constraint("uq_routes_note_chain_id", "routes", ["note_chain_id"])


def downgrade() -> None:
    op.drop_constraint("uq_routes_note_chain_id", "routes", type_="unique")
    op.drop_constraint("uq_locations_note_chain_id", "locations", type_="unique")
    op.drop_constraint("uq_drivers_note_chain_id", "drivers", type_="unique")

    # Note chains backfilled for existing drivers are left in place; the FK link
    # is removed with the column.
    op.drop_constraint("fk_drivers_note_chain_id", "drivers", type_="foreignkey")
    op.drop_column("drivers", "note_chain_id")

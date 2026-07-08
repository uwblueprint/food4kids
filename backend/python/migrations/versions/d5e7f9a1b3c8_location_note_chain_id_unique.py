"""Add uniqueness constraints to note_chain_id owner columns

Revision ID: d5e7f9a1b3c8
Revises: b7c1d2e3f4a5
Create Date: 2026-07-08 00:00:00.000000

A note chain belongs to at most one owner (one-to-one). The owning tables are
`locations` and `routes`; enforce the invariant at the DB level on both.
note_chain_id is nullable, and Postgres treats NULLs as distinct, so rows
without a chain remain unconstrained. (`notes` and `note_chain_reads` reference
a chain from the many side and are intentionally left non-unique.)
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "d5e7f9a1b3c8"
down_revision = "b7c1d2e3f4a5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_locations_note_chain_id",
        "locations",
        ["note_chain_id"],
    )
    op.create_unique_constraint(
        "uq_routes_note_chain_id",
        "routes",
        ["note_chain_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_routes_note_chain_id", "routes", type_="unique")
    op.drop_constraint("uq_locations_note_chain_id", "locations", type_="unique")

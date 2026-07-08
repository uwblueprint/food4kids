"""Add uniqueness constraint to locations.note_chain_id

Revision ID: d5e7f9a1b3c8
Revises: b7c1d2e3f4a5
Create Date: 2026-07-08 00:00:00.000000

A note chain belongs to at most one location (one-to-one). Enforce it at the DB
level. note_chain_id is nullable, and Postgres treats NULLs as distinct, so
locations without a chain remain unconstrained.
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


def downgrade() -> None:
    op.drop_constraint("uq_locations_note_chain_id", "locations", type_="unique")

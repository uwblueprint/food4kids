"""Drop the flat notes string from locations

Locations no longer carry a flat `notes` string — the note chain
(`note_chain_id`) is the sole notes mechanism, mirroring the earlier
drivers migration that replaced `drivers.notes` with a note chain.

Revision ID: a7f3c1e94b28
Revises: d7e8f9a0b1c2
Create Date: 2026-07-12 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a7f3c1e94b28"
down_revision = "d7e8f9a0b1c2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("locations", "notes")


def downgrade() -> None:
    # Re-add the flat notes column. A temporary server_default satisfies NOT
    # NULL for existing rows; drop it afterward to match the original schema
    # (which had no default). The old contents are not recoverable.
    op.add_column(
        "locations",
        sa.Column("notes", sa.String(), nullable=False, server_default=""),
    )
    op.alter_column("locations", "notes", server_default=None)

"""Track each admin's viewed location notes.

Revision ID: a7329b1c4d60
Revises: d41b6c9f2a73
"""

import sqlalchemy as sa
from alembic import op

revision = "a7329b1c4d60"
down_revision = "d41b6c9f2a73"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "note_read_receipts",
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.user_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "note_id",
            sa.Uuid(),
            sa.ForeignKey("notes.note_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("note_read_receipts")

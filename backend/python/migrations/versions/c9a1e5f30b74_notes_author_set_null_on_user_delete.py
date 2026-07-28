"""notes.user_id: SET NULL when the author is deleted

Revision ID: c9a1e5f30b74
Revises: b3d4a1c2e5f6
Create Date: 2026-07-27 00:00:00.000000

`notes.user_id` was created with no ON DELETE action, so it defaulted to
NO ACTION: deleting a user who had ever written a note raised a foreign key
violation. That made a hard delete of a driver (which deletes the underlying
`users` row) impossible for any driver who had actually done the job.

SET NULL is the right action rather than CASCADE. A note is an operational
record — "gate was locked", "left with the office" — that the org still needs
after the driver leaves. The column is already nullable and readers already
render an authorless note (system notes have no author), so dropping the
authorship link is both expressible and the privacy-preserving choice for a
hard delete.
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "c9a1e5f30b74"
down_revision = "b3d4a1c2e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("notes_user_id_fkey", "notes", type_="foreignkey")
    op.create_foreign_key(
        "notes_user_id_fkey",
        "notes",
        "users",
        ["user_id"],
        ["user_id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("notes_user_id_fkey", "notes", type_="foreignkey")
    op.create_foreign_key(
        "notes_user_id_fkey",
        "notes",
        "users",
        ["user_id"],
        ["user_id"],
    )

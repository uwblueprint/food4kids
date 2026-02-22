"""merge migration heads

Revision ID: a1b2c3d4e5f6
Revises: 9e693c4553f7, ba76119b3e4c
Create Date: 2026-02-08

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = ("9e693c4553f7", "ba76119b3e4c")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Merge migration: no schema changes.
    pass


def downgrade() -> None:
    # Merge migration: no schema changes.
    pass

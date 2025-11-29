"""add_queued_to_progress_enum

Revision ID: c967b946e4f9
Revises: 7af7d4689b08
Create Date: 2025-11-28 00:44:35.958724

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c967b946e4f9'
down_revision = '7af7d4689b08'
branch_labels = None
depends_on = None


def upgrade():
    try:
        op.execute("ALTER TYPE progressenum ADD VALUE 'QUEUED'")
    except Exception:
        pass


def downgrade():
    pass

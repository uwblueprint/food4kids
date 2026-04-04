"""merge announcements and note chain migrations

Revision ID: 595032f5ede7
Revises: 88d4ec63dfb5, 407499fe5f15
Create Date: 2026-04-02 07:41:26.597388

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '595032f5ede7'
down_revision = ('88d4ec63dfb5', '407499fe5f15')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass

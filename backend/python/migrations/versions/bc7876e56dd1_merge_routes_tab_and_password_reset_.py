"""merge routes tab and password reset heads

Revision ID: bc7876e56dd1
Revises: 605f4884c65b, f40596bcb025
Create Date: 2026-07-28 00:15:23.928228

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bc7876e56dd1'
down_revision = ('605f4884c65b', 'f40596bcb025')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass

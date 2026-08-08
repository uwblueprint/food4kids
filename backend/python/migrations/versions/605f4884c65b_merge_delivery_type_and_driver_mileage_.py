"""merge delivery_type and driver mileage heads

Revision ID: 605f4884c65b
Revises: b8e2a4c6d9f1, b3d4a1c2e5f6
Create Date: 2026-07-26 22:34:35.484194

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '605f4884c65b'
down_revision = ('b8e2a4c6d9f1', 'b3d4a1c2e5f6')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass

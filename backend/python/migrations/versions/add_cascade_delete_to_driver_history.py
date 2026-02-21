"""add cascade delete to driver_history

Revision ID: a1b2c3d4e5f6
Revises: eb010a6ed5ad
Create Date: 2026-02-19 00:00:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'eb010a6ed5ad'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the existing foreign key constraint
    op.drop_constraint('driver_history_driver_id_fkey', 'driver_history', type_='foreignkey')

    # Recreate the foreign key constraint with ON DELETE CASCADE
    op.create_foreign_key(
        'driver_history_driver_id_fkey',
        'driver_history',
        'drivers',
        ['driver_id'],
        ['driver_id'],
        ondelete='CASCADE'
    )


def downgrade():
    # Drop the CASCADE foreign key constraint
    op.drop_constraint('driver_history_driver_id_fkey', 'driver_history', type_='foreignkey')

    # Recreate the original foreign key constraint without CASCADE
    op.create_foreign_key(
        'driver_history_driver_id_fkey',
        'driver_history',
        'drivers',
        ['driver_id'],
        ['driver_id']
    )

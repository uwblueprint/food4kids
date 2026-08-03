"""Store route_groups.drive_date as a date instead of a timestamp.

A drive date is a calendar day, not an instant. Holding it as a naive
TIMESTAMP meant every read had to decide what timezone those midnights were
in, and the answer drifted between the scheduler (Eastern) and the container
clock (UTC).

The USING clause truncates rather than converts: existing values are all
midnight-anchored in local terms already, so the calendar day is preserved.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '188db1e0eeae'
down_revision = 'd2e91c47ab08'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('route_groups', 'drive_date',
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.Date(),
        existing_nullable=False,
        postgresql_using='drive_date::date',
    )


def downgrade():
    op.alter_column('route_groups', 'drive_date',
        existing_type=sa.Date(),
        type_=postgresql.TIMESTAMP(),
        existing_nullable=False,
        postgresql_using='drive_date::timestamp',
    )

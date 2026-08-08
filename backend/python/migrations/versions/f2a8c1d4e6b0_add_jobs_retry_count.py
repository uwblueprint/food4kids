"""Add jobs.retry_count for one-shot restart requeue

Tracks how many times startup recovery has automatically returned an
orphaned RUNNING job to PENDING. Caps crash-loop retries at one automatic
requeue (see recover_route_generation_jobs).

Revision ID: f2a8c1d4e6b0
Revises: d4eefe397549
Create Date: 2026-08-08 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f2a8c1d4e6b0"
down_revision = "d4eefe397549"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "jobs",
        sa.Column(
            "retry_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("jobs", "retry_count")

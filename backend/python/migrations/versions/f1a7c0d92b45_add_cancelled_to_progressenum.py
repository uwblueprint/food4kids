"""add Cancelled to progressenum

`ProgressEnum.CANCELLED` was added in Python when job cancellation landed, but
the Postgres type has carried only PENDING/RUNNING/COMPLETED/FAILED since it was
created. POST /jobs/{id}/cancel therefore fails on a migrated database with
`invalid input value for enum progressenum: "CANCELLED"`. The test suite builds
its schema from the models with `create_all`, so it never saw the gap.

Revision ID: f1a7c0d92b45
Revises: d4eefe397549
Create Date: 2026-08-07 10:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "f1a7c0d92b45"
down_revision = "d4eefe397549"
branch_labels = None
depends_on = None


def upgrade():
    # ALTER TYPE ... ADD VALUE cannot run inside a transaction block, so step
    # outside Alembic's. BEFORE 'COMPLETED' keeps the type's sort order matching
    # the declaration order in app/models/enum.py.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE progressenum ADD VALUE 'CANCELLED' BEFORE 'COMPLETED'")


def downgrade():
    # Postgres cannot drop a value from an enum, so rebuild the type. Cancelled
    # jobs become Failed: it is the only terminal state left that says the run
    # did not produce routes.
    op.execute("UPDATE jobs SET progress = 'FAILED' WHERE progress = 'CANCELLED'")
    op.execute("ALTER TYPE progressenum RENAME TO progressenum_old")
    op.execute(
        "CREATE TYPE progressenum AS ENUM ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED')"
    )
    op.execute(
        "ALTER TABLE jobs ALTER COLUMN progress TYPE progressenum "
        "USING progress::text::progressenum"
    )
    op.execute("DROP TYPE progressenum_old")

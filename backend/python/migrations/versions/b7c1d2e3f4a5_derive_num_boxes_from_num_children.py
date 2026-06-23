"""Derive box counts from num_children; drop stored num_boxes

Box counts are no longer stored. A location's boxes are derived as
ceil(num_children / children_per_box) (see app.utilities.boxes), so:

- locations.num_children becomes NOT NULL (existing NULLs backfilled to 0)
- locations.num_boxes is dropped
- route_stop_snapshots stores num_children instead of num_boxes

Existing rows with no children data backfill to 0 (we cannot reconstruct a
children count from the old box count).

Revision ID: b7c1d2e3f4a5
Revises: c6d8e9f0a1b2
Create Date: 2026-06-18 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b7c1d2e3f4a5"
down_revision = "c6d8e9f0a1b2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # locations: num_children required, num_boxes removed.
    op.execute("UPDATE locations SET num_children = 0 WHERE num_children IS NULL")
    op.alter_column(
        "locations",
        "num_children",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.drop_column("locations", "num_boxes")

    # route_stop_snapshots: store children, not boxes.
    op.add_column(
        "route_stop_snapshots",
        sa.Column(
            "num_children",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.alter_column("route_stop_snapshots", "num_children", server_default=None)
    op.drop_column("route_stop_snapshots", "num_boxes")


def downgrade() -> None:
    # route_stop_snapshots: restore num_boxes (data not recoverable -> 0).
    op.add_column(
        "route_stop_snapshots",
        sa.Column(
            "num_boxes",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.alter_column("route_stop_snapshots", "num_boxes", server_default=None)
    op.drop_column("route_stop_snapshots", "num_children")

    # locations: restore num_boxes and make num_children nullable again.
    op.add_column(
        "locations",
        sa.Column(
            "num_boxes",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.alter_column("locations", "num_boxes", server_default=None)
    op.alter_column(
        "locations",
        "num_children",
        existing_type=sa.Integer(),
        nullable=True,
    )

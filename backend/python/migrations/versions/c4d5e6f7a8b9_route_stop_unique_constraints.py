"""Add uniqueness constraints to route_stops

Revision ID: c4d5e6f7a8b9
Revises: e8f7d6c5b4a3
Create Date: 2026-06-06 00:00:00.000000

Two structural guards on route_stops:
 - (route_id, stop_number): stop ordering within a route is unambiguous.
 - (route_id, location_id): a location appears at most once per route, so a
   family can't be double-delivered within one route. (Duplicates across
   routes in the same RouteGroup still need an app-level check.)
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "c4d5e6f7a8b9"
down_revision = "e8f7d6c5b4a3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_route_stops_route_id_stop_number",
        "route_stops",
        ["route_id", "stop_number"],
    )
    op.create_unique_constraint(
        "uq_route_stops_route_id_location_id",
        "route_stops",
        ["route_id", "location_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_route_stops_route_id_location_id", "route_stops", type_="unique"
    )
    op.drop_constraint(
        "uq_route_stops_route_id_stop_number", "route_stops", type_="unique"
    )

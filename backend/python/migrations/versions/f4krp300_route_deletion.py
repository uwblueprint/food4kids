"""Cascade route stop deletion and preserve generation job records."""

from alembic import op

revision = "f4krp300"
down_revision = "c6e249a7b310"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # routes.route_group_id already cascades from the routes refactor.
    _replace_foreign_keys(stop_action="CASCADE", job_action="SET NULL")


def downgrade() -> None:
    _replace_foreign_keys(stop_action=None, job_action=None)


def _replace_foreign_keys(*, stop_action: str | None, job_action: str | None) -> None:
    op.drop_constraint("route_stops_route_id_fkey", "route_stops", type_="foreignkey")
    op.create_foreign_key(
        "route_stops_route_id_fkey",
        "route_stops",
        "routes",
        ["route_id"],
        ["route_id"],
        ondelete=stop_action,
    )
    op.drop_constraint("jobs_route_group_id_fkey", "jobs", type_="foreignkey")
    op.create_foreign_key(
        "jobs_route_group_id_fkey",
        "jobs",
        "route_groups",
        ["route_group_id"],
        ["route_group_id"],
        ondelete=job_action,
    )

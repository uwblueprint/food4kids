"""Routes/locations refactor: per-day routes, snapshots, in_roster + delivery_type

Revision ID: e8f7d6c5b4a3
Revises: a9c4e7f21b38
Create Date: 2026-05-26 00:00:00.000000

Destructive refactor with no prod data. Re-seed afterwards.

Routes side:
 - Drop driver_assignments (driver moves to routes.driver_id).
 - Drop route_group_memberships (route → group becomes a direct FK).
 - Drop routes.expires_at (drive_date carries the timeline).
 - encoded_polyline VARCHAR(10000) → TEXT (cap was a latent landmine on long
   routes; Postgres stores VARCHAR(n) and TEXT identically).
 - Add routes.route_group_id (mandatory; routes belong to one group).
 - Add routes.driver_id (nullable; null = unassigned).
 - Add routes.start_time (per-driver start).
 - Add routes.cloned_from_route_id (lineage for upcoming Duplicate flow).
 - Add route_snapshots + route_stop_snapshots (per-grain freeze tables;
   presence == frozen, no separate flag column).

Existing routes/route_stops are deleted: the old M2M cannot be cleanly
collapsed into a single route_group_id without losing information (a route
in N memberships should become N cloned routes). Re-seed restores fidelity.

Locations side:
 - Add in_roster (replaces state; bool: "appeared in latest spreadsheet"),
   backfilled from state. Drop state column. (delivery_type + the
   school_name → name rename come from e4f6a7b8c9d0 on main.)
"""

import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision = "e8f7d6c5b4a3"
# main's two open heads (user-invites and the location name/delivery_type
# rename) are joined by the a9c4e7f21b38 merge migration; build on that.
down_revision = "a9c4e7f21b38"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. Drop doomed join tables. Order matters: driver_assignments first
    #    because it has its own FKs; then route_group_memberships.
    # ------------------------------------------------------------------
    op.drop_table("driver_assignments")
    op.drop_table("route_group_memberships")

    # ------------------------------------------------------------------
    # 2. Clear routes + route_stops so we can add NOT NULL columns
    #    without backfill. The membership M2M cannot be losslessly
    #    collapsed; the intended workflow is to re-seed after migrate.
    # ------------------------------------------------------------------
    op.execute("DELETE FROM route_stops")
    op.execute("DELETE FROM routes")

    # ------------------------------------------------------------------
    # 3. Routes table mutations
    # ------------------------------------------------------------------
    op.drop_column("routes", "expires_at")

    # VARCHAR(10000) → TEXT. Postgres stores both the same; the cap only
    # gave us a hard failure on the longest routes.
    op.alter_column(
        "routes",
        "encoded_polyline",
        existing_type=sqlmodel.sql.sqltypes.AutoString(length=10000),
        type_=sa.Text(),
        existing_nullable=True,
    )

    op.add_column(
        "routes",
        sa.Column("route_group_id", sa.Uuid(), nullable=False),
    )
    op.create_foreign_key(
        "fk_routes_route_group_id_route_groups",
        "routes",
        "route_groups",
        ["route_group_id"],
        ["route_group_id"],
        ondelete="CASCADE",
    )

    op.add_column(
        "routes",
        sa.Column("driver_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_routes_driver_id_drivers",
        "routes",
        "drivers",
        ["driver_id"],
        ["driver_id"],
        ondelete="SET NULL",
    )

    op.add_column(
        "routes",
        sa.Column("start_time", sa.Time(), nullable=True),
    )

    op.add_column(
        "routes",
        sa.Column("cloned_from_route_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_routes_cloned_from_route_id_routes",
        "routes",
        "routes",
        ["cloned_from_route_id"],
        ["route_id"],
        ondelete="SET NULL",
    )

    # Indices for frequent lookups
    op.create_index("ix_routes_route_group_id", "routes", ["route_group_id"])
    op.create_index("ix_routes_driver_id", "routes", ["driver_id"])
    op.create_index(
        "ix_routes_cloned_from_route_id",
        "routes",
        ["cloned_from_route_id"],
    )

    # ------------------------------------------------------------------
    # 4. Locations table mutations. (delivery_type and the school_name →
    #    name rename now come from main's e4f6a7b8c9d0, one of this
    #    revision's two parents — we only add in_roster here.)
    # ------------------------------------------------------------------
    op.add_column(
        "locations",
        sa.Column(
            "in_roster",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )

    # Backfill: in_roster from old state.
    op.execute(
        """
        UPDATE locations
        SET in_roster = (state = 'ACTIVE')
        WHERE state IS NOT NULL
        """
    )

    # Drop server default — app must specify the value going forward.
    op.alter_column("locations", "in_roster", server_default=None)

    # Old state column is gone.
    op.drop_column("locations", "state")

    # ------------------------------------------------------------------
    # 5. Create snapshot tables. Existence of a row == the parent grain
    #    is frozen. No separate flag column; created_at / updated_at
    #    come from BaseModel and double as freeze-time / last-correction.
    # ------------------------------------------------------------------
    op.create_table(
        "route_snapshots",
        sa.Column("route_id", sa.Uuid(), nullable=False),
        sa.Column("start_address", sa.String(), nullable=False),
        sa.Column("start_latitude", sa.Float(), nullable=False),
        sa.Column("start_longitude", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["route_id"],
            ["routes.route_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("route_id"),
    )

    op.create_table(
        "route_stop_snapshots",
        sa.Column("route_stop_id", sa.Uuid(), nullable=False),
        sa.Column("address", sa.String(), nullable=False),
        sa.Column("contact_name", sa.String(), nullable=False),
        sa.Column("phone_number", sa.String(), nullable=False),
        sa.Column("num_boxes", sa.Integer(), nullable=False),
        sa.Column("notes", sa.String(), nullable=False, server_default=""),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["route_stop_id"],
            ["route_stops.route_stop_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("route_stop_id"),
    )
    op.alter_column("route_stop_snapshots", "notes", server_default=None)


def downgrade() -> None:
    # Best-effort downgrade. The route data was deleted on upgrade, so
    # this restores the schema only — the rows are gone for good.
    op.drop_table("route_stop_snapshots")
    op.drop_table("route_snapshots")

    op.add_column(
        "locations",
        sa.Column(
            "state",
            sa.String(),
            nullable=False,
            server_default="ACTIVE",
        ),
    )
    op.execute(
        """
        UPDATE locations
        SET state = CASE WHEN in_roster THEN 'ACTIVE' ELSE 'ARCHIVED' END
        """
    )
    op.alter_column("locations", "state", server_default=None)
    op.drop_column("locations", "in_roster")

    op.drop_index("ix_routes_cloned_from_route_id", table_name="routes")
    op.drop_index("ix_routes_driver_id", table_name="routes")
    op.drop_index("ix_routes_route_group_id", table_name="routes")
    op.drop_constraint(
        "fk_routes_cloned_from_route_id_routes", "routes", type_="foreignkey"
    )
    op.drop_constraint("fk_routes_driver_id_drivers", "routes", type_="foreignkey")
    op.drop_constraint(
        "fk_routes_route_group_id_route_groups", "routes", type_="foreignkey"
    )
    op.drop_column("routes", "cloned_from_route_id")
    op.drop_column("routes", "start_time")
    op.drop_column("routes", "driver_id")
    op.drop_column("routes", "route_group_id")

    op.alter_column(
        "routes",
        "encoded_polyline",
        existing_type=sa.Text(),
        type_=sqlmodel.sql.sqltypes.AutoString(length=10000),
        existing_nullable=True,
    )
    op.add_column(
        "routes",
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.create_table(
        "route_group_memberships",
        sa.Column("route_group_membership_id", sa.Uuid(), nullable=False),
        sa.Column("route_group_id", sa.Uuid(), nullable=False),
        sa.Column("route_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["route_group_id"], ["route_groups.route_group_id"]),
        sa.ForeignKeyConstraint(["route_id"], ["routes.route_id"]),
        sa.PrimaryKeyConstraint("route_group_membership_id"),
    )

    op.create_table(
        "driver_assignments",
        sa.Column("driver_assignment_id", sa.Uuid(), nullable=False),
        sa.Column("driver_id", sa.Uuid(), nullable=False),
        sa.Column("route_id", sa.Uuid(), nullable=False),
        sa.Column("route_group_id", sa.Uuid(), nullable=False),
        sa.Column("time", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["driver_id"], ["drivers.driver_id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["route_id"], ["routes.route_id"]),
        sa.ForeignKeyConstraint(["route_group_id"], ["route_groups.route_group_id"]),
        sa.PrimaryKeyConstraint("driver_assignment_id"),
    )

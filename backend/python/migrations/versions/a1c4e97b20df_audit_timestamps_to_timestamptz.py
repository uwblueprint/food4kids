"""Store audit timestamps as timestamptz holding UTC

Every timestamp column outside the handful that were already `timestamptz`
(`routes.polyline_updated_at`, `user_invites.expires_at`,
`password_reset_tokens.expires_at`) held a *naive* local time: the wall clock
in America/New_York with the offset discarded. The zone survived only as
convention, and Python reads a naive value back as the container's local time
(UTC in every environment we run), so the same column meant one thing to the
code that wrote it and another to the code that read it.

The `USING <col> AT TIME ZONE 'America/New_York'` clause is what makes this
safe: it reinterprets each existing naive value as the EST it actually was and
converts to the equivalent instant. Without it Postgres would assume the values
were already UTC and silently shift everything by four or five hours.

Values landing in the ambiguous 01:00-02:00 window of a DST fall-back are the
one lossy case — Postgres picks one of the two possible instants. That is
inherent to naive local storage and cannot be recovered from the data.

Revision ID: a1c4e97b20df
Revises: f1a7c0d92b45
"""

from collections.abc import Sequence

from alembic import op

revision: str = "a1c4e97b20df"
down_revision: str | None = "f2a8c1d4e6b0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# The zone these naive values were stamped in. Hardcoded rather than read from
# settings.scheduler_timezone: this is a statement about data already on disk,
# so it must not change if that setting ever does.
LEGACY_ZONE = "America/New_York"

# (table, column) for every timestamp that was naive before this migration.
COLUMNS: list[tuple[str, str]] = [
    ("admin_info", "created_at"),
    ("admin_info", "updated_at"),
    ("announcement_last_reads", "created_at"),
    ("announcement_last_reads", "last_read_at"),
    ("announcement_last_reads", "updated_at"),
    ("announcements", "created_at"),
    ("announcements", "updated_at"),
    ("drivers", "created_at"),
    ("drivers", "updated_at"),
    ("jobs", "created_at"),
    ("jobs", "finished_at"),
    ("jobs", "started_at"),
    ("jobs", "updated_at"),
    ("location_groups", "created_at"),
    ("location_groups", "updated_at"),
    ("locations", "created_at"),
    ("locations", "updated_at"),
    ("note_chains", "created_at"),
    ("note_chains", "updated_at"),
    ("notes", "created_at"),
    ("notes", "updated_at"),
    ("password_reset_tokens", "created_at"),
    ("password_reset_tokens", "updated_at"),
    ("route_groups", "created_at"),
    ("route_groups", "updated_at"),
    ("route_snapshots", "created_at"),
    ("route_snapshots", "updated_at"),
    ("route_stop_snapshots", "created_at"),
    ("route_stop_snapshots", "updated_at"),
    ("route_stops", "created_at"),
    ("route_stops", "updated_at"),
    ("routes", "created_at"),
    ("routes", "updated_at"),
    ("system_settings", "created_at"),
    ("system_settings", "updated_at"),
    ("user_invites", "created_at"),
    ("user_invites", "updated_at"),
    ("users", "created_at"),
    ("users", "updated_at"),
]


def upgrade() -> None:
    for table, column in COLUMNS:
        op.execute(
            f'ALTER TABLE "{table}" ALTER COLUMN "{column}" '
            f"TYPE TIMESTAMP WITH TIME ZONE "
            f"USING \"{column}\" AT TIME ZONE '{LEGACY_ZONE}'"
        )


def downgrade() -> None:
    # The mirror image: render each instant back into EST wall-clock time and
    # drop the offset, so a downgrade restores exactly what upgrade() read.
    for table, column in COLUMNS:
        op.execute(
            f'ALTER TABLE "{table}" ALTER COLUMN "{column}" '
            f"TYPE TIMESTAMP WITHOUT TIME ZONE "
            f"USING \"{column}\" AT TIME ZONE '{LEGACY_ZONE}'"
        )

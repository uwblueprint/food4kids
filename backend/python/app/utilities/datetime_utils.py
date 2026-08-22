from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app.config import settings


def now_utc() -> datetime:
    """Current instant, timezone-aware in UTC.

    Timestamps are stored as `timestamptz` and converted to
    `settings.scheduler_timezone` at the edges (reports, emails, the API's
    presentation layer) rather than at the point of writing.

    Never store a naive datetime. A naive value keeps the wall-clock digits and
    drops the offset, so the zone it was stamped in survives only as convention.
    Python then reads it back as the container's local time — UTC in every
    environment we run — which is four or five hours off from the EST the
    caller meant, with no exception raised.
    """
    return datetime.now(timezone.utc)


def from_local_wall_clock(wall_clock: datetime) -> datetime:
    """Read a naive local wall-clock time as a real instant, in UTC.

    For values that genuinely mean "08:00 in Waterloo" — a time typed by a
    coordinator, a seeded schedule — as opposed to an instant already known in
    UTC, which needs no conversion.

    Unlike the migration's hardcoded zone, this reads
    `settings.scheduler_timezone`: it interprets input arriving now, so it
    should follow the timezone the app is configured to operate in.
    """
    if wall_clock.tzinfo is not None:
        raise ValueError(
            f"expected a naive wall-clock datetime, got {wall_clock!r} "
            "which already carries a timezone"
        )
    return wall_clock.replace(tzinfo=ZoneInfo(settings.scheduler_timezone)).astimezone(
        timezone.utc
    )

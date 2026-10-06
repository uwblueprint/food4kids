from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from app.config import settings


def app_timezone() -> ZoneInfo:
    """The zone the organization operates in, per `settings.scheduler_timezone`."""
    return ZoneInfo(settings.scheduler_timezone)


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


def now_local() -> datetime:
    """The same instant as `now_utc()`, rendered on the organization's clock.

    Aware, so it stays comparable with stored `timestamptz` values. Use it when
    the answer is a wall-clock fact — which calendar day, month or year it is
    where the deliveries happen — rather than a point on the timeline.
    """
    return now_utc().astimezone(app_timezone())


def today_local() -> date:
    """Today's calendar date on the organization's clock.

    Drive dates, freeze runs and reminder lead days are all local calendar
    facts, so this is the only correct source for "today" in that logic.
    `date.today()` reads the process clock, which is UTC in every container we
    deploy: for the four or five hours between local evening and local midnight
    it is already tomorrow, and nothing raises.
    """
    return now_local().date()


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
    return wall_clock.replace(tzinfo=app_timezone()).astimezone(timezone.utc)

"""Tests for the timestamp helpers in ``app.utilities.datetime_utils``.

These need no database: they pin down the two conversions every timestamp in
the schema depends on. The property that matters throughout is that a stored
timestamp carries its offset, so it means the same instant to the code that
writes it and the code that reads it back.
"""

from datetime import UTC, date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from app.config import settings
from app.utilities.datetime_utils import (
    from_local_wall_clock,
    now_local,
    now_utc,
    today_local,
)

APP_ZONE = ZoneInfo(settings.scheduler_timezone)


class TestNowUtc:
    def test_is_timezone_aware(self) -> None:
        assert now_utc().tzinfo is not None

    def test_is_utc(self) -> None:
        assert now_utc().utcoffset() == timedelta(0)

    def test_tracks_real_time(self) -> None:
        """Sanity check that it returns *now*, not a fixed or local-shifted value."""
        drift = abs((now_utc() - datetime.now(UTC)).total_seconds())
        assert drift < 5

    def test_comparable_with_other_aware_datetimes(self) -> None:
        """The whole point: no TypeError against an aware value from the DB."""
        assert now_utc() > datetime(2020, 1, 1, tzinfo=UTC)

    def test_not_comparable_with_naive_datetimes(self) -> None:
        """A naive value is now a loud failure rather than a silent 4-hour skew."""
        with pytest.raises(TypeError):
            _ = now_utc() > datetime(2020, 1, 1)


class TestFromLocalWallClock:
    @pytest.mark.parametrize(
        ("wall_clock", "expected_offset_hours"),
        [
            # EST (no DST): Waterloo is UTC-5, so 08:00 local is 13:00 UTC.
            (datetime(2026, 1, 15, 8, 0), 5),
            # EDT (DST): UTC-4, so 08:00 local is 12:00 UTC.
            (datetime(2026, 7, 15, 8, 0), 4),
        ],
    )
    def test_offset_follows_dst(
        self, wall_clock: datetime, expected_offset_hours: int
    ) -> None:
        result = from_local_wall_clock(wall_clock)

        assert result.tzinfo is not None
        assert result.utcoffset() == timedelta(0)
        assert result.hour == wall_clock.hour + expected_offset_hours

    def test_preserves_the_wall_clock_reading_in_the_app_zone(self) -> None:
        """Converting back into the app's zone returns the original digits."""
        wall_clock = datetime(2026, 3, 20, 14, 37, 12)

        round_tripped = from_local_wall_clock(wall_clock).astimezone(APP_ZONE)

        assert round_tripped.replace(tzinfo=None) == wall_clock

    def test_midnight_boundary_lands_on_the_previous_utc_day(self) -> None:
        """Local midnight is the prior day in UTC — the case a naive value hides."""
        result = from_local_wall_clock(datetime(2026, 2, 1, 0, 30))

        assert result.date() == datetime(2026, 2, 1).date()
        assert result.hour == 5

    def test_ordering_is_preserved(self) -> None:
        earlier = from_local_wall_clock(datetime(2026, 5, 1, 9, 0))
        later = from_local_wall_clock(datetime(2026, 5, 1, 17, 0))

        assert earlier < later

    def test_rejects_an_already_aware_datetime(self) -> None:
        """Passing an instant would double-apply the offset, so it must fail."""
        with pytest.raises(ValueError, match="naive wall-clock"):
            from_local_wall_clock(datetime(2026, 1, 15, 8, 0, tzinfo=UTC))

    def test_rejects_an_aware_datetime_even_in_the_app_zone(self) -> None:
        with pytest.raises(ValueError, match="naive wall-clock"):
            from_local_wall_clock(datetime(2026, 1, 15, 8, 0, tzinfo=APP_ZONE))

    def test_result_is_comparable_with_now_utc(self) -> None:
        past = from_local_wall_clock(datetime(2020, 1, 1, 0, 0))

        assert past < now_utc()

    def test_dst_spring_forward_gap_resolves_without_raising(self) -> None:
        """02:30 on the spring-forward date does not exist locally; zoneinfo
        resolves it rather than failing, which is the documented behaviour."""
        result = from_local_wall_clock(datetime(2026, 3, 8, 2, 30))

        assert result.tzinfo is not None
        assert result.utcoffset() == timedelta(0)

    def test_dst_fall_back_ambiguity_picks_the_first_instant(self) -> None:
        """01:30 on the fall-back date happens twice; zoneinfo picks fold=0.
        This is the one lossy case inherent to naive local storage."""
        ambiguous = datetime(2026, 11, 1, 1, 30)

        result = from_local_wall_clock(ambiguous)
        expected = ambiguous.replace(tzinfo=APP_ZONE, fold=0).astimezone(timezone.utc)

        assert result == expected


class TestNowLocal:
    """`now_local()` is the same instant as `now_utc()`, read on F4K's clock."""

    def test_carries_the_app_zone_offset(self) -> None:
        assert now_local().utcoffset() == datetime.now(APP_ZONE).utcoffset()

    def test_is_the_same_instant_as_now_utc(self) -> None:
        """Rendering in another zone must not move the point on the timeline."""
        assert abs((now_local() - now_utc()).total_seconds()) < 5

    def test_comparable_with_stored_utc_timestamps(self) -> None:
        """It stays aware, so it compares against a `timestamptz` read."""
        assert now_local() > datetime(2020, 1, 1, tzinfo=UTC)


class TestTodayLocal:
    """The boundary this helper exists for: local evening, once UTC has rolled."""

    def test_matches_the_date_of_now_local(self) -> None:
        assert today_local() == now_local().date()

    def test_returns_a_plain_date(self) -> None:
        assert type(today_local()) is date

    @pytest.mark.parametrize(
        ("local_wall_clock", "utc_date"),
        [
            # 23:30 EDT on Aug 31 is 03:30 UTC on Sep 1. A UTC `date.today()`
            # has already rolled into September; the local calendar has not.
            (datetime(2026, 8, 31, 23, 30), date(2026, 9, 1)),
            # 23:59 EST on Dec 31 is 04:59 UTC on Jan 1 — the year rolls too.
            (datetime(2026, 12, 31, 23, 59), date(2027, 1, 1)),
            # 20:00 EDT is exactly midnight UTC: the first minute of the skew.
            (datetime(2026, 6, 15, 20, 0), date(2026, 6, 16)),
            # 19:00 EST (winter offset is an hour deeper) is midnight UTC.
            (datetime(2026, 1, 20, 19, 0), date(2026, 1, 21)),
        ],
    )
    def test_local_evening_is_already_the_next_utc_day(
        self, local_wall_clock: datetime, utc_date: date
    ) -> None:
        """Pin the skew without freezing the clock.

        `today_local()` reads the real time, so instead of faking it these
        assert the property it relies on: at these instants the UTC date and
        the local date genuinely differ, and the local one is what the drive
        calendar means. If they ever agreed, the helper would be pointless.
        """
        instant = from_local_wall_clock(local_wall_clock)

        assert instant.date() == utc_date
        assert instant.astimezone(APP_ZONE).date() == local_wall_clock.date()
        assert instant.date() != local_wall_clock.date()

    def test_local_daytime_agrees_with_utc(self) -> None:
        """Mid-day is the case that hides the bug: both notions match."""
        instant = from_local_wall_clock(datetime(2026, 8, 31, 9, 0))

        assert instant.date() == instant.astimezone(APP_ZONE).date()

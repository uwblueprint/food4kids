"""Tests for the timestamp helpers in ``app.utilities.datetime_utils``.

These need no database: they pin down the two conversions every timestamp in
the schema depends on. The property that matters throughout is that a stored
timestamp carries its offset, so it means the same instant to the code that
writes it and the code that reads it back.
"""

from datetime import UTC, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from app.config import settings
from app.utilities.datetime_utils import from_local_wall_clock, now_utc

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

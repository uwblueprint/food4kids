"""Tests for the reports monthly series window.

The window is what the homepage statistics charts plot, so the invariant
under test is that `month_span` always returns exactly `months` consecutive
calendar months, oldest first, ending on the requested month — including
across year boundaries, where naive month arithmetic goes wrong.
"""

from app.services.implementations.driver_report_service import month_span


def test_span_ends_on_requested_month_oldest_first():
    assert month_span(2026, 8, 6) == [
        (2026, 3),
        (2026, 4),
        (2026, 5),
        (2026, 6),
        (2026, 7),
        (2026, 8),
    ]


def test_span_walks_back_across_a_year_boundary():
    assert month_span(2026, 3, 6) == [
        (2025, 10),
        (2025, 11),
        (2025, 12),
        (2026, 1),
        (2026, 2),
        (2026, 3),
    ]


def test_january_is_month_one_not_month_zero():
    # December/January is where an off-by-one in the modulo shows up.
    assert month_span(2026, 1, 3) == [(2025, 11), (2025, 12), (2026, 1)]
    assert month_span(2026, 12, 2) == [(2026, 11), (2026, 12)]


def test_single_month_window():
    assert month_span(2026, 7, 1) == [(2026, 7)]


def test_window_length_always_matches_months_requested():
    for months in range(1, 25):
        assert len(month_span(2026, 5, months)) == months

import logging
from datetime import date
from typing import Any

from sqlalchemy import extract, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Subquery
from sqlmodel import col, select

from app.models.driver import Driver
from app.models.route import Route
from app.models.route_group import RouteGroup
from app.models.route_stop import RouteStop
from app.models.route_stop_snapshot import RouteStopSnapshot
from app.models.user import User
from app.services.implementations.driver_history_service import (
    mileage_events,
    month_bounds,
)


def month_span(end_year: int, end_month: int, months: int) -> list[tuple[int, int]]:
    """The `months` consecutive (year, month) pairs ending at end_year/end_month.

    Oldest first, so the caller can render it left-to-right without reversing.
    """
    ordinals = range(
        end_year * 12 + (end_month - 1) - (months - 1), end_year * 12 + end_month
    )
    return [(ordinal // 12, ordinal % 12 + 1) for ordinal in ordinals]


def delivery_events(bounds: tuple[date, date] | None = None) -> Subquery:
    """Deliveries as (year, month) rows — one row per delivery.

    A delivery is one stop on one drive date: a route_stop_snapshots row,
    which exists only once the route has been driven and frozen. Routes with
    no driver are included, mirroring `mileage_events`: the column is nulled
    when a driver is deleted, so excluding them would drop a departed
    volunteer's deliveries out of the org's all-time total for good.

    `bounds` is a half-open [start, end) drive_date range, applied to the raw
    column so it stays index-friendly. None means all time.
    """
    events: Any = (
        select(
            extract("year", col(RouteGroup.drive_date)).label("year"),
            extract("month", col(RouteGroup.drive_date)).label("month"),
        )
        .select_from(RouteStopSnapshot)
        .join(RouteStop)
        .join(Route)
        .join(RouteGroup)
    )

    if bounds is not None:
        start, end = bounds
        events = events.where(
            col(RouteGroup.drive_date) >= start, col(RouteGroup.drive_date) < end
        )

    subquery: Subquery = events.subquery()
    return subquery


class DriverReportService:
    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger

    async def get_monthly_series(
        self, session: AsyncSession, end_year: int, end_month: int, months: int
    ) -> list[dict]:
        """Per-month km and deliveries for the `months` window ending at
        end_year/end_month, oldest first.

        Two grouped queries rather than one round trip per month, then months
        with no activity are filled back in as zeroes so the caller always
        gets a dense series it can chart directly.
        """
        try:
            span = month_span(end_year, end_month, months)
            start_year, start_month = span[0]
            bounds = (
                date(start_year, start_month, 1),
                month_bounds(end_year, end_month)[1],
            )

            events = mileage_events(bounds=bounds)
            km_statement = select(
                events.c.year,
                events.c.month,
                func.coalesce(func.sum(events.c.km), 0.0).label("km"),
            ).group_by(events.c.year, events.c.month)
            km_rows = (await session.execute(km_statement)).all()
            km_by_month = {(int(r.year), int(r.month)): float(r.km) for r in km_rows}

            deliveries = delivery_events(bounds)
            deliveries_statement = select(
                deliveries.c.year,
                deliveries.c.month,
                func.count().label("deliveries"),
            ).group_by(deliveries.c.year, deliveries.c.month)
            delivery_rows = (await session.execute(deliveries_statement)).all()
            deliveries_by_month = {
                (int(r.year), int(r.month)): int(r.deliveries) for r in delivery_rows
            }

            return [
                {
                    "year": year,
                    "month": month,
                    "total_km": km_by_month.get((year, month), 0.0),
                    "total_deliveries": deliveries_by_month.get((year, month), 0),
                }
                for year, month in span
            ]
        except Exception:
            self.logger.exception("Failed to compute monthly series")
            raise

    async def get_monthly_km_ranking(
        self, session: AsyncSession, year: int, month: int
    ) -> list[dict]:
        """Return per-driver km for given year/month ordered desc by km.

        Derived from frozen-route lengths. The join to Driver is what drops
        routes with no driver — they count towards the org's totals but have
        nobody to rank."""
        try:
            events = mileage_events(bounds=month_bounds(year, month))
            km_sum = func.sum(events.c.km).label("km")
            statement = (
                select(events.c.driver_id, User.first_name, User.last_name, km_sum)
                .select_from(events)
                .join(Driver, col(Driver.driver_id) == events.c.driver_id)
                .join(User, col(User.user_id) == col(Driver.user_id))
                .group_by(events.c.driver_id, User.first_name, User.last_name)
                .order_by(km_sum.desc())
            )
            result = await session.execute(statement)
            rows = result.all()

            rankings: list[dict] = []
            for row in rows:
                rankings.append(
                    {
                        "driver_id": str(row.driver_id),
                        "driver_name": f"{row.first_name} {row.last_name}",
                        "km": float(row.km),
                    }
                )

            return rankings
        except Exception:
            self.logger.exception("Failed to compute monthly km ranking")
            raise

    async def get_total_km(
        self, session: AsyncSession, bounds: tuple[date, date] | None = None
    ) -> float:
        """Total km driven over a half-open [start, end) drive_date range, or
        over all time when `bounds` is None."""
        try:
            events = mileage_events(bounds=bounds)
            statement = select(func.coalesce(func.sum(events.c.km), 0.0))
            result = await session.execute(statement)
            return float(result.scalar_one() or 0.0)
        except Exception:
            self.logger.exception("Failed to compute total km")
            raise

    async def get_total_deliveries(
        self, session: AsyncSession, bounds: tuple[date, date] | None = None
    ) -> int:
        """Total deliveries over a half-open [start, end) drive_date range, or
        over all time when `bounds` is None.

        The all-time figure is aggregated in SQL rather than by summing a
        series, so it neither grows a round trip per month of history nor ties
        a headline total to whatever window a chart happens to plot.
        """
        try:
            events = delivery_events(bounds)
            statement = select(func.count()).select_from(events)
            result = await session.execute(statement)
            return int(result.scalar_one() or 0)
        except Exception:
            self.logger.exception("Failed to count deliveries")
            raise

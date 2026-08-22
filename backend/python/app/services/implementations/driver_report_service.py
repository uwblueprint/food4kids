import logging
from datetime import date, datetime
from zoneinfo import ZoneInfo

from sqlalchemy import extract, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from app.config import settings
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


class DriverReportService:
    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger
        self.timezone = ZoneInfo(settings.scheduler_timezone)

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

            drive_year = extract("year", col(RouteGroup.drive_date)).label("year")
            drive_month = extract("month", col(RouteGroup.drive_date)).label("month")
            deliveries_statement = (
                select(drive_year, drive_month, func.count().label("deliveries"))
                .select_from(RouteStopSnapshot)
                .join(RouteStop)
                .join(Route)
                .join(RouteGroup)
                .where(
                    col(RouteGroup.drive_date) >= bounds[0],
                    col(RouteGroup.drive_date) < bounds[1],
                )
                .group_by(drive_year, drive_month)
            )
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

        Derived from frozen-route lengths."""
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

    async def get_total_km_for_month(
        self, session: AsyncSession, year: int, month: int
    ) -> float:
        try:
            events = mileage_events(bounds=month_bounds(year, month))
            statement = select(func.coalesce(func.sum(events.c.km), 0.0))
            result = await session.execute(statement)
            total = result.scalar_one()
            return float(total or 0.0)
        except Exception:
            self.logger.exception("Failed to compute total km for month")
            raise

    async def get_total_deliveries_between(
        self, session: AsyncSession, start_dt: datetime, end_dt: datetime
    ) -> int:
        """Count RouteStopSnapshot rows whose parent RouteGroup.drive_date
        falls between start_dt and end_dt.
        start_dt and end_dt should be timezone-aware datetimes.
        """
        try:
            # Land in the scheduler timezone before taking the calendar day —
            # the same instant is a different date either side of midnight.
            if start_dt.tzinfo is not None:
                start_dt = start_dt.astimezone(self.timezone)
            if end_dt.tzinfo is not None:
                end_dt = end_dt.astimezone(self.timezone)

            start_d = start_dt.date()
            end_d = end_dt.date()

            # Join route_stop_snapshots -> route_stops -> routes -> route_groups
            # Use model-based joins so sqlalchemy resolves FK-based ON clauses
            stmt = (
                select(func.count())
                .select_from(RouteStopSnapshot)
                .join(RouteStop)
                .join(Route)
                .join(RouteGroup)
                .where(RouteGroup.drive_date >= start_d, RouteGroup.drive_date <= end_d)
            )

            result = await session.execute(stmt)
            count = result.scalar_one()
            return int(count or 0)
        except Exception:
            self.logger.exception("Failed to count deliveries between dates")
            raise

    async def get_total_deliveries_for_month(
        self, session: AsyncSession, year: int, month: int
    ) -> int:
        # Build month boundaries in scheduler timezone and pass them through
        start = datetime(year, month, 1, 0, 0, tzinfo=self.timezone)
        if month == 12:
            end = datetime(year + 1, 1, 1, 0, 0, tzinfo=self.timezone)
        else:
            end = datetime(year, month + 1, 1, 0, 0, tzinfo=self.timezone)

        return await self.get_total_deliveries_between(session, start, end)

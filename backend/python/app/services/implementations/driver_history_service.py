import logging
from datetime import date, datetime
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import extract, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Subquery
from sqlmodel import col, select

from app.config import settings
from app.models.driver import Driver
from app.models.driver_mileage import (
    MAX_YEAR,
    MIN_YEAR,
    DriverHistoryRead,
    DriverHistorySummary,
)
from app.models.route import Route
from app.models.route_group import RouteGroup
from app.models.route_snapshot import RouteSnapshot


def month_bounds(year: int, month: int | None = None) -> tuple[date, date]:
    """Half-open [start, end) covering a whole year, or one month of it.

    Callers filter on the raw drive_date with these instead of
    `extract(year/month) = ...`, which can't use the drive_date index.
    """
    if month is None:
        return date(year, 1, 1), date(year + 1, 1, 1)
    if month == 12:
        return date(year, 12, 1), date(year + 1, 1, 1)
    return date(year, month, 1), date(year, month + 1, 1)


def mileage_events(
    driver_id: UUID | None = None,
    bounds: tuple[date, date] | None = None,
) -> Subquery:
    """Frozen-route mileage as (driver_id, year, month, km) rows.

    A route counts once it's frozen (has a RouteSnapshot), bucketed by its
    group's drive_date month. `bounds` is a half-open [start, end)
    drive_date range, applied to the raw column so it stays index-friendly.
    """
    events: Any = (
        select(
            col(Route.driver_id).label("driver_id"),
            extract("year", col(RouteGroup.drive_date)).label("year"),
            extract("month", col(RouteGroup.drive_date)).label("month"),
            col(Route.length).label("km"),
        )
        .join(RouteSnapshot, RouteSnapshot.route_id == Route.route_id)  # type: ignore[arg-type]
        .join(RouteGroup, RouteGroup.route_group_id == Route.route_group_id)  # type: ignore[arg-type]
        .where(col(Route.driver_id).isnot(None))
    )

    if driver_id is not None:
        events = events.where(Route.driver_id == driver_id)

    if bounds is not None:
        start, end = bounds
        events = events.where(
            col(RouteGroup.drive_date) >= start, col(RouteGroup.drive_date) < end
        )

    subquery: Subquery = events.subquery()
    return subquery


class DriverHistoryService:
    """Driver mileage service.

    Mileage is derived, never stored: the sum of Route.length over a
    driver's frozen routes, bucketed by the route group's drive_date month.
    Reassigning a route, correcting its stops, or fixing a group's date
    therefore updates history automatically — there is no stored total to
    drift out of sync.
    """

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize service"""
        self.logger = logger
        self.timezone = ZoneInfo(settings.scheduler_timezone)

    def validate_year(self, year: int) -> bool:
        return isinstance(year, int) and MIN_YEAR <= year <= MAX_YEAR

    async def driver_exists(self, session: AsyncSession, driver_id: UUID) -> bool:
        statement = select(Driver.driver_id).where(Driver.driver_id == driver_id)
        result = await session.execute(statement)
        return result.scalar_one_or_none() is not None

    async def get_monthly_totals(
        self,
        session: AsyncSession,
        driver_id: UUID,
        year: int | None = None,
        month: int | None = None,
    ) -> list[DriverHistoryRead]:
        """Monthly km totals for a driver, optionally narrowed to a year or
        a single month."""
        try:
            bounds = month_bounds(year, month) if year is not None else None
            events = mileage_events(driver_id, bounds)
            statement = (
                select(
                    events.c.year,
                    events.c.month,
                    func.sum(events.c.km).label("km"),
                )
                .group_by(events.c.year, events.c.month)
                .order_by(events.c.year, events.c.month)
            )

            result = await session.execute(statement)
            return [
                DriverHistoryRead(
                    driver_id=driver_id,
                    year=int(row.year),
                    month=int(row.month),
                    km=float(row.km),
                )
                for row in result.all()
            ]
        except Exception as e:
            self.logger.error(f"Failed to get monthly totals: {e!s}")
            raise e

    async def get_yearly_totals_by_driver(
        self, session: AsyncSession, year: int
    ) -> dict[UUID, float]:
        """Per-driver km totals for one year (powers the CSV export)."""
        try:
            events = mileage_events(bounds=month_bounds(year))
            statement = select(
                events.c.driver_id,
                func.sum(events.c.km).label("km"),
            ).group_by(events.c.driver_id)
            result = await session.execute(statement)
            return {row.driver_id: float(row.km) for row in result.all()}
        except Exception as e:
            self.logger.error(f"Failed to get yearly totals: {e!s}")
            raise e

    async def get_driver_history_summary(
        self, session: AsyncSession, driver_id: UUID
    ) -> DriverHistorySummary:
        """Total km driven by the driver across all time, plus the current
        year's km (current year determined in the local timezone)."""
        try:
            current_year = datetime.now(self.timezone).year
            monthly = await self.get_monthly_totals(session, driver_id)

            return DriverHistorySummary(
                lifetime_km=sum(m.km for m in monthly),
                current_year_km=sum(m.km for m in monthly if m.year == current_year),
            )
        except Exception as e:
            self.logger.error(
                f"Failed to get summary of driver's history (i.e. km driven in total and this year): {e}"
            )
            raise e

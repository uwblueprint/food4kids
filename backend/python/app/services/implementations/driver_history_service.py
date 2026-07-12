import logging
from datetime import date, datetime
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import extract, func, union_all
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from app.config import settings
from app.models.driver import Driver
from app.models.driver_history import (
    MAX_YEAR,
    MIN_YEAR,
    DriverHistoryRead,
    DriverHistorySummary,
    DriverMileageAdjustment,
)
from app.models.route import Route
from app.models.route_group import RouteGroup
from app.models.route_snapshot import RouteSnapshot


class DriverHistoryService:
    """Driver mileage service.

    Mileage is DERIVED, never stored: a driver's km is the sum of
    Route.length over their frozen routes (routes with a RouteSnapshot),
    bucketed by the route group's drive_date month, plus signed manual
    adjustments. Reassigning a route, correcting its stops/length, or
    fixing a group's date therefore updates history automatically — there
    is no stored total to drift out of sync.
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

    @staticmethod
    def _mileage_events(driver_id: UUID | None = None):  # type: ignore[no-untyped-def]
        """UNION ALL of the two mileage sources as (driver_id, year, month,
        km) rows: frozen-route lengths and manual adjustments. Optionally
        scoped to one driver."""
        frozen_routes: Any = (
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
        adjustments: Any = select(
            col(DriverMileageAdjustment.driver_id).label("driver_id"),
            extract("year", col(DriverMileageAdjustment.drive_date)).label("year"),
            extract("month", col(DriverMileageAdjustment.drive_date)).label("month"),
            col(DriverMileageAdjustment.km).label("km"),
        ).where(col(DriverMileageAdjustment.driver_id).isnot(None))

        if driver_id is not None:
            frozen_routes = frozen_routes.where(Route.driver_id == driver_id)
            adjustments = adjustments.where(
                DriverMileageAdjustment.driver_id == driver_id
            )

        return union_all(frozen_routes, adjustments).subquery("mileage_events")

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
            events = self._mileage_events(driver_id)
            statement = (
                select(
                    events.c.year,
                    events.c.month,
                    func.sum(events.c.km).label("km"),
                )
                .group_by(events.c.year, events.c.month)
                .order_by(events.c.year, events.c.month)
            )
            if year is not None:
                statement = statement.where(events.c.year == year)
            if month is not None:
                statement = statement.where(events.c.month == month)

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
            events = self._mileage_events()
            statement = (
                select(
                    events.c.driver_id,
                    func.sum(events.c.km).label("km"),
                )
                .where(events.c.year == year)
                .group_by(events.c.driver_id)
            )
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

    async def create_adjustment(
        self,
        session: AsyncSession,
        driver_id: UUID,
        drive_date: date,
        km: float,
        note: str,
    ) -> DriverMileageAdjustment:
        """Post a signed manual mileage adjustment.

        Corrections never overwrite: the driver's total is derived from
        routes plus the sum of adjustments, so this composes with route
        credits instead of fighting them.
        """
        if km == 0:
            raise ValueError("Adjustment km must be non-zero")
        try:
            adjustment = DriverMileageAdjustment(
                driver_id=driver_id,
                drive_date=drive_date,
                km=km,
                note=note,
            )
            session.add(adjustment)
            await session.commit()
            await session.refresh(adjustment)
            return adjustment
        except Exception as e:
            self.logger.error(f"Failed to create mileage adjustment: {e!s}")
            await session.rollback()
            raise e

    async def get_adjustments(
        self, session: AsyncSession, driver_id: UUID
    ) -> list[DriverMileageAdjustment]:
        """A driver's manual adjustments, newest first (audit view)."""
        try:
            statement = (
                select(DriverMileageAdjustment)
                .where(col(DriverMileageAdjustment.driver_id) == driver_id)
                .order_by(
                    col(DriverMileageAdjustment.drive_date).desc(),
                    col(DriverMileageAdjustment.created_at).desc(),
                )
            )
            result = await session.execute(statement)
            return list(result.scalars().all())
        except Exception as e:
            self.logger.error(f"Failed to get mileage adjustments: {e!s}")
            raise e

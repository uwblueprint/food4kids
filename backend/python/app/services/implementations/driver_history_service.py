import logging
from datetime import date, datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import extract, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from app.config import settings
from app.models.driver import Driver
from app.models.driver_history import (
    MAX_YEAR,
    MIN_YEAR,
    DriverHistory,
    DriverHistoryRead,
    DriverHistorySummary,
)
from app.models.enum import MileageEntryKindEnum


class DriverHistoryService:
    """Driver mileage ledger service.

    driver_history is an append-only ledger (one row per mileage event);
    every total here is a SUM(km) aggregate bucketed by drive_date. Nothing
    in this service mutates or deletes existing entries — corrections are
    new signed MANUAL_ADJUSTMENT entries.
    """

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize service"""
        self.logger = logger
        self.timezone = ZoneInfo(settings.scheduler_timezone)

    def validate_year(self, year: int) -> bool:
        return isinstance(year, int) and MIN_YEAR <= year <= MAX_YEAR

    def validate_year_and_month(self, year: int, month: int | None) -> bool:
        return self.validate_year(year) and (not month or 1 <= month <= 12)

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
        """Monthly km totals for a driver: SUM(km) bucketed by drive_date
        month, optionally narrowed to a year or a single month."""
        try:
            year_expr = extract("year", col(DriverHistory.drive_date))
            month_expr = extract("month", col(DriverHistory.drive_date))

            statement = (
                select(
                    year_expr.label("year"),
                    month_expr.label("month"),
                    func.sum(DriverHistory.km).label("km"),
                )
                .where(col(DriverHistory.driver_id) == driver_id)
                .group_by(year_expr, month_expr)
                .order_by(year_expr, month_expr)
            )
            if year is not None:
                statement = statement.where(year_expr == year)
            if month is not None:
                statement = statement.where(month_expr == month)

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

    async def get_entries(
        self,
        session: AsyncSession,
        driver_id: UUID,
        year: int | None = None,
        month: int | None = None,
    ) -> list[DriverHistory]:
        """Individual ledger entries for a driver (audit view), newest first."""
        try:
            statement = (
                select(DriverHistory)
                .where(col(DriverHistory.driver_id) == driver_id)
                .order_by(
                    col(DriverHistory.drive_date).desc(),
                    col(DriverHistory.created_at).desc(),
                )
            )
            if year is not None:
                statement = statement.where(
                    extract("year", col(DriverHistory.drive_date)) == year
                )
            if month is not None:
                statement = statement.where(
                    extract("month", col(DriverHistory.drive_date)) == month
                )

            result = await session.execute(statement)
            return list(result.scalars().all())
        except Exception as e:
            self.logger.error(f"Failed to get ledger entries: {e!s}")
            raise e

    async def create_adjustment(
        self,
        session: AsyncSession,
        driver_id: UUID,
        drive_date: date,
        km: float,
        note: str,
    ) -> DriverHistory:
        """Post a signed MANUAL_ADJUSTMENT ledger entry.

        Corrections never overwrite: the driver's total is the sum of all
        entries, so this composes with AUTO credits instead of being
        re-inflated by them.
        """
        if km == 0:
            raise ValueError("Adjustment km must be non-zero")
        try:
            entry = DriverHistory(
                driver_id=driver_id,
                route_id=None,
                drive_date=drive_date,
                km=km,
                kind=MileageEntryKindEnum.MANUAL_ADJUSTMENT,
                note=note,
            )
            session.add(entry)
            await session.commit()
            await session.refresh(entry)
            return entry
        except Exception as e:
            self.logger.error(f"Failed to create mileage adjustment: {e!s}")
            await session.rollback()
            raise e

    async def get_yearly_totals_by_driver(
        self, session: AsyncSession, year: int
    ) -> dict[UUID, float]:
        """Per-driver km totals for one year (powers the CSV export)."""
        try:
            statement = (
                select(
                    col(DriverHistory.driver_id),
                    func.sum(DriverHistory.km).label("km"),
                )
                .where(extract("year", col(DriverHistory.drive_date)) == year)
                .where(col(DriverHistory.driver_id).isnot(None))
                .group_by(col(DriverHistory.driver_id))
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

            lifetime_result = await session.execute(
                select(func.coalesce(func.sum(DriverHistory.km), 0.0)).where(
                    col(DriverHistory.driver_id) == driver_id
                )
            )
            current_year_result = await session.execute(
                select(func.coalesce(func.sum(DriverHistory.km), 0.0))
                .where(col(DriverHistory.driver_id) == driver_id)
                .where(extract("year", col(DriverHistory.drive_date)) == current_year)
            )

            return DriverHistorySummary(
                lifetime_km=float(lifetime_result.scalar_one()),
                current_year_km=float(current_year_result.scalar_one()),
            )
        except Exception as e:
            self.logger.error(
                f"Failed to get summary of driver's history (i.e. km driven in total and this year): {e}"
            )
            raise e

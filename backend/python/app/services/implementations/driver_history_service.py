import logging
from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.config import settings
from app.models.driver import Driver
from app.models.driver_history import (
    MAX_YEAR,
    MIN_YEAR,
    DriverHistory,
    DriverHistorySummary,
)


class DriverHistoryService:
    """Driver history service"""

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize service"""
        self.logger = logger
        self.timezone = ZoneInfo(settings.scheduler_timezone)

    def validate_year(self, year: int) -> bool:
        return MIN_YEAR <= year <= MAX_YEAR

    def validate_year_and_month(self, year: int, month: int | None) -> bool:
        return self.validate_year(year) and (not month or 1 <= month <= 12)

    async def driver_exists(self, session: AsyncSession, driver_id: UUID) -> bool:
        statement = select(Driver.driver_id).where(Driver.driver_id == driver_id)
        result = await session.execute(statement)
        return result.scalar_one_or_none() is not None

    async def get_all_driver_histories(
        self, session: AsyncSession
    ) -> list[DriverHistory]:
        """Get all driver histories"""
        try:
            statement = select(DriverHistory)
            result = await session.execute(statement)
            return list(result.scalars().all())
        except Exception as e:
            self.logger.error(f"Failed to get driver histories: {e!s}")
            raise e

    async def get_driver_history_by_id_year_and_month(
        self, session: AsyncSession, driver_id: UUID, year: int, month: int
    ) -> DriverHistory | None:
        """Return a single driver history for a specific month"""
        statement = select(DriverHistory).where(
            DriverHistory.driver_id == driver_id,
            DriverHistory.year == year,
            DriverHistory.month == month,
        )
        result = await session.execute(statement)
        return result.scalars().first()

    async def get_driver_history_by_id_and_year(
        self, session: AsyncSession, driver_id: UUID, year: int
    ) -> list[DriverHistory]:
        """Return all driver histories for a driver for a specific year"""
        # Fetch all 12 months using the month-specific service
        histories = []
        for month in range(1, 13):
            history = await self.get_driver_history_by_id_year_and_month(
                session, driver_id, year, month
            )
            if history:
                histories.append(history)

        # Sort by month (ascending)
        histories.sort(key=lambda h: h.month)
        return histories

    async def get_driver_history_by_id(
        self, session: AsyncSession, driver_id: UUID
    ) -> list[DriverHistory]:
        """Return all driver histories for a driver"""
        # Fetch all years by first getting distinct years from DB
        statement = (
            select(DriverHistory.year)
            .where(DriverHistory.driver_id == driver_id)
            .distinct()
        )
        result = await session.execute(statement)
        years = [row[0] for row in result.fetchall()]

        histories = []
        for year in sorted(years):
            year_histories = await self.get_driver_history_by_id_and_year(
                session, driver_id, year
            )
            histories.extend(year_histories)

        # Sort overall by year then month
        histories.sort(key=lambda h: (h.year, h.month))
        return histories

    async def create_driver_history(
        self,
        session: AsyncSession,
        driver_id: UUID,
        year: int,
        month: int,
        km: float,
    ) -> DriverHistory:
        """
        Create a new monthly driver history record.
        Enforces:
        - driver must exist
        - unique (driver_id, year, month)
        """
        try:
            driver_history = DriverHistory(
                driver_id=driver_id,
                year=year,
                month=month,
                km=km,
            )

            session.add(driver_history)
            await session.commit()
            await session.refresh(driver_history)

            return driver_history

        except Exception as e:
            self.logger.error(f"Failed to create driver history: {e!s}")
            await session.rollback()
            raise e

    async def update_driver_history(
        self,
        session: AsyncSession,
        driver_id: UUID,
        year: int,
        month: int,
        km: float,
    ) -> DriverHistory:
        """
        Update an existing monthly driver history record.
        """
        try:
            existing_history = await self.get_driver_history_by_id_year_and_month(
                session, driver_id, year, month
            )

            if existing_history is None:
                raise ValueError(
                    f"Driver history for driver {driver_id}, year {year}, month {month} not found"
                )

            existing_history.km = km
            existing_history.updated_at = datetime.now()

            await session.commit()
            await session.refresh(existing_history)

            return existing_history

        except Exception as e:
            self.logger.error(f"Failed to update driver history: {e!s}")
            await session.rollback()
            raise e

    async def delete_driver_history(
        self, session: AsyncSession, driver_id: UUID, year: int, month: int
    ) -> None:
        """
        Delete a monthly driver history record.
        """
        try:
            statement = select(DriverHistory).where(
                DriverHistory.driver_id == driver_id,
                DriverHistory.year == year,
                DriverHistory.month == month,
            )
            result = await session.execute(statement)
            driver_history = result.scalars().first()

            if driver_history is None:
                raise ValueError(
                    f"Driver history for driver {driver_id}, year {year}, month {month} not found"
                )

            await session.delete(driver_history)
            await session.commit()

        except Exception as e:
            self.logger.error(f"Error deleting driver history: {e}")
            await session.rollback()
            raise e

    async def get_driver_history_by_year(
        self, session: AsyncSession, year: int
    ) -> list[DriverHistory]:
        """Get all driver histories by year"""
        try:
            statement = select(DriverHistory).where(DriverHistory.year == year)
            result = await session.execute(statement)
            driver_history = result.scalars().all()

            return list(driver_history)
        except Exception as e:
            self.logger.error(f"Failed to get driver history by year: {e!s}")
            raise e

    async def get_driver_history_summary(
        self, session: AsyncSession, driver_id: UUID
    ) -> DriverHistorySummary:
        """Given a driver's ID, give the total km driven by the driver
        (across all years, etc.), as well as the kilometers driven by the driver during the current year"""
        try:
            # Get driver's info
            driver_history = await self.get_driver_history_by_id(session, driver_id)

            # Calculate the current year in the local timezone to determine which year to get data for
            current_year = datetime.now(self.timezone).year

            # Var to store total kms driven by driver
            total_kms = sum([entry.km for entry in driver_history])

            # Var to store total kms driven by the driver in the current year
            current_year_km = sum(
                [entry.km for entry in driver_history if current_year == entry.year]
            )

            driver_history_summary = DriverHistorySummary(
                lifetime_km=total_kms, current_year_km=current_year_km
            )

            return driver_history_summary

        except Exception as e:
            self.logger.error(
                f"Failed to get summary of driver's history (i.e. km driven in total and this year): {e}"
            )
            raise e

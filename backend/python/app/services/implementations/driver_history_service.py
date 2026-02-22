import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.driver_history import DriverHistory


class DriverHistoryService:
    """Driver history service"""

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize service"""
        self.logger = logger

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
            DriverHistory.month == month
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
            history = await self.get_driver_history_by_id_year_and_month(session, driver_id, year, month)
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
        statement = select(DriverHistory.year).where(
            DriverHistory.driver_id == driver_id
        ).distinct()
        result = await session.execute(statement)
        years = [row[0] for row in result.fetchall()]

        histories = []
        for year in sorted(years):
            year_histories = await self.get_driver_history_by_id_and_year(session, driver_id, year)
            histories.extend(year_histories)

        # Sort overall by year then month
        histories.sort(key=lambda h: (h.year, h.month))
        return histories

    async def create_driver_history(
        self,
        session: AsyncSession,
        driver_id: UUID,
        year: int = datetime.now().year,
        km: float = 0,
    ) -> DriverHistory:
        """Create a new driver history"""
        try:
            driver_history = DriverHistory(
                driver_id=driver_id,
                year=year,
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

    async def update_driver_history_by_id_and_year(
        self,
        session: AsyncSession,
        driver_id: UUID,
        year: int,
        km: float,
    ) -> DriverHistory:
        """Update a driver history by ID and year"""
        try:
            existing_history = await self.get_driver_history_by_id_and_year(
                session, driver_id, year
            )

            if existing_history is None:
                raise ValueError(
                    f"Driver history with id {driver_id} and year {year} not found"
                )

            existing_history.km = km
            existing_history.updated_at = datetime.now()

            await session.commit()
            await session.refresh(existing_history)
            return existing_history
        except Exception as e:
            self.logger.error(f"Failed to update driver history by id and year: {e!s}")
            await session.rollback()
            raise e

    async def delete_driver_history_by_id(
        self, session: AsyncSession, driver_id: UUID, year: int
    ) -> None:
        """Delete a driver history by driver history id and year. In case we no longer want to keep records of a driver."""
        try:
            statement = select(DriverHistory).where(
                DriverHistory.driver_id == driver_id,
                DriverHistory.year == year,
            )
            result = await session.execute(statement)
            driver_history = result.scalars().first()

            if driver_history is None:
                raise ValueError(
                    f"Driver history with id {driver_id} and year {year} not found"
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

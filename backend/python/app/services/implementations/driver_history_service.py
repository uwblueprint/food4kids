import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Sequence, select

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

    async def get_driver_history_by_id(
        self, session: AsyncSession, driver_id: UUID
    ) -> list[DriverHistory]:
        """Get a driver history by ID"""
        try:
            statement = select(DriverHistory).where(
                DriverHistory.driver_id == driver_id
            )
            result = await session.execute(statement)
            driver_history = result.scalars().all()

            return list(driver_history)
        except Exception as e:
            self.logger.error(f"Failed to get driver history by id: {e!s}")
            raise e

    async def get_driver_history_by_id_and_year(
        self, session: AsyncSession, driver_id: UUID, year: int
    ) -> DriverHistory | None:
        """Get a driver history by ID and year"""
        try:
            statement = select(DriverHistory).where(
                DriverHistory.driver_id == driver_id,
                DriverHistory.year == year,
            )
            result = await session.execute(statement)
            driver_history = result.scalars().first()

            return driver_history
        except Exception as e:
            self.logger.error(f"Failed to get driver history by id and year: {e!s}")
            raise e

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

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

    async def get_driver_history_by_id(
        self, session: AsyncSession, driver_history_id: UUID
    ) -> DriverHistory:
        """Get a driver history by ID"""
        try:
            statement = select(DriverHistory).where(
                DriverHistory.driver_history_id == driver_history_id
            )
            result = await session.execute(statement)
            driver_history = result.scalars().all()

            if not driver_history:
                self.logger.error(
                    f"Driver history with id {driver_history_id} not found"
                )
                return None
            return driver_history
        except Exception as e:
            self.logger.error(f"Failed to get driver history by id: {e!s}")
            raise e

    async def get_driver_history_by_id_and_year(
        self, session: AsyncSession, driver_history_id: UUID, year: int
    ) -> DriverHistory:
        """Get a driver history by ID and year"""
        try:
            statement = select(DriverHistory).where(
                DriverHistory.driver_history_id == driver_history_id,
                DriverHistory.year == year,
            )
            result = await session.execute(statement)
            driver_history = result.scalars().first()

            if not driver_history:
                self.logger.error(
                    f"Driver history with id {driver_history_id} and year {year} not found"
                )
                return None
            return driver_history
        except Exception as e:
            self.logger.error(f"Failed to get driver history by id and year: {e!s}")
            raise e

    async def create_driver_history(
        self,
        session: AsyncSession,
        driver_id: UUID,
        year: int = datetime.now().year(),
        km: float = 0,
    ) -> DriverHistory:
        """Create a new driver history"""
        try:
            # verify that there is no existing history for the driver and year
            existing_history = await self.get_driver_history_by_id_and_year(
                session, driver_id, year
            )

            if existing_history:
                self.logger.error(
                    f"Driver history with id {driver_id} and year {year} already exists, cannot create new history"
                )
                return None

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
        driver_history_id: UUID,
        year: int,
        km: float,
    ) -> DriverHistory:
        """Update a driver history by ID and year"""
        try:
            # verify that there is an existing history for the driver and year
            existing_history = await self.get_driver_history_by_id_and_year(
                session, driver_history_id, year
            )

            if not existing_history:
                self.logger.error(
                    f"Driver history with id {driver_history_id} and year {year} not found"
                )
                return None

            existing_history.km = km
            await session.commit()
            await session.refresh(existing_history)
            return existing_history
        except Exception as e:
            self.logger.error(f"Failed to update driver history by id and year: {e!s}")
            await session.rollback()
            raise e

    async def delete_driver_history_by_id(
        self, session: AsyncSession, driver_history_id: UUID
    ) -> None:
        """Delete a driver history by ID. In case we no longer want to keep records of a driver."""
        try:
            statement = select(DriverHistory).where(
                DriverHistory.driver_history_id == driver_history_id
            )
            result = await session.execute(statement)
            driver_history = result.scalars().all()

            if not driver_history:
                self.logger.error(
                    f"Driver history with id {driver_history_id} not found"
                )
                return None
            await session.delete(driver_history)
            await session.commit()
        except Exception as e:
            self.logger.error(f"Error deleting driver history: {e}")
            await session.rollback()
            raise e

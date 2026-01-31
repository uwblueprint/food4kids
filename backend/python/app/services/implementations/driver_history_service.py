import logging
from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.config import settings

from app.models.driver_history import DriverHistory, DriverHistorySummary


class DriverHistoryService:
    """Driver history service"""

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize service"""
        self.logger = logger
        self.timezone = ZoneInfo(settings.scheduler_timezone)

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
        
    async def get_driver_history_summary(
        self, session: AsyncSession, driver_id: UUID
    ) -> DriverHistorySummary:
        """Given a driver's ID, give the total km driven by the driver 
        (across all years, etc.), as well as the kilometers driven by the driver during the current year"""
        try:
            # Get driver's info
            driver_history = self.get_driver_history_by_id(session, driver_id)

            # Var to hold sum of the driver's driven kms
            total_kms = 0

            # Var to hold the kms driven by the driver in the current year (when found)
            current_year_km = 0

            # Calculate the current year in the local timezone to determine which year to get data for
            current_year = datetime.now(self.timezone).year

            # Go through list and calculate total kms driven + record current kms driven this year
            for entry in driver_history:
                if current_year == entry.year:
                    current_year_km += entry.km
                
                total_kms += entry.km
            
            driver_history_summary = DriverHistorySummary(
                                        lifetime_km=total_kms,
                                        current_year_km=current_year_km)

            return driver_history_summary
        
        except Exception as e:
            self.logger.error(f"Failed to get summary of driver's history (i.e. km driven in total and this year): {e}")
            raise e

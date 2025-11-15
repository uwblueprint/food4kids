from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.routers.driver_routes import get_driver, get_drivers
from app.services.implementations.driver_history_service import DriverHistoryService


class DriverHistoryCSVGenerator:
    """Handles CSV generation logic for driver history exports."""

    def __init__(
        self, session: AsyncSession, driver_history_service: DriverHistoryService
    ):
        self.session = session
        self.service = driver_history_service

    async def generate_all_drivers_csv(
        self, year: int
    ) -> tuple[list[dict[str, Any]], str]:
        """Generate CSV data for all drivers for a given year."""
        driver_history_current_year = await self.service.get_driver_history_by_year(
            self.session, year
        )
        driver_history_past_year = await self.service.get_driver_history_by_year(
            self.session, year - 1
        )
        
        driver_history = driver_history_current_year + driver_history_past_year

        if not driver_history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No driver history found for year {year}",
            )

        driver_data = await get_drivers(self.session, driver_id=None, email=None)
        driver_lookup = {driver.driver_id: driver for driver in driver_data}

        csv_data = [
            {
                "name": driver_lookup[history.driver_id].name,
                "email": driver_lookup[history.driver_id].email,
                "distance (km)": history.km,
                "tax year": history.year,
            }
            for history in driver_history
            if history.driver_id in driver_lookup
        ]

        filename = f"driver_history_all_drivers_{year}.csv"
        return csv_data, filename
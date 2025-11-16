from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.routers.driver_routes import get_drivers
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
        """Generate CSV data for all drivers for a given year.

        Drivers with history in the current year appear first, sorted alphabetically.
        Drivers with only previous year history appear after, also sorted alphabetically.
        """
        driver_history_current_year = await self.service.get_driver_history_by_year(
            self.session, year
        )
        driver_history_past_year = await self.service.get_driver_history_by_year(
            self.session, year - 1
        )

        if not driver_history_current_year and not driver_history_past_year:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No driver history found for year {year} or {year - 1}",
            )

        current_year_lookup = {
            history.driver_id: history.km for history in driver_history_current_year
        }
        past_year_lookup = {
            history.driver_id: history.km for history in driver_history_past_year
        }

        all_driver_ids = set(current_year_lookup.keys()) | set(past_year_lookup.keys())

        driver_data = await get_drivers(self.session, driver_id=None, email=None)
        driver_lookup = {driver.driver_id: driver for driver in driver_data}

        csv_data = []
        for driver_id in all_driver_ids:
            if driver_id not in driver_lookup:
                continue

            driver = driver_lookup[driver_id]
            name_parts = driver.name.split(" ", 1)  # Split on first space only
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ""

            has_current_year = driver_id in current_year_lookup

            csv_data.append(
                {
                    "first": first_name,
                    "last": last_name,
                    "email": driver.email,
                    f"distance (km) in {year}": current_year_lookup.get(driver_id, 0),
                    f"distance (km) in {year - 1}": past_year_lookup.get(driver_id, 0),
                    "_has_current_year": has_current_year,  # Internal field for sorting
                }
            )

        if not csv_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No valid driver data found for years {year} and {year - 1}",
            )

        # Sort: current year drivers first (descending), then by last name, then first name
        csv_data.sort(
            key=lambda x: (
                not x["_has_current_year"],
                str(x["last"]).lower(),
                str(x["first"]).lower(),
            )
        )

        for row in csv_data:
            del row["_has_current_year"]

        filename = f"driver_history_all_drivers_{year}.csv"
        return csv_data, filename

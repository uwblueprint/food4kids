from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.driver import DriverRead
from app.services.implementations.driver_history_service import DriverHistory


class DriverHistoryCSVGenerator:
    """Handles CSV generation logic for driver history exports."""

    def __init__(
        self,
        session: AsyncSession,
        driver_history_current_year: list[DriverHistory],
        driver_history_past_year: list[DriverHistory],
        driver_data: list[DriverRead],
    ):
        self.session = session
        self.driver_history_current_year = driver_history_current_year
        self.driver_history_past_year = driver_history_past_year
        self.driver_data = driver_data

    async def generate_all_drivers_csv(
        self, year: int
    ) -> tuple[list[dict[str, Any]], str]:
        """Generate CSV data for all drivers for a given year.

        Drivers with history in the current year appear first, sorted alphabetically.
        Drivers with only previous year history appear after, also sorted alphabetically.
        """

        current_year_lookup = {
            history.driver_id: history.km
            for history in self.driver_history_current_year
        }
        past_year_lookup = {
            history.driver_id: history.km for history in self.driver_history_past_year
        }

        all_driver_ids = set(current_year_lookup.keys()) | set(past_year_lookup.keys())

        driver_lookup = {driver.driver_id: driver for driver in self.driver_data}

        csv_data = []
        for driver_id in all_driver_ids:
            if driver_id not in driver_lookup:
                continue

            driver = driver_lookup[driver_id]
            name_parts = driver.name.split(" ", 1)  # Split on first space only
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ""

            csv_data.append(
                {
                    "first": first_name,
                    "last": last_name,
                    "email": driver.email,
                    f"distance (km) in {year}": current_year_lookup.get(driver_id, 0),
                    f"distance (km) in {year - 1}": past_year_lookup.get(driver_id, 0),
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
                int(x[f"distance (km) in {year}"]) > 0,
                str(x["last"]).lower(),
                str(x["first"]).lower(),
            )
        )

        filename = f"driver_history_all_drivers_{year}.csv"
        return csv_data, filename

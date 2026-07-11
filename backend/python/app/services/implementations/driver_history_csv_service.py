from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.driver import DriverRead


class DriverHistoryCSVGenerator:
    """Handles CSV generation logic for driver history exports."""

    def __init__(
        self,
        session: AsyncSession,
        current_year_totals: dict[UUID, float],
        past_year_totals: dict[UUID, float],
        driver_data: list[DriverRead],
    ):
        self.session = session
        self.current_year_totals = current_year_totals
        self.past_year_totals = past_year_totals
        self.driver_data = driver_data

    async def generate_all_drivers_csv(
        self, year: int
    ) -> tuple[list[dict[str, Any]], str]:
        """Generate CSV data for all drivers for a given year.

        Totals are per-driver yearly sums over the mileage ledger. Drivers
        with km in the requested year appear first, sorted by last name then
        first name; drivers with only previous-year km follow, sorted the
        same way.
        """

        all_driver_ids = set(self.current_year_totals) | set(self.past_year_totals)

        driver_lookup = {driver.driver_id: driver for driver in self.driver_data}

        csv_data = []
        for driver_id in all_driver_ids:
            if driver_id not in driver_lookup:
                continue

            driver = driver_lookup[driver_id]
            csv_data.append(
                {
                    "first": driver.first_name,
                    "last": driver.last_name,
                    "email": driver.email,
                    f"distance (km) in {year}": self.current_year_totals.get(
                        driver_id, 0
                    ),
                    f"distance (km) in {year - 1}": self.past_year_totals.get(
                        driver_id, 0
                    ),
                }
            )

        if not csv_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No valid driver data found for years {year} and {year - 1}",
            )

        # Sort: current year drivers first, then last name, then first name.
        csv_data.sort(
            key=lambda x: (
                not x[
                    f"distance (km) in {year}"
                ],  # current year drivers first, no people with 0 km
                str(x["last"]).lower(),
                str(x["first"]).lower(),
            )
        )

        filename = f"driver_history_all_drivers_{year}.csv"
        return csv_data, filename

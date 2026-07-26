from uuid import UUID

from sqlmodel import SQLModel

MIN_YEAR = 2025
MAX_YEAR = 2100


class DriverHistoryRead(SQLModel):
    """One month's km for a driver.

    Computed, never stored: the sum of `Route.length` over the driver's
    frozen routes (those with a RouteSnapshot) in that month. Reassigning a
    route or correcting its stops updates history automatically, so there is
    no stored total to drift out of sync.
    """

    driver_id: UUID
    year: int
    month: int
    km: float


class DriverHistorySummary(SQLModel):
    """Summary of driver's lifetime and current year kilometers"""

    lifetime_km: float
    current_year_km: float

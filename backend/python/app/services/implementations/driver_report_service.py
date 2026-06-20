import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from app.config import settings
from app.models.driver import Driver
from app.models.driver_history import DriverHistory
from app.models.route_group import RouteGroup
from app.models.route_stop_snapshot import RouteStopSnapshot
from app.models.user import User


class DriverReportService:
    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger
        self.timezone = ZoneInfo(settings.scheduler_timezone)

    async def get_monthly_km_ranking(
        self, session: AsyncSession, year: int, month: int
    ) -> list[dict]:
        """Return per-driver km for given year/month ordered desc by km."""
        try:
            # Build explicit ON clauses using `col()` so types info is preserved
            on_driver = col(Driver.driver_id) == col(DriverHistory.driver_id)
            on_user = col(User.user_id) == col(Driver.user_id)

            statement = (
                select(DriverHistory, Driver, User)
                .select_from(DriverHistory)
                .join(Driver, on_driver)
                .join(User, on_user)
                .where(DriverHistory.year == year, DriverHistory.month == month)
                .order_by(col(DriverHistory.km).desc())
            )
            result = await session.execute(statement)
            rows = result.all()

            rankings: list[dict] = []
            for history, driver, user in rows:
                rankings.append(
                    {
                        "driver_id": str(driver.driver_id),
                        "driver_name": f"{user.first_name} {user.last_name}",
                        "km": float(history.km),
                    }
                )

            return rankings
        except Exception:
            self.logger.exception("Failed to compute monthly km ranking")
            raise

    async def get_total_km_for_month(
        self, session: AsyncSession, year: int, month: int
    ) -> float:
        try:
            statement = select(func.coalesce(func.sum(DriverHistory.km), 0.0)).where(
                DriverHistory.year == year, DriverHistory.month == month
            )
            result = await session.execute(statement)
            total = result.scalar_one()
            return float(total or 0.0)
        except Exception:
            self.logger.exception("Failed to compute total km for month")
            raise

    async def get_total_deliveries_between(
        self, session: AsyncSession, start_dt: datetime, end_dt: datetime
    ) -> int:
        """Count RouteStopSnapshot rows whose parent RouteGroup.drive_date
        falls between start_dt and end_dt.
        start_dt and end_dt should be timezone-aware datetimes.
        """
        try:
            # Normalise datetimes to naive local (scheduler) time to match DB storage
            # Convert incoming tz-aware datetimes to scheduler timezone then drop tzinfo
            if start_dt.tzinfo is not None:
                start_dt = start_dt.astimezone(self.timezone).replace(tzinfo=None)
            if end_dt.tzinfo is not None:
                end_dt = end_dt.astimezone(self.timezone).replace(tzinfo=None)

            # Join route_stop_snapshots -> route_stops -> routes -> route_groups
            from app.models.route import Route
            from app.models.route_stop import RouteStop

            # Use model-based joins so sqlalchemy resolves FK-based ON clauses
            stmt = (
                select(func.count())
                .select_from(RouteStopSnapshot)
                .join(RouteStop)
                .join(Route)
                .join(RouteGroup)
                .where(
                    RouteGroup.drive_date >= start_dt, RouteGroup.drive_date <= end_dt
                )
            )

            result = await session.execute(stmt)
            count = result.scalar_one()
            return int(count or 0)
        except Exception:
            self.logger.exception("Failed to count deliveries between dates")
            raise

    async def get_total_deliveries_for_month(
        self, session: AsyncSession, year: int, month: int
    ) -> int:
        # Build month boundaries in scheduler timezone and pass them through
        start = datetime(year, month, 1, 0, 0, tzinfo=self.timezone)
        if month == 12:
            end = datetime(year + 1, 1, 1, 0, 0, tzinfo=self.timezone)
        else:
            end = datetime(year, month + 1, 1, 0, 0, tzinfo=self.timezone)

        return await self.get_total_deliveries_between(session, start, end)

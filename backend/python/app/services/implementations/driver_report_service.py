import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import List

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.config import settings
from app.models.driver import Driver
from app.models.user import User
from app.models.driver_history import DriverHistory
from app.models.route_group import RouteGroup
from app.models.route_stop_snapshot import RouteStopSnapshot

class DriverReportService:
    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger
        self.timezone = ZoneInfo(settings.scheduler_timezone)

    async def get_monthly_km_ranking(
        self, session: AsyncSession, year: int, month: int
    ) -> List[dict]:
        """Return per-driver km for given year/month ordered desc by km."""
        try:
            statement = (
                select(DriverHistory, Driver, User)
                .join(Driver, Driver.driver_id == DriverHistory.driver_id)
                .join(User, User.user_id == Driver.user_id)
                .where(DriverHistory.year == year, DriverHistory.month == month)
                .order_by(DriverHistory.km.desc())
            )
            result = await session.execute(statement)
            rows = result.all()

            rankings: List[dict] = []
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
            statement = (
                select(func.coalesce(func.sum(DriverHistory.km), 0.0))
                .where(DriverHistory.year == year, DriverHistory.month == month)
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
            # Normalise datetimes to naive UTC to match DB TIMESTAMP WITHOUT TIME ZONE
            if start_dt.tzinfo is not None:
                start_dt = start_dt.astimezone(timezone.utc).replace(tzinfo=None)
            if end_dt.tzinfo is not None:
                end_dt = end_dt.astimezone(timezone.utc).replace(tzinfo=None)

            # Join route_stop_snapshots -> route_stops -> routes -> route_groups
            from app.models.route_stop import RouteStop
            from app.models.route import Route

            stmt = (
                select(func.count())
                .select_from(RouteStopSnapshot)
                .join(RouteStop, RouteStopSnapshot.route_stop_id == RouteStop.route_stop_id)
                .join(Route, Route.route_id == RouteStop.route_id)
                .join(
                    RouteGroup, Route.route_group_id == RouteGroup.route_group_id
                )
                .where(RouteGroup.drive_date >= start_dt, RouteGroup.drive_date <= end_dt)
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
        # Build month boundaries in scheduler timezone, then convert to UTC
        start = datetime(year, month, 1, 0, 0, tzinfo=self.timezone)
        if month == 12:
            end = datetime(year + 1, 1, 1, 0, 0, tzinfo=self.timezone)
        else:
            end = datetime(year, month + 1, 1, 0, 0, tzinfo=self.timezone)

        # Convert boundaries to UTC for DB comparisons
        start_utc = start.astimezone(timezone.utc)
        end_utc = end.astimezone(timezone.utc)

        return await self.get_total_deliveries_between(session, start_utc, end_utc)

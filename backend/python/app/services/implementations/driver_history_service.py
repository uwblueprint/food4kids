from apscheduler.schedulers.background import BackgroundScheduler
from uuid import UUID
from app.models.driver_history import DriverHistory
import logging
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

class DriverHistoryService:
    """Modern FastAPI-style driver history service"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
    
    ## PROCESS
    ## first, get driver assignments from driverassignments table
    ## then, iterate through each driver assignment and get the route id
    ## then, get the route distance from the routes table, add to local total distance variable
    ## mark the route as completed in driverassignments table
    ## update driverhistory table with the total distance, 


    async def get_driver_history(self, session: AsyncSession, driver_id: UUID) -> list[DriverHistory]:
        """Get driver history"""
        return await session.execute(select(DriverHistory).where(DriverHistory.driver_id == driver_id)).scalars().all()

    
    async def get_driver_assignments(self, session: AsyncSession, driver_id: UUID, date: datetime) -> list[DriverAssignment]:
        """Get driver assignments"""
        return await session.execute(select(DriverAssignment).where(DriverAssignment.driver_id == driver_id and DriverAssignment.date == date)).scalars().all()

    async def get_routes_distance(self, session: AsyncSession, route_ids: list[UUID]) -> float:
        """Get routes distance"""
        return await session.execute(select(Route.distance).where(Route.route_id.in_(route_ids))).scalars().all()
    
    
    
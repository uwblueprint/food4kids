"""Driver history scheduled jobs"""

from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import and_
from sqlmodel import select

from app.dependencies.services import get_logger
from app.models import async_session_maker_instance
from app.models.driver_assignment import DriverAssignment
from app.models.driver_history import DriverHistory
from app.models.route import Route


async def process_daily_driver_history() -> None:
    """Process driver history for the day - runs at 11:59 PM every day

    This job:
    1. Finds all incomplete driver assignments from today
    2. Calculates total distance for each driver by joining with routes
    3. Marks assignments as completed
    4. Updates or creates driver history entries with the total distance
    """
    logger = get_logger()

    if async_session_maker_instance is None:
        logger.error("Database session maker not initialized")
        return

    today = date.today()
    current_year = today.year
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = datetime.combine(today, datetime.max.time())

    try:
        async with async_session_maker_instance() as session:
            # Get all incomplete assignments from today with route distances
            # Using a join to get route lengths in a single query
            statement = (
                select(
                    DriverAssignment.driver_id,
                    DriverAssignment.driver_assignment_id,
                    Route.length,
                )
                .join(Route, DriverAssignment.route_id == Route.route_id)  # type: ignore[arg-type]
                .where(
                    and_(
                        DriverAssignment.completed.is_(False),  # type: ignore[attr-defined]
                        DriverAssignment.time >= start_of_day,  # type: ignore[arg-type]
                        DriverAssignment.time <= end_of_day,  # type: ignore[arg-type]
                    )
                )
            )

            result = await session.execute(statement)
            assignments_with_distances = result.all()

            if not assignments_with_distances:
                logger.info("No incomplete assignments found for today")
                return

            # Group by driver_id and sum distances
            driver_distances: dict[UUID, float] = {}
            assignment_ids_to_complete: list[UUID] = []

            for row in assignments_with_distances:
                driver_id = row.driver_id
                assignment_id = row.driver_assignment_id
                distance = row.length

                driver_distances[driver_id] = (
                    driver_distances.get(driver_id, 0.0) + distance
                )
                assignment_ids_to_complete.append(assignment_id)

            # Mark all assignments as completed
            for assignment_id in assignment_ids_to_complete:
                assignment = await session.get(DriverAssignment, assignment_id)
                if assignment:
                    assignment.completed = True

            # Update or create driver history entries
            for driver_id, total_distance in driver_distances.items():
                # Check if history entry exists for this driver and year
                existing_history = (
                    (
                        await session.execute(
                            select(DriverHistory).where(
                                and_(
                                    DriverHistory.driver_id == driver_id,  # type: ignore[arg-type]
                                    DriverHistory.year == current_year,  # type: ignore[arg-type]
                                )
                            )
                        )
                    )
                    .scalars()
                    .first()
                )

                if existing_history:
                    # Update existing entry
                    existing_history.km += total_distance
                    logger.info(
                        f"Updated driver history for driver {driver_id}: "
                        f"added {total_distance} km (new total: {existing_history.km} km)"
                    )
                else:
                    # Create new entry
                    new_history = DriverHistory(
                        driver_id=driver_id,
                        year=current_year,
                        km=total_distance,
                    )
                    session.add(new_history)
                    logger.info(
                        f"Created driver history for driver {driver_id}: "
                        f"{total_distance} km for year {current_year}"
                    )

            await session.commit()
            logger.info(
                f"Successfully processed {len(assignment_ids_to_complete)} assignments "
                f"for {len(driver_distances)} drivers"
            )

    except Exception as error:
        logger.error(
            f"Failed to process daily driver history: {error!s}", exc_info=True
        )
        raise error

"""Scheduled email sending jobs

This module contains all cron-scheduled email jobs that run at specific times.
Jobs use the unified EmailDispatcher to render and send emails.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy import and_
from sqlmodel import select

from app.dependencies.services import get_email_dispatcher, get_logger
from app.models.driver import Driver
from app.models.route import Route
from app.models.route_group import RouteGroup
from app.models.user import User


async def send_route_reminders() -> None:
    """Scheduled job: Send route reminders to drivers for tomorrow's routes.

    Runs daily (typically at 7:00 AM) and sends reminder emails to all drivers
    assigned to routes the next day.

    This job:
    - Queries all driver assignments for tomorrow
    - For each driver, renders and sends a route reminder email
    - Logs successes and failures individually
    - Continues sending even if one email fails
    """

    from app.models import async_session_maker_instance

    logger = get_logger()
    dispatcher = get_email_dispatcher()

    if async_session_maker_instance is None:
        logger.error("Database session maker not initialized")
        return

    tomorrow = date.today() + timedelta(days=1)
    start_of_day = datetime.combine(tomorrow, datetime.min.time())
    end_of_day = datetime.combine(tomorrow, datetime.max.time())

    try:
        async with async_session_maker_instance() as session:
            # Get all drivers assigned to routes tomorrow
            statement = (
                select(
                    User.email,
                    User.name,
                    Route.start_time,
                    Route.length,
                    Route.route_id,
                    Route.driver_id,
                    RouteGroup.drive_date,
                )
                .join(Route, Route.driver_id == Driver.driver_id)  # type: ignore[arg-type]
                .join(User, Driver.user_id == User.user_id)  # type: ignore[arg-type]
                .join(RouteGroup, Route.route_group_id == RouteGroup.route_group_id)  # type: ignore[arg-type]
                .where(
                    and_(
                        RouteGroup.drive_date >= start_of_day,  # type: ignore[arg-type]
                        RouteGroup.drive_date <= end_of_day,  # type: ignore[arg-type]
                        Route.driver_id != None,  # type: ignore[arg-type]
                    )
                )
                .order_by(User.email)
            )

            result = await session.execute(statement)
            upcoming_routes = result.all()

            if not upcoming_routes:
                logger.info("No upcoming routes found for tomorrow, skipping reminders")
                return

            sent_count = 0
            failed_count = 0

            # Send reminder email to each driver
            for row in upcoming_routes:
                recipient_email = row.email
                driver_name = row.name
                # Combine drive_date (date) with route start_time (time) if present
                if getattr(row, "start_time", None):
                    route_date = datetime.combine(row.drive_date.date(), row.start_time)
                else:
                    route_date = row.drive_date
                route_distance = row.length

                # Format date, time, and distance for email
                date_only = route_date.date().strftime("%A, %B %d, %Y")
                time_only = route_date.time().strftime("%I:%M %p")
                rounded_distance = str(round(route_distance))

                # Prepare context matching `view-upcoming-route` template placeholders
                context = {
                    "Driver_Name_To_Replace": driver_name,
                    "Date_To_Replace": date_only,
                    "Time_To_Replace": time_only,
                    "Route_Duration_To_Replace": rounded_distance,
                    "Upcoming_Route_URL": "https://app.example.com/routes",  # Note: update to actual route URL!
                }

                try:
                    await dispatcher.dispatch(
                        email_type="view-upcoming-route",
                        to=recipient_email,
                        context=context,
                    )
                    sent_count += 1
                except Exception as e:
                    failed_count += 1
                    logger.error(
                        f"Failed to send route reminder to {recipient_email}: {e!s}",
                        exc_info=True,
                    )
                    # Continue sending to other drivers even if one fails

            logger.info(
                f"Route reminder job completed: sent {sent_count}, failed {failed_count}"
            )

    except Exception as error:
        logger.error(
            f"Failed to process route reminder emails: {error!s}",
            exc_info=True,
        )
        raise error

"""Scheduled email sending jobs

This module contains all cron-scheduled email jobs that run at specific times.
Jobs use the unified EmailDispatcher to render and send emails.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING, Any, cast

from sqlalchemy import and_
from sqlmodel import col, select

from app.config import settings

if TYPE_CHECKING:
    from sqlalchemy.sql.schema import Table

from app.dependencies.services import get_email_dispatcher, get_logger
from app.models.driver import Driver
from app.models.route import Route
from app.models.route_group import RouteGroup
from app.models.system_settings import SystemSettings
from app.models.user import User
from app.services.implementations.email_service import EmailService


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
            # Cast model tables to SQLAlchemy Table objects so mypy can reason
            # about column expressions.
            # Cast the model classes to Any before accessing `__table__` so
            # mypy does not complain about missing attributes on the class
            # objects.
            Route_table = cast("Table", cast("Any", Route).__table__)
            Driver_table = cast("Table", cast("Any", Driver).__table__)
            User_table = cast("Table", cast("Any", User).__table__)
            RouteGroup_table = cast("Table", cast("Any", RouteGroup).__table__)

            # Select full models so typing is recognized by mypy; use table
            # columns for SQL expressions.
            statement = (
                select(Route, User, RouteGroup)
                .join(Driver, Route_table.c.driver_id == Driver_table.c.driver_id)
                .join(User, Driver_table.c.user_id == User_table.c.user_id)
                .join(
                    RouteGroup,
                    Route_table.c.route_group_id == RouteGroup_table.c.route_group_id,
                )
                .where(
                    and_(
                        RouteGroup_table.c.drive_date >= start_of_day,
                        RouteGroup_table.c.drive_date <= end_of_day,
                        Route_table.c.driver_id.isnot(None),
                    )
                )
                .order_by(User_table.c.email)
            )

            result = await session.execute(statement)
            upcoming_routes = result.all()

            if not upcoming_routes:
                logger.info("No upcoming routes found for tomorrow, skipping reminders")
                return

            sent_count = 0
            failed_count = 0

            # Send reminder email to each driver
            for route, user, route_group in upcoming_routes:
                recipient_email = user.email
                driver_name = user.full_name
                # Combine drive_date (date) with route start_time (time) if present
                if route.start_time:
                    route_date = datetime.combine(
                        route_group.drive_date.date(), route.start_time
                    )
                else:
                    route_date = route_group.drive_date
                route_distance = route.length

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


async def process_daily_reminder_emails() -> None:
    """Sends out daily reminder emails for the configured reminder window.

    Emails each driver assigned (via Route.driver_id) to a route whose
    RouteGroup.drive_date falls on one of the configured lead days.
    """

    from app.models import (
        async_session_maker_instance,  # Placed here to ensure testing file functions as normal
    )

    logger = get_logger()

    if async_session_maker_instance is None:
        logger.error("Database session maker not initialized")
        return

    try:
        async with async_session_maker_instance() as session:
            settings_result = await session.execute(select(SystemSettings).limit(1))
            system_settings = settings_result.scalars().first()
            reminder_days = (
                system_settings.email_reminder_days_before
                if system_settings and system_settings.email_reminder_days_before
                else [1]
            )
            target_dates = {date.today() + timedelta(days=day) for day in reminder_days}
            start_of_day = datetime.combine(min(target_dates), datetime.min.time())
            end_of_day = datetime.combine(max(target_dates), datetime.max.time())
            statement = (
                select(
                    User.email,
                    RouteGroup.drive_date,
                    col(Route.start_time),
                    Route.length,
                )
                .join(RouteGroup, RouteGroup.route_group_id == Route.route_group_id)  # type: ignore[arg-type]
                .join(Driver, Driver.driver_id == Route.driver_id)  # type: ignore[arg-type]
                .join(User, User.user_id == Driver.user_id)  # type: ignore[arg-type]
                .where(
                    and_(
                        RouteGroup.drive_date >= start_of_day,  # type: ignore[arg-type]
                        RouteGroup.drive_date <= end_of_day,  # type: ignore[arg-type]
                        col(Route.driver_id).isnot(None),
                    )
                )
                .order_by(User.email)
            )

            result = await session.execute(statement)
            upcoming_routes = result.all()

            if not upcoming_routes:
                logger.info(
                    "No Upcoming Routes found for configured reminder days, skipping emails"
                )
                return

            email_service = EmailService(
                logger,
                {
                    "refresh_token": settings.mailer_refresh_token,
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "client_id": settings.mailer_client_id,
                    "client_secret": settings.mailer_client_secret,
                },
                settings.mailer_user,
                "Food4Kids",
            )

            with open("./app/templates/view-upcoming-route.html") as file:
                template_html = file.read()

            for row in upcoming_routes:
                recipient_email = row.email
                drive_date: datetime = row.drive_date
                route_distance = row.length

                date_only = drive_date.date().strftime("%A, %B %d, %Y")
                # Per-route start time if set, else fall back to a sensible default.
                start_time = row.start_time
                time_only = start_time.strftime("%I:%M %p") if start_time else "TBD"
                rounded_distance = str(round(route_distance))

                formatted_email = template_html.replace("Date_To_Replace", date_only)
                formatted_email = formatted_email.replace("Time_To_Replace", time_only)
                formatted_email = formatted_email.replace(
                    "Route_Duration_To_Replace", rounded_distance
                )
                logger.info(f"Sending Email to {recipient_email}")
                email_service.send_email(
                    to=recipient_email,
                    subject="Upcoming Route Reminder",
                    body=formatted_email,
                )

            logger.info("Successfully sent reminder emails")

    except Exception as error:
        logger.error(
            f"Failed to process daily reminder emails: {error!s}", exc_info=True
        )
        raise error

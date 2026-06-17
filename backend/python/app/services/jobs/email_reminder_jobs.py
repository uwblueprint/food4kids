"""Email reminder scheduled jobs"""

from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy import and_
from sqlmodel import col, select

from app.config import settings
from app.dependencies.services import get_logger
from app.models.driver import Driver
from app.models.route import Route
from app.models.route_group import RouteGroup
from app.models.system_settings import SystemSettings
from app.models.user import User
from app.services.implementations.email_service import EmailService


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
            upcoming_routes = [
                row for row in result.all() if row.drive_date.date() in target_dates
            ]

            if not upcoming_routes:
                logger.info("No Upcoming Routes found for tomorrow, skipping emails")
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
                formatted_email = file.read()

            for row in upcoming_routes:
                recipient_email = row.email
                drive_date: datetime = row.drive_date
                route_distance = row.length

                date_only = drive_date.date().strftime("%A, %B %d, %Y")
                # Per-route start time if set, else fall back to a sensible default.
                start_time = row.start_time
                time_only = start_time.strftime("%I:%M %p") if start_time else "TBD"
                rounded_distance = str(round(route_distance))

                formatted_email = formatted_email.replace("Date_To_Replace", date_only)
                formatted_email = formatted_email.replace("Time_To_Replace", time_only)
                formatted_email = formatted_email.replace(
                    "Length_To_Replace", rounded_distance
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

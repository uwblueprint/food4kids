"""Scheduled jobs - follows same pattern as routers"""

from __future__ import annotations

from datetime import time
from typing import TYPE_CHECKING, Any, Protocol

from sqlmodel import select

from app.models.system_settings import SystemSettings

if TYPE_CHECKING:
    from collections.abc import Callable

    from sqlalchemy.ext.asyncio import AsyncSession


class DailyReminderScheduler(Protocol):
    scheduler: object | None

    def remove_job(self, job_id: str) -> None:
        pass

    def add_cron_job(
        self,
        func: Callable[..., Any],
        job_id: str,
        hour: int | str = "*",
        minute: int | str = "*",
        day_of_week: int | str = "*",
        day: int | str = "*",
        month: int | str = "*",
    ) -> None:
        pass


DEFAULT_DAILY_REMINDER_TIME = time(9, 0)
DAILY_REMINDER_JOB_ID = "daily_reminder_emails"


def _schedule_daily_reminder_emails(
    scheduler_service: DailyReminderScheduler, reminder_time: time
) -> None:
    from .email_reminder_jobs import process_daily_reminder_emails

    scheduler_service.remove_job(DAILY_REMINDER_JOB_ID)
    scheduler_service.add_cron_job(
        process_daily_reminder_emails,
        job_id=DAILY_REMINDER_JOB_ID,
        hour=reminder_time.hour,
        minute=reminder_time.minute,
    )


async def refresh_daily_reminder_email_schedule(
    scheduler_service: DailyReminderScheduler, session: AsyncSession
) -> None:
    """Reschedule the reminder job from the persisted system settings."""
    if getattr(scheduler_service, "scheduler", None) is None:
        return

    result = await session.execute(select(SystemSettings).limit(1))
    system_settings = result.scalars().first()
    reminder_time = (
        system_settings.email_reminder_time
        if system_settings is not None
        else DEFAULT_DAILY_REMINDER_TIME
    )
    _schedule_daily_reminder_emails(scheduler_service, reminder_time)


async def init_jobs(
    scheduler_service: DailyReminderScheduler, session: AsyncSession
) -> None:
    """Initialize all scheduled jobs - add new jobs here

    This function follows the same pattern as app.routers.init_app().
    To add a new scheduled job:
    1. Create a new file in this directory (e.g., email_jobs.py)
    2. Define your job function
    3. Import and register it here
    """
    from .driver_history_jobs import process_daily_driver_history
    from .email_jobs import send_route_reminders

    # Driver history mark daily routes as complete
    scheduler_service.add_cron_job(
        process_daily_driver_history,
        job_id="daily_driver_history",
        hour=23,
        minute=59,
    )

    await refresh_daily_reminder_email_schedule(scheduler_service, session)
    # Route reminders stay on the existing daily schedule.
    scheduler_service.add_cron_job(
        send_route_reminders,
        job_id="route_reminders",
        hour=7,
        minute=0,
    )

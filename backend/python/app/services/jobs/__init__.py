"""Scheduled jobs - follows same pattern as routers"""

from __future__ import annotations

from collections import defaultdict
from datetime import time
from functools import partial
from typing import TYPE_CHECKING, Any, Protocol

from sqlmodel import select

from app.models.system_settings import EmailReminder, SystemSettings

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

    def list_jobs(self) -> list[dict[str, Any]]: ...


DEFAULT_EMAIL_REMINDERS = [EmailReminder(days_before=1, time=time(9, 0))]
DAILY_REMINDER_JOB_PREFIX = "daily_reminder_emails"


def _reminder_job_id(reminder_time: time) -> str:
    """Stable per-time job id, e.g. ``daily_reminder_emails_0900``."""
    return f"{DAILY_REMINDER_JOB_PREFIX}_{reminder_time.hour:02d}{reminder_time.minute:02d}"


def _schedule_daily_reminder_emails(
    scheduler_service: DailyReminderScheduler, reminders: list[EmailReminder]
) -> None:
    """Register one cron job per distinct reminder time.

    Each reminder carries its own time, so reminders are grouped by time and a
    single cron job is registered per time with the lead days that share it. Any
    previously-registered reminder jobs are removed first so stale times stop
    firing after the settings change.
    """
    from .email_jobs import process_daily_reminder_emails

    for job in scheduler_service.list_jobs():
        if str(job["id"]).startswith(DAILY_REMINDER_JOB_PREFIX):
            scheduler_service.remove_job(str(job["id"]))

    days_by_time: dict[time, list[int]] = defaultdict(list)
    for reminder in reminders:
        days_by_time[reminder.time].append(reminder.days_before)

    for reminder_time, days_before in sorted(days_by_time.items()):
        scheduler_service.add_cron_job(
            partial(process_daily_reminder_emails, sorted(set(days_before))),
            job_id=_reminder_job_id(reminder_time),
            hour=reminder_time.hour,
            minute=reminder_time.minute,
        )


async def refresh_daily_reminder_email_schedule(
    scheduler_service: DailyReminderScheduler, session: AsyncSession
) -> None:
    """Reschedule the reminder jobs from the persisted system settings."""
    if getattr(scheduler_service, "scheduler", None) is None:
        return

    result = await session.execute(select(SystemSettings).limit(1))
    system_settings = result.scalars().first()
    reminders = (
        system_settings.email_reminders
        if system_settings is not None and system_settings.email_reminders
        else DEFAULT_EMAIL_REMINDERS
    )
    _schedule_daily_reminder_emails(scheduler_service, reminders)


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

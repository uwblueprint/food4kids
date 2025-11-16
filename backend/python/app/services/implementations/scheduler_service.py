import asyncio
import logging
from collections.abc import Callable
from typing import Any

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger


class SchedulerService:
    """Centralized service for managing scheduled tasks (cron jobs)"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.scheduler: BackgroundScheduler | None = None
        self._is_running = False

    def start(self) -> None:
        """Start the scheduler"""
        if self._is_running:
            self.logger.warning("Scheduler is already running")
            return

        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        self._is_running = True
        self.logger.info("Scheduler started")

    def stop(self) -> None:
        """Stop the scheduler"""
        if not self._is_running or self.scheduler is None:
            return

        self.scheduler.shutdown(wait=True)
        self._is_running = False
        self.logger.info("Scheduler stopped")

    def add_cron_job(
        self,
        func: Callable,
        job_id: str,
        hour: int | str = "*",
        minute: int | str = "*",
        day_of_week: int | str = "*",
        day: int | str = "*",
        month: int | str = "*",
    ) -> None:
        """Add a cron job to the scheduler

        Args:
            func: The function to execute (can be sync or async)
            job_id: Unique identifier for the job
            hour: Hour (0-23) or '*' for every hour
            minute: Minute (0-59) or '*' for every minute
            day_of_week: Day of week (0-6, 0=Monday) or '*' for every day
            day: Day of month (1-31) or '*' for every day
            month: Month (1-12) or '*' for every month
        """
        if not self._is_running or self.scheduler is None:
            raise RuntimeError("Scheduler must be started before adding jobs")

        # Wrap async functions to run in event loop
        if asyncio.iscoroutinefunction(func):
            def async_wrapper():
                # Create new event loop for the background thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(func())
                finally:
                    loop.close()

            wrapped_func = async_wrapper
        else:
            wrapped_func = func

        trigger = CronTrigger(
            hour=hour,
            minute=minute,
            day_of_week=day_of_week,
            day=day,
            month=month,
        )

        self.scheduler.add_job(
            wrapped_func,
            trigger=trigger,
            id=job_id,
            replace_existing=True,
        )
        self.logger.info(
            f"Registered job '{job_id}' - schedule: {month}/{day} {hour}:{minute} (day_of_week={day_of_week})"
        )

    def remove_job(self, job_id: str) -> None:
        """Remove a job from the scheduler"""
        if self.scheduler is None:
            return
        try:
            self.scheduler.remove_job(job_id)
            self.logger.info(f"Removed cron job '{job_id}'")
        except Exception as e:
            self.logger.warning(f"Failed to remove job '{job_id}': {e}")

    def list_jobs(self) -> list[dict[str, Any]]:
        """List all scheduled jobs"""
        if self.scheduler is None:
            return []
        return [
            {
                "id": job.id,
                "next_run": str(job.next_run_time),
                "trigger": str(job.trigger),
            }
            for job in self.scheduler.get_jobs()
        ]


import asyncio
import logging
from collections.abc import Callable
from typing import Any
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import (  # type: ignore[import-untyped]
    BackgroundScheduler,
)
from apscheduler.triggers.cron import CronTrigger  # type: ignore[import-untyped]

from app.config import settings


class SchedulerService:
    """Centralized service for managing scheduled tasks (cron jobs)"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.scheduler: BackgroundScheduler | None = None
        self._is_running = False
        # Get timezone from settings
        self.timezone = ZoneInfo(settings.scheduler_timezone)

    def start(self) -> None:
        """Start the scheduler"""
        if self._is_running:
            self.logger.warning("Scheduler is already running")
            return

        # Pass timezone to scheduler (applies to all jobs)
        self.scheduler = BackgroundScheduler(timezone=self.timezone)
        self.scheduler.start()
        self._is_running = True
        self.logger.info(f"Scheduler started with timezone: {self.timezone}")

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
            hour: Hour (0-23) or '*' for every hour (in configured timezone)
            minute: Minute (0-59) or '*' for every minute
            day_of_week: Day of week (0-6, 0=Monday) or '*' for every day
            day: Day of month (1-31) or '*' for every day
            month: Month (1-12) or '*' for every month
        """
        if not self._is_running or self.scheduler is None:
            raise RuntimeError("Scheduler must be started before adding jobs")

        # Wrap async functions to run in event loop
        if asyncio.iscoroutinefunction(func):

            def async_wrapper() -> None:
                # Create new event loop for the background thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    # Reinitialize database connection for this event loop
                    # This is necessary because asyncpg connections are tied to a specific event loop
                    import app.models as models_module
                    models_module.init_database()
                    
                    # Update the session maker reference in job modules that import it
                    # This is needed because 'from module import name' creates a reference
                    # that doesn't update when the original module's global is reassigned
                    import sys
                    for module_name, module in sys.modules.items():
                        if module_name.startswith('app.services.jobs') and hasattr(module, 'async_session_maker_instance'):
                            module.async_session_maker_instance = models_module.async_session_maker_instance
                    
                    # Run the async function
                    loop.run_until_complete(func())
                finally:
                    # Clean up: close all pending tasks and the loop
                    pending = asyncio.all_tasks(loop)
                    for task in pending:
                        task.cancel()
                    if pending:
                        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                    loop.close()

            wrapped_func = async_wrapper
        else:
            wrapped_func = func

        # Explicitly pass timezone to CronTrigger to ensure the trigger uses the intended timezone,
        # even though the scheduler also has a timezone setting.
        trigger = CronTrigger(
            hour=hour,
            minute=minute,
            day_of_week=day_of_week,
            day=day,
            month=month,
            timezone=self.timezone,
        )

        self.scheduler.add_job(
            wrapped_func,
            trigger=trigger,
            id=job_id,
            replace_existing=True,
        )
        self.logger.info(
            f"Registered job '{job_id}' - schedule: {month}/{day} {hour}:{minute} (day_of_week={day_of_week}) in {self.timezone}"
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

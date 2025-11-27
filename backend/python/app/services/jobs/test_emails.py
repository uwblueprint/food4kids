import asyncio
import logging

from app.models import init_app
from app.services.jobs.email_reminder_jobs import process_daily_reminder_emails

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    init_app()
    asyncio.run(process_daily_reminder_emails())

"""Tests for the reminder email scheduled job."""

from datetime import date, datetime, timedelta
from typing import Any, ClassVar

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.driver import Driver
from app.models.route import Route
from app.models.route_group import RouteGroup
from app.models.system_settings import SystemSettings
from app.models.user import User
from app.services.jobs import email_jobs, refresh_daily_reminder_email_schedule


class _FakeEmailService:
    sent: ClassVar[list[dict[str, str]]] = []

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        pass

    def send_email(self, to: str, subject: str, body: str) -> dict[str, Any]:
        self.sent.append({"to": to, "subject": subject, "body": body})
        return {"to": to, "subject": subject}


@pytest.mark.asyncio
async def test_process_daily_reminder_emails_uses_configured_lead_days(
    test_db_engine: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The job emails routes that fall on any configured lead day."""
    maker = async_sessionmaker(
        test_db_engine, class_=AsyncSession, expire_on_commit=False
    )
    monkeypatch.setattr("app.models.async_session_maker_instance", maker)
    monkeypatch.setattr(email_jobs, "EmailService", _FakeEmailService)
    _FakeEmailService.sent.clear()

    async with maker() as session:
        user = User(
            first_name="Test",
            last_name="Driver",
            email="driver@test.dev",
            auth_id="driver-uid",
        )
        settings = SystemSettings(email_reminder_days_before=[1, 3])
        driver = Driver(
            user_id=user.user_id,
            phone="+12125551234",
            address="1 Depot Rd",
            license_plate="DRV1",
            car_make_model="Toyota Corolla",
        )
        session.add_all([user, settings, driver])
        await session.commit()
        await session.refresh(driver)

        for offset in (1, 3):
            group = RouteGroup(
                name=f"Route {offset}",
                drive_date=datetime.combine(
                    date.today() + timedelta(days=offset), datetime.min.time()
                ),
            )
            session.add(group)
            await session.commit()
            await session.refresh(group)
            session.add(
                Route(
                    name=f"R{offset}",
                    length=offset * 10.0,
                    route_group_id=group.route_group_id,
                    driver_id=driver.driver_id,
                )
            )
            await session.commit()

    await email_jobs.process_daily_reminder_emails()

    assert len(_FakeEmailService.sent) == 2
    assert {item["to"] for item in _FakeEmailService.sent} == {"driver@test.dev"}
    assert all(
        item["subject"] == "Upcoming Route Reminder" for item in _FakeEmailService.sent
    )
    assert all(
        "Date_To_Replace" not in item["body"]
        and "Time_To_Replace" not in item["body"]
        and "Route_Duration_To_Replace" not in item["body"]
        for item in _FakeEmailService.sent
    )


class _FakeScheduler:
    def __init__(self) -> None:
        self.scheduler = object()
        self.removed: list[str] = []
        self.added: list[dict[str, int | str]] = []

    def remove_job(self, job_id: str) -> None:
        self.removed.append(job_id)

    def add_cron_job(
        self,
        _func: Any,
        job_id: str,
        hour: int | str = "*",
        minute: int | str = "*",
        day_of_week: int | str = "*",
        day: int | str = "*",
        month: int | str = "*",
    ) -> None:
        self.added.append(
            {
                "job_id": job_id,
                "hour": hour,
                "minute": minute,
                "day_of_week": day_of_week,
                "day": day,
                "month": month,
            }
        )


@pytest.mark.asyncio
async def test_refresh_daily_reminder_email_schedule_uses_db_time(
    test_db_engine: Any,
) -> None:
    """The cron registration reads the stored reminder time from settings."""
    maker = async_sessionmaker(
        test_db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with maker() as session:
        session.add(
            SystemSettings(
                email_reminder_time=datetime.strptime("08:30:00", "%H:%M:%S").time()
            )
        )
        await session.commit()

    scheduler = _FakeScheduler()
    async with maker() as session:
        await refresh_daily_reminder_email_schedule(scheduler, session)

    assert scheduler.removed == ["daily_reminder_emails"]
    assert scheduler.added == [
        {
            "job_id": "daily_reminder_emails",
            "hour": 8,
            "minute": 30,
            "day_of_week": "*",
            "day": "*",
            "month": "*",
        }
    ]

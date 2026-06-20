"""Tests for the reminder email scheduled job."""

from datetime import date, datetime, time, timedelta
from functools import partial
from typing import Any, ClassVar

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.driver import Driver
from app.models.route import Route
from app.models.route_group import RouteGroup
from app.models.system_settings import EmailReminder, SystemSettings
from app.models.user import User
from app.services.jobs import email_jobs, refresh_daily_reminder_email_schedule


class _FakeEmailService:
    sent: ClassVar[list[dict[str, str]]] = []

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        pass

    def send_email(self, to: str, subject: str, body: str) -> dict[str, Any]:
        self.sent.append({"to": to, "subject": subject, "body": body})
        return {"to": to, "subject": subject}


async def _seed_driver_with_routes(
    maker: async_sessionmaker[AsyncSession], offsets: tuple[int, ...]
) -> None:
    """Create one driver assigned to a route on each of the given day offsets."""
    async with maker() as session:
        user = User(
            first_name="Test",
            last_name="Driver",
            email="driver@test.dev",
            auth_id="driver-uid",
        )
        driver = Driver(
            user_id=user.user_id,
            phone="+12125551234",
            address="1 Depot Rd",
            license_plate="DRV1",
            car_make_model="Toyota Corolla",
        )
        session.add_all([user, driver])
        await session.commit()
        await session.refresh(driver)

        for offset in offsets:
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


@pytest.mark.asyncio
async def test_process_daily_reminder_emails_uses_passed_lead_days(
    test_db_engine: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The job emails routes that fall on any of the passed lead days."""
    maker = async_sessionmaker(
        test_db_engine, class_=AsyncSession, expire_on_commit=False
    )
    monkeypatch.setattr("app.models.async_session_maker_instance", maker)
    monkeypatch.setattr(email_jobs, "EmailService", _FakeEmailService)
    _FakeEmailService.sent.clear()

    # Routes exist 1 and 3 days out; only the passed lead days should be emailed.
    await _seed_driver_with_routes(maker, offsets=(1, 3))

    await email_jobs.process_daily_reminder_emails([1, 3])

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


@pytest.mark.asyncio
async def test_process_daily_reminder_emails_only_targets_given_days(
    test_db_engine: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A job bound to a single lead day ignores routes on other days."""
    maker = async_sessionmaker(
        test_db_engine, class_=AsyncSession, expire_on_commit=False
    )
    monkeypatch.setattr("app.models.async_session_maker_instance", maker)
    monkeypatch.setattr(email_jobs, "EmailService", _FakeEmailService)
    _FakeEmailService.sent.clear()

    await _seed_driver_with_routes(maker, offsets=(1, 3))

    # Only the same-day-before-by-one lead day; the 3-day-out route must be skipped.
    await email_jobs.process_daily_reminder_emails([1])

    assert len(_FakeEmailService.sent) == 1


@pytest.mark.asyncio
async def test_process_daily_reminder_emails_noop_without_days(
    test_db_engine: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An empty lead-day list sends nothing rather than erroring."""
    maker = async_sessionmaker(
        test_db_engine, class_=AsyncSession, expire_on_commit=False
    )
    monkeypatch.setattr("app.models.async_session_maker_instance", maker)
    monkeypatch.setattr(email_jobs, "EmailService", _FakeEmailService)
    _FakeEmailService.sent.clear()

    await email_jobs.process_daily_reminder_emails([])

    assert _FakeEmailService.sent == []


class _FakeScheduler:
    def __init__(self) -> None:
        self.scheduler = object()
        self.removed: list[str] = []
        self.jobs: dict[str, dict[str, Any]] = {}

    def list_jobs(self) -> list[dict[str, Any]]:
        return [{"id": job_id, **info} for job_id, info in self.jobs.items()]

    def remove_job(self, job_id: str) -> None:
        self.removed.append(job_id)
        self.jobs.pop(job_id, None)

    def add_cron_job(
        self,
        func: Any,
        job_id: str,
        hour: int | str = "*",
        minute: int | str = "*",
        day_of_week: int | str = "*",
        day: int | str = "*",
        month: int | str = "*",
    ) -> None:
        self.jobs[job_id] = {
            "func": func,
            "hour": hour,
            "minute": minute,
            "day_of_week": day_of_week,
            "day": day,
            "month": month,
        }


@pytest.mark.asyncio
async def test_refresh_schedules_one_job_per_distinct_time(
    test_db_engine: Any,
) -> None:
    """Each distinct reminder time becomes its own cron job, bound to its lead days."""
    maker = async_sessionmaker(
        test_db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with maker() as session:
        session.add(
            SystemSettings(
                email_reminders=[
                    EmailReminder(days_before=1, time=time(8, 30)),
                    EmailReminder(days_before=0, time=time(11, 0)),
                ]
            )
        )
        await session.commit()

    scheduler = _FakeScheduler()
    # A stale reminder job from a previous configuration that must be cleared.
    scheduler.jobs["daily_reminder_emails_0700"] = {"hour": 7, "minute": 0}

    async with maker() as session:
        await refresh_daily_reminder_email_schedule(scheduler, session)

    assert "daily_reminder_emails_0700" in scheduler.removed

    schedule = {
        job_id: (info["hour"], info["minute"])
        for job_id, info in scheduler.jobs.items()
    }
    assert schedule == {
        "daily_reminder_emails_0830": (8, 30),
        "daily_reminder_emails_1100": (11, 0),
    }

    # Each job is bound to the lead days configured for its time.
    job_0830 = scheduler.jobs["daily_reminder_emails_0830"]["func"]
    job_1100 = scheduler.jobs["daily_reminder_emails_1100"]["func"]
    assert isinstance(job_0830, partial)
    assert isinstance(job_1100, partial)
    assert job_0830.args == ([1],)
    assert job_1100.args == ([0],)


@pytest.mark.asyncio
async def test_refresh_groups_shared_time_into_one_job(
    test_db_engine: Any,
) -> None:
    """Reminders sharing a time collapse into a single job covering both lead days."""
    maker = async_sessionmaker(
        test_db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with maker() as session:
        session.add(
            SystemSettings(
                email_reminders=[
                    EmailReminder(days_before=2, time=time(9, 0)),
                    EmailReminder(days_before=1, time=time(9, 0)),
                ]
            )
        )
        await session.commit()

    scheduler = _FakeScheduler()
    async with maker() as session:
        await refresh_daily_reminder_email_schedule(scheduler, session)

    assert list(scheduler.jobs) == ["daily_reminder_emails_0900"]
    job = scheduler.jobs["daily_reminder_emails_0900"]["func"]
    assert isinstance(job, partial)
    assert job.args == ([1, 2],)


@pytest.mark.asyncio
async def test_refresh_falls_back_to_default_when_unset(
    test_db_engine: Any,
) -> None:
    """With no settings row, the default 9 AM day-before reminder is scheduled."""
    maker = async_sessionmaker(
        test_db_engine, class_=AsyncSession, expire_on_commit=False
    )
    scheduler = _FakeScheduler()
    async with maker() as session:
        await refresh_daily_reminder_email_schedule(scheduler, session)

    assert list(scheduler.jobs) == ["daily_reminder_emails_0900"]
    job = scheduler.jobs["daily_reminder_emails_0900"]["func"]
    assert isinstance(job, partial)
    assert job.args == ([1],)

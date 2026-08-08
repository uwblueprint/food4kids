"""Tests for the reminder email scheduled job."""

import re
from datetime import date, time, timedelta
from functools import partial
from typing import Any, ClassVar

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.driver import Driver
from app.models.route import ASSIGNED_ROUTE_HAS_START_TIME_CONSTRAINT, Route
from app.models.route_group import RouteGroup
from app.models.system_settings import EmailReminder, SystemSettings
from app.models.user import User
from app.services.jobs import email_jobs, refresh_daily_reminder_email_schedule

# Every name the view-upcoming-route template expects the backend to substitute.
PLACEHOLDER_NAMES = (
    "Driver_Name_To_Replace",
    "Date_To_Replace",
    "Time_To_Replace",
    "Route_Duration_To_Replace",
    "Upcoming_Route_URL",
)


class _FakeEmailService:
    """Captures sends in place of the real Gmail-backed EmailService."""

    sent: ClassVar[list[dict[str, str]]] = []

    def send_email(self, to: str, subject: str, body: str) -> dict[str, Any]:
        self.sent.append({"to": to, "subject": subject, "body": body})
        return {"to": to, "subject": subject}


@pytest.fixture
def captured_emails(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, str]]:
    """Route the job's dispatcher through a fake transport and return the outbox.

    The dispatcher itself is real, so these tests exercise the actual Jinja2
    render -- which is the point: the bug this job had was a rendering bug.
    """
    from app.services.implementations.email_dispatcher import EmailDispatcher
    from app.templates.email_renderer import TemplateRenderer

    _FakeEmailService.sent.clear()

    import logging

    dispatcher = EmailDispatcher(
        email_service=_FakeEmailService(),  # type: ignore[arg-type]
        template_renderer=TemplateRenderer(template_dir="./app/templates"),
        logger=logging.getLogger("test-email-dispatcher"),
    )
    monkeypatch.setattr(email_jobs, "get_email_dispatcher", lambda: dispatcher)
    return _FakeEmailService.sent


async def _seed_driver_with_routes(
    maker: async_sessionmaker[AsyncSession],
    offsets: tuple[int, ...],
    start_time: time = time(9, 30),
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
                drive_date=date.today() + timedelta(days=offset),
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
                    start_time=start_time,
                )
            )
            await session.commit()


def _maker(test_db_engine: Any) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        test_db_engine, class_=AsyncSession, expire_on_commit=False
    )


@pytest.mark.asyncio
async def test_uses_passed_lead_days(
    test_db_engine: Any,
    monkeypatch: pytest.MonkeyPatch,
    captured_emails: list[dict[str, str]],
) -> None:
    """The job emails routes that fall on any of the passed lead days."""
    maker = _maker(test_db_engine)
    monkeypatch.setattr("app.models.async_session_maker_instance", maker)

    await _seed_driver_with_routes(maker, offsets=(1, 3))

    await email_jobs.send_route_reminders([1, 3])

    assert len(captured_emails) == 2
    assert {item["to"] for item in captured_emails} == {"driver@test.dev"}


@pytest.mark.asyncio
async def test_only_targets_given_days(
    test_db_engine: Any,
    monkeypatch: pytest.MonkeyPatch,
    captured_emails: list[dict[str, str]],
) -> None:
    """A job bound to a single lead day ignores routes on other days."""
    maker = _maker(test_db_engine)
    monkeypatch.setattr("app.models.async_session_maker_instance", maker)

    await _seed_driver_with_routes(maker, offsets=(1, 3))

    await email_jobs.send_route_reminders([1])

    assert len(captured_emails) == 1


@pytest.mark.asyncio
async def test_skips_days_inside_the_span_but_not_requested(
    test_db_engine: Any,
    monkeypatch: pytest.MonkeyPatch,
    captured_emails: list[dict[str, str]],
) -> None:
    """Non-contiguous lead days do not sweep up the days between them.

    Lead days 1 and 3 span a range that also contains day 2. Filtering on the
    span alone would email the day-2 driver, who asked for no such reminder.
    """
    maker = _maker(test_db_engine)
    monkeypatch.setattr("app.models.async_session_maker_instance", maker)

    await _seed_driver_with_routes(maker, offsets=(1, 2, 3))

    await email_jobs.send_route_reminders([1, 3])

    assert len(captured_emails) == 2
    day_two = (date.today() + timedelta(days=2)).strftime("%A, %B %d, %Y")
    assert not any(day_two in item["body"] for item in captured_emails)


@pytest.mark.asyncio
async def test_lead_day_zero_targets_today(
    test_db_engine: Any,
    monkeypatch: pytest.MonkeyPatch,
    captured_emails: list[dict[str, str]],
) -> None:
    """A lead day of 0 means routes driving today, not an empty selection."""
    maker = _maker(test_db_engine)
    monkeypatch.setattr("app.models.async_session_maker_instance", maker)

    await _seed_driver_with_routes(maker, offsets=(0, 1))

    await email_jobs.send_route_reminders([0])

    assert len(captured_emails) == 1
    assert date.today().strftime("%A, %B %d, %Y") in captured_emails[0]["body"]


@pytest.mark.asyncio
async def test_noop_without_days(
    test_db_engine: Any,
    monkeypatch: pytest.MonkeyPatch,
    captured_emails: list[dict[str, str]],
) -> None:
    """An empty lead-day list sends nothing rather than erroring."""
    maker = _maker(test_db_engine)
    monkeypatch.setattr("app.models.async_session_maker_instance", maker)

    await email_jobs.send_route_reminders([])

    assert captured_emails == []


@pytest.mark.asyncio
async def test_unassigned_routes_are_not_emailed(
    test_db_engine: Any,
    monkeypatch: pytest.MonkeyPatch,
    captured_emails: list[dict[str, str]],
) -> None:
    """A route with no driver has nobody to remind."""
    maker = _maker(test_db_engine)
    monkeypatch.setattr("app.models.async_session_maker_instance", maker)

    async with maker() as session:
        group = RouteGroup(
            name="Unassigned",
            drive_date=date.today() + timedelta(days=1),
        )
        session.add(group)
        await session.commit()
        await session.refresh(group)
        session.add(
            Route(
                name="R-unassigned",
                length=10.0,
                route_group_id=group.route_group_id,
                driver_id=None,
            )
        )
        await session.commit()

    await email_jobs.send_route_reminders([1])

    assert captured_emails == []


@pytest.mark.asyncio
async def test_rendered_body_has_no_leftover_placeholders(
    test_db_engine: Any,
    monkeypatch: pytest.MonkeyPatch,
    captured_emails: list[dict[str, str]],
) -> None:
    """Every placeholder is substituted -- no bare names, no leftover braces.

    This is the regression that shipped: the job used to str.replace bare
    identifiers against a template whose placeholders were Jinja2 `{{ Name }}`,
    so recipients saw `{{ Friday, ... }}` and an unsubstituted greeting.
    """
    maker = _maker(test_db_engine)
    monkeypatch.setattr("app.models.async_session_maker_instance", maker)

    await _seed_driver_with_routes(maker, offsets=(1,))

    await email_jobs.send_route_reminders([1])

    assert len(captured_emails) == 1
    body = captured_emails[0]["body"]

    for name in PLACEHOLDER_NAMES:
        assert name not in body, f"{name} was never substituted"
    assert not re.search(r"\{\{|\}\}", body), "Jinja2 delimiters survived rendering"

    # And the real values actually landed.
    assert "Test Driver" in body
    assert (date.today() + timedelta(days=1)).strftime("%A, %B %d, %Y") in body
    assert "09:30 AM" in body
    assert email_jobs.UPCOMING_ROUTE_URL in body


@pytest.mark.asyncio
async def test_assigned_route_without_start_time_is_not_emailed(
    test_db_engine: Any,
    monkeypatch: pytest.MonkeyPatch,
    captured_emails: list[dict[str, str]],
) -> None:
    """An assigned route with no start time fails loudly instead of guessing.

    The CHECK constraint makes this state unreachable through the app, so
    reaching it means the database drifted from its schema. Inventing a time
    (RouteGroup.drive_date is always midnight, so the obvious fallback renders
    "12:00 AM") would quietly tell a driver the wrong thing.
    """
    maker = _maker(test_db_engine)
    monkeypatch.setattr("app.models.async_session_maker_instance", maker)

    # Insert past the ORM's constraint so we can exercise the guard at all.
    await _seed_driver_with_routes(maker, offsets=(1,))
    async with maker() as session:
        await session.execute(
            text(
                "ALTER TABLE routes DROP CONSTRAINT "
                f"{ASSIGNED_ROUTE_HAS_START_TIME_CONSTRAINT}"
            )
        )
        await session.execute(text("UPDATE routes SET start_time = NULL"))
        await session.commit()

    await email_jobs.send_route_reminders([1])

    assert captured_emails == []


@pytest.mark.asyncio
async def test_one_failure_does_not_stop_the_rest(
    test_db_engine: Any,
    monkeypatch: pytest.MonkeyPatch,
    captured_emails: list[dict[str, str]],
) -> None:
    """A send that raises is logged and the remaining drivers still get theirs."""
    maker = _maker(test_db_engine)
    monkeypatch.setattr("app.models.async_session_maker_instance", maker)

    await _seed_driver_with_routes(maker, offsets=(1, 3))

    calls = {"n": 0}
    real_send = _FakeEmailService.send_email

    def flaky(self: Any, to: str, subject: str, body: str) -> dict[str, Any]:
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("SMTP exploded")
        return real_send(self, to=to, subject=subject, body=body)

    monkeypatch.setattr(_FakeEmailService, "send_email", flaky)

    await email_jobs.send_route_reminders([1, 3])

    assert calls["n"] == 2
    assert len(captured_emails) == 1


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
    maker = _maker(test_db_engine)
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
async def test_refresh_binds_the_dispatcher_backed_job(test_db_engine: Any) -> None:
    """The scheduled callable is send_route_reminders, not a stale rendering path."""
    maker = _maker(test_db_engine)
    scheduler = _FakeScheduler()
    async with maker() as session:
        await refresh_daily_reminder_email_schedule(scheduler, session)

    job = scheduler.jobs["daily_reminder_emails_0900"]["func"]
    assert isinstance(job, partial)
    assert job.func is email_jobs.send_route_reminders


@pytest.mark.asyncio
async def test_refresh_groups_shared_time_into_one_job(
    test_db_engine: Any,
) -> None:
    """Reminders sharing a time collapse into a single job covering both lead days."""
    maker = _maker(test_db_engine)
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
    maker = _maker(test_db_engine)
    scheduler = _FakeScheduler()
    async with maker() as session:
        await refresh_daily_reminder_email_schedule(scheduler, session)

    assert list(scheduler.jobs) == ["daily_reminder_emails_0900"]
    job = scheduler.jobs["daily_reminder_emails_0900"]["func"]
    assert isinstance(job, partial)
    assert job.args == ([1],)

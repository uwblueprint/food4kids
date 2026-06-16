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
from app.services.jobs import email_reminder_jobs


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
    monkeypatch.setattr(email_reminder_jobs, "EmailService", _FakeEmailService)
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

    await email_reminder_jobs.process_daily_reminder_emails()

    assert len(_FakeEmailService.sent) == 2
    assert {item["to"] for item in _FakeEmailService.sent} == {"driver@test.dev"}
    assert all(item["subject"] == "Upcoming Route Reminder" for item in _FakeEmailService.sent)

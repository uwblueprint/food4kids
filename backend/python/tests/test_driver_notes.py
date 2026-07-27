"""Drivers own an admin-only note chain.

Admins can leave notes about a driver; the driver themselves (a non-admin
role) can neither read nor write that chain. See DriverService.create_driver
and the ADMIN read/write permission on the auto-created NoteChain.
"""

import logging
from typing import Any

import pytest

from app.models.driver import DriverCreate
from app.models.enum import NotePermission
from app.models.note import NoteCreate
from app.models.user import User
from app.services.implementations.driver_service import DriverService
from app.services.implementations.note_chain_service import NoteChainService

logger = logging.getLogger(__name__)


async def _make_user(session: Any, role: str, email: str, auth_id: str) -> User:
    user = User(
        first_name="Test",
        last_name=role.capitalize(),
        email=email,
        role=role,
        auth_id=auth_id,
    )
    session.add(user)
    await session.flush()
    return user


@pytest.mark.asyncio
async def test_create_driver_auto_creates_admin_only_note_chain(
    test_session: Any,
) -> None:
    driver_user = await _make_user(
        test_session, "driver", "driver@example.com", "auth-driver"
    )
    driver_service = DriverService(logger)

    driver = await driver_service.create_driver(
        test_session,
        DriverCreate(
            user_id=driver_user.user_id,
            phone="+12125551234",
            license_plate="ABC123",
            car_make_model="Toyota Camry",
            address="123 Main St, City, State 12345",
        ),
    )
    await test_session.commit()

    assert driver.note_chain_id is not None

    note_chain_service = NoteChainService(logger)
    chain = await note_chain_service.get_note_chain_by_id(
        test_session, driver.note_chain_id
    )
    assert chain.read_permission == NotePermission.ADMIN
    assert chain.write_permission == NotePermission.ADMIN


@pytest.mark.asyncio
async def test_driver_cannot_read_or_write_own_note_chain(test_session: Any) -> None:
    admin_user = await _make_user(
        test_session, "admin", "admin@example.com", "auth-admin"
    )
    driver_user = await _make_user(
        test_session, "driver", "driver@example.com", "auth-driver"
    )
    # Capture ids eagerly: create_note's rollback (on the driver's rejected
    # write) expires the ORM objects, so a later `user.user_id` access would
    # trigger a sync lazy-load.
    admin_user_id = admin_user.user_id
    driver_user_id = driver_user.user_id
    driver_service = DriverService(logger)
    note_chain_service = NoteChainService(logger)

    driver = await driver_service.create_driver(
        test_session,
        DriverCreate(
            user_id=driver_user_id,
            phone="+12125551234",
            license_plate="ABC123",
            car_make_model="Toyota Camry",
            address="123 Main St, City, State 12345",
        ),
    )
    await test_session.commit()
    chain_id = driver.note_chain_id
    assert chain_id is not None

    # The driver (non-admin) can neither read the chain nor its notes...
    with pytest.raises(PermissionError):
        await note_chain_service.get_note_chain_with_permission(
            test_session, chain_id, driver_user_id
        )
    with pytest.raises(PermissionError):
        await note_chain_service.get_notes_by_chain_id(
            test_session, chain_id, driver_user_id
        )
    # ...nor write a note to it.
    with pytest.raises(PermissionError):
        await note_chain_service.create_note(
            test_session,
            chain_id,
            driver_user_id,
            NoteCreate(message="I should not be able to write this"),
        )

    # An admin can read and write.
    chain = await note_chain_service.get_note_chain_with_permission(
        test_session, chain_id, admin_user_id
    )
    assert chain.note_chain_id == chain_id
    note = await note_chain_service.create_note(
        test_session,
        chain_id,
        admin_user_id,
        NoteCreate(message="Driver was late twice this week"),
    )
    assert note.note_chain_id == chain_id

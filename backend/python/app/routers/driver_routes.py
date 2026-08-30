import logging
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import (
    DriverAccess,
    require_admin,
    require_driver_or_admin,
    require_self_driver_or_admin,
)
from app.dependencies.services import (
    get_email_dispatcher_depends,
    get_note_chain_service,
    get_user_invite_service,
    get_user_service,
)
from app.models import get_session
from app.models.driver import (
    DriverCreate,
    DriverListRead,
    DriverRead,
    DriverRegister,
    DriverUpdate,
)
from app.models.user import UserBase
from app.models.user_invite import UserInviteCreate
from app.schemas.pagination import PaginatedResponse, PaginationParams, get_pagination
from app.services.implementations.driver_service import DriverService
from app.services.implementations.email_dispatcher import EmailDispatcher
from app.services.implementations.note_chain_service import NoteChainService
from app.services.implementations.user_invite_service import UserInviteService
from app.services.implementations.user_service import UserService
from app.utilities.utils import build_invite_url

# Initialize service
logger = logging.getLogger(__name__)
driver_service = DriverService(logger)

router = APIRouter(prefix="/drivers", tags=["drivers"])


@router.get("/", response_model=PaginatedResponse[DriverListRead])
async def get_drivers(
    session: AsyncSession = Depends(get_session),
    search: str | None = Query(None, description="Filter by first or last name"),
    sort_by: Literal[
        "name", "current_year_km", "last_year_km", "last_delivery"
    ] = Query("name"),
    order: Literal["asc", "desc"] = Query("asc"),
    pagination: PaginationParams = Depends(get_pagination),
    _auth: bool = Depends(require_driver_or_admin),
) -> PaginatedResponse[DriverListRead]:
    """
    Paginated driver rows with server-side name search and list aggregates.
    """
    return await driver_service.get_driver_list(
        session, pagination, search, sort_by, order
    )


@router.get("/{driver_id}", response_model=DriverRead)
async def get_driver(
    driver_id: UUID,
    session: AsyncSession = Depends(get_session),
    _auth: DriverAccess = Depends(require_self_driver_or_admin),
) -> DriverRead:
    """
    Get a single driver by ID
    """
    driver = await driver_service.get_driver_by_id(session, driver_id)
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Driver with id {driver_id} not found",
        )
    return DriverRead.model_validate(driver)


@router.post(
    "/initialize", response_model=DriverRead, status_code=status.HTTP_201_CREATED
)
async def initialize_driver(
    register_request: DriverRegister,
    session: AsyncSession = Depends(get_session),
    email_dispatcher: EmailDispatcher = Depends(get_email_dispatcher_depends),
    user_service: UserService = Depends(get_user_service),
    user_invite_service: UserInviteService = Depends(get_user_invite_service),
    _: bool = Depends(require_admin),
) -> DriverRead:
    """
    Register a new driver in our backend, creates a User and Driver object, returns DriverRead
    NOTE: This does not create a firebase user, ie the User is in a hanging state
    We need to do this so that we can implement our invite only system
    """
    async with session.begin_nested():
        # Create user first
        user_data = register_request.model_dump(
            include=set(UserBase.model_fields.keys())
        )
        user_base = UserBase(**user_data)
        user = await user_service.create_user(session, user_base)

        # Create driver after
        driver_data = register_request.model_dump(
            include=set(DriverCreate.model_fields.keys())
        )
        driver_data["user_id"] = user.user_id
        driver = DriverCreate(**driver_data)
        created_driver = await driver_service.create_driver(session, driver)

        # Create User Invite Record
        user_invite_create = UserInviteCreate(user_id=user.user_id)
        user_invite = await user_invite_service.create_user_invite(
            session, user_invite_create
        )

    await session.commit()
    await session.refresh(created_driver)

    # Send invitation email
    driver_signup_url = build_invite_url(user_invite.user_invite_id)
    driver_name = f"{register_request.first_name} {register_request.last_name}".strip()

    await email_dispatcher.dispatch(
        email_type="account-creation",
        to=register_request.email,
        context={
            "Driver_Name_To_Replace": driver_name if driver_name else "Driver",
            "Sign_Up_URL": driver_signup_url,
            "Hours_Till_Expiry": 48,
        },
    )

    return DriverRead.model_validate(created_driver)


@router.put("/{driver_id}", response_model=DriverRead)
async def update_driver(
    driver_id: UUID,
    driver: DriverUpdate,
    session: AsyncSession = Depends(get_session),
    access: DriverAccess = Depends(require_self_driver_or_admin),
) -> DriverRead:
    """
    Update an existing driver
    """
    if access is not DriverAccess.ADMIN:
        self_editable_fields = {"first_name", "last_name", "phone"}
        requested_fields = set(driver.model_fields_set)
        admin_only_fields = requested_fields - self_editable_fields
        if admin_only_fields:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can update these driver fields.",
            )

    updated_driver = await driver_service.update_driver_by_id(
        session, driver_id, driver
    )
    if not updated_driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Driver with id {driver_id} not found",
        )
    return DriverRead.model_validate(updated_driver)


@router.delete("/{driver_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_driver(
    driver_id: UUID,
    session: AsyncSession = Depends(get_session),
    user_service: UserService = Depends(get_user_service),
    note_chain_service: NoteChainService = Depends(get_note_chain_service),
    _auth: bool = Depends(require_admin),
) -> None:
    """
    Delete a driver by ID.

    A hard delete of the person: the user account and their Firebase login go
    with the driver record, so a deleted driver can no longer sign in. Their
    routes are detached (driver_id SET NULL) rather than deleted, so the
    driver's km stop counting toward anyone.
    """
    # Deleting the `users` row cascades to `drivers`, `user_invites`,
    # `password_reset_tokens`, `announcement_last_reads` and `announcements`. A
    # live reset token is as good as a credential, so it has to go with the
    # Firebase account. Notes the driver wrote survive with user_id SET NULL.
    #
    # delete_user_by_id deletes from Firebase first and commits after, in one
    # transaction. Not reorderable: DB-first leaves a working login for a driver
    # the admin has been told is gone, where Firebase-first just rolls back.
    driver = await driver_service.get_driver_by_id(session, driver_id)
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Driver with id {driver_id} not found",
        )

    # The admin-only chain create_driver made for this driver. Once the driver
    # row is gone nothing references it, so it would sit there permanently
    # unreachable, holding notes about someone who has been deleted.
    if driver.note_chain_id is not None:
        await note_chain_service.delete_note_chain_rows(session, driver.note_chain_id)

    await user_service.delete_user_by_id(session, driver.user_id)

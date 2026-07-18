import logging
import traceback
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies.auth import (
    require_admin,
    require_driver_or_admin,
    require_self_driver_or_admin,
)
from app.dependencies.services import (
    get_auth_service,
    get_email_dispatcher_depends,
    get_user_invite_service,
    get_user_service,
)
from app.models import get_session
from app.models.driver import (
    DriverCreate,
    DriverRead,
    DriverRegister,
    DriverUpdate,
)
from app.models.user import UserBase, UserFinalize
from app.models.user_invite import UserInviteCreate
from app.schemas.auth import DriverRegisterResponse
from app.services.implementations.auth_service import AuthService
from app.services.implementations.driver_service import DriverService
from app.services.implementations.email_dispatcher import EmailDispatcher
from app.services.implementations.user_invite_service import UserInviteService
from app.services.implementations.user_service import UserService
from app.utilities.cookies import set_refresh_token_cookie

# Initialize service
logger = logging.getLogger(__name__)
driver_service = DriverService(logger)

router = APIRouter(prefix="/drivers", tags=["drivers"])


@router.get("/", response_model=list[DriverRead])
async def get_drivers(
    session: AsyncSession = Depends(get_session),
    driver_id: UUID | None = Query(None, description="Filter by driver ID"),
    email: str | None = Query(None, description="Filter by email"),
    _auth: bool = Depends(require_driver_or_admin),
) -> list[DriverRead]:
    """
    Get all drivers, optionally filter by driver_id or email
    """
    if driver_id and email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot query by both driver_id and email",
        )

    try:
        if driver_id:
            driver = await driver_service.get_driver_by_id(session, driver_id)
            if not driver:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Driver with id {driver_id} not found",
                )
            return [DriverRead.model_validate(driver)]

        elif email:
            driver = await driver_service.get_driver_by_email(session, email)
            if not driver:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Driver with email {email} not found",
                )
            return [DriverRead.model_validate(driver)]

        else:
            drivers = await driver_service.get_drivers(session)
            return [DriverRead.model_validate(driver) for driver in drivers]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


@router.get("/{driver_id}", response_model=DriverRead)
async def get_driver(
    driver_id: UUID,
    session: AsyncSession = Depends(get_session),
    _auth: bool = Depends(require_self_driver_or_admin),
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
    user = None

    try:
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
        driver_signup_url = f"{settings.FRONTEND_BASE_URL.rstrip('/')}/create-password/{user_invite.user_invite_id}"
        driver_name = (
            f"{register_request.first_name} {register_request.last_name}".strip()
        )

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

    except HTTPException:
        raise
    except Exception as e:
        # Compensating transaction: rollback all changes
        logger.error(f"Error registering driver: {e}")
        logger.error(traceback.format_exc())

        error_message = getattr(e, "message", None)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message if error_message else str(e),
        ) from e


@router.post(
    "/register",
    response_model=DriverRegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def complete_driver_registration(
    registration_data: UserFinalize,
    response: Response,
    session: AsyncSession = Depends(get_session),
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service),
    user_invite_service: UserInviteService = Depends(get_user_invite_service),
) -> DriverRegisterResponse:
    """
    Creates Firebase user and attaches to hanging state user in our local db, returns DriverRegisterResponse
    """
    try:
        async with session.begin_nested():
            # Validate invite token and lock the row to prevent race conditions
            user_invite_id = registration_data.user_invite_id
            user_invite = await user_invite_service.get_user_invite_by_id(
                session, user_invite_id, for_update=True
            )

            if (
                not user_invite
                or user_invite.is_used
                or user_invite.expires_at < datetime.now(timezone.utc)
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid or expired registration link.",
                )

            # Create Firebase account for user
            user = user_invite.user
            await user_service.link_firebase_to_user(
                session, user, registration_data.password
            )

            user_invite.is_used = True

        await session.commit()

        # Generate authentication tokens
        auth_dto, refresh_token = await auth_service.generate_token(
            session, user.email, registration_data.password
        )

        # Set refresh token as httpOnly cookie
        set_refresh_token_cookie(response, refresh_token)

        return DriverRegisterResponse(
            driver=DriverRead.model_validate(user.driver), auth=auth_dto
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering driver: {e}")
        logger.error(traceback.format_exc())

        error_message = getattr(e, "message", None)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message if error_message else str(e),
        ) from e


@router.put("/{driver_id}", response_model=DriverRead)
async def update_driver(
    driver_id: UUID,
    driver: DriverUpdate,
    session: AsyncSession = Depends(get_session),
    is_admin: bool = Depends(require_self_driver_or_admin),
) -> DriverRead:
    """
    Update an existing driver
    """
    if not is_admin:
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
    _auth: bool = Depends(require_admin),
) -> None:
    """
    Delete a driver by ID
    """
    await driver_service.delete_driver_by_id(session, driver_id)


@router.post("/test-event-email")
async def test_event_email(
    test_email: str, dispatcher: EmailDispatcher = Depends(get_email_dispatcher_depends)
) -> dict[str, str]:
    """
    Temporary endpoint to test event-driven emails.
    Delete this after testing!
    """
    simulated_db_info = {
        "first_name": "Test-Driver-Bob",
        "url": "https://food4kids.ca/fake-link-123",
    }

    # Test email sending (feel free to change with provided params, etc. as needed!)
    """
     Testable options: 
     - account-creation (context params that need to be filled in: Driver_Name_To_Replace, Sign_Up_URL, Hours_Till_Expiry), 
     - check-latest-announcement (context params that need to be filled in: Driver_Name_To_Replace, Announcement_Name, Announcement_Body, Announcement_URL), 
     - reset-password (context params that need to be filled in: Driver_Name_To_Replace, Reset_Password_URL, Days_Till_Expiry), 
     - view-upcoming-route (context params that need to be filled in: Driver_Name_To_Replace, Date_To_Replace, Time_To_Replace, Route_Duration_To_Replace,Upcoming_Route_URL)
    """
    await dispatcher.dispatch(
        email_type="reset-password",
        to=test_email,
        context={
            "Driver_Name_To_Replace": simulated_db_info["first_name"],
            "Reset_Password_URL": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "Days_Till_Expiry": 10000,
        },
    )

    return {"message": f"Test email dispatched to {test_email}!"}

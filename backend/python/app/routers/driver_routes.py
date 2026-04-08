import logging
import traceback
from typing import Literal, cast
from uuid import UUID

import firebase_admin.auth
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.services import (
    get_auth_service,
    get_user_service,
    get_user_invite_service,
)
from app.models import get_session
from app.models.driver import (
    DriverCreate,
    DriverRead,
    DriverRegister,
    DriverUpdate,
)
from app.models.user import UserCreate, UserBase, UserFinalize
from app.models.user_invite import UserInviteCreate
from app.schemas.auth import DriverRegisterResponse
from app.services.implementations.auth_service import AuthService
from app.services.implementations.driver_service import DriverService
from app.services.implementations.user_service import UserService
from app.services.implementations.user_invite_services import UserInviteService
from app.utilities.cookies import get_cookie_options

from datetime import datetime, timezone

# Initialize service
logger = logging.getLogger(__name__)
driver_service = DriverService(logger)

router = APIRouter(prefix="/drivers", tags=["drivers"])


@router.get("/", response_model=list[DriverRead])
async def get_drivers(
    session: AsyncSession = Depends(get_session),
    driver_id: UUID | None = Query(None, description="Filter by driver ID"),
    email: str | None = Query(None, description="Filter by email"),
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
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service),
    user_invite_service: UserInviteService = Depends(get_user_invite_service)
) -> DriverRead:
    """
    Register a new driver in our backend, creates a User and Driver object, returns DriverRead
    NOTE: This does not create a firebase user, ie the User is in a hanging state
    We need to do this so that we can implement our invite only system
    """
    user = None

    try:
        async with session.begin():
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
            user_invite = await user_invite_service.create_user_invite(session, user_invite_create)

        # Send invitation email
        auth_service.send_create_password_email(register_request.email, user_invite.user_invite_id)

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
    "/register", response_model=DriverRegisterResponse, status_code=status.HTTP_201_CREATED
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
        # Validate invite token
        user_invite_id = registration_data.user_invite_id
        user_invite = await user_invite_service.get_user_invite_by_id(session, user_invite_id)

        if not user_invite or user_invite.is_used or user_invite.expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or expired registration link."
            )

        # Create Firebase account for user
        user = user_invite.user
        await user_service.link_firebase_to_user(session, user, registration_data.password)

        # Generate authentication tokens
        auth_dto, refresh_token = await auth_service.generate_token(
            session, user.email, registration_data.password
        )

        # Set refresh token as httpOnly cookie
        cookie_options = get_cookie_options()
        response.set_cookie(
            "refreshToken",
            value=refresh_token,
            httponly=bool(cookie_options["httponly"]),
            samesite=cast(
                "Literal['none', 'strict', 'lax']", cookie_options["samesite"]
            ),
            secure=bool(cookie_options["secure"]),
        )

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


# @router.post(
#     "/", response_model=DriverRegisterResponse, status_code=status.HTTP_201_CREATED
# )
# async def register_driver(
#     register_request: DriverRegister,
#     response: Response,
#     session: AsyncSession = Depends(get_session),
#     auth_service: AuthService = Depends(get_auth_service),
#     user_service: UserService = Depends(get_user_service),
# ) -> DriverRegisterResponse:
#     """
#     Register a new driver in our backend, creates a User and Driver object, returns DriverRead
#     """
#     user = None
#     firebase_auth_id = None

#     try:
#         # Create user first
#         user_data = register_request.model_dump(
#             include=set(UserCreate.model_fields.keys())
#         )
#         user_create = UserCreate(**user_data)
#         user = await user_service.create_user(session, user_create)
#         firebase_auth_id = user.auth_id

#         # Set custom claims on Firebase user
#         firebase_admin.auth.set_custom_user_claims(user.auth_id, {"role": user.role})

#         # Create driver after
#         driver_data = register_request.model_dump(
#             include=set(DriverCreate.model_fields.keys())
#         )
#         driver_data["user_id"] = user.user_id
#         driver = DriverCreate(**driver_data)
#         created_driver = await driver_service.create_driver(session, driver)

#         # Generate authentication tokens
#         auth_dto, refresh_token = await auth_service.generate_token(
#             session, register_request.email, register_request.password
#         )

#         # Send email verification link
#         auth_service.send_email_verification_link(register_request.email)

#         # Set refresh token as httpOnly cookie
#         cookie_options = get_cookie_options()
#         response.set_cookie(
#             "refreshToken",
#             value=refresh_token,
#             httponly=bool(cookie_options["httponly"]),
#             samesite=cast(
#                 "Literal['none', 'strict', 'lax']", cookie_options["samesite"]
#             ),
#             secure=bool(cookie_options["secure"]),
#         )

#         return DriverRegisterResponse(
#             driver=DriverRead.model_validate(created_driver), auth=auth_dto
#         )
#     except HTTPException:
#         raise
#     except Exception as e:
#         # Compensating transaction: rollback all changes
#         logger.error(f"Error registering driver: {e}")
#         logger.error(traceback.format_exc())

#         # Attempt to clean up database user (which also attempts Firebase cleanup)
#         db_cleanup_failed = False
#         if user:
#             try:
#                 await user_service.delete_user_by_id(
#                     session=session, user_id=user.user_id
#                 )
#             except Exception as db_error:
#                 logger.error(f"Failed to rollback database user: {db_error}")
#                 db_cleanup_failed = True

#         # If database cleanup failed and we have a Firebase auth_id, attempt direct Firebase cleanup
#         # This ensures Firebase user is deleted even if database cleanup failed
#         if db_cleanup_failed and firebase_auth_id:
#             try:
#                 firebase_admin.auth.delete_user(firebase_auth_id)
#                 logger.info(
#                     f"Successfully deleted Firebase user {firebase_auth_id} via direct cleanup"
#                 )
#             except Exception as firebase_error:
#                 logger.error(
#                     f"Failed to rollback Firebase user via direct cleanup: {firebase_error}"
#                 )

#         error_message = getattr(e, "message", None)
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=error_message if error_message else str(e),
#         ) from e


@router.put("/{driver_id}", response_model=DriverRead)
async def update_driver(
    driver_id: UUID,
    driver: DriverUpdate,
    session: AsyncSession = Depends(get_session),
) -> DriverRead:
    """
    Update an existing driver
    """
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
) -> None:
    """
    Delete a driver by ID
    """
    await driver_service.delete_driver_by_id(session, driver_id)

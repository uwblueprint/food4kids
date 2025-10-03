import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import require_user_or_admin
from app.models import get_session
from app.models.user import UserCreate, UserRead, UserUpdate
from app.services.implementations.user_service import UserService

# Initialize service
logger = logging.getLogger(__name__)
user_service = UserService(logger)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=list[UserRead])
async def get_users(
    session: AsyncSession = Depends(get_session),
    user_id: int | None = Query(None, description="Filter by user ID"),
    email: str | None = Query(None, description="Filter by email"),
    _: bool = Depends(require_user_or_admin),
) -> list[UserRead]:
    """
    Get all users, optionally filter by user_id or email
    """
    if user_id and email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot query by both user_id and email",
        )

    try:
        if user_id:
            user = await user_service.get_user_by_id(session, user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with id {user_id} not found",
                )
            return [UserRead.model_validate(user)]

        elif email:
            user = await user_service.get_user_by_email(session, email)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with email {email} not found",
                )
            return [UserRead.model_validate(user)]

        else:
            users = await user_service.get_users(session)
            return [UserRead.model_validate(user) for user in users]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_user_or_admin),
) -> UserRead:
    """
    Get a single user by ID
    """
    user = await user_service.get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found",
        )
    return UserRead.model_validate(user)


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_user_or_admin),
) -> UserRead:
    """
    Create a new user
    """
    try:
        created_user = await user_service.create_user(session, user)
        return UserRead.model_validate(created_user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


@router.put("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int,
    user: UserUpdate,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_user_or_admin),
) -> UserRead:
    """
    Update an existing user
    """
    updated_user = await user_service.update_user_by_id(session, user_id, user)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found",
        )
    return UserRead.model_validate(updated_user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_user_or_admin),
) -> None:
    """
    Delete a user by ID
    """
    await user_service.delete_user_by_id(session, user_id)

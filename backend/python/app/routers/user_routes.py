import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import get_session
from ..dependencies.auth import require_user_or_admin
from ..models.user import UserCreate, UserUpdate, UserRead
from ..services.implementations.user_service import UserService

# Initialize service
logger = logging.getLogger(__name__)
user_service = UserService(logger)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=List[UserRead])
async def get_users(
    session: AsyncSession = Depends(get_session),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    email: Optional[str] = Query(None, description="Filter by email"),
    _: bool = Depends(require_user_or_admin),
) -> List[UserRead]:
    """
    Get all users, optionally filter by user_id or email
    """
    if user_id and email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot query by both user_id and email"
        )

    try:
        if user_id:
            user = await user_service.get_user_by_id(session, user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with id {user_id} not found"
                )
            return [user]
        
        elif email:
            user = await user_service.get_user_by_email(session, email)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with email {email} not found"
                )
            return [user]
        
        else:
            users = await user_service.get_users(session)
            return users

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


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
            detail=f"User with id {user_id} not found"
        )
    return user


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
        return created_user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


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
            detail=f"User with id {user_id} not found"
        )
    return updated_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_user_or_admin),
):
    """
    Delete a user by ID
    """
    success = await user_service.delete_user_by_id(session, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )

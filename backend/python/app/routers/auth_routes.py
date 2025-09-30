import os
import logging
import traceback
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import EmailStr

from ..models import get_session
from ..dependencies.auth import get_current_user_id, get_current_user_email, get_current_database_user_id
from ..models.user import UserCreate, UserRegister
from ..schemas.auth import LoginRequest, AuthResponse, RefreshResponse
from ..services.implementations.auth_service import AuthService
from ..services.implementations.email_service import EmailService
from ..services.implementations.user_service import UserService
from ..models.enum import RoleEnum
from ..config import settings

# Initialize services
logger = logging.getLogger(__name__)
user_service = UserService(logger)
email_service = EmailService(
    logger,
    {
        "refresh_token": settings.mailer_refresh_token,
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": settings.mailer_client_id,
        "client_secret": settings.mailer_client_secret,
    },
    settings.mailer_user,
    "Food4Kids",
)
auth_service = AuthService(logger, user_service, email_service)

router = APIRouter(prefix="/auth", tags=["authentication"])


def get_cookie_options():
    """Get cookie options based on environment"""
    return {
        "httponly": True,
        "samesite": "none" if settings.preview_deploy else "strict",
        "secure": settings.is_production,
    }


@router.post("/login", response_model=AuthResponse)
async def login(
    login_request: LoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_session),
):
    """
    Returns access token in response body and sets refreshToken as an httpOnly cookie
    """
    logger.info(f"Login request: {login_request}")
    try:
        if not login_request.email or not login_request.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email and password are required"
            )
        auth_dto, refresh_token = await auth_service.generate_token(
            session, login_request.email, login_request.password
        )
        
        # Set refresh token as httpOnly cookie
        response.set_cookie(
            "refreshToken",
            value=refresh_token,
            **get_cookie_options(),
        )
        
        return auth_dto
    except Exception as e:
        error_message = getattr(e, "message", None)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message if error_message else str(e)
        )


@router.post("/register", response_model=AuthResponse)
async def register(
    register_request: UserRegister,
    response: Response,
    session: AsyncSession = Depends(get_session),
):
    """
    Returns access token and user info in response body and sets refreshToken as an httpOnly cookie
    """
    try:
        # Create user with default role
        user_data = register_request.model_dump()
        user_data["role"] = RoleEnum.USER
        user = UserCreate(**user_data)
        
        await user_service.create_user(session, user)
        auth_dto, refresh_token = await auth_service.generate_token(
            session, register_request.email, register_request.password
        )

        auth_service.send_email_verification_link(register_request.email)

        # Set refresh token as httpOnly cookie
        response.set_cookie(
            "refreshToken",
            value=refresh_token,
            **get_cookie_options(),
        )
        
        return auth_dto
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        # Stack trace
        logger.error(traceback.format_exc())
        error_message = getattr(e, "message", None)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message if error_message else str(e)
        )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
):
    """
    Returns access token in response body and sets refreshToken as an httpOnly cookie
    """
    try:
        refresh_token = request.cookies.get("refreshToken")
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not found"
            )
        
        token = auth_service.renew_token(refresh_token)
        
        # Set new refresh token as httpOnly cookie
        response.set_cookie(
            "refreshToken",
            value=token.refresh_token,
            **get_cookie_options(),
        )
        
        return {"access_token": token.access_token}
    except Exception as e:
        error_message = getattr(e, "message", None)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message if error_message else str(e)
        )


@router.post("/logout/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    current_database_user_id: int = Depends(get_current_database_user_id),
):
    """
    Revokes all of the specified user's refresh tokens
    """
    # Check if the user is authorized to logout this user_id
    if user_id != current_database_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not authorized to logout this user"
        )
    
    try:
        await auth_service.revoke_tokens(session, user_id)
    except Exception as e:
        error_message = getattr(e, "message", None)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message if error_message else str(e)
        )


@router.post("/resetPassword/{email}", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    email: EmailStr,
    session: AsyncSession = Depends(get_session),
    current_user_email: str = Depends(get_current_user_email),
):
    """
    Triggers password reset for user with specified email (reset link will be emailed)
    """
    # Check if the user is authorized to reset this email's password
    if email != current_user_email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not authorized to reset this email's password"
        )
    
    try:
        auth_service.reset_password(email)
    except Exception as e:
        error_message = getattr(e, "message", None)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message if error_message else str(e)
        )

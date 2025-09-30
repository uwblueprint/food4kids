from typing import Set, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import firebase_admin.auth

from ..services.implementations.auth_service import AuthService
from ..services.implementations.user_service import UserService
from ..services.implementations.email_service import EmailService
from ..models import get_session
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

# Security scheme
security = HTTPBearer()


def get_access_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Extract access token from Authorization header"""
    return credentials.credentials


def require_authorization_by_role(roles: Set[str]):
    """
    Create a dependency that checks if the user has one of the required roles
    
    :param roles: Set of authorized roles
    :return: FastAPI dependency function
    """
    async def check_role(
        access_token: str = Depends(get_access_token),
        session: AsyncSession = Depends(get_session)
    ) -> bool:
        try:
            authorized = await auth_service.is_authorized_by_role(session, access_token, roles)
            if not authorized:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="You are not authorized to make this request."
                )
            return True
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You are not authorized to make this request."
            )
    
    return check_role


def require_authorization_by_user_id(user_id: str):
    """
    Create a dependency that checks if the user is authorized for a specific user_id
    
    :param user_id: The user ID to check authorization for
    :return: FastAPI dependency function
    """
    async def check_user_id(
        access_token: str = Depends(get_access_token),
        session: AsyncSession = Depends(get_session)
    ) -> bool:
        try:
            authorized = await auth_service.is_authorized_by_user_id(session, access_token, user_id)
            if not authorized:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="You are not authorized to make this request."
                )
            return True
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You are not authorized to make this request."
            )
    
    return check_user_id


def require_authorization_by_email(email: str):
    """
    Create a dependency that checks if the user is authorized for a specific email
    
    :param email: The email to check authorization for
    :return: FastAPI dependency function
    """
    def check_email(access_token: str = Depends(get_access_token)) -> bool:
        try:
            authorized = auth_service.is_authorized_by_email(access_token, email)
            if not authorized:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="You are not authorized to make this request."
                )
            return True
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You are not authorized to make this request."
            )
    
    return check_email


# Common role dependencies
require_user_or_admin = require_authorization_by_role({"User", "Admin"})
require_admin = require_authorization_by_role({"Admin"})


def get_current_user_id(access_token: str = Depends(get_access_token)) -> str:
    """
    Get the current user ID from the access token
    
    :param access_token: JWT access token
    :return: User ID
    """
    try:
        decoded_token = firebase_admin.auth.verify_id_token(access_token, check_revoked=True)
        return decoded_token["uid"]
    except Exception as e:
        logger.error(f"Failed to decode access token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


def get_current_user_email(access_token: str = Depends(get_access_token)) -> str:
    """
    Get the current user email from the access token
    
    :param access_token: JWT access token
    :return: User email
    """
    try:
        decoded_token = firebase_admin.auth.verify_id_token(access_token, check_revoked=True)
        return decoded_token["email"]
    except Exception as e:
        logger.error(f"Failed to decode access token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


async def get_current_database_user_id(
    access_token: str = Depends(get_access_token),
    session: AsyncSession = Depends(get_session)
) -> int:
    """
    Get the current database user ID from the access token
    
    :param access_token: JWT access token
    :param session: Database session
    :return: Database user ID (integer)
    """
    try:
        decoded_token = firebase_admin.auth.verify_id_token(access_token, check_revoked=True)
        firebase_uid = decoded_token["uid"]
        
        # Convert Firebase UID to database user ID
        database_user_id = await user_service.get_user_id_by_auth_id(session, firebase_uid)
        return database_user_id
    except Exception as e:
        logger.error(f"Failed to get database user ID from access token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

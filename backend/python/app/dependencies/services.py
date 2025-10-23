"""
Service dependency injection module
"""

import logging
from functools import lru_cache

from fastapi import Depends

from app.config import settings
from app.services.implementations.auth_service import AuthService
from app.services.implementations.driver_assignment_service import (
    DriverAssignmentService,
)
from app.services.implementations.driver_service import DriverService
from app.services.implementations.email_service import EmailService
from app.services.implementations.entity_service import EntityService
from app.services.implementations.location_group_service import LocationGroupService
from app.services.implementations.route_group_service import RouteGroupService
from app.services.implementations.simple_entity_service import SimpleEntityService
from app.services.interfaces.auth_service import IAuthService
from app.services.interfaces.driver_assignment_service import IDriverAssignmentService
from app.services.interfaces.driver_service import IDriverService
from app.services.interfaces.email_service import IEmailService
from app.services.interfaces.entity_service import IEntityService
from app.services.interfaces.location_group_service import ILocationGroupService
from app.services.interfaces.route_group_service import IRouteGroupService
from app.services.interfaces.simple_entity_service import ISimpleEntityService


@lru_cache
def get_logger() -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(__name__)


@lru_cache
def get_email_service() -> IEmailService:
    """Get email service instance"""
    logger = get_logger()
    return EmailService(
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


@lru_cache
def get_driver_service() -> IDriverService:
    """Get driver service instance"""
    logger = get_logger()
    return DriverService(logger)


@lru_cache
def get_auth_service(
    driver_service: IDriverService = Depends(get_driver_service),
    email_service: IEmailService = Depends(get_email_service),
) -> IAuthService:
    """Get auth service instance"""
    logger = get_logger()
    return AuthService(logger, driver_service, email_service)


@lru_cache
def get_entity_service() -> IEntityService:
    """Get entity service instance"""
    logger = get_logger()
    return EntityService(logger)


@lru_cache
def get_simple_entity_service() -> ISimpleEntityService:
    """Get simple entity service instance"""
    logger = get_logger()
    return SimpleEntityService(logger)


@lru_cache
def get_driver_assignment_service() -> IDriverAssignmentService:
    """Get driver assignment service instance"""
    logger = get_logger()
    return DriverAssignmentService(logger)


@lru_cache
def get_location_group_service() -> ILocationGroupService:
    """Get location group service instance"""
    logger = get_logger()
    return LocationGroupService(logger)


@lru_cache
def get_route_group_service() -> IRouteGroupService:
    """Get route group service instance"""
    logger = get_logger()
    return RouteGroupService(logger)

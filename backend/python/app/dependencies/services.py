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
from app.services.implementations.mock_routing_algorithm import (
    MockRoutingAlgorithm,
)
from app.services.implementations.route_group_service import RouteGroupService
from app.services.implementations.scheduler_service import SchedulerService
from app.services.implementations.simple_entity_service import SimpleEntityService
from app.services.implementations.user_service import UserService
from app.services.protocols.routing_algorithm import RoutingAlgorithmProtocol
from app.utilities.google_maps_client import GoogleMapsClient


@lru_cache
def get_logger() -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(__name__)


@lru_cache
def get_email_service() -> EmailService:
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
def get_user_service() -> UserService:
    """Get user service instance"""
    logger = get_logger()
    return UserService(logger)


@lru_cache
def get_driver_service() -> DriverService:
    """Get driver service instance"""
    logger = get_logger()
    return DriverService(logger)


def get_auth_service(
    user_service: UserService = Depends(get_user_service),
    driver_service: DriverService = Depends(get_driver_service),
    email_service: EmailService = Depends(get_email_service),
) -> AuthService:
    """Get auth service instance"""
    logger = get_logger()
    return AuthService(logger, user_service, driver_service, email_service)


@lru_cache
def get_entity_service() -> EntityService:
    """Get entity service instance"""
    logger = get_logger()
    return EntityService(logger)


@lru_cache
def get_simple_entity_service() -> SimpleEntityService:
    """Get simple entity service instance"""
    logger = get_logger()
    return SimpleEntityService(logger)


@lru_cache
def get_driver_assignment_service() -> DriverAssignmentService:
    """Get driver assignment service instance"""
    logger = get_logger()
    return DriverAssignmentService(logger)


@lru_cache
def get_location_group_service() -> LocationGroupService:
    """Get location group service instance"""
    logger = get_logger()
    return LocationGroupService(logger)


@lru_cache
def get_route_group_service() -> RouteGroupService:
    """Get route group service instance"""
    logger = get_logger()
    return RouteGroupService(logger)


@lru_cache
def get_routing_algorithm() -> RoutingAlgorithmProtocol:
    """Get routing algorithm instance (mock).

    Swap this to use a different algorithm implementation.
    """
    return MockRoutingAlgorithm()


@lru_cache
def get_scheduler_service() -> SchedulerService:
    """Get scheduler service instance"""
    logger = get_logger()
    return SchedulerService(logger)


@lru_cache
def get_google_maps_client() -> GoogleMapsClient:
    """Get Google Maps client instance"""
    logger = get_logger()
    return GoogleMapsClient(logger, settings.google_maps_api_key)

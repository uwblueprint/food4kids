"""Service dependency injection module.

Convention:
- Leaf factories (no service dependencies — just a logger, settings, or an
  expensive client like GoogleMapsClient) use ``@lru_cache`` and call
  ``get_logger()`` directly. They are process-wide singletons.
- Composite factories (those that depend on other services/clients) take those
  dependencies via ``Depends(...)`` rather than calling the other factory
  directly in the body. This keeps the dependency graph explicit and lets tests
  swap pieces via ``app.dependency_overrides``. See ``get_auth_service`` and
  ``get_location_service``.
"""

import logging
from functools import lru_cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import settings
from app.models.enum import RouteGenerationMethod
from app.services.implementations.admin_service import AdminService
from app.services.implementations.announcement_service import AnnouncementService
from app.services.implementations.auth_service import AuthService
from app.services.implementations.billing_service import BillingService
from app.services.implementations.cascading_routing_algorithm import (
    build_default_cascade,
)
from app.services.implementations.driver_service import DriverService
from app.services.implementations.email_dispatcher import EmailDispatcher
from app.services.implementations.email_service import EmailService
from app.services.implementations.google_maps_routing_service import (
    GoogleMapsFleetRoutingAlgorithm,
)
from app.services.implementations.location_group_service import LocationGroupService
from app.services.implementations.location_service import LocationService
from app.services.implementations.note_chain_service import NoteChainService
from app.services.implementations.password_reset_token_service import (
    PasswordResetTokenService,
)
from app.services.implementations.quota_service import QuotaService
from app.services.implementations.route_group_service import RouteGroupService
from app.services.implementations.routes_api_routing_service import (
    RoutesApiSingleVehicleAlgorithm,
)
from app.services.implementations.scheduler_service import SchedulerService
from app.services.implementations.sweep_algorithm import SweepAlgorithm
from app.services.implementations.system_settings_service import SystemSettingsService
from app.services.implementations.user_invite_service import UserInviteService
from app.services.implementations.user_service import UserService
from app.services.protocols.routing_algorithm import RoutingAlgorithmProtocol
from app.templates.email_renderer import TemplateRenderer
from app.utilities.billing_client import BillingClient
from app.utilities.gcp_client import GCPStorageClient
from app.utilities.google_maps_client import GoogleMapsClient


@lru_cache
def get_logger() -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(__name__)


@lru_cache
def get_announcement_service() -> AnnouncementService:
    """Get announcement service instance"""
    logger = get_logger()
    return AnnouncementService(logger)


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
def get_template_renderer() -> TemplateRenderer:
    """Get template renderer instance"""
    logger = get_logger()
    return TemplateRenderer(template_dir="./app/templates", logger=logger)


@lru_cache
def get_email_dispatcher() -> EmailDispatcher:
    """Get email dispatcher instance"""
    return EmailDispatcher(
        email_service=get_email_service(),
        template_renderer=get_template_renderer(),
        logger=get_logger(),
    )


def get_email_dispatcher_depends() -> EmailDispatcher:
    """Get email dispatcher for dependency injection in route handlers"""
    return get_email_dispatcher()


@lru_cache
def get_user_service() -> UserService:
    """Get user service instance"""
    logger = get_logger()
    return UserService(logger)


@lru_cache
def get_user_invite_service() -> UserInviteService:
    """Get user invite service instance"""
    logger = get_logger()
    return UserInviteService(logger)


@lru_cache
def get_password_reset_token_service() -> PasswordResetTokenService:
    """Get password reset token service instance"""
    logger = get_logger()
    return PasswordResetTokenService(logger)


@lru_cache
def get_driver_service() -> DriverService:
    """Get driver service instance"""
    logger = get_logger()
    return DriverService(logger)


@lru_cache
def get_admin_service() -> AdminService:
    """Get admin service instance"""
    logger = get_logger()
    return AdminService(logger)


def get_auth_service(
    user_service: UserService = Depends(get_user_service),
    driver_service: DriverService = Depends(get_driver_service),
    admin_service: AdminService = Depends(get_admin_service),
    email_service: EmailService = Depends(get_email_service),
) -> AuthService:
    """Get auth service instance"""
    logger = get_logger()
    return AuthService(
        logger, user_service, driver_service, admin_service, email_service
    )


@lru_cache
def get_note_chain_service() -> NoteChainService:
    """Get note chain service instance"""
    logger = get_logger()
    return NoteChainService(logger)


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
def get_quota_service() -> QuotaService:
    """Get quota service instance"""
    logger = get_logger()
    return QuotaService(logger, settings)


@lru_cache
def get_routing_algorithm() -> RoutingAlgorithmProtocol:
    """The routing engine used when no system settings are available.

    Prefer ``build_routing_algorithm``, which honours the configured method and
    can cascade. This remains for callers with no session to read settings on.
    """
    return GoogleMapsFleetRoutingAlgorithm()


def build_routing_algorithm(
    method: RouteGenerationMethod,
    session_maker: async_sessionmaker[AsyncSession],
    warehouse_lat: float,
    warehouse_lon: float,
    children_per_box: int,
) -> RoutingAlgorithmProtocol:
    """Build the routing engine for one generation job.

    ``AUTO`` returns the cascade, which spends each API's free monthly
    allowance in quality order before falling back. The explicit methods pin
    generation to a single engine and skip the quota check entirely — forcing a
    paid engine past its free room is a deliberate decision to start paying.

    Built per job rather than cached: the cascade records which tier it used,
    and a shared instance would race between concurrent jobs.
    """
    fleet_routing = GoogleMapsFleetRoutingAlgorithm()
    single_vehicle = RoutesApiSingleVehicleAlgorithm(
        warehouse_lat=warehouse_lat,
        warehouse_lon=warehouse_lon,
        children_per_box=children_per_box,
    )
    cluster_sweep = SweepAlgorithm(
        warehouse_lat=warehouse_lat,
        warehouse_lon=warehouse_lon,
        children_per_box=children_per_box,
    )

    if method == RouteGenerationMethod.FLEET_ROUTING:
        return fleet_routing
    if method == RouteGenerationMethod.SINGLE_VEHICLE:
        return single_vehicle
    if method == RouteGenerationMethod.CLUSTER_SWEEP:
        return cluster_sweep

    return build_default_cascade(
        get_quota_service(),
        session_maker,
        fleet_routing,
        single_vehicle,
        cluster_sweep,
    )


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


@lru_cache
def get_system_settings_service() -> SystemSettingsService:
    """Get system settings service instance"""
    logger = get_logger()
    return SystemSettingsService(logger, get_google_maps_client())


def get_location_service(
    google_maps_client: GoogleMapsClient = Depends(get_google_maps_client),
    system_settings_service: SystemSettingsService = Depends(
        get_system_settings_service
    ),
) -> LocationService:
    """Get location service instance"""
    logger = get_logger()
    return LocationService(logger, google_maps_client, system_settings_service)


@lru_cache
def get_gcp_storage_client() -> GCPStorageClient:
    """Get GCP Storage client instance"""
    logger = get_logger()
    return GCPStorageClient(logger, settings.gcp_bucket_name)


@lru_cache
def get_billing_client() -> BillingClient:
    """Get billing client instance"""
    logger = get_logger()
    return BillingClient(logger)


def get_billing_service(
    billing_client: BillingClient = Depends(get_billing_client),
) -> BillingService:
    """Get billing service instance"""
    logger = get_logger()
    return BillingService(logger, billing_client)

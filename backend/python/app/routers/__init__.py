from fastapi import APIRouter, FastAPI

from . import (
    admin_routes,
    announcement_routes,
    auth_routes,
    billing_routes,
    driver_history_routes,
    driver_routes,
    job_routes,
    location_group_routes,
    location_routes,
    note_chain_routes,
    note_routes,
    report_routes,
    route_group_routes,
    route_routes,
    system_settings_routes,
    upload_routes,
)

# Every route is mounted under this prefix so Firebase Hosting can rewrite
# /api/** to this service and the browser sees a single origin — which is what
# lets the refresh cookie stay SameSite=strict. Hosting forwards the matched
# path verbatim rather than stripping the prefix, so the routes carry it.
API_PREFIX = "/api"


def init_app(app: FastAPI) -> None:
    """Initialize all routers with the FastAPI app"""
    api = APIRouter(prefix=API_PREFIX)
    api.include_router(admin_routes.router)
    api.include_router(announcement_routes.router)
    api.include_router(auth_routes.router)
    api.include_router(billing_routes.router)
    api.include_router(driver_history_routes.router)
    api.include_router(driver_routes.router)
    api.include_router(location_group_routes.router)
    api.include_router(route_group_routes.router)
    api.include_router(route_routes.router)
    api.include_router(location_routes.router)
    api.include_router(note_chain_routes.router)
    api.include_router(note_routes.router)
    api.include_router(job_routes.router)
    api.include_router(system_settings_routes.router)
    api.include_router(upload_routes.router)
    api.include_router(report_routes.router)

    app.include_router(api)

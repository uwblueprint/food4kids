from fastapi import APIRouter, FastAPI

from . import (
    admin_routes,
    announcement_routes,
    auth_routes,
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


def init_app(app: FastAPI) -> None:
    """Initialize all routers with the FastAPI app.

    Everything is mounted under /api so Firebase Hosting can rewrite
    ``/api/**`` to this service and the browser sees one origin. Hosting
    forwards the matched path verbatim — it does not strip the prefix — so the
    routes have to carry it themselves.
    """
    api = APIRouter(prefix="/api")

    api.include_router(admin_routes.router)
    api.include_router(announcement_routes.router)
    api.include_router(auth_routes.router)
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

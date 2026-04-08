from fastapi import FastAPI

from . import (
    admin_routes,
    announcement_routes,
    auth_routes,
    driver_assignment_routes,
    driver_history_routes,
    driver_routes,
    entity_routes,
    job_routes,
    location_group_routes,
    location_routes,
    note_chain_routes,
    route_group_routes,
    route_routes,
    upload_routes,
)


def init_app(app: FastAPI) -> None:
    """Initialize all routers with the FastAPI app"""
    app.include_router(admin_routes.router)
    app.include_router(announcement_routes.router)
    app.include_router(driver_assignment_routes.router)
    app.include_router(auth_routes.router)
    app.include_router(driver_history_routes.router)
    app.include_router(driver_routes.router)
    app.include_router(entity_routes.router)
    app.include_router(location_group_routes.router)
    app.include_router(route_group_routes.router)
    app.include_router(route_routes.router)
    app.include_router(location_routes.router)
    app.include_router(note_chain_routes.router)
    app.include_router(job_routes.router)
    app.include_router(upload_routes.router)

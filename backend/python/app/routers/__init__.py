from fastapi import FastAPI

from . import (
    auth_routes,
    entity_routes,
    location_group_routes,
    route_group_routes,
    route_routes,
    simple_entity_routes,
)


def init_app(app: FastAPI) -> None:
    """Initialize all routers with the FastAPI app"""
    app.include_router(auth_routes.router)
    app.include_router(entity_routes.router)
    app.include_router(simple_entity_routes.router)
    app.include_router(location_group_routes.router)
    app.include_router(route_group_routes.router)
    app.include_router(route_routes.router)

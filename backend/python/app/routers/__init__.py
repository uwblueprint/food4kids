from fastapi import FastAPI

from . import (
    auth_routes,
    entity_routes,
    job_routes,
    location_group_routes,
<<<<<<< HEAD
    route_group_routes,
    simple_entity_routes,
=======
    simple_entity_routes,
    user_routes,
>>>>>>> 60cc40f1582d3e202aafec387e2306bfd622a8a6
)


def init_app(app: FastAPI) -> None:
    """Initialize all routers with the FastAPI app"""
    app.include_router(auth_routes.router)
    app.include_router(entity_routes.router)
    app.include_router(simple_entity_routes.router)
    app.include_router(location_group_routes.router)
    app.include_router(job_routes.router)

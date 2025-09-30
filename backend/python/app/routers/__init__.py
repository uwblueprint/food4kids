from fastapi import FastAPI

from . import user_routes, auth_routes, entity_routes, simple_entity_routes


def init_app(app: FastAPI):
    """Initialize all routers with the FastAPI app"""
    app.include_router(user_routes.router)
    app.include_router(auth_routes.router)
    app.include_router(entity_routes.router)
    app.include_router(simple_entity_routes.router)

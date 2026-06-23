from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from logging.config import dictConfig

import firebase_admin
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute

import app.models as models
from app.dependencies.services import get_scheduler_service
from app.services.jobs import init_jobs

from .config import settings
from .models import init_app as init_models
from .routers import init_app as init_routers


def configure_logging() -> None:
    """Configure application logging based on environment"""

    # Base configuration that applies to all environments
    base_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s"
            },
            "simple": {"format": "%(levelname)s - %(message)s"},
        },
        "handlers": {},
        "root": {},
    }

    if settings.is_development:
        # Development: Log to console with INFO level, and errors to file
        base_config["handlers"] = {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "detailed",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.FileHandler",
                "level": "ERROR",
                "filename": "error.log",
                "formatter": "detailed",
            },
        }
        base_config["root"] = {"level": "INFO", "handlers": ["console", "file"]}

        # Set specific loggers to appropriate levels
        base_config["loggers"] = {
            "uvicorn": {"level": "INFO"},
            "uvicorn.access": {"level": "INFO"},
            "sqlalchemy.engine": {
                "level": "INFO"
            },  # Use "WARNING" to avoid SQL query noise
            "app": {"level": "DEBUG"},  # Your app logs at DEBUG level
        }

    elif settings.is_testing:
        # Testing: Minimal logging to avoid test output noise
        base_config["handlers"] = {
            "console": {
                "class": "logging.StreamHandler",
                "level": "WARNING",
                "formatter": "simple",
                "stream": "ext://sys.stdout",
            },
        }
        base_config["root"] = {"level": "WARNING", "handlers": ["console"]}

    else:  # Production
        # Production: Only errors to file, warnings and above to console
        base_config["handlers"] = {
            "console": {
                "class": "logging.StreamHandler",
                "level": "WARNING",
                "formatter": "simple",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.FileHandler",
                "level": "ERROR",
                "filename": "error.log",
                "formatter": "detailed",
            },
        }
        base_config["root"] = {"level": "WARNING", "handlers": ["console", "file"]}

    dictConfig(base_config)


def initialize_firebase() -> None:
    """Initialize Firebase Admin SDK"""
    firebase_admin.initialize_app(
        firebase_admin.credentials.Certificate(
            {
                "type": "service_account",
                "project_id": settings.firebase_project_id,
                "private_key_id": settings.firebase_svc_account_private_key_id,
                "private_key": settings.firebase_svc_account_private_key.replace(
                    "\\n", "\n"
                ),
                "client_email": settings.firebase_svc_account_client_email,
                "client_id": settings.firebase_svc_account_client_id,
                "auth_uri": settings.firebase_svc_account_auth_uri,
                "token_uri": settings.firebase_svc_account_token_uri,
                "auth_provider_x509_cert_url": settings.firebase_svc_account_auth_provider_x509_cert_url,
                "client_x509_cert_url": settings.firebase_svc_account_client_x509_cert_url,
            }
        ),
    )


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan management"""
    # Startup
    configure_logging()
    initialize_firebase()
    init_models()

    # Initialize scheduler
    scheduler_service = get_scheduler_service()
    scheduler_service.start()
    if models.async_session_maker_instance is None:
        raise RuntimeError("Database not initialized. Call init_app() first.")
    async with models.async_session_maker_instance() as session:
        await init_jobs(scheduler_service, session)

    yield

    # Cleanup: stop the scheduler service during application shutdown
    scheduler_service.stop()


def _use_route_name_as_operation_id(route: APIRoute) -> str:
    """Use the route's function name as the OpenAPI operation ID.

    Why: FastAPI's default operation IDs include the full path and method
    (e.g. ``read_announcements_announcements__get``), which produces ugly
    function names in generated TypeScript clients. Using the route name
    yields clean names like ``get_announcements``.
    """
    return route.name


def _assert_unique_operation_ids(app: FastAPI) -> None:
    """Fail fast if two routes resolve to the same OpenAPI operation ID.

    Operation IDs come from the route's function name (see
    ``_use_route_name_as_operation_id``). FastAPI does not enforce uniqueness,
    but duplicates silently produce colliding function names in the generated
    TypeScript client. Catch the collision at startup instead of debugging a
    confusing client later — if this fires, rename one of the route handlers.
    """
    seen: dict[str, str] = {}
    for route in app.routes:
        if isinstance(route, APIRoute):
            if route.name in seen:
                raise ValueError(
                    f"Duplicate OpenAPI operation ID '{route.name}': used by "
                    f"both {seen[route.name]} and {route.path}. Route handler "
                    "function names must be unique across routers."
                )
            seen[route.name] = route.path


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""

    app = FastAPI(
        title="Food4Kids API",
        description="Backend API for the Food4Kids application",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        generate_unique_id_function=_use_route_name_as_operation_id,
    )

    # Configure CORS
    cors_origins = settings.cors_origins.copy()
    if settings.is_development:
        cors_origins.extend(
            [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
            ]
        )

    # Add regex pattern for preview deployments
    cors_origins.append("https://uw-blueprint-starter-code--pr.*\\.web\\.app")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=settings.cors_supports_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize routers
    init_routers(app)
    _assert_unique_operation_ids(app)

    return app

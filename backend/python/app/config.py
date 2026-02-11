import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings using Pydantic BaseSettings
    """

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )

    # Environment
    environment: str = Field(default="development")
    debug: bool = Field(default=True)
    testing: bool = Field(default=False)

    # Database
    postgres_user: str = Field(default="")
    postgres_password: str = Field(default="")
    postgres_db_dev: str = Field(default="")
    postgres_db_test: str = Field(default="")
    db_host: str = Field(default="")
    database_url: str = Field(default="")

    # CORS
    cors_origins: list[str] = Field(
        default=[
            "http://localhost:3000",
            "https://uw-blueprint-starter-code.firebaseapp.com",
            "https://uw-blueprint-starter-code.web.app",
        ]
    )
    cors_supports_credentials: bool = Field(default=True)

    # Firebase
    firebase_project_id: str = Field(default="")
    firebase_svc_account_private_key_id: str = Field(default="")
    firebase_svc_account_private_key: str = Field(default="")
    firebase_svc_account_client_email: str = Field(default="")
    firebase_svc_account_client_id: str = Field(default="")
    firebase_svc_account_auth_uri: str = Field(default="")
    firebase_svc_account_token_uri: str = Field(default="")
    firebase_svc_account_auth_provider_x509_cert_url: str = Field(default="")
    firebase_svc_account_client_x509_cert_url: str = Field(default="")

    # Email
    mailer_refresh_token: str = Field(default="")
    mailer_client_id: str = Field(default="")
    mailer_client_secret: str = Field(default="")
    mailer_user: str = Field(default="")

    # Server
    port: int = Field(default=8080)
    host: str = Field(default="0.0.0.0")

    # Scheduler
    scheduler_timezone: str = Field(default="America/New_York")

    # Google Maps
    google_maps_api_key: str = Field(default="")

    # Route Optimization (service account for Fleet Routing API)
    route_opt_project_id: str = Field(default="")
    route_opt_private_key_id: str = Field(default="")
    route_opt_private_key: str = Field(default="")
    route_opt_client_email: str = Field(default="")

    # Preview deploy
    preview_deploy: bool = Field(default=False)

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_testing(self) -> bool:
        return self.environment == "testing"


class DevelopmentSettings(Settings):
    """Development-specific settings"""

    debug: bool = True
    testing: bool = False
    postgres_user: str = Field(default="postgres")
    postgres_password: str = Field(default="password")
    postgres_db_dev: str = Field(default="f4k")
    postgres_db_test: str = Field(default="f4k_test")
    db_host: str = Field(default="localhost")
    firebase_project_id: str = Field(default="")
    firebase_svc_account_private_key_id: str = Field(default="")
    firebase_svc_account_private_key: str = Field(default="")
    firebase_svc_account_client_email: str = Field(default="")
    firebase_svc_account_client_id: str = Field(default="")
    firebase_svc_account_auth_uri: str = Field(default="")
    firebase_svc_account_token_uri: str = Field(default="")
    firebase_svc_account_auth_provider_x509_cert_url: str = Field(default="")
    firebase_svc_account_client_x509_cert_url: str = Field(default="")
    google_maps_api_key: str = Field(default="")


class ProductionSettings(Settings):
    """Production-specific settings"""

    debug: bool = False
    testing: bool = False
    postgres_user: str = Field(default="postgres")
    postgres_password: str = Field(default="password")
    postgres_db_dev: str = Field(default="f4k")
    postgres_db_test: str = Field(default="f4k_test")
    db_host: str = Field(default="localhost")
    firebase_project_id: str = Field(default="")
    firebase_svc_account_private_key_id: str = Field(default="")
    firebase_svc_account_private_key: str = Field(default="")
    firebase_svc_account_client_email: str = Field(default="")
    firebase_svc_account_client_id: str = Field(default="")
    firebase_svc_account_auth_uri: str = Field(default="")
    firebase_svc_account_token_uri: str = Field(default="")
    firebase_svc_account_auth_provider_x509_cert_url: str = Field(default="")
    firebase_svc_account_client_x509_cert_url: str = Field(default="")
    google_maps_api_key: str = Field(default="")


class TestingSettings(Settings):
    """Testing-specific settings"""

    debug: bool = False
    testing: bool = True
    mongodb_url: str = "mongomock://localhost"
    postgres_user: str = Field(default="postgres")
    postgres_password: str = Field(default="password")
    postgres_db_dev: str = Field(default="f4k")
    postgres_db_test: str = Field(default="f4k_test")
    db_host: str = Field(default="localhost")
    firebase_project_id: str = Field(default="")
    firebase_svc_account_private_key_id: str = Field(default="")
    firebase_svc_account_private_key: str = Field(default="")
    firebase_svc_account_client_email: str = Field(default="")
    firebase_svc_account_client_id: str = Field(default="")
    firebase_svc_account_auth_uri: str = Field(default="")
    firebase_svc_account_token_uri: str = Field(default="")
    firebase_svc_account_auth_provider_x509_cert_url: str = Field(default="")
    firebase_svc_account_client_x509_cert_url: str = Field(default="")
    google_maps_api_key: str = Field(default="")


def get_settings() -> Settings:
    """Get settings based on environment"""
    environment = os.getenv("APP_ENV", "development")

    if environment == "production":
        return ProductionSettings()
    elif environment == "testing":
        return TestingSettings()
    else:
        return DevelopmentSettings()


# Global settings instance
settings = get_settings()

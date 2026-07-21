import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import json
from pathlib import Path


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

    # GCP
    gcp_bucket_name: str = Field(default="")
    gcp_service_account_project_id: str = Field(default="")
    gcp_service_account_private_key_id: str = Field(default="")
    gcp_service_account_private_key: str = Field(default="")
    gcp_service_account_client_email: str = Field(default="")
    gcp_service_account_client_id: str = Field(default="")
    gcp_service_account_auth_uri: str = Field(default="")
    gcp_service_account_token_uri: str = Field(default="")
    gcp_service_account_auth_provider_x509_cert_url: str = Field(default="")
    gcp_service_account_client_x509_cert_url: str = Field(default="")
    # Preview deploy
    preview_deploy: bool = Field(default=False)

    # Frontend URL
    frontend_base_url: str = Field(default="http://localhost:3000")

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_testing(self) -> bool:
        return self.environment == "testing"

    @property
    def FRONTEND_BASE_URL(self) -> str:
        return self.frontend_base_url


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
    """Get settings based on environment, parsing cloud secrets if mounted"""
    environment = os.getenv("APP_ENV", "development")
    
    secrets_file_path = Path("/secrets/config.json")
    cloud_secrets = {}
    
    if secrets_file_path.exists():
        try:
            with open(secrets_file_path, "r") as f:
                raw_secrets = json.load(f)
                
                # Convert uppercase JSON keys to lowercase for Pydantic mapping
                lowercased_secrets = {k.lower(): v for k, v in raw_secrets.items()}
                
                target_class = DevelopmentSettings
                if environment == "production":
                    target_class = ProductionSettings
                elif environment == "testing":
                    target_class = TestingSettings
                
                # Filter keys using Pydantic v1 __fields__ syntax to avoid breaking
                allowed_fields = target_class.__fields__.keys()
                cloud_secrets = {k: v for k, v in lowercased_secrets.items() if k in allowed_fields}

                print(f"--- DIAGNOSTIC DB_HOST: '{cloud_secrets.get('db_host')}' ---")
                print(f"--- DIAGNOSTIC USER: '{cloud_secrets.get('postgres_user')}' ---")
                # Print the length and first 3 characters to protect your secret while confirming it
                pwd = cloud_secrets.get('postgres_password', '')
                print(f"--- DIAGNOSTIC PWD_LEN: {len(pwd)} | PWD_START: '{pwd[:3]}' ---")
                
        except Exception as e:
            print(f"WARNING: Found secret file but failed to parse JSON: {e}")

    if secrets_file_path.exists():
        return Settings(**cloud_secrets)

    if environment == "production":
        return ProductionSettings()
    elif environment == "testing":
        return TestingSettings()
    else:
        return DevelopmentSettings()


# Global settings instance
settings = get_settings()

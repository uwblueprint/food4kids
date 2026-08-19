from enum import StrEnum

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    """Which deployment this process is running as.

    Set by APP_ENV, and the only thing that says so. Pydantic rejects any
    other value, so a typo fails at startup rather than silently meaning
    development.
    """

    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """
    Application settings using Pydantic BaseSettings
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        populate_by_name=True,
    )

    # Environment
    environment: Environment = Field(default=Environment.DEVELOPMENT, alias="APP_ENV")

    # Database
    postgres_user: str = Field(default="")
    postgres_password: str = Field(default="")
    postgres_db_dev: str = Field(default="")
    postgres_db_test: str = Field(default="")
    db_host: str = Field(default="")
    database_url: str = Field(default="")

    # CORS
    # Empty by default: every deployed origin belongs to a specific
    # deployment and is configured there. Development adds its own localhost
    # entries in create_app(). An origin listed here is trusted with
    # credentialed requests, so the default has to be nothing.
    cors_origins: list[str] = Field(default=[])
    cors_supports_credentials: bool = Field(default=True)

    # Firebase
    firebase_project_id: str = Field(default="")
    # Used for the Identity Toolkit REST sign-in/refresh calls. Has to be a
    # Settings field, not an os.getenv read: on Cloud Run the config arrives
    # as a mounted secrets file, which os.getenv cannot see.
    firebase_web_api_key: str = Field(default="")
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

    # Billing — dedicated service account, kept separate from the storage and
    # Fleet Routing accounts because billing.viewer is granted on the *billing
    # account* and so spans every project on it.
    billing_service_account_private_key_id: str = Field(default="")
    billing_service_account_private_key: str = Field(default="")
    billing_service_account_client_email: str = Field(default="")
    billing_service_account_client_id: str = Field(default="")
    billing_service_account_auth_uri: str = Field(default="")
    billing_service_account_token_uri: str = Field(default="")
    billing_service_account_auth_provider_x509_cert_url: str = Field(default="")
    # Non-secret billing config. billing_account_id is the Cloud Billing account
    # ("012345-6789AB-CDEF01"); billing_target_project_id scopes spend to one
    # project. The export dataset must live in billing_target_project_id.
    billing_account_id: str = Field(default="")
    billing_target_project_id: str = Field(default="")
    billing_export_dataset: str = Field(default="")
    billing_export_table: str = Field(default="")
    # Cost data only refreshes every few hours, so a short TTL costs no accuracy
    # while protecting against a polling caller running up BigQuery scans.
    # Set to 0 to query live on every request.
    billing_cache_ttl_seconds: int = Field(default=300)
    # Hard ceiling per query. BigQuery kills the job rather than billing beyond
    # this, so a runaway caller fails loudly instead of quietly costing money.
    billing_max_bytes_billed: int = Field(default=1024**3)

    # Preview deploy
    preview_deploy: bool = Field(default=False)

    # Frontend URL
    frontend_base_url: str = Field(default="http://localhost:3000")

    @property
    def FRONTEND_BASE_URL(self) -> str:
        return self.frontend_base_url


# Global settings instance
settings = Settings()

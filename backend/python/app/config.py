import os
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings using Pydantic BaseSettings
    """
    
    # Environment
    environment: str = Field(default="development", env="APP_ENV")
    debug: bool = Field(default=True)
    testing: bool = Field(default=False)
    
    # Database
    postgres_user: str = Field(env="POSTGRES_USER")
    postgres_password: str = Field(env="POSTGRES_PASSWORD")
    postgres_db_dev: str = Field(env="POSTGRES_DB_DEV")
    postgres_db_test: str = Field(env="POSTGRES_DB_TEST")
    db_host: str = Field(env="DB_HOST")
    database_url: str = Field(default="", env="DATABASE_URL")
    
    
    # CORS
    cors_origins: List[str] = Field(default=[
        "http://localhost:3000",
        "https://uw-blueprint-starter-code.firebaseapp.com",
        "https://uw-blueprint-starter-code.web.app",
    ])
    cors_supports_credentials: bool = Field(default=True)
    
    # Firebase
    firebase_project_id: str = Field(env="FIREBASE_PROJECT_ID")
    firebase_svc_account_private_key_id: str = Field(env="FIREBASE_SVC_ACCOUNT_PRIVATE_KEY_ID")
    firebase_svc_account_private_key: str = Field(env="FIREBASE_SVC_ACCOUNT_PRIVATE_KEY")
    firebase_svc_account_client_email: str = Field(env="FIREBASE_SVC_ACCOUNT_CLIENT_EMAIL")
    firebase_svc_account_client_id: str = Field(env="FIREBASE_SVC_ACCOUNT_CLIENT_ID")
    firebase_svc_account_auth_uri: str = Field(env="FIREBASE_SVC_ACCOUNT_AUTH_URI")
    firebase_svc_account_token_uri: str = Field(env="FIREBASE_SVC_ACCOUNT_TOKEN_URI")
    firebase_svc_account_auth_provider_x509_cert_url: str = Field(env="FIREBASE_SVC_ACCOUNT_AUTH_PROVIDER_X509_CERT_URL")
    firebase_svc_account_client_x509_cert_url: str = Field(env="FIREBASE_SVC_ACCOUNT_CLIENT_X509_CERT_URL")
    
    # Email
    mailer_refresh_token: str = Field(default="", env="MAILER_REFRESH_TOKEN")
    mailer_client_id: str = Field(default="", env="MAILER_CLIENT_ID")
    mailer_client_secret: str = Field(default="", env="MAILER_CLIENT_SECRET")
    mailer_user: str = Field(default="", env="MAILER_USER")
    
    # Server
    port: int = Field(default=8080, env="PORT")
    host: str = Field(default="0.0.0.0")
    
    # Preview deploy
    preview_deploy: bool = Field(default=False, env="PREVIEW_DEPLOY")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
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


class ProductionSettings(Settings):
    """Production-specific settings"""
    debug: bool = False
    testing: bool = False


class TestingSettings(Settings):
    """Testing-specific settings"""
    debug: bool = False
    testing: bool = True
    mongodb_url: str = "mongomock://localhost"


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

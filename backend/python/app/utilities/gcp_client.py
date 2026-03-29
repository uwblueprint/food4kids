import logging
import uuid
from dataclasses import dataclass
from datetime import timedelta

from google.api_core import exceptions as gcp_exceptions
from google.cloud import storage  # type: ignore[import-untyped]
from google.oauth2 import service_account

from app.config import settings


class GCSStorageError(Exception):
    """Raised when a GCS operation fails; safe to expose detail strings to API clients."""


@dataclass
class UploadResult:
    filename: str
    url: str
    content_type: str
    size_bytes: int


class GCPStorageClient:
    """Google Cloud Storage client"""

    def __init__(self, logger: logging.Logger, bucket_name: str) -> None:
        self.logger = logger

        credentials = service_account.Credentials.from_service_account_info(
            {
                "type": "service_account",
                "project_id": settings.gcp_service_account_project_id,
                "private_key_id": settings.gcp_service_account_private_key_id,
                "private_key": settings.gcp_service_account_private_key.replace(
                    "\\n", "\n"
                ).strip(),
                "client_email": settings.gcp_service_account_client_email,
                "client_id": settings.gcp_service_account_client_id,
                "auth_uri": settings.gcp_service_account_auth_uri,
                "token_uri": settings.gcp_service_account_token_uri,
                "auth_provider_x509_cert_url": settings.gcp_service_account_auth_provider_x509_cert_url,
                "client_x509_cert_url": settings.gcp_service_account_client_x509_cert_url,
            }
        )
        self.client = storage.Client(credentials=credentials)
        self.bucket = self.client.bucket(bucket_name)

    def upload_file(
        self,
        contents: bytes,
        filename: str,
        content_type: str,
        expiration_hours: int = 1,
    ) -> UploadResult:
        """Upload a file to GCS and return a signed URL"""
        key = f"{uuid.uuid4()}-{filename}"
        blob = self.bucket.blob(key)
        try:
            blob.upload_from_string(contents, content_type=content_type)

            url = blob.generate_signed_url(
                expiration=timedelta(hours=expiration_hours),
                method="GET",
            )
        except gcp_exceptions.Forbidden as e:
            self.logger.exception("GCS upload forbidden (check IAM / bucket access)")
            raise GCSStorageError("Storage upload failed: permission denied.") from e
        except gcp_exceptions.NotFound as e:
            self.logger.exception("GCS bucket or object not found during upload")
            raise GCSStorageError(
                "Storage upload failed: bucket or resource not found."
            ) from e
        except Exception as e:
            self.logger.exception("Unexpected error during GCS upload")
            raise GCSStorageError(
                "Storage upload failed due to an unexpected error."
            ) from e

        return UploadResult(
            filename=key,
            url=url,
            content_type=content_type,
            size_bytes=len(contents),
        )

    def delete_file(self, filename: str) -> None:
        """Delete a file from GCS"""
        blob = self.bucket.blob(filename)

        try:
            if not blob.exists():
                self.logger.warning(f"File not found in GCS: {filename}")
                raise FileNotFoundError(f"{filename} not found")

            blob.delete()
        except FileNotFoundError:
            raise
        except gcp_exceptions.Forbidden as e:
            self.logger.exception("GCS delete forbidden (check IAM / bucket access)")
            raise GCSStorageError("Storage delete failed: permission denied.") from e
        except gcp_exceptions.NotFound as e:
            self.logger.exception("GCS bucket or object not found during delete")
            raise GCSStorageError(
                "Storage delete failed: bucket or resource not found."
            ) from e
        except Exception as e:
            self.logger.exception("Unexpected error during GCS delete")
            raise GCSStorageError(
                "Storage delete failed due to an unexpected error."
            ) from e

        self.logger.info(f"Deleted file from GCS: {filename}")

    def file_exists(self, filename: str) -> bool:
        """Check if a file exists in GCS"""
        return bool(self.bucket.blob(filename).exists())

import logging
import uuid
from dataclasses import dataclass
from datetime import timedelta

import google.auth
import google.auth.transport.requests
from google.api_core import exceptions as gcp_exceptions
from google.cloud import storage  # type: ignore[import-untyped]

SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]


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

        credentials, project = google.auth.default(scopes=SCOPES)
        signer_email = getattr(credentials, "service_account_email", None)
        if not signer_email:
            raise GCSStorageError(
                "Application Default Credentials did not resolve to a service "
                "account, so signed URLs cannot be issued. On Cloud Run, attach a "
                "runtime service account; locally, point "
                "GOOGLE_APPLICATION_CREDENTIALS at one."
            )

        self._credentials = credentials
        self._signer_email: str = signer_email
        self.client = storage.Client(credentials=credentials, project=project)
        self.bucket = self.client.bucket(bucket_name)

    def _sign_blob_kwargs(self) -> dict[str, str]:
        """Arguments that route URL signing through the IAM SignBlob API.

        Metadata-server credentials hold no private key, so they cannot sign a
        URL locally the way a downloaded key could. Handing generate_signed_url
        an access token and the signing identity makes it call
        iamcredentials.googleapis.com instead — which needs
        roles/iam.serviceAccountTokenCreator on the service account itself.

        Deliberately unconditional: a key-backed credential *could* sign
        locally, but then development would exercise a signing path production
        never takes, and the difference would only surface after deploy.
        """
        if not self._credentials.valid:
            self._credentials.refresh(google.auth.transport.requests.Request())
        token = self._credentials.token
        if not token:
            raise GCSStorageError(
                "Credentials refreshed without yielding an access token, so the "
                "upload URL cannot be signed."
            )
        return {
            "service_account_email": self._signer_email,
            "access_token": token,
        }

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
                **self._sign_blob_kwargs(),
            )
        except gcp_exceptions.Forbidden as e:
            raise GCSStorageError("Storage upload failed: permission denied.") from e
        except gcp_exceptions.NotFound as e:
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
                raise FileNotFoundError(f"{filename} not found")

            blob.delete()
        except FileNotFoundError:
            raise
        except gcp_exceptions.Forbidden as e:
            raise GCSStorageError("Storage delete failed: permission denied.") from e
        except gcp_exceptions.NotFound as e:
            raise GCSStorageError(
                "Storage delete failed: bucket or resource not found."
            ) from e
        except Exception as e:
            raise GCSStorageError(
                "Storage delete failed due to an unexpected error."
            ) from e

    def file_exists(self, filename: str) -> bool:
        """Check if a file exists in GCS"""
        return bool(self.bucket.blob(filename).exists())

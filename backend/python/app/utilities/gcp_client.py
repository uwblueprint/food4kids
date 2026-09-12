import logging
import uuid
from dataclasses import dataclass
from datetime import timedelta

import google.auth
import google.auth.transport.requests
from google.api_core import exceptions as gcp_exceptions

# google-cloud-bigquery ships py.typed, so mypy now resolves the google.cloud
# namespace and reports the untyped storage package as a missing attribute.
from google.cloud import storage  # type: ignore[attr-defined]

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
                "URL cannot be signed."
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
        key: str | None = None,
    ) -> UploadResult:
        """Upload a file to GCS and return a signed URL

        :param key: Object key to write, instead of the default
            ``<uuid>-<filename>``. User uploads must keep the default so two
            people uploading ``photo.jpg`` don't collide. A caller that owns
            its whole keyspace and wants writes to be repeatable — the seed
            script, which would otherwise orphan a fresh copy of every image
            on each run — passes one explicitly.
        """
        object_key = key if key is not None else f"{uuid.uuid4()}-{filename}"
        blob = self.bucket.blob(object_key)
        try:
            blob.upload_from_string(contents, content_type=content_type)

            url = self.generate_signed_url(
                object_key, expiration_hours=expiration_hours
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
            filename=object_key,
            url=url,
            content_type=content_type,
            size_bytes=len(contents),
        )

    def generate_signed_url(self, filename: str, expiration_hours: int = 24) -> str:
        """Mint a time-limited GET URL for an existing object.

        Upload stores these URLs on notes, but they expire (default upload
        expiry is 1h). Callers that *read* notes should re-sign from
        ``filename`` so thumbnails keep working after the stored URL dies.
        """
        try:
            return str(
                self.bucket.blob(filename).generate_signed_url(
                    expiration=timedelta(hours=expiration_hours),
                    method="GET",
                    **self._sign_blob_kwargs(),
                )
            )
        except gcp_exceptions.Forbidden as e:
            raise GCSStorageError(
                "Storage signed URL failed: permission denied."
            ) from e
        except Exception as e:
            self.logger.exception("Unexpected error generating signed URL.")
            raise GCSStorageError(
                "Storage signed URL failed due to an unexpected error."
            ) from e

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

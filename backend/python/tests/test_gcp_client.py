from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

import pytest

from app.utilities.gcp_client import SCOPES, GCPStorageClient, GCSStorageError

MODULE = "app.utilities.gcp_client"


@pytest.fixture()
def logger() -> logging.Logger:
    return logging.getLogger("test")


def _patch_adc(mocker: Any, credentials: Any, project: str | None = "f4k-test") -> Any:
    """Stub google.auth.default and storage.Client; return the storage mock."""
    mocker.patch(f"{MODULE}.google.auth.default", return_value=(credentials, project))
    return mocker.patch(f"{MODULE}.storage.Client")


def _service_account_credentials(mocker: Any, *, valid: bool = True) -> Any:
    return mocker.Mock(
        service_account_email="uploader@f4k-test.iam.gserviceaccount.com",
        valid=valid,
        token="ya29.test-token",
    )


class TestCredentialResolution:
    """Identity comes from ADC — no key material is read from settings."""

    def test_uses_adc_credentials_and_project(
        self, logger: logging.Logger, mocker: Any
    ) -> None:
        credentials = _service_account_credentials(mocker)
        default = mocker.patch(
            f"{MODULE}.google.auth.default", return_value=(credentials, "f4k-test")
        )
        storage_client = mocker.patch(f"{MODULE}.storage.Client")

        client = GCPStorageClient(logger, "f4k-bucket")

        default.assert_called_once_with(scopes=SCOPES)
        storage_client.assert_called_once_with(
            credentials=credentials, project="f4k-test"
        )
        storage_client.return_value.bucket.assert_called_once_with("f4k-bucket")
        assert client._signer_email == "uploader@f4k-test.iam.gserviceaccount.com"

    def test_non_service_account_identity_raises(
        self, logger: logging.Logger, mocker: Any
    ) -> None:
        """A user credential can't sign URLs — say so at construction, not at upload."""
        credentials = mocker.Mock(spec=["valid", "token", "refresh"])
        _patch_adc(mocker, credentials)

        with pytest.raises(GCSStorageError, match="did not resolve to a service"):
            GCPStorageClient(logger, "f4k-bucket")

    def test_empty_signer_email_raises(
        self, logger: logging.Logger, mocker: Any
    ) -> None:
        credentials = mocker.Mock(service_account_email="", valid=True, token="t")
        _patch_adc(mocker, credentials)

        with pytest.raises(GCSStorageError, match="did not resolve to a service"):
            GCPStorageClient(logger, "f4k-bucket")


class TestSignBlobKwargs:
    """Signing always goes through IAM SignBlob, in every environment."""

    def test_returns_signer_email_and_token(
        self, logger: logging.Logger, mocker: Any
    ) -> None:
        credentials = _service_account_credentials(mocker)
        _patch_adc(mocker, credentials)
        client = GCPStorageClient(logger, "f4k-bucket")

        assert client._sign_blob_kwargs() == {
            "service_account_email": "uploader@f4k-test.iam.gserviceaccount.com",
            "access_token": "ya29.test-token",
        }
        credentials.refresh.assert_not_called()

    def test_refreshes_when_expired(
        self, logger: logging.Logger, mocker: Any
    ) -> None:
        credentials = _service_account_credentials(mocker, valid=False)
        _patch_adc(mocker, credentials)
        client = GCPStorageClient(logger, "f4k-bucket")

        client._sign_blob_kwargs()

        credentials.refresh.assert_called_once()

    def test_missing_token_after_refresh_raises(
        self, logger: logging.Logger, mocker: Any
    ) -> None:
        credentials = _service_account_credentials(mocker, valid=False)
        credentials.token = None
        _patch_adc(mocker, credentials)
        client = GCPStorageClient(logger, "f4k-bucket")

        with pytest.raises(GCSStorageError, match="access token"):
            client._sign_blob_kwargs()


class TestUploadFile:
    def test_signs_url_via_iam(self, logger: logging.Logger, mocker: Any) -> None:
        credentials = _service_account_credentials(mocker)
        storage_client = _patch_adc(mocker, credentials)
        blob = storage_client.return_value.bucket.return_value.blob.return_value
        blob.generate_signed_url.return_value = "https://signed.test/object"

        client = GCPStorageClient(logger, "f4k-bucket")
        result = client.upload_file(b"payload", "photo.png", "image/png", 2)

        blob.upload_from_string.assert_called_once_with(
            b"payload", content_type="image/png"
        )
        blob.generate_signed_url.assert_called_once_with(
            expiration=timedelta(hours=2),
            method="GET",
            service_account_email="uploader@f4k-test.iam.gserviceaccount.com",
            access_token="ya29.test-token",
        )
        assert result.url == "https://signed.test/object"
        assert result.filename.endswith("-photo.png")
        assert result.size_bytes == len(b"payload")

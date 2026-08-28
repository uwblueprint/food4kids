"""Assemble Google service-account credentials from settings.

Each Google integration runs as its own service account — storage, Fleet
Routing, and billing — because their roles are granted on different resources
(a bucket, a project, the billing account). The credential *shape* is identical
across them even though the settings differ, so it is built here rather than
copied per client, where a newly required field would only get added to
whichever copy someone happened to be editing.

The `\\n` repair matters: private keys arrive from `.env` with escaped
newlines, and passing them through unrepaired fails inside the JWT signer with
an error that names framing rather than the key.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from google.oauth2 import service_account

if TYPE_CHECKING:
    from collections.abc import Sequence


def build_service_account_credentials(
    *,
    project_id: str,
    private_key_id: str,
    private_key: str,
    client_email: str,
    client_id: str,
    auth_uri: str,
    token_uri: str,
    auth_provider_x509_cert_url: str,
    client_x509_cert_url: str = "",
    scopes: Sequence[str] | None = None,
) -> service_account.Credentials:
    """Build credentials from already-read settings values.

    Values are passed in rather than read from a settings prefix so a typo is a
    type error instead of an empty string that fails later at the API call.
    """
    info = {
        "type": "service_account",
        "project_id": project_id,
        "private_key_id": private_key_id,
        "private_key": private_key.replace("\\n", "\n").strip(),
        "client_email": client_email,
        "client_id": client_id,
        "auth_uri": auth_uri,
        "token_uri": token_uri,
        "auth_provider_x509_cert_url": auth_provider_x509_cert_url,
    }
    if client_x509_cert_url:
        info["client_x509_cert_url"] = client_x509_cert_url

    # from_service_account_info is untyped in the stubs, so bind it to the
    # declared type here rather than returning Any.
    credentials: service_account.Credentials = (
        service_account.Credentials.from_service_account_info(info, scopes=scopes)
    )
    return credentials

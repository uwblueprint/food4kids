"""Phase 0 scratch script — throwaway. Delete before committing anything.

Run it with:
    docker compose exec backend python scratch_phase0.py

Goal: see with your own eyes that the Budget API does NOT return spend.
"""

import json
import os

from google.oauth2 import service_account
from googleapiclient.discovery import build

# What we're asking Google for permission to do. "cloud-platform" is the broad
# one; the service account's actual IAM roles still limit what it can touch.
SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]


def load_credentials() -> service_account.Credentials:
    """Turn the BILLING_* env vars back into a Google credentials object.

    A service account is a robot user. Google gave us a JSON key file for it;
    that file's contents were split into env vars so they can live in .env
    instead of on disk. Here we reassemble the same shape the library wants.
    """
    private_key = os.environ["BILLING_SERVICE_ACCOUNT_PRIVATE_KEY"]

    info = {
        "type": "service_account",
        "project_id": os.environ["BILLING_TARGET_PROJECT_ID"],
        "private_key_id": os.environ["BILLING_SERVICE_ACCOUNT_PRIVATE_KEY_ID"],
        # The \n repair: .env files can't hold real newlines, so the key arrives
        # with the two characters \ and n where line breaks should be. Without
        # this the error you get complains about key framing, not about newlines.
        "private_key": private_key.replace("\\n", "\n").strip(),
        "client_email": os.environ["BILLING_SERVICE_ACCOUNT_CLIENT_EMAIL"],
        "client_id": os.environ["BILLING_SERVICE_ACCOUNT_CLIENT_ID"],
        "auth_uri": os.environ["BILLING_SERVICE_ACCOUNT_AUTH_URI"],
        "token_uri": os.environ["BILLING_SERVICE_ACCOUNT_TOKEN_URI"],
        "auth_provider_x509_cert_url": os.environ.get(
            "BILLING_SERVICE_ACCOUNT_AUTH_PROVIDER_X509_CERT_URL", ""
        ),
    }
    return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)


def main() -> None:
    credentials = load_credentials()
    print(f"authenticating as: {credentials.service_account_email}\n")

    # build() constructs a client for any Google API by name+version. It works
    # by downloading a "discovery document" describing every method the API has,
    # then generating the methods on the fly. That's why the call chain below
    # (.billingAccounts().budgets().list) isn't something you can jump to in
    # your editor — it doesn't exist until runtime.
    budgets_api = build(
        "billingbudgets", "v1", credentials=credentials, cache_discovery=False
    )

    account_id = os.environ["BILLING_ACCOUNT_ID"]
    response = (
        budgets_api.billingAccounts()
        .budgets()
        .list(parent=f"billingAccounts/{account_id}")
        .execute()
    )

    print("=== RAW BUDGET API RESPONSE ===")
    print(json.dumps(response, indent=2))


if __name__ == "__main__":
    main()

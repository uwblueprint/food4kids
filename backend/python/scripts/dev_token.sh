#!/usr/bin/env bash
#
# Mint a Firebase ID token for local API testing.
#
# Logs in through the backend's public POST /auth/login and prints the
# access token (valid ~1 hour). Use it as a Bearer token for gated endpoints.
#
# Usage:
#   scripts/dev_token.sh <email> <password>
#   DEV_EMAIL=a@b.com DEV_PASSWORD=secret scripts/dev_token.sh
#
# Handy pattern:
#   export TOKEN=$(scripts/dev_token.sh a@b.com secret)
#   curl -H "Authorization: Bearer $TOKEN" http://localhost:8080/drivers/
#
# Override the API base with F4K_API_BASE (default http://localhost:8080).
#
# Requires: a real, email-verified Firebase account in the project. Seeded
# drivers are DB-only (synthetic auth_ids) and cannot log in; use the admin
# account (ADMIN_AUTH_ID) or a driver registered via POST /drivers/.

set -euo pipefail

email="${1:-${DEV_EMAIL:-}}"
password="${2:-${DEV_PASSWORD:-}}"
base="${F4K_API_BASE:-http://localhost:8080}"

if [[ -z "$email" || -z "$password" ]]; then
  echo "usage: $0 <email> <password>  (or set DEV_EMAIL / DEV_PASSWORD)" >&2
  exit 2
fi

# Build the JSON body with python so special characters in the password are
# escaped correctly.
body="$(python3 -c 'import json, sys; print(json.dumps({"email": sys.argv[1], "password": sys.argv[2]}))' "$email" "$password")"

resp="$(curl -fsS -X POST "$base/auth/login" \
  -H 'Content-Type: application/json' \
  -d "$body")"

python3 -c 'import json, sys; print(json.load(sys.stdin)["access_token"])' <<<"$resp"

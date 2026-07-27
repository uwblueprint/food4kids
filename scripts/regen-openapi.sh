#!/usr/bin/env bash
#
# Regenerate the frontend OpenAPI client from the backend schema.
#
# Runs the same two-stage pipeline as `pnpm generate:api`, but sources the
# schema by introspecting the FastAPI app directly (no running server, no DB):
#
#   1. backend/python/scripts/dump_openapi_schema.py  -> raw schema JSON
#   2. frontend/scripts/fetch-openapi.mjs (OPENAPI_FILE) -> frontend/openapi.json
#   3. openapi-ts                                     -> frontend/src/api/generated
#
# Stage 1 needs the Python env; stages 2-3 are pure local file transforms.
# Used by the pre-commit hook and runnable by hand:  ./scripts/regen-openapi.sh
set -euo pipefail

# Explicit escape hatch: skip the whole regen (e.g. mid-rebase, or when you know
# the contract is unchanged). CI verifies openapi.json, so this can't merge drift.
if [[ "${SKIP_OPENAPI_REGEN:-}" == "1" ]]; then
  echo "openapi: SKIP_OPENAPI_REGEN=1 set — skipping client regen." >&2
  exit 0
fi

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

RAW_SCHEMA="$(mktemp -t openapi-raw.XXXXXX.json)"
trap 'rm -f "$RAW_SCHEMA"' EXIT

DUMP_SCRIPT="scripts/dump_openapi_schema.py"
BACKEND_CONTAINER="${OPENAPI_BACKEND_CONTAINER:-f4k_backend}"

# --- stage 1: dump the schema from the app (no server, no DB) -----------------
# Stage 1 needs a Python env with the backend deps installed. Try, in order:
#   1. host venv  — for devs running the backend toolchain directly
#   2. running backend container — for Docker-only devs (no venv on the host)
#   3. system python3, but only if it can actually import the backend deps
# If none apply (e.g. a Docker dev whose container isn't up), warn and skip the
# regen entirely — CI verifies openapi.json as the backstop, so a skipped local
# regen can never let contract drift merge. Whichever tier IS selected is
# fail-fast: a dump error there is a real problem and aborts the commit.
#
# We run from backend/python so Settings' env_file=".env" resolves to the
# backend's own config, not an unrelated root .env (which carries keys Settings
# rejects). Inside the container WORKDIR is already /app (== backend/python).
if [[ -x "$REPO_ROOT/backend/python/venv/bin/python" ]]; then
  echo "→ Dumping OpenAPI schema via host venv…"
  ( cd "$REPO_ROOT/backend/python" \
    && APP_ENV=testing PYTHONPATH="$REPO_ROOT/backend/python" \
       "$REPO_ROOT/backend/python/venv/bin/python" "$DUMP_SCRIPT" "$RAW_SCHEMA" )

elif command -v docker >/dev/null 2>&1 \
     && docker ps --format '{{.Names}}' 2>/dev/null | grep -qx "$BACKEND_CONTAINER"; then
  echo "→ Dumping OpenAPI schema via running '$BACKEND_CONTAINER' container…"
  # The dump script writes to stdout when given no path; capture it on the host.
  docker exec -e APP_ENV=testing -e PYTHONPATH=/app "$BACKEND_CONTAINER" \
    python "$DUMP_SCRIPT" >"$RAW_SCHEMA"

elif command -v python3 >/dev/null 2>&1 && python3 -c 'import fastapi' >/dev/null 2>&1; then
  echo "⚠ No venv and no running '$BACKEND_CONTAINER' container — using system python3." >&2
  ( cd "$REPO_ROOT/backend/python" \
    && APP_ENV=testing PYTHONPATH="$REPO_ROOT/backend/python" \
       python3 "$DUMP_SCRIPT" "$RAW_SCHEMA" )

else
  echo "openapi: no backend Python env available — skipping client regen." >&2
  echo "  Looked for: host venv, a running '$BACKEND_CONTAINER' container, or a" >&2
  echo "  system python3 with the backend deps. CI will verify openapi.json." >&2
  echo "  To regen locally, start the backend (docker compose up backend) and" >&2
  echo "  re-commit, or run ./scripts/regen-openapi.sh once it's up." >&2
  exit 0
fi

# --- stages 2-3: normalize into openapi.json and generate the TS client -------
cd frontend
echo "→ Writing frontend/openapi.json…"
OPENAPI_FILE="$RAW_SCHEMA" node scripts/fetch-openapi.mjs

echo "→ Generating frontend/src/api/generated…"
pnpm exec openapi-ts

echo "✔ OpenAPI client regenerated."

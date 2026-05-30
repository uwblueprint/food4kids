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

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

# --- locate the backend Python interpreter (absolute path) -------------------
if [[ -x "$REPO_ROOT/backend/python/venv/bin/python" ]]; then
  PYTHON="$REPO_ROOT/backend/python/venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON="$(command -v python3)"
  echo "⚠ backend/python/venv not found — falling back to system python3." >&2
  echo "  The dump will fail unless the backend deps (FastAPI, Pydantic, …) are installed there." >&2
else
  echo "✘ No Python interpreter found (looked for backend/python/venv/bin/python and python3)." >&2
  exit 1
fi

RAW_SCHEMA="$(mktemp -t openapi-raw.XXXXXX.json)"
trap 'rm -f "$RAW_SCHEMA"' EXIT

# --- stage 1: dump the schema from the app (no server, no DB) -----------------
# Run from backend/python so Settings' env_file=".env" resolves to the backend's
# own config, not an unrelated root .env (which carries keys Settings rejects).
echo "→ Dumping OpenAPI schema from the backend app…"
( cd "$REPO_ROOT/backend/python" \
  && APP_ENV=testing PYTHONPATH="$REPO_ROOT/backend/python" \
     "$PYTHON" scripts/dump_openapi_schema.py "$RAW_SCHEMA" )

# --- stages 2-3: normalize into openapi.json and generate the TS client -------
cd frontend
echo "→ Writing frontend/openapi.json…"
OPENAPI_FILE="$RAW_SCHEMA" node scripts/fetch-openapi.mjs

echo "→ Generating frontend/src/api/generated…"
pnpm exec openapi-ts

echo "✔ OpenAPI client regenerated."

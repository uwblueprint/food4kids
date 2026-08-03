#!/usr/bin/env bash
#
# Sync the exported email HTML into the backend template directory.
#
# The React Email sources in frontend/emails/*.tsx are the single source of
# truth. `pnpm run email:export` renders them to frontend/emails/html/, and the
# backend renders those same files with Jinja2 from backend/python/app/templates/.
# Both copies are committed, so they have to be kept identical.
#
# Usage:
#   ./scripts/sync-email-templates.sh           # re-export, then copy into the backend
#   ./scripts/sync-email-templates.sh --check   # verify the two copies match (no writes)
#
# --check needs nothing but git and diff, so CI can run it on any change. The
# default mode runs the export and therefore needs the frontend deps installed.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXPORT_DIR="$REPO_ROOT/frontend/emails/html"
BACKEND_DIR="$REPO_ROOT/backend/python/app/templates"

# The templates the backend actually renders. Kept explicit rather than globbed
# so that a stray file in either directory is a visible error, not a silent sync.
TEMPLATES=(
  account-creation.html
  check-latest-announcement.html
  reset-password.html
  view-upcoming-route.html
)

mode="sync"
if [[ $# -gt 0 ]]; then
  case "$1" in
    --check) mode="check" ;;
    *)
      echo "error: unknown argument '$1' (expected --check or no arguments)" >&2
      exit 2
      ;;
  esac
fi

if [[ "$mode" == "check" ]]; then
  drifted=()
  for template in "${TEMPLATES[@]}"; do
    if [[ ! -f "$EXPORT_DIR/$template" ]]; then
      echo "error: missing export $EXPORT_DIR/$template" >&2
      exit 1
    fi
    if [[ ! -f "$BACKEND_DIR/$template" ]]; then
      echo "error: missing backend template $BACKEND_DIR/$template" >&2
      exit 1
    fi
    if ! diff -q "$EXPORT_DIR/$template" "$BACKEND_DIR/$template" >/dev/null; then
      drifted+=("$template")
    fi
  done

  if [[ ${#drifted[@]} -gt 0 ]]; then
    echo "error: email templates have drifted between the frontend export and the backend." >&2
    echo "       Out of sync: ${drifted[*]}" >&2
    echo "" >&2
    echo "       frontend/emails/html/ is the export output; backend/python/app/templates/" >&2
    echo "       is what actually gets rendered and sent. Run:" >&2
    echo "" >&2
    echo "         ./scripts/sync-email-templates.sh" >&2
    echo "" >&2
    echo "       and commit the result. Edit frontend/emails/*.tsx, never the HTML." >&2
    exit 1
  fi

  echo "email templates: frontend export and backend templates are in sync."
  exit 0
fi

echo "email templates: exporting from frontend/emails/*.tsx ..."
(cd "$REPO_ROOT/frontend" && pnpm run email:export >/dev/null)

for template in "${TEMPLATES[@]}"; do
  cp "$EXPORT_DIR/$template" "$BACKEND_DIR/$template"
done

echo "email templates: synced ${#TEMPLATES[@]} templates into backend/python/app/templates/."
echo "Review 'git diff' and commit both directories together."

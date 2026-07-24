#!/bin/bash
export GOOGLE_APPLICATION_CREDENTIALS="$(dirname "$0")/food4kids-env-service-account.json"

if gcloud secrets versions access latest \
# replace with food4kids-config-dev if pulling dev deployment secrets
  --secret="f4k-development-backend-env" \
  --project="food4kids-473501" > .env.tmp; then

  if jq -e . .env.tmp >/dev/null 2>&1; then
    jq -r 'to_entries[] | "\(.key)=\"\(.value | tostring | gsub("\\\\"; "\\\\") | gsub("\""; "\\\"") | gsub("\n"; "\\n"))\""' .env.tmp > .env.converted \
      && mv .env.converted .env.tmp
  fi

  mv .env.tmp .env
  echo "✅ .env pulled successfully"
else
  rm -f .env.tmp
  echo "❌ Failed to pull .env — existing file unchanged"
  exit 1
fi
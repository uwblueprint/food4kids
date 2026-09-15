#!/bin/bash
export GOOGLE_APPLICATION_CREDENTIALS="$(dirname "$0")/food4kids-env-service-account.json"

if [ ! -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
  echo "❌ $GOOGLE_APPLICATION_CREDENTIALS not found."
  echo "   Download it from the Food4Kids Developers shared Drive into the repo root."
  echo "   docker-compose mounts this same file as the backend's credentials, so a"
  echo "   missing file breaks route generation as well as this script."
  exit 1
fi

if gcloud secrets versions access latest \
  --secret="f4k-development-backend-env" \
  --project="food4kids-473501" > .env.tmp; then
  mv .env.tmp .env
  echo "✅ .env pulled successfully"
else
  rm -f .env.tmp
  echo "❌ Failed to pull .env — existing file unchanged"
  exit 1
fi
#!/bin/bash
export GOOGLE_APPLICATION_CREDENTIALS="$(dirname "$0")/food4kids-env-service-account.json"

if gcloud secrets versions access latest \
  --secret="f4k-backend-env" \
  --project="food4kids-473501" > .env.tmp; then
  mv .env.tmp .env
  echo "✅ .env pulled successfully"
else
  rm -f .env.tmp
  echo "❌ Failed to pull .env — existing file unchanged"
  exit 1
fi
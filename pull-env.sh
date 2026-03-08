#!/bin/bash
export GOOGLE_APPLICATION_CREDENTIALS="$(dirname "$0")/food4kids-env-service-account.json"

gcloud secrets versions access latest \
  --secret="f4k-backend-env" \
  --project="food4kids-473501" > .env

echo "✅ .env pulled successfully"
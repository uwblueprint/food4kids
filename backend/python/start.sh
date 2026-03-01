#!/bin/sh

echo "Waiting for database..."

while ! nc -z f4k_db 5432; do
  sleep 1
done

echo "Database is up"

alembic upgrade head
python -m app.seed_database
exec python server.py

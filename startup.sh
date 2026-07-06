#!/usr/bin/env sh
set -eu

PORT="${PORT:-8000}"

echo "Running enterprise database migrations..."
python -m alembic upgrade head

echo "Starting ARDO Enterprise API on port ${PORT}..."
exec python -m uvicorn api.main:app --host 0.0.0.0 --port "${PORT}"

#!/usr/bin/env bash
# Container entrypoint: wait for the database, run migrations, optionally seed,
# then exec the given command (defaults to the uvicorn server).
set -euo pipefail

echo "[entrypoint] Applying database migrations..."
alembic upgrade head

if [ "${SEED_ON_START:-false}" = "true" ]; then
  echo "[entrypoint] Seeding demo data..."
  python -m scripts.seed || echo "[entrypoint] Seed step failed (continuing)."
fi

echo "[entrypoint] Starting: $*"
exec "$@"

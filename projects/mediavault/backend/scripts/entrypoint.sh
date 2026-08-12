#!/usr/bin/env bash
# Container entrypoint: wait for the database, run migrations, optionally seed,
# then exec the given command (defaults to the uvicorn server).
set -euo pipefail

echo "[entrypoint] Applying database migrations..."
alembic upgrade head

if [ "${SEED_ON_START:-false}" = "true" ]; then
  echo "[entrypoint] Seeding demo data..."
  # Seed commits demo users first, then workspace content. A non-zero exit
  # still means users may be available — log and continue so the API starts.
  if ! python -m scripts.seed; then
    echo "[entrypoint] Seed step reported an error (continuing). Demo login may still work."
  fi
fi

echo "[entrypoint] Starting: $*"
exec "$@"

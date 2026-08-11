#!/usr/bin/env bash
# API container entrypoint: apply migrations, optionally seed, then serve.
set -euo pipefail

echo "[entrypoint] running database migrations…"
alembic upgrade head

if [ "${SEED_ON_START:-false}" = "true" ]; then
  echo "[entrypoint] seeding demo data…"
  python -m scripts.seed || echo "[entrypoint] seed skipped/failed (non-fatal)"
fi

echo "[entrypoint] starting API…"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers

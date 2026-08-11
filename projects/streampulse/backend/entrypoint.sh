#!/usr/bin/env bash
set -euo pipefail

# Wait for Postgres to accept connections before migrating.
echo "[entrypoint] waiting for database..."
python - <<'PY'
import time
import sys
from sqlalchemy import create_engine, text
from app.core.config import settings

engine = create_engine(settings.database_url)
for attempt in range(30):
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("[entrypoint] database is ready")
        sys.exit(0)
    except Exception as exc:  # noqa: BLE001
        print(f"[entrypoint] db not ready ({attempt+1}/30): {exc}")
        time.sleep(2)
print("[entrypoint] database never became ready")
sys.exit(1)
PY

echo "[entrypoint] running migrations..."
alembic upgrade head

# Seed on first boot (idempotent-ish: only seeds when there are no videos).
if [ "${RUN_SEED:-true}" = "true" ]; then
  python - <<'PY'
from sqlalchemy import func, select
from app.db.session import SessionLocal
from app.models.analytics import Video

with SessionLocal() as db:
    count = db.execute(select(func.count(Video.id))).scalar_one()

if count and count > 0:
    print(f"[entrypoint] {count} videos already present; skipping seed")
else:
    print("[entrypoint] empty database; seeding demo data...")
    from app.seed import main as seed_main
    seed_main()
PY
fi

echo "[entrypoint] starting: $*"
exec "$@"

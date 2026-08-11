#!/bin/sh
set -e

echo "Waiting for database..."
until python -c "
import sys
from sqlalchemy import create_engine, text
from app.core.config import get_settings
try:
    create_engine(get_settings().database_url).connect().close()
except Exception as exc:
    print(exc)
    sys.exit(1)
"; do
  sleep 1
done

echo "Seeding demo data (skips automatically if already seeded)..."
python -m app.seed

echo "Starting API server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000

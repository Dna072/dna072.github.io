# MediaVault Backend

FastAPI service for MediaVault (video asset management). See the
[project README](../README.md) for the full overview, architecture and AWS
deployment design.

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

export DATABASE_URL="postgresql+psycopg://mediavault:mediavault@localhost:5432/mediavault"
alembic upgrade head
python -m scripts.seed        # optional demo data
uvicorn app.main:app --reload
```

Docs: <http://localhost:8000/docs>

## Test & lint

```bash
pytest -q            # runs on an isolated SQLite database
ruff check app tests
```

## Layout

- `app/api` — routers + dependencies (`/api/v1`)
- `app/core` — config, security, logging, database, exceptions
- `app/models` — SQLAlchemy models
- `app/schemas` — Pydantic schemas
- `app/services` — business logic (auth, assets, search, storage, shares…)
- `app/repositories` — data-access layer
- `app/utils` — middleware, file/text helpers
- `alembic/` — migrations (incl. full-text search trigger + GIN index)
- `scripts/` — container entrypoint and seed script

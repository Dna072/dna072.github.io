# StreamPulse

Video analytics & performance dashboard built as a **production-style portfolio project** (not a commercial product with live customers).

## Demo

```bash
docker compose up --build
```

- UI: http://localhost:5173  
- API docs: http://localhost:8000/docs  
- Seeded demo user is created on startup when enabled (see env)

## Screenshots

Run locally and capture the dashboard after seed completes.

## Architecture

```
React dashboard  →  FastAPI metrics APIs  →  PostgreSQL (events + dimensions)
                              ↑
                        seed script (demo history)
```

Charts never hardcode series — every panel fetches aggregations from the API.

## Tech Stack

- Python 3.12, FastAPI, SQLAlchemy, Pydantic, pytest
- PostgreSQL
- React, TypeScript, Vite, Recharts
- Docker Compose

## Features

- JWT auth
- Overview KPIs with optional comparison period
- Time series, top videos, engagement funnel
- Geo + device breakdowns
- Date/video filters
- Loading / error / empty states
- `/health` and `/ready`

## API

OpenAPI at `/docs`. Primary routes under `/api/...` for auth, metrics, videos, audience, geo, device.

## Database

Event-centric schema optimized for range filters. Suggested indexes (implemented in models/migrations as available):

| Index | Why |
|-------|-----|
| `(occurred_at)` on events | Date-range scans for overview/timeseries |
| `(video_id, occurred_at)` | Video-scoped analytics |
| `(country_code)` / `(device_type)` | Breakdown queries |

## AI

Not applicable — analytics focus.

## Running Locally

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

Or run API with local Postgres and `uvicorn app.main:app --reload` from `backend/`.

## Environment Variables

See `backend/.env.example`. Never commit real secrets.

## Testing

```bash
cd backend && pip install -r requirements.txt && pytest
cd frontend && npm test   # if configured
```

## Docker

`docker compose up --build` starts postgres, api, frontend.

## Deployment

Documented AWS shape: RDS PostgreSQL, ECS/Fargate API, CloudFront + S3 for UI. No expensive infra is provisioned by this repo.

## Engineering Decisions

- Push aggregations into SQL
- Explicit loading/error/empty UI states
- Seeded data labeled as demo/seed

## Future Improvements

- Materialized rollups for longer history
- Async export jobs
- Row-level security per organization

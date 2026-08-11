# StreamPulse

Video analytics and performance dashboard. Every chart on the frontend is
rendered from data returned by the FastAPI backend — there are no hardcoded
or mocked series in the UI. The backend seeds a realistic, multi-month
event history into PostgreSQL and exposes SQL aggregations (overview KPIs,
time series, per-video performance, engagement funnel, and audience / geo /
device breakdowns) that the React dashboard consumes directly.

<p>
  <img alt="stack" src="https://img.shields.io/badge/backend-FastAPI-009688">
  <img alt="stack" src="https://img.shields.io/badge/db-PostgreSQL-336791">
  <img alt="stack" src="https://img.shields.io/badge/frontend-React%20%2B%20TypeScript-61dafb">
  <img alt="stack" src="https://img.shields.io/badge/charts-Recharts-8884d8">
</p>

## Table of contents

- [Architecture](#architecture)
- [Project structure](#project-structure)
- [Quick start (Docker)](#quick-start-docker)
- [Local development (without Docker)](#local-development-without-docker)
- [Backend](#backend)
  - [Data model](#data-model)
  - [Database indexes](#database-indexes)
  - [API reference](#api-reference)
  - [Seed data](#seed-data)
  - [Testing](#testing)
- [Frontend](#frontend)
- [Environment variables](#environment-variables)
- [Design notes / trade-offs](#design-notes--trade-offs)

## Architecture

```
Seeded events (views, funnel milestones, geo, device, referrer)
  → PostgreSQL (view_events, engagement_events, videos, users)
  → FastAPI aggregation layer (app/core/metrics.py — GROUP BY / date_trunc / CASE in SQL)
  → REST API (auth, overview, timeseries, videos, audience, geo, device, health/ready)
  → React + TypeScript dashboard (Recharts) with date-range / video filters and
    optional comparison period
```

The guiding principle: **push aggregation to SQL, keep the API layer thin,
and never fabricate a metric in the frontend.** Every panel on the
dashboard renders from a typed API response and has explicit loading,
error, and empty states.

## Project structure

```
streampulse/
├── backend/
│   ├── app/
│   │   ├── core/            # config, db session, security, deps, metrics (SQL), reference data
│   │   ├── routers/         # auth, overview, timeseries, videos, audience, geo, device
│   │   ├── models.py        # SQLAlchemy models + indexes
│   │   ├── schemas.py       # Pydantic request/response schemas
│   │   ├── seed.py          # realistic demo data generator
│   │   └── main.py          # FastAPI app, /health, /ready
│   ├── tests/                # pytest suite (auth + every aggregation endpoint)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/client.ts     # typed fetch client (JWT auth, query building)
│   │   ├── components/       # KPI cards, charts, filters, table, state views
│   │   ├── pages/            # Login, Dashboard
│   │   ├── context/          # AuthContext
│   │   └── hooks/useAsyncData.ts
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

## Quick start (Docker)

Requires Docker and Docker Compose.

```bash
cd projects/streampulse
cp .env.example .env   # optional — sane defaults work out of the box
docker compose up --build
```

This starts three services:

| Service    | URL                              | Notes                                             |
| ---------- | --------------------------------- | -------------------------------------------------- |
| `db`       | internal only (`5432`)            | PostgreSQL 16                                      |
| `backend`  | http://localhost:8000              | FastAPI; seeds demo data automatically on first boot |
| `frontend` | http://localhost:8080              | Static build served by nginx, proxies `/api` to backend |

Open http://localhost:8080 and sign in with the demo account:

```
email:    demo@streampulse.io
password: streampulse123
```

Interactive API docs are available at http://localhost:8000/docs.

## Local development (without Docker)

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Point at a local PostgreSQL instance (create the db/user first, see below)
cp .env.example .env   # edit DATABASE_URL / JWT_SECRET_KEY as needed

python -m app.seed --reset      # creates tables + realistic demo data
uvicorn app.main:app --reload   # http://localhost:8000
```

Create the local database/role once, e.g.:

```sql
CREATE USER streampulse WITH PASSWORD 'streampulse' CREATEDB;
CREATE DATABASE streampulse OWNER streampulse;
```

### Frontend

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173, proxies /api to http://localhost:8000
```

## Backend

### Data model

| Table               | Purpose                                                                                     |
| -------------------- | --------------------------------------------------------------------------------------------- |
| `users`              | Dashboard operators (email + bcrypt password hash).                                          |
| `videos`             | Video catalogue (title, category, duration, publish date, thumbnail).                         |
| `view_events`        | One row per playback session — the primary fact table for views, watch time, device, geo, referrer. |
| `engagement_events`  | One row per funnel/engagement milestone (`play`, `reach_25/50/75`, `complete`, `like`, `comment`, `share`) tied to a session. |

Two fact tables (rather than one wide table) keep the funnel query simple —
counting milestone rows by `event_type` — while the view-level table stays
narrow and fast to aggregate for KPIs, time series, and device/geo/referrer
breakdowns.

### Database indexes

Defined in `app/models.py`, created automatically by `Base.metadata.create_all`
(see `app/seed.py`). Rationale:

| Index                                   | Table               | Why                                                                                          |
| ---------------------------------------- | -------------------- | ----------------------------------------------------------------------------------------------- |
| `ix_view_events_video_occurred`          | `view_events`        | Composite `(video_id, occurred_at)` — every endpoint filters by an optional video **and** a date range (video detail, per-video time series). |
| `ix_view_events_occurred`                 | `view_events`        | Pure date-range scans for account-wide overview/time-series queries with no video filter.       |
| `ix_view_events_device`                   | `view_events`        | Supports `GROUP BY device_type` for the device-breakdown endpoint.                              |
| `ix_view_events_country`                  | `view_events`        | Supports `GROUP BY country_code` for the geo-breakdown endpoint.                                |
| `ix_engagement_events_video_occurred`     | `engagement_events`  | Same composite rationale as above, for the funnel endpoint scoped to a single video.            |
| `ix_engagement_events_type_occurred`      | `engagement_events`  | Supports `GROUP BY event_type` for funnel-stage counts and like/comment/share KPIs.              |
| `ix_videos_published_at`                  | `videos`              | Video catalogue sorted by recency; also used to bound "already published" checks during seeding. |
| `ix_videos_category`                      | `videos`              | Category filter/grouping if the catalogue grows.                                                |
| `ix_users_email` (unique)                 | `users`               | Login lookups by email.                                                                          |

All heavy-lifting (`COUNT`, `SUM`, `AVG`, `GROUP BY`, `date()`) happens in
PostgreSQL via SQLAlchemy Core expressions in `app/core/metrics.py` — the API
layer only shapes already-aggregated rows into response schemas.

### API reference

All endpoints except `/health`, `/ready`, `/api/auth/register`, and
`/api/auth/login` require `Authorization: Bearer <token>`.

| Method | Path                        | Description                                                                 |
| ------ | ---------------------------- | ----------------------------------------------------------------------------- |
| GET    | `/health`                    | Liveness probe (no dependencies checked).                                    |
| GET    | `/ready`                      | Readiness probe — verifies the database connection (`503` if unreachable).  |
| POST   | `/api/auth/register`          | Create an account, returns a JWT.                                            |
| POST   | `/api/auth/login`              | Exchange email/password for a JWT.                                           |
| GET    | `/api/auth/me`                | Current authenticated user.                                                  |
| GET    | `/api/metrics/overview`        | Headline KPIs for a date range (+ optional comparison period, + optional video filter). |
| GET    | `/api/metrics/timeseries`      | Daily time series (views, unique viewers, watch time, avg watched %, completion rate); missing days are zero-filled. |
| GET    | `/api/videos`                  | Full video catalogue (powers the video filter dropdown).                    |
| GET    | `/api/videos/performance`      | Ranked video performance table — sortable, paginated, filterable by date range and video. |
| GET    | `/api/videos/{id}`             | Single video detail + KPIs for a date range.                                 |
| GET    | `/api/audience/funnel`          | Engagement funnel stage counts (`play → 25% → 50% → 75% → complete`).       |
| GET    | `/api/audience`                | Device + referrer breakdown together (used for the traffic-sources panel). |
| GET    | `/api/geo`                     | Views/watch-time by country.                                                  |
| GET    | `/api/device`                  | Views/watch-time by device type (dedicated endpoint, also used by `/api/audience`). |

Common query params on the metrics/audience/geo/device/video-performance
endpoints: `start`, `end` (dates, default to the last 30 days),
`video_id` (optional scope), `compare` (bool — also returns the immediately
preceding period of equal length).

### Seed data

`app/seed.py` generates a believable content lifecycle rather than pure
randomness:

- each video gets a random "popularity" weight (log-normal distribution),
- views spike shortly after a video's publish date and decay to a
  long-tail baseline,
- weekday traffic runs heavier than weekend traffic,
- watch percentage follows a beta distribution, so most sessions drop off
  early and a smaller share watch to completion,
- like/comment/share probability scales with watch percentage,
- device, country, and referrer are drawn from realistic weighted
  distributions.

```bash
python -m app.seed            # seeds only if the videos table is empty
python -m app.seed --reset    # drops and recreates all tables, then seeds
```

Tune volume via `SEED_VIDEOS` / `SEED_DAYS` (see `.env.example`). Defaults
produce ~35–100k view events and ~150–300k engagement events, which loads
in a few seconds locally.

### Testing

```bash
cd backend
createdb streampulse_test    # once, matching TEST_DATABASE_URL
pytest
```

Tests run against a real PostgreSQL database (so Postgres-specific SQL —
`date()`, enum columns — is exercised exactly as in production), with each
test wrapped in a rolled-back transaction for isolation. A dedicated
`seeded_videos` fixture inserts a small, fully deterministic set of
view/engagement events so aggregation results can be asserted exactly
(exact counts, percentages, and shares) rather than just "greater than
zero". Coverage includes: auth (register/login/duplicate/bad password/
protected routes), overview KPIs (aggregation, video filter, comparison
period, inverted-range validation, empty range), time series (gap-filling,
video filter), video performance (sorting, pagination, video filter, 404),
and audience/geo/device breakdowns (funnel percentages, device/referrer
shares, geo filtering).

## Frontend

React + TypeScript + Vite, charts via Recharts, no UI component library —
all styling is hand-written CSS using the navy/charcoal + cyan design
system in `src/theme.css`.

- **KPI cards** — total views, unique viewers, watch time, avg watched %,
  completion rate, engagement rate, each with a delta badge when the
  comparison period is enabled.
- **Time-series chart** — views (area) + watch time (line) over the
  selected range, with an optional dashed "previous period" overlay
  aligned by day offset.
- **Engagement funnel** — `play → 25% → 50% → 75% → complete`, rendered
  with Recharts' `Funnel` component plus exact counts/percentages.
- **Device breakdown** — donut chart of desktop/mobile/tablet/tv.
- **Top countries** — horizontal bar chart of the top 8 countries by views.
- **Traffic sources** — referrer share as horizontal progress bars.
- **Top videos table** — sortable (click any column), backed by
  `/api/videos/performance`.
- **Filters** — date-range presets (7D/30D/90D) or a custom range, a video
  selector (all videos or one specific video, applied consistently across
  every panel), and a "compare to previous period" toggle.
- **Loading / error / empty states** — every panel (`src/components/Panel.tsx`)
  renders one of four states: skeleton/spinner while loading, an inline
  error with a retry button on failure, an explicit empty-state message
  when the range/video combination has no data, or the populated chart.
  Nothing is ever mocked client-side to paper over an empty response.

Run `npm run typecheck` and `npm run build` to verify; there is no
separate frontend test runner configured beyond typechecking + the
production build, since the primary testing investment went into the
aggregation layer that the charts depend on.

## Environment variables

See `.env.example` at the repo root (for `docker-compose`), and
`backend/.env.example` / `frontend/.env.example` for standalone
(non-Docker) development.

| Variable                     | Where           | Default                                         | Purpose                                  |
| ----------------------------- | ---------------- | -------------------------------------------------- | ------------------------------------------ |
| `DATABASE_URL`                 | backend           | `postgresql+psycopg2://streampulse:streampulse@localhost:5432/streampulse` | SQLAlchemy connection string             |
| `JWT_SECRET_KEY`               | backend           | _(dev placeholder)_                              | HMAC signing key for auth tokens — **set a real secret in any shared environment** |
| `ACCESS_TOKEN_EXPIRE_MINUTES`  | backend           | `1440`                                            | JWT lifetime                              |
| `CORS_ORIGINS`                 | backend           | `http://localhost:5173,http://localhost:3000`     | Comma-separated allowed origins           |
| `SEED_VIDEOS` / `SEED_DAYS`    | backend           | `36` / `90`                                       | Demo data volume                          |
| `VITE_API_URL`                 | frontend          | _(empty → same-origin, proxied)_                  | Point the SPA at a different API origin   |
| `POSTGRES_*` / `*_PORT`        | docker-compose    | see `.env.example`                                | Container credentials/ports               |

## Design notes / trade-offs

- **Two fact tables instead of one.** `view_events` (session grain) and
  `engagement_events` (milestone grain) keep both the KPI/time-series
  queries and the funnel query simple, at the cost of an extra join when a
  panel needs both (e.g. likes/comments/shares alongside views).
- **Day-level time series, not pre-aggregated rollups.** With indexes on
  `(video_id, occurred_at)` and `occurred_at`, `GROUP BY date(occurred_at)`
  over a 30–120 day window stays fast without a separate nightly rollup
  job — appropriate for this data volume, but a `daily_video_metrics`
  materialized rollup would be the next step at much larger scale.
- **Comparison periods computed on demand**, not stored. The "previous
  period" is just the same query with a shifted date range, reusing every
  aggregation helper — no duplicated query logic, at the cost of one extra
  round-trip when comparison is enabled.
- **Frontend never fabricates a series.** Every chart's props come
  directly from a typed API response; empty results render an explicit
  empty state rather than a chart with a flat/fake line.

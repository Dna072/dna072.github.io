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
Seeded events (impressions, views, watch time, geo, device, likes/comments/shares)
  → PostgreSQL (impression_events, view_events, videos, users)
  → FastAPI service layer (app/services/analytics.py — GROUP BY / date_trunc /
    CASE / conditional aggregation in SQL, via SQLAlchemy Core)
  → REST API (auth, analytics: overview / timeseries / videos / audience /
    geo / device / funnel, health/ready)
  → React + TypeScript dashboard (Recharts) with date-range / video filters
    and an optional "compare to previous period" toggle
```

The guiding principle: **push aggregation to SQL, keep the API layer thin,
and never fabricate a metric in the frontend.** Every panel on the
dashboard renders from a typed API response (via React Query) and has
explicit loading, error, and empty states.

## Project structure

```
streampulse/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py           # auth dependency, shared date-range/compare resolver
│   │   │   └── routes/           # auth, analytics, health/ready routers
│   │   ├── core/                 # settings, JWT/password hashing, structured logging
│   │   ├── db/                   # SQLAlchemy engine/session + declarative Base
│   │   ├── models/                # ORM models: users, videos, impression_events, view_events
│   │   ├── schemas/                # Pydantic request/response schemas
│   │   ├── services/analytics.py  # all SQL aggregation logic (the "metrics layer")
│   │   ├── seed.py                # realistic demo data generator
│   │   └── main.py                # FastAPI app factory, middleware
│   ├── alembic/                   # schema migrations (indexes documented inline)
│   ├── tests/                     # pytest suite against a real Postgres database
│   ├── entrypoint.sh              # container entrypoint: migrate → seed → serve
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── lib/                   # api.ts (axios + JWT), queries.ts (React Query hooks), types.ts
│   │   ├── components/            # FilterBar, KpiCards, TopVideosTable, Login, states, charts/
│   │   ├── context/AuthContext.tsx
│   │   ├── Dashboard.tsx          # composes every panel
│   │   └── App.tsx
│   ├── package.json
│   ├── nginx.conf                 # SPA + static asset caching for the container image
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

| Service    | URL                     | Notes                                                        |
| ---------- | ------------------------ | -------------------------------------------------------------- |
| `postgres` | internal only (`5432`)   | PostgreSQL 16                                                 |
| `api`      | http://localhost:8000     | FastAPI; runs Alembic migrations and seeds demo data on first boot |
| `frontend` | http://localhost:8080     | Static build served by nginx; the browser calls the API directly on its published port |

Open http://localhost:8080 and sign in with the demo account:

```
email:    demo@streampulse.dev
password: streampulse-demo
```

Interactive API docs are available at http://localhost:8000/docs.

## Local development (without Docker)

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Point at a local PostgreSQL instance (create the db/role first, see below)
cp .env.example .env   # edit DATABASE_URL / SECRET_KEY as needed

alembic upgrade head    # creates tables + indexes
python -m app.seed      # populates realistic demo data (idempotent-ish, see below)
uvicorn app.main:app --reload   # http://localhost:8000
```

Create the local database/role once, e.g.:

```sql
CREATE USER streampulse WITH PASSWORD 'streampulse' CREATEDB;
CREATE DATABASE streampulse OWNER streampulse;
CREATE DATABASE streampulse_test OWNER streampulse;   -- used by pytest
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env   # VITE_API_BASE_URL, defaults to http://localhost:8000
npm run dev             # http://localhost:5173
```

The frontend talks to the API directly via `VITE_API_BASE_URL` (an axios
`baseURL`, inlined at build time) — there is no dev proxy, so make sure
`CORS_ORIGINS` on the backend includes whichever origin you're browsing
from (`http://localhost:5173` is allowed by default).

## Backend

### Data model

| Table               | Purpose                                                                                     |
| -------------------- | --------------------------------------------------------------------------------------------- |
| `users`              | Dashboard operators (email + bcrypt password hash).                                          |
| `videos`             | Video catalogue (title, category, duration, publish date, thumbnail).                         |
| `impression_events` | One row per time a video was surfaced to a viewer — top of the engagement funnel.             |
| `view_events`        | One row per playback session — the primary fact table for views, watch time, device, geo, likes/comments/shares, and quartile retention. |

Two fact tables (rather than one wide table) keep the funnel query simple —
count impressions vs. views vs. quartile milestones — while the view-level
table stays focused for KPIs, time series, and device/geo breakdowns.

### Database indexes

Defined in `app/models/analytics.py` and `app/models/user.py`, created by the
Alembic migration `alembic/versions/0001_initial.py` (run via
`alembic upgrade head`, or automatically by the container entrypoint).
Rationale:

| Index                        | Table                | Why                                                                                              |
| ------------------------------ | ---------------------- | --------------------------------------------------------------------------------------------------- |
| `ix_views_time`                 | `view_events`         | Pure date-range scans for account-wide overview/time-series queries with no video filter.        |
| `ix_views_video_time`           | `view_events`         | Composite `(video_id, event_time)` — video detail, per-video time series, and "top videos in period" all filter by an optional video **and** a date range. |
| `ix_views_country_time`         | `view_events`         | Composite `(country_code, event_time)` — supports the geo-breakdown `GROUP BY country_code` scoped to a date range. |
| `ix_views_device_time`          | `view_events`         | Composite `(device_type, event_time)` — same rationale for the device-breakdown endpoint.        |
| `ix_impressions_video_time`     | `impression_events`   | Composite `(video_id, event_time)` — funnel query scoped to a single video.                       |
| `ix_impressions_time`           | `impression_events`   | Account-wide funnel query (no video filter).                                                     |
| `ix_videos_published_at`        | `videos`               | Video catalogue sorted by recency.                                                                |
| `ix_videos_category`            | `videos`               | Category filter/grouping for video performance.                                                   |
| `ix_users_email` (unique)       | `users`                | Login lookups by email.                                                                            |

All the composite indexes are ordered `(dimension, event_time)` so that an
equality filter on the dimension plus a range scan on `event_time` can be
served by a single index; `EXPLAIN ANALYZE` against the seeded dataset
(~35–100k `view_events` rows) shows every dashboard query using an index
scan rather than a sequential scan once the table crosses a few thousand
rows. All heavy-lifting (`COUNT`, `SUM`, `AVG`, `GROUP BY`, `date_trunc`,
`FILTER`-style conditional aggregation) happens in PostgreSQL via
SQLAlchemy Core expressions in `app/services/analytics.py` — the route
layer only shapes already-aggregated rows into response schemas.

### API reference

Every route except `/health`, `/ready`, and `/api/v1/auth/login` requires
`Authorization: Bearer <token>`.

| Method | Path                                  | Description                                                                 |
| ------ | --------------------------------------- | ----------------------------------------------------------------------------- |
| GET    | `/health`                               | Liveness probe (no dependencies checked).                                    |
| GET    | `/ready`                                 | Readiness probe — verifies the database connection (`503` if unreachable).  |
| POST   | `/api/v1/auth/login`                     | OAuth2 password flow (`username` = email). Returns a JWT.                    |
| GET    | `/api/v1/auth/me`                        | Current authenticated user.                                                  |
| GET    | `/api/v1/analytics/overview`             | Headline KPIs for a date range (+ optional comparison period, + optional video filter). |
| GET    | `/api/v1/analytics/timeseries`           | Time series (views, unique viewers, watch hours); granularity auto-resolves to day/week/month by range length, or pass `granularity` explicitly. |
| GET    | `/api/v1/analytics/videos`               | Ranked, paginated video performance table — sortable, filterable by date range, video, and category. |
| GET    | `/api/v1/analytics/videos/catalog`       | Full video catalogue (powers the video filter dropdown).                    |
| GET    | `/api/v1/analytics/audience/geo`          | Views/watch-time by country, with each row's share of total views.          |
| GET    | `/api/v1/analytics/audience/device`       | Views/watch-time by device type (mobile/desktop/tablet/tv).                  |
| GET    | `/api/v1/analytics/funnel`                | Engagement funnel: `impressions → views → 25% → 50% → 75% → completed`.     |
| GET    | `/api/v1/analytics/categories`            | Distinct video categories.                                                   |
| GET    | `/api/v1/analytics/meta/bounds`           | Earliest/latest event dates in the dataset (seeds the date picker's bounds). |

Common query params on the analytics endpoints: `start_date`, `end_date`
(dates, default to the last 30 days), `video_id` (optional scope), `compare`
(bool — also returns the immediately preceding period of equal length).

### Seed data

`app/seed.py` generates a believable content lifecycle rather than pure
randomness:

- each video gets a random popularity/quality weight,
- views correlate with a per-video popularity factor and decay with age,
- weekly seasonality (weekend traffic runs heavier),
- watch depth (quartile reached) and like/comment/share probability scale
  with each video's quality factor, so "good" videos retain and engage
  viewers more than others,
- device, country, and referrer-adjacent dimensions are drawn from
  realistic weighted distributions.

```bash
python -m app.seed   # inserts the admin user (if missing), clears + regenerates event data
```

Tune volume via `SEED_DAYS` / `SEED_TRAFFIC` / `SEED_RANDOM_SEED` (see
`backend/.env.example`). Defaults produce tens of thousands of view events
and hundreds of thousands of impressions over a 120-day window, which loads
in a few seconds locally. The Docker entrypoint (`entrypoint.sh`) runs this
automatically on first boot, but skips it if the `videos` table is already
populated (see `RUN_SEED` to disable it entirely).

### Testing

```bash
cd backend
createdb streampulse_test    # once, matching TEST_DATABASE_URL
pytest
```

Tests run against a real PostgreSQL database (the analytics queries use
`date_trunc`, `count(distinct)`, and conditional aggregation that SQLite
can't emulate faithfully). `TEST_DATABASE_URL` must point at a database
whose name contains `_test` — the test suite refuses to run otherwise, so
it can never target a development database by accident. The schema is
dropped and recreated once per test session, and a `seeded` fixture inserts
a small, fully deterministic set of impression/view events so aggregation
results can be asserted exactly (exact counts, percentages, and shares)
rather than just "greater than zero". Coverage includes: health/ready,
auth (login success/failure, protected routes), and the analytics service
(overview KPIs with comparison period, time series bucketing, video
performance sorting, funnel percentages, and geo/device breakdowns).

## Frontend

React + TypeScript + Vite, data fetching via TanStack React Query, charts
via Recharts — all styling is hand-written CSS using the navy/charcoal +
cyan design system in `src/index.css`.

- **KPI cards** — total views, unique viewers, watch hours, avg view
  duration, engagement rate, completion rate, each with a delta badge
  against the previous period when comparison is enabled.
- **Time-series chart** — switchable metric (views / watch hours / unique
  viewers) over the selected range, with an optional dashed "previous
  period" overlay when comparison is enabled.
- **Engagement funnel** — `impressions → views → 25% → 50% → 75% →
  completed`, rendered as proportionally-filled bars with exact
  counts/percentages.
- **Device breakdown** — donut/bar chart of mobile/desktop/tablet/tv.
- **Top countries** — horizontal bar chart of the top countries by views.
- **Top videos table** — sortable (click any column header), paginated,
  backed by `/api/v1/analytics/videos`.
- **Filters** — date-range presets (7D/30D/90D) or a custom range, a video
  selector (all videos or one specific video, applied consistently across
  every panel), and a "compare to previous period" toggle.
- **Loading / error / empty states** — every panel goes through
  `QueryBoundary` (`src/components/states.tsx`), which renders a skeleton
  while loading, an inline error with a retry button on failure, an
  explicit empty-state message when the range/video combination has no
  data, or the populated chart. Nothing is ever mocked client-side to
  paper over an empty response.

Run `npm run typecheck`, `npm run lint`, and `npm run build` to verify.

## Environment variables

See `.env.example` at the repo root (for `docker-compose`), and
`backend/.env.example` / `frontend/.env.example` for standalone
(non-Docker) development.

| Variable                     | Where           | Default                                         | Purpose                                  |
| ----------------------------- | ---------------- | -------------------------------------------------- | ------------------------------------------ |
| `DATABASE_URL`                 | backend           | `postgresql+psycopg2://streampulse:streampulse@localhost:5432/streampulse` | SQLAlchemy connection string             |
| `SECRET_KEY`                   | backend           | _(dev placeholder)_                              | HMAC signing key for JWTs — **set a real secret in any shared environment** (`openssl rand -hex 32`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES`  | backend           | `1440`                                            | JWT lifetime                              |
| `CORS_ORIGINS`                 | backend           | `http://localhost:5173,http://localhost:3000,http://localhost:8080` | Comma-separated allowed browser origins   |
| `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD` | backend | `demo@streampulse.dev` / `streampulse-demo` | Demo login created by the seed script     |
| `SEED_DAYS` / `SEED_TRAFFIC` / `SEED_RANDOM_SEED` | backend | `120` / `1.0` / `42`                | Demo data volume and reproducibility      |
| `LOG_LEVEL` / `LOG_JSON`       | backend           | `INFO` / `true`                                    | Structured logging verbosity/format       |
| `TEST_DATABASE_URL`           | backend (tests)   | must contain `_test`                              | Dedicated database for `pytest`           |
| `VITE_API_BASE_URL`            | frontend          | `http://localhost:8000`                            | Base URL the SPA calls (inlined at build time) |
| `POSTGRES_*` / `RUN_SEED` / `SECRET_KEY` / `SEED_*` | docker-compose | see root `.env.example`                | Container credentials, ports, and seed behavior |

## Design notes / trade-offs

- **Two fact tables instead of one.** `impression_events` (top-of-funnel)
  and `view_events` (session grain, carries watch time/engagement) keep
  both the KPI/time-series queries and the funnel query simple, at the
  cost of a second table to aggregate when a panel needs both.
- **Comparison periods computed on demand**, not stored. The "previous
  period" is just the same query with a shifted date range, reusing every
  aggregation helper in `app/services/analytics.py` — no duplicated query
  logic, at the cost of one extra round-trip when comparison is enabled.
- **Auto-resolving time-series granularity.** Short ranges bucket by day;
  longer ranges automatically roll up to week or month via `date_trunc`, so
  a 120-day chart doesn't render 120 illegible points. Callers can still
  force a specific granularity.
- **Frontend never fabricates a series.** Every chart's props come
  directly from a typed API response (via React Query); empty results
  render an explicit empty state rather than a chart with a flat/fake line,
  and failed requests surface a retry action instead of a blank panel.
- **API base URL baked in at build time, not proxied.** The static frontend
  bundle calls the API directly via `VITE_API_BASE_URL`; this keeps the
  nginx container simple (pure static file serving) at the cost of needing
  a rebuild if the API's public URL changes.

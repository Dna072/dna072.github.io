# StreamPulse — Video Analytics & Performance Dashboard

A production-style analytics product for video content: a **FastAPI** backend that
serves aggregated metrics straight from PostgreSQL, and a polished **React +
TypeScript** dashboard that renders them. Every chart is fed by a real API call —
**nothing is hardcoded in the UI**.

> **Honesty note:** this is a portfolio project. All data is **synthetic**, produced
> by a seed script (`app/seed.py`). There are no real users, no real traffic, and no
> uptime/revenue claims anywhere.

Built by **Derrick Adjei** as part of a media-technology portfolio (targeting
Backlight — Junior Fullstack, backend focus).

---

## Table of contents

- [What it does](#what-it-does)
- [Architecture](#architecture)
- [Tech stack](#tech-stack)
- [Quick start (Docker Compose)](#quick-start-docker-compose)
- [Local development](#local-development)
- [API reference](#api-reference)
- [Data model](#data-model)
- [Database & indexing — the *why*](#database--indexing--the-why)
- [Query design](#query-design)
- [Comparison mode](#comparison-mode)
- [Seed data](#seed-data)
- [Testing & CI](#testing--ci)
- [Observability](#observability)
- [AWS deployment notes](#aws-deployment-notes)
- [Project structure](#project-structure)

---

## What it does

- **KPI overview** — total views, unique viewers, watch hours, average view duration,
  engagement rate, completion rate — each with an optional period-over-period delta.
- **Time series** — views / watch-hours / unique-viewers over time with automatic
  day/week/month bucketing and an overlaid *previous period* line in comparison mode.
- **Engagement funnel** — impressions → views → 25% → 50% → 75% → completion, with
  per-step conversion.
- **Audience breakdowns** — top countries and device-type split.
- **Video performance** — paginated, sortable per-video table.
- **Filters** — date range (quick presets + custom), single-video filter, comparison
  toggle. All filters flow to every endpoint.
- **UX states** — every panel has loading (skeleton), error (with retry), and empty
  states.

---

## Architecture

```mermaid
flowchart LR
    subgraph Browser
      UI["React + TS SPA<br/>(Vite, Recharts, React Query)"]
    end
    subgraph Edge
      NX["nginx<br/>(serves built SPA)"]
    end
    subgraph API["FastAPI service"]
      MW["Request-ID + structured logging<br/>middleware"]
      AUTH["JWT auth<br/>(OAuth2 password flow)"]
      AN["Analytics routers<br/>(aggregation queries)"]
    end
    DB[("PostgreSQL 16<br/>videos · impression_events · view_events")]

    UI -->|"/api/v1/* (Bearer JWT)"| API
    NX --- UI
    MW --> AUTH --> AN
    AN -->|"date_trunc, count(distinct),<br/>conditional aggregation"| DB
```

Request flow: the SPA authenticates via `/api/v1/auth/login`, stores the JWT, and
attaches it to every request. The API validates the token, resolves the shared
date-range/comparison filter, runs a bounded aggregation query, and returns a small
reduced payload. PostgreSQL does the heavy lifting; the API ships only summarized data.

---

## Tech stack

| Layer | Choices |
|-------|---------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, structlog |
| Auth | JWT (python-jose), bcrypt password hashing (passlib) |
| Database | PostgreSQL 16 |
| Frontend | React 18, TypeScript, Vite, Recharts, TanStack Query, Axios |
| Tests | pytest (backend, against real Postgres); ESLint + `tsc` (frontend) |
| Infra | Docker, docker-compose, nginx, GitHub Actions CI |

---

## Quick start (Docker Compose)

Requires Docker + Docker Compose.

```bash
cd projects/streampulse
cp .env.example .env          # optional; sensible defaults are baked in
docker compose up --build
```

On first boot the API container waits for Postgres, runs Alembic migrations, and
seeds ~120 days of synthetic data. Then:

- **Dashboard:** http://localhost:8080
- **API docs (Swagger):** http://localhost:8000/docs
- **Health / readiness:** http://localhost:8000/health · http://localhost:8000/ready

**Demo login** (created by the seed script):

```
email:    demo@streampulse.dev
password: streampulse-demo
```

Tune seed volume via `.env` (`SEED_DAYS`, `SEED_TRAFFIC`) before the first `up`, or set
`RUN_SEED=false` to skip seeding.

---

## Local development

### Backend

```bash
cd projects/streampulse/backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Point at a Postgres you control:
export DATABASE_URL="postgresql+psycopg2://streampulse:streampulse@localhost:5432/streampulse"

alembic upgrade head            # create schema
python -m app.seed              # load synthetic data
uvicorn app.main:app --reload   # http://localhost:8000
```

### Frontend

```bash
cd projects/streampulse/frontend
npm install
echo "VITE_API_BASE_URL=http://localhost:8000" > .env
npm run dev                     # http://localhost:5173
```

---

## API reference

All analytics endpoints require a `Bearer` token and share these query params:
`start_date`, `end_date` (UTC dates; end is exclusive), `compare` (bool), and an
optional `video_id`.

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/auth/login` | OAuth2 password login → JWT (`username` = email) |
| `GET`  | `/api/v1/auth/me` | Current user |
| `GET`  | `/api/v1/analytics/overview` | Headline KPIs (+ deltas in comparison mode) |
| `GET`  | `/api/v1/analytics/timeseries` | Views/watch-hours/unique over time (`granularity=auto\|day\|week\|month`) |
| `GET`  | `/api/v1/analytics/videos` | Per-video performance (`limit`, `offset`, `sort_by`, `category`) |
| `GET`  | `/api/v1/analytics/audience/geo` | Views by country |
| `GET`  | `/api/v1/analytics/audience/device` | Views by device type |
| `GET`  | `/api/v1/analytics/funnel` | Impressions → views → retention → completion |
| `GET`  | `/api/v1/analytics/videos/catalog` | All videos (for the filter dropdown) |
| `GET`  | `/api/v1/analytics/categories` | Distinct categories |
| `GET`  | `/api/v1/analytics/meta/bounds` | Earliest/latest data dates |
| `GET`  | `/health` · `/ready` | Liveness / readiness probes |

Full, interactive schema at `/docs`.

---

## Data model

Two append-only **fact** tables around a `videos` **dimension** table:

- **`videos`** — one row per piece of content (title, category, duration, publish date).
- **`impression_events`** — a video was surfaced to a viewer (top of the funnel).
- **`view_events`** — a viewer started watching. Carries `watch_seconds`,
  `quartile_reached` (0–4 → highest 25% milestone reached), engagement flags
  (`liked`/`commented`/`shared`), a pseudonymous `viewer_id` (for unique-viewer counts),
  and `country_code` / `device_type` dimensions.

Splitting impressions from views keeps the common "views" queries scanning a smaller
table, while still supporting a true impressions-based funnel.

---

## Database & indexing — the *why*

Every dashboard query is an **aggregation over a time window**, optionally narrowed by
video, and often grouped by a dimension (country/device). The indexes are chosen to
serve exactly those access patterns.

| Index | Columns | Serves | Why |
|-------|---------|--------|-----|
| `ix_views_time` | `(event_time)` | Every time-bounded query | The date range is present in *all* dashboard queries, so a leading `event_time` index bounds every scan. |
| `ix_views_video_time` | `(video_id, event_time)` | Single-video views; "top videos" | Composite with `video_id` first lets a video filter + date range resolve via one index range scan. |
| `ix_views_country_time` | `(country_code, event_time)` | Geo breakdown; country filters | Supports slicing a country over a time window without scanning the whole table. |
| `ix_views_device_time` | `(device_type, event_time)` | Device breakdown | Same rationale for the device dimension. |
| `ix_impressions_video_time` | `(video_id, event_time)` | Funnel (per video) | Impression counts by video + range for the top of the funnel. |
| `ix_impressions_time` | `(event_time)` | Funnel (all videos) | Time-bounded impression totals. |
| `ix_videos_category` / `ix_videos_published_at` | — | Category filter / recency sort | Small dimension table lookups. |

### Proof: the planner uses them

Time-series over a 30-day window (82k-view seed) — bounded by `ix_views_time`:

```
GroupAggregate
  ->  Sort  (Sort Key: date_trunc('day', event_time))
        ->  Index Scan using ix_views_time on view_events
              Index Cond: ((event_time >= now() - '30 days') AND (event_time < now()))
```

Per-video + date range — resolved by the composite `ix_views_video_time`:

```
Aggregate
  ->  Bitmap Heap Scan on view_events
        ->  Bitmap Index Scan on ix_views_video_time
              Index Cond: ((video_id = 5) AND (event_time >= …) AND (event_time < …))
```

### Scaling further (documented, not built)

For very large, append-only event tables the next steps would be **native range
partitioning by month** on `event_time` (partition pruning + cheap retention drops)
and a **BRIN index** on `event_time` (tiny, ideal for time-ordered inserts). Heavy
dashboards would then read from **pre-aggregated daily rollup tables** refreshed by a
scheduled job, rather than scanning raw events on every request.

---

## Query design

- **`date_trunc(granularity, event_time)`** for time bucketing, with granularity chosen
  automatically from the window length (≤31d → day, ≤120d → week, else month).
- **`count(DISTINCT viewer_id)`** for unique viewers.
- **Conditional aggregation** (`avg`/`sum` over `CASE` expressions) computes engagement
  rate, completion rate, and all funnel quartiles in a **single table scan** each,
  instead of multiple round-trips.
- Every query is **bounded by `event_time`** so the indexes above apply.

---

## Comparison mode

When `compare=true`, the API computes the **immediately preceding, equal-length window**
(`[start - span, start)`). Overview KPIs return `{ value, previous, delta_pct }`; the
time series returns a parallel `previous_points` array aligned by index so the UI can
overlay it as a dashed line.

---

## Seed data

`app/seed.py` generates months of plausible-but-synthetic events:

- 24 videos across 6 categories with per-video **popularity** and **quality** traits.
- **Recency decay** (interest fades after publish) and **weekly seasonality** (weekends
  run hotter), plus a mild upward trend.
- **Impression → view** click-through, then per-view **retention** sampled from a
  quality-shifted distribution (TV/desktop watch slightly longer than mobile).
- A bounded **viewer pool** with a "power viewer" subset, so unique viewers are
  meaningfully fewer than total views.

Reproducible via `SEED_RANDOM_SEED`. Volume via `SEED_DAYS` / `SEED_TRAFFIC`.

---

## Testing & CI

```bash
cd projects/streampulse/backend
export TEST_DATABASE_URL="postgresql+psycopg2://streampulse:streampulse@localhost:5432/streampulse_test"
pytest        # 18 tests: auth, health/request-id, and every analytics endpoint
ruff check .
```

Tests run against a **real Postgres** (the queries use Postgres-only features) and are
hard-guarded to a `*_test` database so they can never touch a dev DB. GitHub Actions
(`.github/workflows/streampulse-ci.yml`) runs backend lint + migrate + pytest (with a
Postgres service), frontend lint + typecheck + build, and builds both Docker images.

---

## Observability

- **structlog** JSON logs (toggle `LOG_JSON=false` for pretty local output).
- A **request-ID** middleware assigns/propagates `X-Request-ID` and binds it to every
  log line for correlation; it also logs method, path, status, and duration.
- **`/health`** (process liveness) and **`/ready`** (verifies DB connectivity, returns
  503 when degraded) for container/orchestrator probes.

---

## AWS deployment notes

A pragmatic path to production (architecture only — no live infra is provisioned):

```mermaid
flowchart LR
    U[Users] --> CF[CloudFront]
    CF --> S3[(S3 static SPA)]
    CF --> ALB[Application Load Balancer]
    ALB --> ECS["ECS Fargate<br/>FastAPI tasks (autoscaled)"]
    ECS --> RDS[(RDS PostgreSQL<br/>Multi-AZ)]
    ECS --> CW[CloudWatch Logs/Alarms]
```

- **Frontend:** build the SPA and host on **S3** behind **CloudFront** (CDN + TLS).
- **API:** container image on **ECS Fargate** behind an **ALB**, using the `/health` and
  `/ready` probes for target-group health and autoscaling.
- **Database:** **RDS for PostgreSQL** (Multi-AZ for availability); credentials in
  **Secrets Manager**, injected as env vars; `SECRET_KEY` likewise.
- **Migrations:** run `alembic upgrade head` as a one-off ECS task in the deploy
  pipeline before shifting traffic.
- **Logs/metrics:** ship structured logs to **CloudWatch** (request IDs make tracing a
  single request across log lines trivial); alarm on 5xx rate and DB connections.
- **Scale:** as event volume grows, add read replicas, monthly partitioning, and daily
  rollup tables (see [scaling notes](#scaling-further-documented-not-built)).

---

## Project structure

```
projects/streampulse/
├── backend/
│   ├── app/
│   │   ├── api/            # deps + route modules (auth, analytics, health)
│   │   ├── core/           # config, structured logging, security (JWT/bcrypt)
│   │   ├── db/             # engine/session, declarative base
│   │   ├── models/         # SQLAlchemy models (+ index definitions)
│   │   ├── schemas/        # Pydantic request/response models
│   │   ├── services/       # analytics query layer (the SQL lives here)
│   │   ├── seed.py         # synthetic data generator
│   │   └── main.py         # app factory, middleware, router wiring
│   ├── alembic/            # migrations
│   ├── tests/              # pytest suite (real Postgres)
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/     # FilterBar, KPI cards, charts, states, table
│   │   ├── context/        # auth context
│   │   ├── lib/            # api client, react-query hooks, types, formatters
│   │   └── Dashboard.tsx
│   ├── nginx.conf
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

# MediaVault — Video Asset Management for Creative Teams

MediaVault is a media library / digital-asset-management (DAM) platform aimed at
video-first creative teams. It focuses on the backend and data engineering that
production media tooling actually requires: multi-tenant workspaces, role-based
access control, a folder hierarchy, tagging, PostgreSQL full-text search, and
tamper-proof **signed URLs** for secure asset delivery — fronted by a polished
React + TypeScript single-page app.

> **Portfolio note.** This is a production-style portfolio project built by
> Derrick Adjei. It ships with realistic seed data but **no real customers,
> revenue, or uptime claims**. Benchmarks (if any) are test results only.

---

## Table of contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech stack](#tech-stack)
- [Quick start (Docker)](#quick-start-docker)
- [Local development](#local-development)
- [Configuration](#configuration)
- [API overview](#api-overview)
- [Data model](#data-model)
- [Authentication & RBAC](#authentication--rbac)
- [Signed URLs & storage](#signed-urls--storage)
- [Search](#search)
- [Testing](#testing)
- [Project layout](#project-layout)
- [Deployment (AWS)](#deployment-aws)
- [Roadmap](#roadmap)
- [License](#license)

---

## Features

**Backend (FastAPI, versioned `/api/v1`)**

- JWT authentication with **access + refresh token rotation** and server-side
  revocation (logout, reuse detection).
- **RBAC** with three workspace-scoped roles — `ADMIN`, `MEMBER`, `VIEWER` —
  enforced centrally.
- Multi-tenant **workspaces** with membership management.
- **Folder hierarchy** (materialized paths) with move/rename that re-paths
  descendants, breadcrumbs, and subtree queries.
- **Tags** and asset tagging with AND-filtering.
- **PostgreSQL full-text search** (weighted `tsvector`, GIN index, trigger) with
  a graceful `ILIKE` fallback on SQLite for tests.
- **Pagination, filtering and sorting** on all list endpoints.
- **Signed URL** generation for asset access (HMAC, expiring) — with a native S3
  presigned-URL path when the S3 backend is enabled.
- Pluggable **storage abstraction** (local disk or S3/MinIO).
- **Upload validation**: content-type allow-list, size limits, and magic-number
  sniffing to catch spoofed content types; SHA-256 checksums.
- Public, revocable, **download-limited share links**.
- Health (`/health`) and readiness (`/ready`) probes.
- **Structured JSON logging** with per-request IDs (`X-Request-ID`).
- Clean layering: `api / core / models / schemas / services / repositories / utils`.

**Frontend (React + TypeScript + Vite)**

- Polished DAM UI (slate + teal, light/soft-dark themes) — not a Bootstrap CRUD.
- Sidebar navigation, workspace switcher, and folder tree.
- Asset **grid and table** views with sorting.
- Full-text **search + type/tag filters**.
- **Upload modal** with drag-and-drop and multi-file support.
- Asset **detail drawer** with preview, tagging, share links and delete.
- **People & permissions** management and tag administration.
- Complete auth flow and first-class loading / error / empty states.

---

## Architecture

```mermaid
flowchart LR
    subgraph Client
      UI[React + TS SPA]
    end
    subgraph Edge
      NG[Nginx / CloudFront]
    end
    subgraph API[FastAPI]
      R[Routers /api/v1]
      S[Services]
      Repo[Repositories]
    end
    DB[(PostgreSQL)]
    RS[(Redis)]
    ST[(Object storage<br/>local disk / S3)]

    UI -->|HTTPS| NG --> R
    R --> S --> Repo --> DB
    S -->|signed URL| ST
    S -. rate limit / cache .-> RS
    UI -->|signed URL GET| ST
```

The request lifecycle and layering are documented in
[`docs/architecture.md`](docs/architecture.md). The cloud deployment model
(S3, RDS, ElastiCache, CloudFront signed URLs) is in [`docs/aws.md`](docs/aws.md).

---

## Tech stack

| Layer      | Technology |
|------------|------------|
| API        | Python 3.12, FastAPI, Pydantic v2 |
| ORM / DB   | SQLAlchemy 2.0, Alembic, PostgreSQL 16 |
| Auth       | PyJWT, passlib/bcrypt |
| Storage    | Local filesystem or S3-compatible (boto3) |
| Cache/RL   | Redis (optional) |
| Frontend   | React 18, TypeScript, Vite, TanStack Query, React Router |
| Tests      | pytest, Vitest, Testing Library |
| Tooling    | Ruff, ESLint, Docker Compose, GitHub Actions |

---

## Quick start (Docker)

```bash
cd projects/mediavault
cp .env.example .env
docker compose up --build
```

Then open:

- Frontend → <http://localhost:5173>
- API docs (Swagger) → <http://localhost:8000/docs>
- Health → <http://localhost:8000/api/v1/health>

The API container runs migrations on start and (with `SEED_ON_START=true`) seeds
a demo workspace. Log in with any seeded account (or click **Use demo** on the
login page):

| Role   | Email                     | Password       |
|--------|---------------------------|----------------|
| Admin  | `admin@mediavault.dev`    | `ChangeMe123!` |
| Member | `editor@mediavault.dev`   | `ChangeMe123!` |
| Viewer | `viewer@mediavault.dev`   | `ChangeMe123!` |

If demo login fails after an earlier broken boot, recreate the API container so
seed runs again (`docker compose up --build`), or exec
`python -m scripts.seed` inside the `api` service. Seed commits demo users
before workspace content, so login works even when content seeding errors.

---

## Local development

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

# Point at a local Postgres, or use SQLite for a zero-dependency run:
export DATABASE_URL="postgresql+psycopg://mediavault:mediavault@localhost:5432/mediavault"
alembic upgrade head
python -m scripts.seed              # optional demo data
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173, proxies /api to :8000
```

---

## Configuration

All configuration is environment-driven (see [`.env.example`](.env.example)).
Key variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | `postgresql+psycopg://…` | SQLAlchemy database URL |
| `SECRET_KEY` | dev value | JWT signing key |
| `SIGNED_URL_SECRET` | dev value | HMAC key for signed asset URLs |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access-token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `14` | Refresh-token lifetime |
| `STORAGE_BACKEND` | `local` | `local` or `s3` |
| `STORAGE_LOCAL_DIR` | `/data/storage` | Local storage root |
| `S3_BUCKET` / `S3_*` | — | S3 / MinIO settings |
| `MAX_UPLOAD_SIZE_MB` | `512` | Upload size cap |
| `REDIS_URL` | `redis://…` | Optional rate limiting / cache |

**Generate strong secrets for anything but local dev:**
`python -c "import secrets; print(secrets.token_urlsafe(48))"`.

---

## API overview

All endpoints are versioned under `/api/v1`. Full interactive docs are served at
`/docs` (Swagger) and `/redoc`.

| Group | Endpoints |
|-------|-----------|
| Auth | `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout`, `GET /auth/me` |
| Users | `GET /users/me`, `PATCH /users/me` |
| Workspaces | `GET/POST /workspaces`, `GET/PATCH/DELETE /workspaces/{id}`, member CRUD under `/workspaces/{id}/members` |
| Folders | `GET/POST /workspaces/{id}/folders`, `PATCH/DELETE /…/folders/{fid}`, `GET /…/folders/{fid}/breadcrumbs` |
| Tags | `GET/POST /workspaces/{id}/tags`, `PATCH/DELETE /…/tags/{tid}` |
| Assets | `GET/POST /workspaces/{id}/assets`, `GET/PATCH/DELETE /…/assets/{aid}`, `PUT /…/assets/{aid}/tags`, `GET /…/assets/{aid}/signed-url` |
| Shares | `GET/POST /…/assets/{aid}/shares`, `DELETE /…/shares/{sid}` |
| Search | `GET /workspaces/{id}/search?q=…` |
| Public | `GET /assets/{aid}/download` (signed), `GET /shares/{token}`, `GET /shares/{token}/download` |
| Ops | `GET /health`, `GET /ready` |

Example — list assets with filters, sorting and pagination:

```bash
curl "http://localhost:8000/api/v1/workspaces/$WS/assets?kind=VIDEO&sort_by=created_at&sort_dir=desc&page=1&page_size=20" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

---

## Data model

```mermaid
erDiagram
    USERS ||--o{ MEMBERSHIPS : has
    WORKSPACES ||--o{ MEMBERSHIPS : has
    WORKSPACES ||--o{ FOLDERS : contains
    WORKSPACES ||--o{ TAGS : contains
    WORKSPACES ||--o{ ASSETS : contains
    FOLDERS ||--o{ FOLDERS : nests
    FOLDERS ||--o{ ASSETS : holds
    ASSETS ||--o{ ASSET_TAGS : labeled
    TAGS ||--o{ ASSET_TAGS : labels
    ASSETS ||--o{ SHARES : shared_by
    USERS ||--o{ REFRESH_TOKENS : owns
```

Indexes cover the hot paths: workspace-scoped listing (`workspace_id, created_at`
/ `folder_id` / `kind`), unique constraints on slugs/emails/tokens, a GIN index
on the assets `search_vector`, and a `pg_trgm` index for name prefix search.

---

## Authentication & RBAC

- Passwords are hashed with bcrypt.
- Login issues a short-lived **access** token and a longer-lived **refresh**
  token; the refresh token's hash is persisted so it can be revoked.
- `POST /auth/refresh` **rotates** the refresh token and invalidates the old one
  (presenting a used token is rejected — basic reuse detection).
- Every workspace request resolves a `WorkspaceContext` binding the user to their
  role. Handlers call `ctx.require(Role.MEMBER)` / `require_admin()`:

| Capability | VIEWER | MEMBER | ADMIN |
|------------|:------:|:------:|:-----:|
| Browse / search / download | ✅ | ✅ | ✅ |
| Upload / edit / tag / delete assets | ❌ | ✅ | ✅ |
| Create folders & tags | ❌ | ✅ | ✅ |
| Manage members & roles | ❌ | ❌ | ✅ |

---

## Signed URLs & storage

Assets are never served from a public bucket path. A download URL is minted on
request and carries an HMAC signature over `asset_id` + expiry:

```
/api/v1/assets/{id}/download?expires=<ts>&signature=<hmac>
```

The download endpoint verifies the signature and expiry before streaming bytes —
the same model as S3 / CloudFront signed URLs. When `STORAGE_BACKEND=s3`, the
service instead returns a native S3 presigned URL so bytes are served directly
from object storage. The `StorageBackend` abstraction (`app/services/storage.py`)
keeps call sites identical across local disk and S3/MinIO.

---

## Search

On PostgreSQL, asset name/description/filename are indexed into a weighted
`tsvector` (`A`/`B`/`C`) maintained by a trigger, queried with
`websearch_to_tsquery` and ranked with `ts_rank`, accelerated by a GIN index.
On SQLite (used in tests) the repository transparently falls back to `ILIKE`
matching, so the same code path is exercised end-to-end without Postgres.

---

## Testing

```bash
# Backend (35 tests: auth, RBAC, assets, search, pagination, folders, health)
cd backend && pytest -q

# Frontend (Vitest smoke tests)
cd frontend && npm run test
```

CI (GitHub Actions, [`.github/workflows/ci.yml`](.github/workflows/ci.yml)) runs
Ruff + pytest (with a Postgres service to validate migrations), the frontend
lint/test/build, and Docker image builds.

---

## Project layout

```
projects/mediavault/
├── backend/
│   ├── app/
│   │   ├── api/            # FastAPI routers + dependencies (v1)
│   │   ├── core/           # config, security, logging, db, exceptions
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # business logic (auth, assets, search, storage…)
│   │   ├── repositories/   # data-access layer
│   │   └── utils/          # middleware, file & text helpers
│   ├── alembic/            # migrations (incl. FTS trigger + GIN index)
│   ├── scripts/            # entrypoint + seed
│   └── tests/              # pytest suite
├── frontend/               # React + TS + Vite SPA
├── docs/                   # architecture + AWS design
├── docker-compose.yml
└── .env.example
```

---

## Deployment (AWS)

See [`docs/aws.md`](docs/aws.md) for the full target architecture: ECS Fargate
for the API, RDS PostgreSQL, ElastiCache Redis, S3 for assets, and CloudFront
with signed URLs/cookies in front of both the SPA and asset delivery. No live
cloud infrastructure is provisioned for this portfolio project.

---

## Roadmap

- Background transcoding / thumbnail generation workers.
- Asset versioning and comments/approvals.
- Redis-backed rate limiting middleware (wired but conservative by default).
- Bulk operations and saved smart collections.

---

## License

MIT — see [`LICENSE`](LICENSE).

# MediaVault — Architecture

This document describes how a request flows through MediaVault and why the code
is layered the way it is.

## Layering

```
HTTP → Router (app/api) → Service (app/services) → Repository (app/repositories) → SQLAlchemy → DB
                              │
                              └── Storage backend (local disk / S3) for bytes
```

- **Routers (`app/api/v1/routers`)** — thin. They parse/validate input via
  Pydantic, resolve dependencies (current user, workspace context, pagination),
  enforce coarse RBAC (`ctx.require(...)`), call a service, commit, and serialize
  the response. No business logic or ORM queries live here.
- **Services (`app/services`)** — the business logic. Transactions are owned by
  the router (`db.commit()`), but services orchestrate repositories, storage and
  domain rules (e.g. upload validation, folder re-pathing, refresh rotation).
- **Repositories (`app/repositories`)** — all ORM queries. This is the only layer
  that builds `select()` statements, so query concerns (filtering, sorting,
  pagination, full-text vs. `ILIKE`) are centralized and testable.
- **Models (`app/models`)** — SQLAlchemy 2.0 declarative models with a portable
  `GUID` type (native UUID on Postgres, `CHAR(36)` elsewhere) and a portable
  `TSVector` type.
- **Schemas (`app/schemas`)** — Pydantic request/response contracts, decoupled
  from ORM models.
- **Core (`app/core`)** — configuration, security primitives, logging, database
  engine/session, and the domain exception hierarchy.

## Request lifecycle

1. `RequestContextMiddleware` assigns an `X-Request-ID` (or echoes the caller's),
   binds it to a `ContextVar`, and emits a structured access log with latency.
2. `get_current_user` validates the `Bearer` access token (type + signature +
   expiry) and loads the user.
3. For workspace-scoped routes, `get_workspace_context` loads the caller's
   membership and role, producing a `WorkspaceContext`.
4. The handler enforces the minimum role, invokes a service, and commits.
5. `AppError` subclasses map to consistent JSON error envelopes
   (`{ "error": { code, message, request_id } }`).

## Authentication & tokens

- Access tokens are short-lived JWTs (`type=access`); refresh tokens are
  longer-lived JWTs (`type=refresh`) whose SHA-256 hash is persisted in
  `refresh_tokens` so they can be revoked.
- Refresh **rotates**: the presented token is marked revoked and a new pair is
  issued. Re-presenting a revoked/rotated token fails — simple reuse detection.
- The SPA stores tokens in `localStorage` and transparently refreshes on a single
  `401` before retrying the original request.

## Folder hierarchy

Folders store a **materialized path** (e.g. `/Campaigns/2026`). This makes
breadcrumbs and "include subfolders" queries a cheap prefix match, and moves
re-path descendants in one pass. Uniqueness is enforced per `(workspace, parent,
name)`.

## Full-text search

On PostgreSQL, `assets.search_vector` is a weighted `tsvector`
(name=A, description=B, filename=C) maintained by a `BEFORE INSERT/UPDATE`
trigger and indexed with GIN. Queries use `websearch_to_tsquery` and rank with
`ts_rank`. A `pg_trgm` GIN index on `name` supports fast prefix/`ILIKE` lookups.
On SQLite the repository falls back to `ILIKE`, so tests exercise the full stack
without Postgres.

## Storage & signed delivery

`StorageBackend` abstracts object storage. `LocalStorage` writes under a storage
root (with path-traversal guards); `S3Storage` uses boto3 and can emit native
presigned URLs. When the backend can't presign (local disk), the app mints its
own HMAC-signed, expiring URL served by a signature-verifying streaming
endpoint — mirroring the CloudFront/S3 signed-URL model.

## Observability

- **Structured JSON logs** (toggle with `LOG_JSON`) with request IDs, method,
  path, status and duration.
- **`/health`** (liveness) and **`/ready`** (readiness — checks the DB) power
  container/orchestrator probes.

## Testing strategy

- Tests run against an isolated SQLite database created per-test via
  `Base.metadata.create_all`, keeping them fast and hermetic.
- CI additionally spins up a Postgres service to validate that Alembic migrations
  (including the FTS trigger and GIN index) apply cleanly on the real engine.

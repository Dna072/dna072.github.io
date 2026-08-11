# RenderFlow — Distributed Media Processing Platform

RenderFlow is a production-style distributed system for processing media at
scale: submit a job (transcode, thumbnail, audio extraction, metadata probe),
and a pool of horizontally-scalable workers pulls it off a priority queue,
runs it with FFmpeg, stores the result, and reports status — with automatic
retries, idempotent submission, worker heartbeats, structured logs, and health
probes wired for Kubernetes.

> **Honesty note:** This is a portfolio project built to demonstrate backend and
> infrastructure engineering. It ships with real, working code and tests, but it
> is **not** running production traffic — there are no real users, uptime, or
> revenue claims. Benchmarks (if any) are local test results only.

---

## Table of contents

- [What it does](#what-it-does)
- [Architecture](#architecture)
- [Job lifecycle (state machine)](#job-lifecycle-state-machine)
- [Tech stack](#tech-stack)
- [Repository layout](#repository-layout)
- [Quickstart](#quickstart)
- [Configuration](#configuration)
- [API reference](#api-reference)
- [Reliability features](#reliability-features)
- [Health probes in production](#health-probes-in-production)
- [Observability](#observability)
- [Testing](#testing)
- [Kubernetes deployment](#kubernetes-deployment)
- [AWS deployment architecture](#aws-deployment-architecture)
- [Design decisions & trade-offs](#design-decisions--trade-offs)
- [Limitations & roadmap](#limitations--roadmap)

---

## What it does

| Job type | Description | Example params |
|----------|-------------|----------------|
| `transcode` | Re-encode video to a target resolution/codec | `{"height": 720, "video_codec": "libx264"}` |
| `thumbnail` | Extract a still frame as a JPEG | `{"timestamp": "00:00:05", "width": 320}` |
| `audio_extract` | Strip an audio track to mp3/aac | `{"format": "mp3", "bitrate": "192k"}` |
| `metadata` | Probe container/stream metadata (ffprobe) | `{}` |

Every job carries: `id`, `status`, `priority`, `created_at`, `started_at`,
`completed_at`, `retries`, `error_message`, and `idempotency_key`.

If FFmpeg is unavailable (e.g. a minimal CI image) or `RENDERFLOW_FORCE_MOCK_PROCESSING=true`,
processors emit deterministic **mock** outputs so the full pipeline — enqueue →
claim → process → store → complete — still runs end to end.

---

## Architecture

```mermaid
flowchart LR
    subgraph Client
        UI[React + TS<br/>Ops Dashboard]
    end

    subgraph API[FastAPI API]
        R[Routers<br/>jobs / workers / health]
        SVC[Service layer<br/>+ state machine]
        RP[Reaper thread<br/>recovers dead-worker jobs]
    end

    DB[(PostgreSQL<br/>jobs + heartbeats)]
    Q[[Redis<br/>priority + delay queue]]
    OS[(Object storage<br/>local / S3)]

    subgraph Workers[Worker pool - scalable]
        W1[Worker]
        W2[Worker]
        W3[Worker ...]
    end

    FF[FFmpeg / ffprobe]

    UI -->|REST /api/v1| R
    R --> SVC
    SVC --> DB
    SVC -->|enqueue job id| Q
    RP --> DB
    Workers -->|dequeue ready job| Q
    Workers -->|claim / complete / fail| DB
    Workers -->|heartbeat| DB
    Workers --> FF
    Workers -->|read input / write output| OS
```

The API and workers are **stateless** and share nothing but PostgreSQL (state)
and Redis (the queue). That means both scale horizontally by adding replicas.
An optional SVG version of this diagram lives at
[`docs/architecture.svg`](docs/architecture.svg).

---

## Job lifecycle (state machine)

Transitions are enforced centrally in [`app/state_machine.py`](backend/app/state_machine.py);
any illegal transition raises rather than silently corrupting state.

```mermaid
stateDiagram-v2
    [*] --> pending
    pending --> queued: enqueue
    queued --> running: worker claims (lease)
    running --> succeeded: processed OK
    running --> retrying: failed, retries left
    retrying --> queued: backoff elapsed → re-enqueue
    running --> failed: retries exhausted
    queued --> cancelled: operator
    running --> cancelled: operator
    failed --> queued: operator retry
    cancelled --> queued: operator retry
    running --> queued: reaper (lease expired)
    succeeded --> [*]
    failed --> [*]
    cancelled --> [*]
```

Terminal states: `succeeded`, `failed`, `cancelled`. `succeeded` is fully
terminal; `failed`/`cancelled` can be manually re-queued by an operator.

---

## Tech stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0, Pydantic v2, Uvicorn
- **Queue:** Redis (sorted-set priority + delayed queue, atomic pop via Lua)
- **Database:** PostgreSQL (SQLite for local dev / tests)
- **Media:** FFmpeg / ffprobe (with mock fallback)
- **Storage:** pluggable object storage (local filesystem or S3-compatible)
- **Frontend:** React 18 + TypeScript + Vite (ops dashboard)
- **Packaging:** Docker (API, worker, frontend), Docker Compose
- **Orchestration:** Kubernetes manifests + HPA
- **Quality:** pytest, Ruff, ESLint

---

## Repository layout

```
projects/renderflow/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app, request-ID middleware, lifespan
│   │   ├── config.py          # env-driven settings (shared API + worker)
│   │   ├── logging_config.py  # structured JSON logs + correlation IDs
│   │   ├── database.py        # SQLAlchemy engine/session
│   │   ├── models.py          # Job, WorkerHeartbeat ORM
│   │   ├── schemas.py         # Pydantic request/response models
│   │   ├── state_machine.py   # job states + validated transitions
│   │   ├── queue.py           # Redis + in-memory priority/delay queue
│   │   ├── storage.py         # local / S3 object storage abstraction
│   │   ├── backoff.py         # exponential backoff w/ jitter
│   │   ├── service.py         # all state mutations flow through here
│   │   ├── reaper.py          # recovers jobs abandoned by dead workers
│   │   ├── routers/           # jobs, workers, health/ready
│   │   └── worker/            # dequeue loop, heartbeat, processors
│   ├── tests/                 # state machine, API, retry/idempotency
│   ├── Dockerfile
│   └── requirements*.txt
├── worker/Dockerfile          # worker image (shares backend/app)
├── frontend/                  # React + TS ops dashboard
├── k8s/                       # Kubernetes manifests + HPA + kustomization
├── docs/                      # AWS architecture, SVG diagram
├── docker-compose.yml
└── .env.example
```

---

## Quickstart

### Option A — Docker Compose (full stack)

```bash
cd projects/renderflow
docker compose up --build
# scale the worker pool:
docker compose up --build --scale worker=3
```

- UI:   http://localhost:8080
- API:  http://localhost:8000  (Swagger at `/docs`)

### Option B — Local dev (no Docker)

Backend + worker with zero infra (SQLite + in-process queue):

```bash
cd projects/renderflow/backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

# Terminal 1 — API
uvicorn app.main:app --reload

# Terminal 2 — worker (shares the SQLite DB & in-process queue only within one
# process; for a separate worker process use Redis + Postgres, see below)
python -m app.worker.runner
```

> For multi-process local runs, set `RENDERFLOW_REDIS_URL` and
> `RENDERFLOW_DATABASE_URL` (Postgres) so the API and worker share the queue and
> DB. The Compose stack does this for you.

Frontend:

```bash
cd projects/renderflow/frontend
npm install
npm run dev     # http://localhost:5173 (proxies /api to :8000)
```

### Submit a job via curl

```bash
curl -s -X POST http://localhost:8000/api/v1/jobs \
  -H 'Content-Type: application/json' \
  -d '{"job_type":"transcode","input_uri":"https://example.com/in.mp4",
       "params":{"height":480},"priority":5,"idempotency_key":"demo-1"}'
```

---

## Configuration

All settings are environment variables prefixed `RENDERFLOW_` (see
[`.env.example`](.env.example)). Highlights:

| Variable | Default | Purpose |
|----------|---------|---------|
| `RENDERFLOW_DATABASE_URL` | `sqlite:///./renderflow.db` | SQLAlchemy DSN (Postgres in prod) |
| `RENDERFLOW_REDIS_URL` | *(empty)* | Redis URL; empty → in-process queue |
| `RENDERFLOW_STORAGE_BACKEND` | `local` | `local` or `s3` |
| `RENDERFLOW_DEFAULT_MAX_RETRIES` | `3` | Default retry budget per job |
| `RENDERFLOW_RETRY_BACKOFF_BASE_SECONDS` | `2.0` | Exponential backoff base |
| `RENDERFLOW_RETRY_BACKOFF_MAX_SECONDS` | `300.0` | Backoff cap |
| `RENDERFLOW_JOB_LEASE_SECONDS` | `600.0` | Lease before a RUNNING job is reaped |
| `RENDERFLOW_WORKER_STALE_AFTER_SECONDS` | `30.0` | Heartbeat age before a worker is "offline" |
| `RENDERFLOW_FORCE_MOCK_PROCESSING` | `false` | Skip FFmpeg, emit mock output |

---

## API reference

Base path: `/api/v1`

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/jobs` | Submit a job (201 new, 200 if idempotent dedupe) |
| `GET`  | `/jobs` | List jobs (`?status=`, `?job_type=`, `?limit=`, `?offset=`) |
| `GET`  | `/jobs/stats` | Counts by status |
| `GET`  | `/jobs/failed` | List terminally failed jobs |
| `GET`  | `/jobs/{id}` | Job detail |
| `POST` | `/jobs/{id}/retry` | Re-queue a failed/cancelled job (`?reset_retries=`) |
| `POST` | `/jobs/{id}/cancel` | Cancel an active job |
| `DELETE` | `/jobs/{id}` | Delete a job record |
| `GET`  | `/workers` | Worker list with liveness (online/total) |
| `POST` | `/workers/heartbeat` | Report a worker heartbeat over HTTP |
| `GET`  | `/health` | Liveness probe |
| `GET`  | `/ready` | Readiness probe (checks DB + queue) |

Interactive docs are served at `/docs` (Swagger) and `/redoc`.

---

## Reliability features

### Idempotent submission
Clients may pass an `idempotency_key`. A DB unique constraint plus a
check-then-insert (with an `IntegrityError` fallback for the race) guarantees a
retried submission returns the **same** job instead of spawning duplicate work.

### Retry with exponential backoff
On failure a job's `retries` counter increments. While `retries <= max_retries`
the job moves to `retrying` and is re-enqueued with a delay of
`base ** attempt` seconds (capped, plus jitter). The Redis queue schedules the
delay natively (the job simply isn't returned until its scheduled time). Once the
budget is exhausted the job becomes terminally `failed` and appears in
`/jobs/failed` for inspection and manual retry.

### Worker heartbeats & the reaper
Each worker writes a heartbeat (state, current job, counters) to the DB on a
timer. The dashboard shows online/offline status. If a worker dies mid-job, its
job stays `running` with an expired **lease** — a background reaper thread in the
API detects the expired lease and requeues the job (subject to the same retry
rules), so no work is lost to a crashed pod.

---

## Health probes in production

RenderFlow exposes two distinct probes because *liveness* and *readiness* answer
different questions — conflating them is a classic cause of cascading outages.

**`GET /health` — liveness.** Cheap and dependency-free. It only asserts the
process itself is responsive. Kubernetes uses it as `livenessProbe`: if it stops
returning `200`, the process is wedged and the pod is **restarted**. Crucially it
does *not* check the database or Redis — otherwise a brief DB blip would make
Kubernetes kill every API pod at once, turning a recoverable dependency hiccup
into a full outage.

**`GET /ready` — readiness.** Verifies the pod can actually serve traffic by
checking the database (`SELECT 1`) and the queue (`PING`). It returns `503` when
a dependency is unreachable. Kubernetes uses it as `readinessProbe`: a failing
pod is **removed from the Service endpoints** (no traffic routed to it) but **not
restarted**. When the dependency recovers, the pod re-enters rotation
automatically. This drains traffic gracefully during dependency outages and
during rollouts (a new pod only receives traffic once it's genuinely ready).

**`startupProbe`.** The API also defines a startup probe so slow first-boot work
(e.g. migrations) doesn't trip the liveness probe and cause a restart loop.

**Workers** have no HTTP server, so their liveness is file-based: the worker
touches `RENDERFLOW_WORKER_LIVENESS_FILE` on every heartbeat, and the Kubernetes
`livenessProbe` execs a check that the file was updated within the heartbeat
window. A hung worker whose loop stalls stops touching the file and is restarted.

See the probe definitions in
[`k8s/api-deployment.yaml`](k8s/api-deployment.yaml) and
[`k8s/worker-deployment.yaml`](k8s/worker-deployment.yaml).

---

## Observability

- **Structured logging:** every log line is JSON (`app/logging_config.py`) with
  `timestamp`, `level`, `logger`, `message`, and structured `extra` fields —
  ready for ingestion by CloudWatch Logs, Loki, or Datadog.
- **Correlation IDs:** the API middleware assigns an `X-Request-ID` (honouring an
  inbound one) and propagates it via `contextvars` so every log line for a
  request is tagged. Workers similarly tag logs with `worker_id` and `job_id`,
  making it trivial to trace one job across API and worker logs.

Example log line:

```json
{"timestamp":"2026-08-11T07:40:52Z","level":"WARNING","logger":"renderflow.service",
 "message":"job failed; scheduled retry","request_id":"...","job_id":"...",
 "retries":1,"max_retries":3,"backoff_seconds":2.4}
```

---

## Testing

```bash
cd projects/renderflow/backend
source .venv/bin/activate
pytest            # 26 tests: state machine, API, retry/idempotency, worker e2e
ruff check .      # lint
```

Test coverage includes:

- **State machine:** valid/invalid transitions, terminal-state enforcement.
- **API:** submit/list/filter/get/cancel, validation errors, health/ready,
  request-ID round-trip, failed-jobs list + retry endpoint.
- **Retry & idempotency:** dedupe by key (incl. the race path), exponential
  backoff growth + cap, retry-until-terminal, manual retry, reaper recovery.
- **End-to-end worker:** a real `Worker` claims and processes a job (mock mode),
  producing a stored artifact and a heartbeat.

Frontend: `npm run build` (type-check + bundle) and `npm run lint`.

---

## Kubernetes deployment

Manifests live in [`k8s/`](k8s/) and can be applied with Kustomize:

```bash
# 1. Build & push images (or load into your local cluster):
#    renderflow/api, renderflow/worker, renderflow/frontend
# 2. Create the real Secret (don't use the example in prod):
kubectl create namespace renderflow
kubectl create secret generic renderflow-secrets -n renderflow \
  --from-literal=RENDERFLOW_DATABASE_URL='postgresql+psycopg://user:pass@host:5432/renderflow'
# 3. Apply everything:
kubectl apply -k k8s
```

Included:

- **API** Deployment (rolling updates, liveness/readiness/startup probes) + Service
- **Worker** Deployment (scalable) + **HPA** (CPU-based, with a documented
  KEDA/queue-depth pattern for production)
- **Redis** and **PostgreSQL** (StatefulSet) for demos, with a documented
  **external DB pattern** for RDS/ElastiCache (just repoint the Secret/ConfigMap
  and delete the in-cluster manifest)
- **ConfigMap** (non-secret config) and an example **Secret**
- **Ingress** and a **frontend** Deployment/Service

---

## AWS deployment architecture

A cloud reference architecture (ECS/EKS + SQS/ElastiCache + S3 + RDS) is
documented in [`docs/aws-architecture.md`](docs/aws-architecture.md). It is a
design reference only — **nothing is provisioned** and no live infra is required
to run this project.

---

## Design decisions & trade-offs

- **Redis sorted-set as the queue** (vs. a list): a single structure gives us
  both priority ordering *and* delayed delivery for backoff, with an atomic
  Lua-scripted "pop earliest ready" so concurrent workers never double-claim.
- **DB-backed leases + reaper** (vs. Redis visibility timeouts): keeps the
  authoritative job state in one place (Postgres) and makes crash recovery
  explicit and testable.
- **All mutations through a service layer** that validates every transition:
  the queue, API, worker, and reaper can't drift into inconsistent state.
- **Pluggable storage/queue** behind interfaces: SQLite + in-process queue for
  fast, hermetic tests; Postgres + Redis for real deployments — no code change.
- **Mock processing fallback:** the pipeline is exercisable in CI without FFmpeg.

---

## Limitations & roadmap

- Schema is created via `create_all` for demo simplicity; a real deployment
  would use **Alembic** migrations.
- Queue-depth autoscaling is documented (KEDA) but not wired — the shipped HPA
  scales on CPU.
- No authentication on the API — an API gateway / auth layer would front it in
  production.
- Metrics are via structured logs; a `/metrics` Prometheus endpoint is a natural
  next step.
```

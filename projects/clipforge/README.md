# ClipForge

AI video processing and content intelligence platform. Upload videos, process them asynchronously through a Redis-backed worker pipeline, and explore transcripts, summaries, chapters, and AI-generated tags in a React dashboard.

> **Portfolio project** — production-style architecture and code quality, not a commercial product with live customers.

## Problem

Creative and media teams need more than file storage. After upload, videos should be processed asynchronously — thumbnails, audio extraction, transcripts, and AI-derived summaries, chapters, and tags — without blocking API requests or the UI.

## Solution

ClipForge accepts validated video uploads, persists metadata, enqueues processing jobs on Redis, and runs workers that orchestrate FFmpeg plus an AI provider abstraction. The React dashboard shows library state, job progress, transcripts, and AI outputs.

## Architecture

```
POST /api/v1/videos/upload
   ↓ store metadata + object
   ↓ enqueue job (Redis)
   ↓ worker: ffprobe → thumbnails → audio
   ↓ transcript → AI summary/chapters/tags
   ↓ persist results
   ↓ frontend polls status updates
```

**Layers:** `api` · `services` · `repositories` · `workers` with SQLAlchemy models and Pydantic schemas.

## Key features

- JWT authentication and workspaces
- Validated video uploads (type, size, MIME, extension)
- Async processing pipeline (Redis + workers)
- Thumbnails, audio extract, transcript
- AI summary, chapters, tags via AIProvider (OpenAI / MockAI)
- Search, filters, dashboard stats
- OpenAPI docs at `/docs`
- Health and readiness endpoints

## Tech stack

| Layer | Technologies |
|-------|-------------|
| Frontend | React 18, TypeScript, Vite, React Router, TanStack Query, Axios |
| Backend | FastAPI, SQLAlchemy, Pydantic, JWT |
| Queue | Redis |
| Media | FFmpeg (ffprobe, thumbnails, audio) |
| AI | OpenAI (optional) or deterministic mock |
| Database | SQLite (local) / PostgreSQL (Docker) |

## Quick start (Docker Compose)

```bash
cd projects/clipforge
cp .env.example .env
docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| API | http://localhost:8000 |
| OpenAPI | http://localhost:8000/docs |

Register an account in the UI — a default workspace is created automatically.

## Local development (without Docker)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

In a second terminal, start the worker (requires Redis):

```bash
cd backend
source .venv/bin/activate
python -m app.workers.worker
```

Without Redis, jobs run inline in stub mode (logged, not ideal for production).

### Frontend

```bash
cd frontend
npm install
cp ../.env.example .env   # optional — defaults to http://localhost:8000
npm run dev
```

Vite proxies `/api` to the backend during development (see `vite.config.ts`).

## API overview

Base URL: `http://localhost:8000/api/v1`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Register `{email, password, full_name}` |
| POST | `/auth/login` | Login → `{user, tokens}` |
| POST | `/auth/refresh` | Refresh access token |
| GET | `/auth/me` | Current user |
| GET | `/dashboard/stats` | Dashboard metrics |
| GET | `/workspaces` | List workspaces |
| GET | `/videos?q=` | Search/list videos |
| POST | `/videos/upload` | Multipart upload |
| GET | `/videos/:id` | Video detail |
| GET | `/videos/:id/job` | Latest processing job |
| GET | `/jobs/:id` | Job by ID |

## Environment variables

See [`.env.example`](.env.example) and [`backend/.env.example`](backend/.env.example).

| Variable | Description |
|----------|-------------|
| `JWT_SECRET_KEY` | JWT signing secret (change in production) |
| `DATABASE_URL` | SQLAlchemy URL (SQLite or PostgreSQL) |
| `REDIS_URL` | Redis connection for job queue |
| `OPENAI_API_KEY` | Optional — enables real AI analysis |
| `AI_PROVIDER` | `auto`, `mock`, or `openai` |
| `VITE_API_URL` | Frontend API base (no path suffix) |

## Project structure

```
clipforge/
├── backend/           # FastAPI application
│   ├── app/
│   │   ├── api/       # Route handlers
│   │   ├── services/  # Business logic
│   │   ├── workers/   # Pipeline + queue consumer
│   │   └── models/    # SQLAlchemy models
│   ├── tests/
│   └── Dockerfile
├── frontend/          # React + TypeScript SPA
│   └── src/
│       ├── api/       # Axios client + types
│       ├── components/
│       ├── context/   # Auth provider
│       └── pages/
├── docker-compose.yml
├── .env.example
└── README.md
```

## Testing

```bash
# Backend
cd backend && pytest

# Frontend
cd frontend && npm test
```

## Technical decisions

- **Async jobs** instead of request-blocking FFmpeg/AI calls
- **Provider interface** so demo mode works without API keys
- **Structured logs** + request IDs for production troubleshooting
- **Docker Compose** for local parity (api, worker, postgres, redis, frontend)

## Infrastructure target

Local: Docker Compose. Documented AWS target: S3 object storage, RDS PostgreSQL, ElastiCache Redis, ECS services for API/worker, CloudFront for UI.

## License

Portfolio / demonstration use. See repository root for author information.

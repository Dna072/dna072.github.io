# MediaVault

Video asset management SaaS built as a **production-style portfolio project**.

## Demo

```bash
docker compose up --build
```

- UI: http://localhost:5174  
- API: http://localhost:8001/docs  

## Architecture

```
React DAM UI → FastAPI /api/v1 → PostgreSQL (+ FTS/indexes)
                     ↓
              local/S3 storage + signed URLs
```

## Tech Stack

Python 3.12, FastAPI, SQLAlchemy, Alembic, PostgreSQL, JWT RBAC, React, TypeScript, Vite, Docker.

## Features

Workspaces, ADMIN/MEMBER/VIEWER roles, folders, tags, asset upload, search, shares, pagination/filtering.

## API

Versioned under `/api/v1` — see OpenAPI `/docs`.

## Database

Relational schema with membership, assets, folders, tags, shares. Indexes + full-text search migrations included.

## Running Locally

```bash
cp .env.example .env   # if present
docker compose up --build
cd backend && pytest
```

## Environment Variables

See backend config / `.env.example`. No production secrets in git.

## Testing

`pytest` under `backend/tests` covers auth, RBAC, search, shares, health.

## Docker

Compose services: postgres, api, frontend.

## Deployment

AWS sketch: S3 + CloudFront signed URLs, RDS PostgreSQL, ECS API. Not provisioned here.

## Engineering Decisions

Authorization at workspace boundaries; signed URLs instead of public object paths; API versioning.

## Future Improvements

Webhook notifications, richer preview pipeline, audit log export.

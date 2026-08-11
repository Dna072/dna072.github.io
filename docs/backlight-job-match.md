# Backlight Job-Match Audit

**Role:** Junior Fullstack Developer (Backend focus) — Backlight  
**Job:** https://www.linkedin.com/jobs/view/4448553868/

## Evidence table

| Job requirement | Portfolio evidence | Project |
|-----------------|-------------------|---------|
| Python backend | FastAPI services, workers, domain services | All four |
| ReactJS | Dashboards, library UIs, ops consoles | All four |
| TypeScript | Typed Vite frontends | All four |
| API development | REST + OpenAPI/Pydantic schemas | All four |
| Clean maintainable code | Layered architecture, lint/CI | All four |
| Code reviews | PR workflow + GitHub Actions | Monorepo |
| Production troubleshooting | Structured logs, request IDs, health/ready | ClipForge, MediaVault, RenderFlow |
| Performance & availability | Async queues, indexes, probes | ClipForge, StreamPulse, RenderFlow |
| Frontend ↔ backend integration | Auth, uploads, live metric fetches | All four |
| Git/GitHub | Branches, Actions, docs | All four |
| Problem solving | Media pipeline, RBAC, analytics SQL, job retries | Domain-specific |
| FastAPI | Primary framework | All four |
| SQL/NoSQL | PostgreSQL; Redis queues | MediaVault/StreamPulse; ClipForge/RenderFlow |
| AWS | Documented S3/RDS/ECS-EKS/ElastiCache/CloudFront | README sections |
| Docker | Compose stacks | All four |
| Kubernetes | Manifests + probes + HPA | RenderFlow |
| AI capabilities | AIProvider + OpenAI + MockAI | ClipForge |

## Test results (local agent run)

| Project | Backend pytest | Frontend build |
|---------|----------------|----------------|
| ClipForge | 21 passed | vite build OK |
| MediaVault | 53 passed | vite build OK |
| StreamPulse | 32 passed | vite build OK |
| RenderFlow | API + worker tests passed | vite build OK |

## Gaps

| Gap | Mitigation |
|-----|------------|
| Separate GitHub repos not created | Source under `projects/`; see `docs/extract-repos.md` |
| No live public demos | Docker Compose local demos documented |
| `Dna072/Portfolio` write access | Case studies on github.io; Next.js integration pending |
| Real OpenAI/FFmpeg in CI | Mock providers / mock media steps |

## Honesty

Projects are production-style portfolio work — no invented customers, revenue, or uptime.

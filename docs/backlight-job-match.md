# Backlight Job-Match Audit

**Role:** Junior Fullstack Developer (Backend focus) — Backlight  
**Job:** https://www.linkedin.com/jobs/view/4448553868/  
**Audit status:** Living document — update as projects land under `projects/`.

## Evidence table

| Job requirement | Portfolio evidence | Project |
|-----------------|-------------------|---------|
| Python backend | FastAPI services, workers, domain services | All four |
| ReactJS | Dashboards, library UIs, ops consoles | All four |
| TypeScript | Typed Vite frontends | All four |
| API development | REST + OpenAPI/Pydantic schemas | All four |
| Clean maintainable code | Layered `api/services/repositories` layout, lint/CI | All four |
| Code reviews | PR-based workflow + CI gates | Monorepo + extractable repos |
| Production troubleshooting | Structured logs, request IDs, error handling | ClipForge, RenderFlow |
| Performance & availability | Async queues, health/ready, SQL indexes | ClipForge, StreamPulse, RenderFlow |
| Frontend ↔ backend integration | Auth sessions, uploads, live metric fetches | All four |
| Git/GitHub | Branches, Actions, documentation | All four |
| Problem solving | Media pipeline, RBAC, analytics SQL, job retries | Domain-specific per project |
| FastAPI | Primary framework | All four |
| SQL/NoSQL | PostgreSQL; Redis queues/cache | MediaVault/StreamPulse; ClipForge/RenderFlow |
| AWS | Documented S3/RDS/ECS-EKS/ElastiCache/CloudFront | README deployment sections |
| Docker | Compose stacks per project | All four |
| Kubernetes | Manifests + probes + HPA | RenderFlow |
| AI capabilities | AIProvider + OpenAI + MockAI, async AI jobs | ClipForge |

## Positioning for hiring managers

Portfolio communicates: **full-stack engineer focused on Python backend systems, React/TypeScript, and scalable cloud applications**, with domain work in **video/media SaaS**—adjacent to Backlight’s content lifecycle products.

## Gaps / follow-ups

| Gap | Mitigation |
|-----|------------|
| Separate GitHub repositories not yet created | Source complete under `projects/`; see `docs/extract-repos.md`; user action requested |
| No live cloud demos | Docker Compose local demo path documented; avoid fake URLs |
| Write access to `Dna072/Portfolio` Next.js site | Case studies on github.io; patch/integration pending access |
| Real OpenAI / FFmpeg in CI | Mock providers and mock media steps; real tools optional locally |
| Expensive AWS not provisioned | Intentional — architecture documented only |

## Honesty checklist

- [x] No invented customers, revenue, or production traffic
- [x] Copy uses “production-style portfolio project”
- [ ] Screenshots added after running UIs (follow-up)
- [ ] Final test/lint matrix filled after implementation agents finish

## Next steps

1. Merge Cloud/local agent implementations for all four projects  
2. Run Compose smoke tests per project  
3. Fill final test matrix  
4. Extract to dedicated repos when remotes exist  
5. Port case studies into `Dna072/Portfolio` when granted access  

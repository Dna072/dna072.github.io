# Skills Audit — Media/Video SaaS Portfolio

**Focus:** Junior/mid fullstack (backend-heavy) for media and video SaaS products.

## Evidence table

| Skill area | Portfolio evidence | Project |
|------------|-------------------|---------|
| Python backend | FastAPI services, workers, domain services | [ClipForge](https://github.com/Dna072/clipforge), [MediaVault](https://github.com/Dna072/mediavault), [StreamPulse](https://github.com/Dna072/streampulse), [RenderFlow](https://github.com/Dna072/renderflow) |
| ReactJS | Dashboards, library UIs, ops consoles | All four |
| TypeScript | Typed Vite frontends | All four |
| API development | REST + OpenAPI/Pydantic schemas | All four |
| Clean maintainable code | Layered architecture, lint/CI | All four |
| Code reviews | PR workflow + GitHub Actions | Separate project repos |
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

## Gaps

| Gap | Mitigation |
|-----|------------|
| No live public demos | Docker Compose local demos documented in each repo |
| `Dna072/Portfolio` Next.js case-study sync | Case studies on github.io; optional Next.js port later |
| Real OpenAI/FFmpeg in CI | Mock providers / mock media steps in project repos |

## Honesty

Projects are production-style portfolio work — no invented customers, revenue, or uptime.

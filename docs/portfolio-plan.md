# Backlight Portfolio — Architecture & Implementation Plan

**Target role:** Junior Fullstack Developer (Backend focus) — Backlight  
**Job:** https://www.linkedin.com/jobs/view/4448553868/  
**Candidate:** Derrick Adjei  
**Date:** 2026-08-11

---

## 1. Repository audit (`dna072.github.io`)

| Area | Finding |
|------|---------|
| **Framework** | None — static HTML |
| **Frontend** | Single `index.html` (Bootstrap 4 CDN) |
| **Backend** | None |
| **Database** | None |
| **Routing** | N/A (one page) |
| **Styling** | `style.css` + Bootstrap 4; Montserrat; coral accent `#F05F44`; full-bleed `header.jpg` |
| **Deployment** | GitHub Pages (user site) |
| **Package manager** | None |
| **Env config** | None |
| **README** | None |
| **Git** | `master` → `origin` (`Dna072/dna072.github.io`) |

**Important related repo (no write access from this agent):**  
`Dna072/Portfolio` — production Next.js 15 portfolio at https://dna072.github.io/Portfolio with Manrope/IBM Plex Mono, green brand `#1db954`, projects/case studies, architecture pages. Design language should inform any site updates here. Cursor bot currently cannot push to that repo.

**Current `index.html` content:** Coursera-style “startup event” landing + Mailchimp — **not** a personal engineering portfolio. Replacing it with a Backlight-targeted portfolio is appropriate; we are not preserving a finished personal brand page.

---

## 2. Job requirement analysis (Backlight)

### Core responsibilities → portfolio evidence

| Requirement | How we demonstrate it |
|-------------|----------------------|
| Python backend | FastAPI services in all four projects |
| ReactJS + TypeScript | Typed React SPAs / dashboards |
| APIs + maintainable code | Versioned REST, Pydantic schemas, clean architecture |
| Code reviews / quality | CI lint + tests; clear PR-ready structure |
| Production troubleshooting | Structured logs, request IDs, health/ready, error handling |
| Performance & availability | Async jobs, Redis queues, indexes, health probes |
| Frontend ↔ backend integration | Real API clients, auth flows, loading/error/empty states |
| Git/GitHub | Separate project packages + Actions workflows |
| Problem solving | Realistic media SaaS workflows (not toys) |

### Bonus → evidence

| Bonus | Project |
|-------|---------|
| FastAPI + SQL/NoSQL | All (PostgreSQL); Redis in ClipForge/RenderFlow |
| AWS | Architecture docs (S3, RDS, ECS/EKS, ElastiCache, CloudFront) — no expensive live infra |
| Docker / Kubernetes | Compose everywhere; K8s manifests in RenderFlow |
| AI capabilities | ClipForge AI provider abstraction (OpenAI + Mock) |

### Domain fit

Backlight = media technology / video content lifecycle. Portfolio theme: **media/video SaaS ecosystem** (processing → asset management → analytics → distributed render).

---

## 3. Portfolio strategy

### Where projects live

1. **Source of truth (this monorepo):** `projects/{clipforge,mediavault,streampulse,renderflow}/`  
   Each package is **fully self-contained** (own README, Docker, CI, `.env.example`) so it can be extracted to its own GitHub repository with `git subtree` / fresh remote.

2. **Separate GitHub repos (requested):**  
   - `Dna072/clipforge`  
   - `Dna072/mediavault`  
   - `Dna072/streampulse`  
   - `Dna072/renderflow`  
   Agent cannot create repos with current token; user action requested.

3. **Portfolio website (this repo):** Replace stub landing with a focused engineering portfolio that:
   - Positions Derrick for Backlight (Python backend + React/TS + cloud)
   - Cards + case-study pages for the four projects
   - Links to GitHub (and live demos when available)
   - States clearly: *“Built as production-style portfolio projects”* — no fake users/revenue/uptime

4. **Ideal future:** Mirror case studies into `Dna072/Portfolio` once write access is granted.

### Presentation model

**Combination:** case studies embedded on the site + GitHub links + optional live demos (Docker Compose local / free-tier deploy docs). Prefer honest “run locally with Docker Compose” over fake production URLs.

---

## 4. Four projects (media SaaS ecosystem)

| # | Name | Focus | Stack highlights |
|---|------|-------|------------------|
| 1 | **ClipForge** | Flagship: AI video intelligence pipeline | FastAPI, Redis workers, FFmpeg, AI providers, React dashboard |
| 2 | **MediaVault** | Asset management, RBAC, search | FastAPI `/api/v1`, JWT roles, FTS, signed URLs, polished React UI |
| 3 | **StreamPulse** | Analytics dashboard + SQL | Metrics APIs, seed data, charts from real APIs, indexes |
| 4 | **RenderFlow** | Infra: queues, workers, K8s | Job lifecycle, retries, heartbeats, Compose + K8s manifests |

Shared standards: Python 3.12+, FastAPI, SQLAlchemy, Alembic, Pydantic, pytest, Ruff; React+TS, ESLint/Prettier; Docker Compose; `.env.example`; no secrets in git.

---

## 5. Agent / workstream plan

| Agent | Scope | Independence |
|-------|-------|--------------|
| **A1** (parent) | Audit, plan, portfolio site, orchestration, job-match audit | Coordinates |
| **A2** | ClipForge full stack | Parallel |
| **A3** | MediaVault full stack | Parallel |
| **A4** | StreamPulse full stack | Parallel |
| **A5** | RenderFlow API/workers/K8s | Parallel |
| **A6** | Portfolio website + case studies | After scaffolds; can start in parallel with shared copy |
| **A7** | Cross-cutting CI/security/job-match polish | After projects land |

Overlaps: only `docs/` and top-level portfolio pages — parent owns those. Project agents own `projects/<name>/` exclusively.

---

## 6. Implementation roadmap

### Phase 1–2 — Done in this doc
Audit + plan + job analysis.

### Phase 3 — Scaffold
Create directory skeletons, shared conventions, empty READMEs, Compose stubs.

### Phase 4–7 — Implement (parallel Cloud Agents)
Full ClipForge → MediaVault → StreamPulse → RenderFlow (order of priority if capacity constrained: ClipForge + RenderFlow first for backend/infra signal, then MediaVault + StreamPulse).

### Phase 8 — Portfolio site
Projects section, four case-study pages, positioning copy, architecture diagrams (Mermaid).

### Phase 9 — Quality pass
Tests, lint, Docker build checks, security review (uploads, auth, secrets).

### Phase 10 — Job-match audit
`docs/backlight-job-match.md` with evidence table + gaps.

---

## 7. Engineering constraints (honesty)

- Do **not** invent customers, revenue, traffic, or uptime.
- Label benchmarks as test results only.
- Demo mode / MockAI when API keys absent.
- No expensive AWS provisioning without explicit approval.
- Prefer depth over breadth; four serious products beat ten toys.

---

## 8. Success criteria for Backlight hiring manager

After review, they should believe the candidate can:

1. Design and ship Python/FastAPI backends with real data models  
2. Build React/TypeScript UIs that talk to those APIs  
3. Reason about async media pipelines, queues, and failure modes  
4. Containerize and describe AWS/K8s deployment  
5. Write tests, CI, and documentation like a production engineer  

They should **not** think these are generated AI wrappers.

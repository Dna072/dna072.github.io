# Media/Video SaaS Portfolio — Architecture & Implementation Plan

**Focus:** Fullstack (backend-heavy) media/video SaaS apps  
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

**Current `index.html` content:** Coursera-style “startup event” landing + Mailchimp — **not** a personal engineering portfolio. Replacing it with a media/video SaaS engineering portfolio is appropriate; we are not preserving a finished personal brand page.

---

## 2. Skills analysis (media/video SaaS)

### Core skills → portfolio evidence

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

Portfolio theme: **media/video SaaS ecosystem** (processing → asset management → analytics → distributed render).

---

## 3. Portfolio strategy

### Where projects live

1. **Separate GitHub repositories (source of truth):**  
   - https://github.com/Dna072/clipforge  
   - https://github.com/Dna072/mediavault  
   - https://github.com/Dna072/streampulse  
   - https://github.com/Dna072/renderflow  

2. **Portfolio website (this repo):** Focused engineering portfolio that:
   - Highlights Python backend + React/TS + cloud skills for media/video SaaS
   - Cards + case-study pages for the four projects
   - Links to the separate GitHub repositories
   - States clearly: *“Built as production-style portfolio projects”* — no fake users/revenue/uptime

3. **Ideal future:** Mirror case studies into `Dna072/Portfolio` once write access is granted.

---

## 4–6. Project briefs

See each repository README for architecture, stack, and local demo instructions.

---

## 6. Delivery phases

### Phase 1–2 — Planning
Audit + plan + skills analysis.

### Phase 3 — Scaffold
Create directory skeletons, shared conventions, empty READMEs, Compose stubs.

### Phase 4–7 — Implement (parallel Cloud Agents)
Full ClipForge → MediaVault → StreamPulse → RenderFlow (order of priority if capacity constrained: ClipForge + RenderFlow first for backend/infra signal, then MediaVault + StreamPulse).

### Phase 8 — Portfolio site
Projects section, four case-study pages, positioning copy, architecture diagrams (Mermaid).

### Phase 9 — Quality pass
Tests, lint, Docker build checks, security review (uploads, auth, secrets).

### Phase 10 — Skills audit
`docs/skills-audit.md` with evidence table + gaps.

---

## 7. Engineering constraints (honesty)

- Do **not** invent customers, revenue, traffic, or uptime.
- Label benchmarks as test results only.
- Demo mode / MockAI when API keys absent.
- No expensive AWS provisioning without explicit approval.
- Prefer depth over breadth; four serious products beat ten toys.

---

## 8. Success criteria

After review, a hiring manager should believe the candidate can:

1. Design and ship Python/FastAPI backends with real data models  
2. Build React/TypeScript UIs that talk to those APIs  
3. Reason about async media pipelines, queues, and failure modes  
4. Containerize and describe AWS/K8s deployment  
5. Write tests, CI, and documentation like a production engineer  

They should **not** think these are generated AI wrappers.

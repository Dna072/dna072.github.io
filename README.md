# Derrick Adjei — Portfolio (GitHub Pages)

Unified personal site at **https://dna072.github.io/** — Next.js UI (from the former `/Portfolio` app) with merged media/video SaaS case studies and data-engineering projects.

## Stack

- Next.js 15 (App Router) · React 19 · TypeScript · Tailwind CSS v4
- Static export → GitHub Pages (user site, root URL)

## Featured work

### Media/video SaaS

| Project | Repository |
|---------|------------|
| ClipForge | https://github.com/Dna072/clipforge |
| MediaVault | https://github.com/Dna072/mediavault |
| StreamPulse | https://github.com/Dna072/streampulse |
| RenderFlow | https://github.com/Dna072/renderflow |

### Data platforms & research

Also featured: Airflow pipelines, Sparkify Redshift warehouse, STEDI lakehouse, DRL job-shop thesis.

Live product links (MedLink, Arctiq, TPG) remain on the homepage.

## Local development

```bash
npm ci
npm run dev
```

## Build / publish

```bash
BASE_PATH= npm run build
./scripts/sync-static.sh   # copies out/ → repo root for Pages
```

GitHub Actions on `master` builds with `BASE_PATH=""` and syncs the export to the repository root (compatible with Pages source: `master` /).

## Note on `/Portfolio`

https://dna072.github.io/Portfolio/ is a separate project Pages site from `Dna072/Portfolio`. This repo is now the main site. Grant write access to that repo (or archive it) if you want it redirected or retired.

## Honesty

Portfolio projects are production-style demonstrations — not commercial products with live customers.

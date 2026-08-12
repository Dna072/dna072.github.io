#!/usr/bin/env bash
# Copy Next.js static export to repo root for GitHub Pages (user site).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -d out ]]; then
  echo "out/ missing — run: BASE_PATH= npm run build" >&2
  exit 1
fi

touch out/.nojekyll

rm -rf _next projects articles architecture github resume contact 404
rm -f index.html 404.html apple-icon.png icon.png favicon.ico robots.txt sitemap-index.xml
rm -rf sitemap.xml

cp -a out/. .
echo "Synced out/ → repository root"

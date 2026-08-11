# Extracting projects into separate GitHub repositories

Each app under `projects/<name>/` is designed to stand alone.

## Target remotes (create empty public repos first)

- https://github.com/Dna072/clipforge
- https://github.com/Dna072/mediavault
- https://github.com/Dna072/streampulse
- https://github.com/Dna072/renderflow

## Method A — subtree split (preserves history for that folder)

```bash
git subtree split -P projects/clipforge -b split-clipforge
git push git@github.com:Dna072/clipforge.git split-clipforge:main
```

Repeat for `mediavault`, `streampulse`, `renderflow`.

## Method B — fresh copy (simplest)

```bash
mkdir /tmp/clipforge && cp -a projects/clipforge/. /tmp/clipforge/
cd /tmp/clipforge
git init && git add . && git commit -m "Initial commit: ClipForge"
git branch -M main
git remote add origin git@github.com:Dna072/clipforge.git
git push -u origin main
```

## After extraction

1. Update portfolio case-study GitHub links (already point at the target repo URLs).
2. Enable GitHub Actions in each new repo (workflows ship inside each project).
3. Remove or keep monorepo copies as mirrors—your choice.

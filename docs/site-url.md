# Portfolio site URL — derrick-adjei.github.io

## Target URL

**https://derrick-adjei.github.io/**

GitHub user sites are always `https://<username>.github.io`, so this URL requires the site to live in a repository named **`derrick-adjei.github.io`** on the GitHub account **`derrick-adjei`**.

Project code repos can stay under `Dna072` (clipforge, mediavault, etc.) — only the portfolio host account needs to match the URL.

## One-time GitHub setup

1. Sign in to GitHub as **`derrick-adjei`** (account already exists).
2. Create a new repository named exactly **`derrick-adjei.github.io`** (public).
3. Push this project to that repo:

   ```bash
   git remote add derrick-adjei https://github.com/derrick-adjei/derrick-adjei.github.io.git
   git push -u derrick-adjei master
   ```

4. In **Settings → Pages**, set source to **Deploy from a branch** → branch **`master`** → folder **`/`** (root).

   The included workflow also builds on push to `master` and syncs the static export to the repo root.

5. Wait 1–2 minutes, then open https://derrick-adjei.github.io/

## Legacy URL (dna072.github.io)

After the new site is live, replace the old `Dna072/dna072.github.io` homepage with a redirect so bookmarks still work:

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta http-equiv="refresh" content="0; url=https://derrick-adjei.github.io/" />
    <link rel="canonical" href="https://derrick-adjei.github.io/" />
    <title>Redirecting…</title>
  </head>
  <body>
    <p>Moved to <a href="https://derrick-adjei.github.io/">derrick-adjei.github.io</a>.</p>
  </body>
</html>
```

Update your resume, LinkedIn, and email signature to use the new URL.

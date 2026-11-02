# Source fixes report

This branch holds only [`reports/source-fixes.md`](reports/source-fixes.md): metadata
errors in the published OpenID specifications, for spec editors to fix at the source.

The dashboard's daily crawl ([workflow on `main`](https://github.com/sakimura/openid-specs-dashboard/blob/main/.github/workflows/pages.yml))
commits a new version here whenever the report changes, so this branch's history shows
what has been fixed and when. The code lives on `main`, which is protected; this branch
is kept separate so the automated commit doesn't need to bypass that protection.

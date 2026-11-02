# OpenID Specifications Dashboard (prototype)

A dashboard of every specification published at <https://openid.net/specs/>:
specification status (Draft → Implementer's Draft → Final, with any errata sets), the latest
approved document, the latest revision, the working group, the editors, and the full revision history.

Two parts, no build step:

| Path | What it is |
|---|---|
| `crawler/build_data.py` | Crawls the specs directory, reads each HTML file, writes `public/data/specs.json`. Python 3.9+, standard library only. |
| `public/` | Static site (`index.html`, `app.js`, `styles.css`) that renders the JSON. Host it anywhere. |

## Run locally

```bash
python3 crawler/build_data.py
```

```bash
python3 -m http.server 8765 --directory public
```

Then open <http://localhost:8765>. The first crawl downloads all ~950 HTML files
(about 30 s); later runs only re-download files whose listing timestamp changed.
`--offline` rebuilds from the cache without touching the network.

## How the data is derived

- **Spec and revision** come from the filename: `<name>-<version>-<rev>.html`,
  where `<rev>` is `NN` (draft), `IDn` (Implementer's Draft), `final`, or `erratan`.
  Older variants are also recognised (`-wd-NN`, dated `-YYYY-MM-DD`, `draft-…-NN`).
  The unversioned file (e.g. `openid-connect-core-1_0.html`) is the spec's canonical URL.
- **Title, date, editors and working group are read from the document**, never from
  the filename. Parsers cover xml2rfc v1, v2 and v3 output, pandoc, the greenbytes
  XSLT, and Word export. Editor initials in headers are expanded to full names from
  the Authors' Addresses section.
- **Revisions are ordered by the date in the document** (the directory listing date
  is used only when the document has none, and the UI marks it with †).
- **Status** is the most advanced stage reached: Final, Implementer's Draft or Draft.
  Only Implementer's Drafts and Finals have been approved by the Foundation membership;
  a Draft is a working group draft.
- **Latest approved** is the most recent approved document: the latest errata set
  of a Final, else the Final, else the latest Implementer's Draft.
- **Drafts after …** flags a spec with a draft dated after its latest approved
  document. The documents don't say what such a draft is for (errata, a revision or
  the next approval step), so the dashboard doesn't either. The headline counts only
  specs whose newer draft is from the last 12 months.
- A new version (e.g. 1.1 after 1.0) has its own filename, so it is a separate spec.
- **Renamed specs are one entry.** A spec published under several filenames (e.g.
  `fapi-2_0-baseline` → `fapi-2_0-security-profile` → `fapi-security-profile-2_0`) is merged
  into its newest name, with one continuous Draft → ID → Final history. Evidence: a
  "Renamed" redirect page on openid.net, an "Obsolete" redirect to a spec with the same
  title, or identical document titles. Renames with none of these are listed in the
  report for confirmation and merged with `renamed_to` in the overrides.
- **Obsolete** specs that were replaced by a different spec (Connect Messages → Core)
  stay separate, are hidden by default, and link to the successor.
- **Working group** comes from the document's Workgroup field, else its IANA
  "Change Controller" entry, else the WG mailing-list address it cites. These are
  normalised to current WG names (e.g. "Artifact Binding Working Group" → AB/Connect).
  When a document states none, the WG is inferred from related specs and marked `*`.

### Curated corrections

Some facts are not stated in the documents (for example, the WG of OpenID 2.0-era
specs). Put corrections in `crawler/overrides.json`:

```json
{
  "openid-simple-registration-extension-1_0": { "status": "final", "note": "Approved 2006" },
  "oauth-v2-form-post-response-mode-1_0": { "workgroup": "AB/Connect" }
}
```

Allowed fields: `title`, `workgroup`, `status`, `note`, and `renamed_to` (merge a spec
renamed without a redirect page into its successor). Keys can be a current or former name. Overridden fields are listed in
the detail panel so it is always clear what came from the document and what did not.

## Source fixes report

Every crawl also writes `reports/source-fixes.md`
([latest](https://github.com/sakimura/openid-specs-dashboard/blob/reports/reports/source-fixes.md)): metadata
errors in the published documents themselves, for spec editors to fix at the source —
wrong or missing working group, inconsistent WG names, renames missing a redirect page,
probable author-name typos. An entry disappears once a corrected revision is published;
the matching override can then be removed. The report reflects the documents before any
override is applied.

## Design

Colors, type and components follow the OpenID Foundation design system
(`OIDF_Slide_Design_System.md`, 1 Nov 2026): one orange hue plus warm neutrals, light only,
Arial. Orange is never used for text on white. In charts and chips, orange means a spec has
reached Final; greys mean it has not. The OpenID logo (`public/img/openid-logo.webp`) sits
top left and links to openid.net. The slide design system places it top right; on a web page
top left follows the usual site convention.

## Hosting on GitHub Pages (current prototype)

`.github/workflows/pages.yml` runs the parser tests and the crawler daily (03:17 UTC),
on every push to `main`, and on demand (Actions → Run workflow). It then deploys
`public/` to GitHub Pages. When the source-fixes report changes, the workflow commits
it to the `reports` branch, which holds only the report, so that branch's history shows
what has been fixed. `public/data/` and `reports/` are generated and not committed on
`main`; run the crawler before previewing locally.

`main` is protected by the "Protect main" ruleset (active since 2 Nov 2026):
- changes arrive only through pull requests (no approval is required, so a maintainer
  can merge their own);
- the `build` check (tests and a trial crawl), reported by GitHub Actions, must pass
  before merging;
- force pushes and deleting the branch are blocked;
- nobody can bypass these rules, repository admins included.

## Sitemap for search engines

Every crawl also writes `public/sitemap-specs.xml`: one URL per live spec, the page a
search engine should send people to. That is the spec's unversioned URL (e.g.
`openid-connect-core-1_0.html`), which openid.net points at the latest approved document,
or at the latest draft when nothing has been approved. A spec without an unversioned URL
gets its latest approved document, else its latest draft. Numbered drafts, superseded
Implementer's Drafts and obsolete specs are left out. `<lastmod>` is the date the file last
changed in the directory listing.

The current `https://openid.net/addl-sitemap.xml` lists only the `/specs` directory and the
specs page, so crawlers see all ~2,600 files as equals. To use this one:

1. Serve it from openid.net, e.g. as `https://openid.net/specs/sitemap-specs.xml`. A sitemap
   may only list URLs on its own host, unless that host's `robots.txt` points to it.
2. Add `Sitemap: https://openid.net/specs/sitemap-specs.xml` to `robots.txt`, or submit it
   in Google Search Console and Bing Webmaster Tools.

A sitemap says what to crawl, not which page to prefer. To stop numbered revisions from
competing with the approved text, openid.net would also send
`Link: <https://openid.net/specs/…-1_0.html>; rel="canonical"` on each numbered revision.
That is a server setting; the published documents stay unchanged.

## Security

The crawler and the page treat everything from openid.net/specs as untrusted input.

- **Crawler:** filenames must be plain basenames (`[A-Za-z0-9][A-Za-z0-9._-]*`, which every
  real spec filename matches); anything else is skipped. Cache writes are confined to the
  cache directory and never follow symlinks. Fetches go only to `https://openid.net`,
  including redirects. Limits: 8 MB for the listing, 16 MB per document, 20,000 listing
  entries, and 5,000 downloads or 1 GB per run. Cache files are written through new
  temporary files and read without following symlinks.
- **The crawl fails, and writes nothing, when** more than 5% of downloads fail, fewer
  than 50 specs come out, or specs or revisions drop by more than 10% since the last good
  build (`.cache/specs/.last-good.json`), or more of that build's spec names or revision
  files disappear than 2% of them or 3, whichever is larger. The floor of 3 lets a small
  set lose one or two items (a withdrawn draft) without failing. A failed run deploys nothing, so the last good
  site stays up.
- **Page:** `specs.json` is checked on load. Only known fields are copied into fresh
  objects. File names, formats, dates, statuses and severities must match expected values,
  or the item is dropped, as is a spec with no usable revision. Values from the documents
  (such as WG names) are never used as object keys. Text is HTML-escaped, and URL parts
  are percent-encoded. URL-hash parameters are checked against allowed values.
- **CSV export:** a cell that starts with `= + - @`, their full-width forms, whitespace or a
  control character gets a leading `'`, and line breaks become spaces. In LibreOffice no
  such cell imports as a formula. Excel hasn't been tested. The `'` shows in the cell; that
  is the price of keeping the cell inert.
  A Content-Security-Policy meta tag allows only same-origin scripts, styles and data.
  `frame-ancestors` needs an HTTP header, which GitHub Pages cannot set; add it on openid.net.
- **CI:** the workflow is read-only by default. The crawl job cannot push or deploy, the
  `report` job only commits the Markdown report, and only `deploy` can publish Pages.
  Actions are pinned to commit SHAs. Pull requests run the tests and a trial crawl,
  but deploy nothing.

## Deploying on openid.net

1. Schedule the crawler (e.g. hourly cron) on the host, writing into the web root:
   `python3 crawler/build_data.py --out /var/www/openid.net/specs-dashboard/data/specs.json`
2. Serve `public/` at a path such as `/specs-dashboard/`. All asset paths are relative.
3. Alternatively, run the crawler in CI and publish `public/` as static files.

## Tests

```bash
python3 -m unittest discover -s crawler
```

```bash
node --test tests/*.test.mjs
```

The second runs `public/app.js` under Node against hostile data: prototype keys,
bad statuses, unsafe file names and URLs, malformed records and CSV formula cells.

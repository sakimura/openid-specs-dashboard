# OpenID Specifications Dashboard (prototype)

A dashboard of every specification published at <https://openid.net/specs/>:
current maturity (Draft → Implementer's Draft → Final → Errata), the current edition,
the latest revision, the working group, the editors, and the full revision history.

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
- **Status** is the highest maturity reached. The "current edition" is the latest
  errata, else Final, else Implementer's Draft. A spec is flagged *in progress* when
  drafts have been published after that edition (e.g. errata work after a Final).
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

Every crawl also writes [`reports/source-fixes.md`](reports/source-fixes.md): metadata
errors in the published documents themselves, for spec editors to fix at the source —
wrong or missing working group, inconsistent WG names, renames missing a redirect page,
probable author-name typos. An entry disappears once a corrected revision is published;
the matching override can then be removed. The report reflects the documents before any
override is applied.

## Design

Colors, type and components follow the OpenID Foundation design system
(`OIDF_Slide_Design_System.md`, 1 Nov 2026): one orange hue plus warm neutrals, light only,
Arial. Orange is never used for text on white. In charts and chips, orange means a spec has
reached Final; greys mean it has not. The OIDF logo is not included yet; the design system
places it top right.

## Hosting on GitHub Pages (current prototype)

`.github/workflows/pages.yml` runs the parser tests and the crawler daily (03:17 UTC),
on every push to `main`, and on demand (Actions → Run workflow). It then deploys
`public/` to GitHub Pages. When the source-fixes report changes, the workflow commits
it back to the repository, so its history shows what has been fixed.
`public/data/` is generated and is not committed; run the crawler before previewing locally.

## Deploying on openid.net

1. Schedule the crawler (e.g. hourly cron) on the host, writing into the web root:
   `python3 crawler/build_data.py --out /var/www/openid.net/specs-dashboard/data/specs.json`
2. Serve `public/` at a path such as `/specs-dashboard/`. All asset paths are relative.
3. Alternatively, run the crawler in CI and publish `public/` as static files.

## Tests

```bash
python3 -m unittest discover -s crawler
```

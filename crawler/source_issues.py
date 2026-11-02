"""Find metadata errors in the published spec documents themselves.

These are problems to fix in the spec sources (the xml/md the editors maintain),
not in this dashboard. The report is regenerated on every crawl, so an entry
disappears once a corrected revision is published.
"""
import collections
import difflib
import re

from build_data import canonical_wg

# Filename families whose owning WG is unambiguous. Weak prefixes such as
# "openid-connect-" are deliberately absent: Connect-named specs live in several WGs.
FAMILY_OWNER = [
    ("fapi-", "FAPI"),
    ("openid-financial-api-", "FAPI"),
    ("openid-4-verifiable-", "Digital Credentials Protocols"),
    ("openid4vc-", "Digital Credentials Protocols"),
    ("openid-connect-4-ida-", "eKYC & IDA"),
    ("openid-connect-4-identity-assurance-", "eKYC & IDA"),
    ("openid-ida-", "eKYC & IDA"),
    ("openid-connect-modrna-", "MODRNA"),
    ("openid-connect-eap-", "EAP"),
    ("openid-igov-", "iGov"),
    ("openid-heart-", "HEART"),
    ("openid-caep-", "Shared Signals"),
    ("openid-risc-", "Shared Signals"),
    ("openid-sse-", "Shared Signals"),
    ("openid-sharedsignals-", "Shared Signals"),
    ("ipsie-", "IPSIE"),
    ("fastfed-", "FastFed"),
    ("authorization-api-", "AuthZEN"),
]

SEVERITY_ORDER = {"error": 0, "check": 1, "rename": 2, "stub": 3, "missing": 4, "naming": 5, "other": 6,
                  "historical": 7}
# A spec whose latest revision predates this is treated as historical: worth knowing,
# but nobody is expected to republish it just to add metadata.
ACTIVE_SINCE = "2021-01-01"


def family_owner(key):
    for prefix, wg in FAMILY_OWNER:
        if key.startswith(prefix):
            return wg
    return None


def _d(r):
    return r["date"] or r["listed"] or ""


def find_issues(specs):
    """Return a list of issue dicts and attach a per-spec summary as spec["issues"]."""
    issues = []
    live = [s for s in specs if not s.get("redirect")]

    # When did each WG first label a document? A label for another WG after the
    # owner WG was already in use is a slip, not a hand-over.
    first_seen = {}
    for s in specs:
        for r in s["revisions"]:
            wg = canonical_wg(r["workgroup"])
            if wg and r["date"] and (wg not in first_seen or r["date"] < first_seen[wg][0]):
                first_seen[wg] = (r["date"], r["file"])

    for s in specs:
        stated = [(r, canonical_wg(r["workgroup"])) for r in s["revisions"] if canonical_wg(r["workgroup"])]
        owner = family_owner(s["key"]) or (stated[-1][1] if stated else None)
        if not owner:
            continue
        seen = first_seen.get(owner)
        # Judge each revision by its own date, then group consecutive ones into ranges.
        wrong = [(r, (wg, "error" if seen and _d(r) >= seen[0] else "check"))
                 for r, wg in stated if wg != owner]
        if not wrong:
            continue
        for (wg, severity), group in _runs(wrong):
            slip = severity == "error"
            files = [r["file"] for r, _ in group]
            issues.append({
                "severity": severity,
                "category": "Working group",
                "key": s["key"],
                "title": s["title"],
                "files": files,
                "found": ", ".join(sorted({r["workgroup"] for r, _ in group})),
                "expected": owner,
                "detail": (
                    "States %s, but the %s WG was already labelling documents (first: %s, %s)."
                    % (wg, owner, seen[1], seen[0]) if slip else
                    "States %s before any document named the %s WG. Probably developed there "
                    "before a hand-over; confirm and leave as-is if so." % (wg, owner)),
                "current": s["latest"] in files or (s["milestone"] in files),
            })

    for s in live:
        latest = next((r for r in s["revisions"] if r["file"] == s["latest"]), None)
        if latest and not latest["workgroup"]:
            active = _d(latest) >= ACTIVE_SINCE
            issues.append({
                "severity": "missing" if active else "historical", "category": "Working group", "key": s["key"], "title": s["title"],
                "files": [latest["file"]], "found": "(none)",
                "expected": s["workgroup"] or "?",
                "detail": "No workgroup in the document header, IANA Change Controller, or WG list address."
                + (" Dashboard infers %s." % s["workgroup"] if s["workgroup"] else ""),
                "current": True,
            })

    # Spellings of the same WG in the latest approved document of each live spec, or the
    # latest draft if none has been approved.
    spellings = collections.defaultdict(lambda: collections.defaultdict(list))
    for s in live:
        rev = next((r for r in s["revisions"] if r["file"] == (s["milestone"] or s["latest"])), None)
        if rev and canonical_wg(rev["workgroup"]) and rev.get("workgroup_from") == "header":
            spellings[canonical_wg(rev["workgroup"])][rev["workgroup"]].append(rev["file"])
    for wg, forms in sorted(spellings.items()):
        if len(forms) > 1:
            for form, files in sorted(forms.items(), key=lambda kv: -len(kv[1])):
                issues.append({
                    "severity": "naming", "category": "Working group name", "key": wg, "title": None,
                    "files": sorted(files), "found": form, "expected": "one agreed name for %s" % wg,
                    "detail": "%d spelling(s) of this WG are in use: %s."
                    % (len(forms), "; ".join('"%s"' % f for f in forms)),
                    "current": True,
                })

    for s in live:
        for r in s["revisions"]:
            if not r["date"] and r["file"] in (s["latest"], s["milestone"]):
                issues.append({
                    "severity": "other", "category": "Date", "key": s["key"], "title": s["title"],
                    "files": [r["file"]], "found": "(none)", "expected": "publication date",
                    "detail": "No date in the document; the directory listing date (%s) is shown." % r["listed"],
                    "current": True,
                })

    issues.extend(_name_typos(specs))
    issues.extend(_renames(specs))

    by_key = collections.defaultdict(list)
    for i in issues:
        by_key[i["key"]].append(i)
    for s in specs:
        if by_key.get(s["key"]):
            s["issues"] = [{k: i[k] for k in ("severity", "category", "files", "found", "expected", "detail")}
                           for i in by_key[s["key"]]]
    issues.sort(key=lambda i: (SEVERITY_ORDER[i["severity"]], i["category"], i["key"]))
    return issues


def _runs(items):
    run, prev = [], None
    for r, wg in items:
        if run and wg != prev:
            yield prev, run
            run = []
        run.append((r, wg))
        prev = wg
    if run:
        yield prev, run


def _first_wg(s):
    for r in s["revisions"]:
        if canonical_wg(r["workgroup"]):
            return canonical_wg(r["workgroup"])
    return s["workgroup"]


def _numbers(t):
    return re.findall(r"\d+", t or "")


def _renames(specs):
    """Renames the dashboard could not tie together from published evidence, and
    renames it did tie together only by identical titles (no redirect stub)."""
    out = []
    live = [s for s in specs if not s.get("redirect") and s["revisions"]]
    first = lambda s: min(_d(r) for r in s["revisions"])
    last = lambda s: max(_d(r) for r in s["revisions"])
    # Drop qualifiers that renames typically remove ("Financial-grade API: ", "Connect", "and Events").
    norm = lambda t: re.sub(r"^[^:]{0,40}:\s*|\bconnect\b|\band events\b|\bmodrna\b|[^a-z0-9 ]", " ",
                            (t or "").lower()).split()
    for a in live:
        best = None
        for b in live:
            # b must start after a stops, and soon after (a rename, not a later unrelated spec).
            if a is b or not a["title"] or not b["title"] or not last(a) < first(b) \
                    or int(first(b)[:4]) - int(last(a)[:4]) > 4:
                continue
            na, nb = _numbers(a["title"]), _numbers(b["title"])
            if na != nb and not ({tuple(na), tuple(nb)} <= {(), ("1", "0")}):
                continue  # different versions (UMA vs UMA 2, 1.1 vs 2.0) are different specs
            wa, wb = a["workgroup"], _first_wg(b)
            if wa and wb and wa != wb:
                continue  # a rename keeps its WG at the moment of renaming
            ta = " ".join(w for w in norm(a["title"]) if not w.isdigit())
            tb = " ".join(w for w in norm(b["title"]) if not w.isdigit())
            ratio = difflib.SequenceMatcher(None, ta, tb).ratio()
            if ratio >= 0.85 and (best is None or ratio > best[0]):
                best = (ratio, b)
        if best:
            b = best[1]
            out.append({
                "severity": "rename", "category": "Rename", "key": a["key"], "title": a["title"],
                "files": [a["latest"]], "found": a["title"], "expected": "%s (`%s`)" % (b["title"], b["key"]),
                "detail": "Last revised %s; the other spec starts %s with a near-identical title. If it is the same "
                          "spec, add `\"renamed_to\": \"%s\"` in overrides.json and a redirect stub at "
                          "https://openid.net/specs/%s.html." % (last(a), first(b), b["key"], a["key"]),
                "current": True,
            })
    for s in specs:
        for f in s.get("former_names", []):
            if f["how"] in ("same title in documents", "curated (overrides.json)") and f.get("old_url_live"):
                out.append({
                    "severity": "stub", "category": "Redirect", "key": s["key"], "title": s["title"],
                    "files": [f["key"]], "found": "no redirect stub", "expected": "redirect to %s" % s["key"],
                    "detail": "Merged into %s (%s). Add a \"Renamed "
                              "Specification\" stub at https://openid.net/specs/%s.html." % (s["key"], f["how"], f["key"]),
                    "current": False,
                })
    return out


def _name_typos(specs):
    """Rare author spellings one edit away from a common one with the same initial."""
    counts = collections.Counter()
    where = collections.defaultdict(list)
    for s in specs:
        for r in s["revisions"]:
            for a in r["authors"]:
                counts[a["name"]] += 1
                where[a["name"]].append((s, r))
    common = [n for n, c in counts.items() if c >= 5]
    out = []
    for name, c in counts.items():
        if c > 2:
            continue
        for good in common:
            if good != name and good[:1] == name[:1] and good.split()[-1] != name.split()[-1] \
                    and difflib.SequenceMatcher(None, name, good).ratio() > 0.9:
                for s, r in where[name]:
                    out.append({
                        "severity": "other", "category": "Author name", "key": s["key"], "title": s["title"],
                        "files": [r["file"]], "found": name, "expected": good,
                        "detail": '"%s" appears %d time(s); "%s" appears %d times.' % (name, c, good, counts[good]),
                        "current": r["file"] in (s["latest"], s["milestone"]),
                    })
                break
    return out


HEADINGS = {
    "error": ("Wrong working group (fix in source)",
              "The document names a WG other than the one that owns the spec, at a time when the owning WG "
              "was already in use. Almost always a copied template."),
    "check": ("Working group changed during the spec's history (confirm)",
              "Earlier revisions name another WG before the owning WG appears anywhere in the corpus. "
              "Usually a real hand-over between WGs; no fix needed if so."),
    "rename": ("Possible renames without a redirect stub (confirm)",
               "Not merged in the dashboard: the only evidence is a near-identical title in consecutive "
               "specs. Confirm each, then add `renamed_to` in `crawler/overrides.json` and a redirect stub "
               "on openid.net."),
    "stub": ("Renames missing a redirect stub (add on openid.net)",
             "Merged in the dashboard because the documents carry the same title, but the old URL has no "
             "\"Renamed Specification\" page pointing to the new one."),
    "missing": ("Working group not stated — active specs (add to source)",
                "Latest revision is %s or later and has no workgroup field. Add `workgroup` to the xml2rfc front matter "
                "(or `<dd class=\"workgroup\">`)." % ACTIVE_SINCE[:4]),
    "naming": ("Inconsistent working group names (harmonise)",
               "The same WG is spelled differently in the `workgroup` header field across specs (each spec's latest "
               "approved document, or its latest draft if none has been approved). "
               "(IANA \"Change Controller\" entries are not listed: those record the registrant.)"),
    "other": ("Other metadata", "Dates missing from documents and probable author-name typos."),
    "historical": ("Working group not stated — historical specs (low priority)",
                   "Last revised before %s. Listed for completeness; fix only if the spec is republished." % ACTIVE_SINCE[:4]),
}


def render_markdown(issues, generated, overrides):
    lines = [
        "# Spec source metadata to fix",
        "",
        "Generated %s by `crawler/build_data.py` from https://openid.net/specs/. "
        "Regenerated on every crawl; an entry disappears once a corrected revision is published." % generated,
        "",
        "Until a fix is published, the dashboard uses `crawler/overrides.json`. "
        "Specs with an override are marked **(overridden)** below.",
        "",
        "| Section | Count |",
        "|---|---|",
    ]
    for sev, (head, _) in HEADINGS.items():
        n = sum(1 for i in issues if i["severity"] == sev)
        if n:
            lines.append("| [%s](#%s) | %d |" % (head, _anchor(head), n))
    for sev, (head, blurb) in HEADINGS.items():
        rows = [i for i in issues if i["severity"] == sev]
        if not rows:
            continue
        lines += ["", "## " + head, "", blurb, ""]
        if sev == "naming":
            lines += ["| WG | Spelling in document | Used by |", "|---|---|---|"]
            for i in rows:
                lines.append("| %s | `%s` | %s |" % (i["key"], i["found"], ", ".join("`%s`" % f for f in i["files"])))
            continue
        lines += ["| Spec | Revision(s) | Document says | Should be | Notes |", "|---|---|---|---|---|"]
        for i in rows:
            name = "%s<br>`%s`" % (i["title"] or i["key"], i["key"])
            if i["key"] in overrides:
                name += " **(overridden)**"
            files = _files(i["files"])
            note = i["detail"] + (" Affects the latest approved document, or the latest draft if none has been approved." if i.get("current") and sev in ("error", "check") else "")
            lines.append("| %s | %s | %s | %s | %s |" % (name, files, i["found"], i["expected"], note))
    lines.append("")
    return "\n".join(lines)


def _files(files):
    if len(files) <= 3:
        return "<br>".join("[`%s`](https://openid.net/specs/%s.html)" % (f, f) for f in files)
    return "[`%s`](https://openid.net/specs/%s.html) … [`%s`](https://openid.net/specs/%s.html) (%d revisions)" % (
        files[0], files[0], files[-1], files[-1], len(files))


def _anchor(h):
    return re.sub(r"[^a-z0-9 -]", "", h.lower()).replace(" ", "-")

#!/usr/bin/env python3
"""Crawl https://openid.net/specs/ and build the dashboard data file.

Standard library only (Python 3.9+), so it can run from cron on the
openid.net host without a virtualenv.

    python3 crawler/build_data.py                 # fetch + build
    python3 crawler/build_data.py --offline       # rebuild from cache only

Every metadata field (title, date, authors, working group) is read from the
document itself. The filename is used only to identify the spec and the
revision (NN / IDn / final / erratan); it is never used as a title.
"""
import argparse
import concurrent.futures
import datetime as dt
import html
import json
import os
import re
import sys
import tempfile
import threading
import urllib.parse
import urllib.request

BASE_URL = "https://openid.net/specs/"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CACHE = os.path.join(ROOT, ".cache", "specs")
DEFAULT_OUT = os.path.join(ROOT, "public", "data", "specs.json")
DEFAULT_OVERRIDES = os.path.join(ROOT, "crawler", "overrides.json")
DEFAULT_REPORT = os.path.join(ROOT, "reports", "source-fixes.md")
USER_AGENT = "OIDF-Specs-Dashboard/0.1 (+https://openid.net/specs/)"

# ---------------------------------------------------------------------------
# Directory listing
# ---------------------------------------------------------------------------

LISTING_ROW = re.compile(
    r'<a href="([^"?/][^"]*)">[^<]*</a></td><td align="right">\s*([\d-]+ [\d:]+)\s*</td>'
    r'<td align="right">\s*([^<]*?)\s*</td>'
)


# The listing and the documents are untrusted input: names become cache paths and
# links in the dashboard, so only plain basenames are accepted (every real spec
# filename matches), and fetches are capped and pinned to openid.net over HTTPS.
SAFE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,199}")
ALLOWED_HOST = urllib.parse.urlsplit(BASE_URL).hostname
MAX_LISTING_BYTES = 8 << 20
MAX_DOC_BYTES = 16 << 20
MAX_LISTING_ENTRIES = 20000
MAX_DOWNLOADS = 5000            # documents fetched in one run
MAX_TOTAL_BYTES = 1 << 30       # bytes downloaded in one run
MAX_FAILURE_RATIO = 0.05        # failed downloads, as a share of those attempted
MIN_SPECS = 50                  # fewer means the listing or parser broke
MIN_SHARE_OF_LAST_GOOD = 0.9    # specs and revisions, compared with the last good build


class FetchError(Exception):
    pass


def _allowed_url(url):
    u = urllib.parse.urlsplit(url)
    return u.scheme == "https" and u.hostname == ALLOWED_HOST and u.port in (None, 443)


class _SameHostRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not _allowed_url(newurl):
            raise FetchError("redirect to %s refused" % newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_opener = urllib.request.build_opener(_SameHostRedirects)


def http_get(url, timeout=60, max_bytes=MAX_DOC_BYTES):
    if not _allowed_url(url):
        raise FetchError("refusing to fetch %s" % url)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with _opener.open(req, timeout=timeout) as resp:
        data = resp.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise FetchError("%s is larger than %d bytes" % (url, max_bytes))
    return data


def safe_name(name):
    return bool(SAFE_NAME.fullmatch(name))


def parse_listing(text):
    """Return {filename: {"modified": iso, "size": str}} from an Apache index."""
    files = {}
    for name, modified, size in LISTING_ROW.findall(text):
        name = urllib.parse.unquote(html.unescape(name))
        if not safe_name(name):
            print("  ! skipping unexpected filename %r" % name, file=sys.stderr)
            continue
        files[name] = {"modified": modified.replace(" ", "T"), "size": size}
        if len(files) > MAX_LISTING_ENTRIES:
            raise FetchError("listing has more than %d entries" % MAX_LISTING_ENTRIES)
    return files


# ---------------------------------------------------------------------------
# Filename -> (spec key, revision)
# ---------------------------------------------------------------------------

FORMATS = ("html", "txt", "xml", "md", "pdf")

# Suffix grammar from the OpenID naming convention, most specific first.
REVISION_PATTERNS = [
    ("errata", re.compile(r"^(?P<key>.+?)-errata(?P<n>\d+)$")),
    ("final", re.compile(r"^(?P<key>.+?)-final$")),
    ("implementers", re.compile(r"^(?P<key>.+?)-ID(?P<n>\d+)$")),
    # Older FAPI "working draft" numbering, e.g. openid-financial-api-ciba-wd-02
    ("draft", re.compile(r"^(?P<key>.+?)-wd-(?P<n>\d+)$")),
    # IETF-style individual drafts hosted here, e.g. draft-jones-json-web-token-07
    ("draft", re.compile(r"^(?P<key>draft-.+?)-(?P<n>\d{2})$")),
    # Snapshot dated drafts, e.g. openid-heart-oauth2-1_0-2017-05-31
    ("draft", re.compile(r"^(?P<key>.+?)-(?P<n>\d{4}-\d{2}-\d{2})$")),
    ("draft", re.compile(r"^(?P<key>.+?)-(?P<n>\d{2})$")),
]

KIND_LABEL = {
    "draft": "Draft",
    "implementers": "Implementer's Draft",
    "final": "Final",
    "errata": "Errata",
}
# Higher = more mature. Errata is a corrected Final.
KIND_RANK = {"draft": 1, "implementers": 2, "final": 3, "errata": 4}


def classify(stem):
    """Split a filename stem into (spec key, kind, number) or None for aliases."""
    for kind, rx in REVISION_PATTERNS:
        m = rx.match(stem)
        if m:
            return m.group("key"), kind, m.groupdict().get("n")
    return None


def revision_label(kind, n):
    if kind == "draft":
        return "Draft " + n if n else "Draft"
    if kind == "implementers":
        return "Implementer's Draft " + n
    if kind == "errata":
        return "Final, Errata Set " + n
    return "Final"


# ---------------------------------------------------------------------------
# Document parsing
# ---------------------------------------------------------------------------

TAG = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")


def text_of(fragment):
    return WS.sub(" ", html.unescape(TAG.sub(" ", fragment))).strip()


MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"], 1)}
MONTHS.update({k[:3]: v for k, v in list(MONTHS.items())})


def parse_date(s):
    """Parse the date formats seen across xml2rfc v1/v2/v3 and pandoc output."""
    if not s:
        return None
    s = s.replace("\xa0", " ").strip()
    m = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", s)
    if m:
        return _iso(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    # "February 25, 2014" / "May 2 2017"
    m = re.search(r"([A-Za-z]{3,9})\.?\s+(\d{1,2}),?\s+(\d{4})", s)
    if m and m.group(1).lower() in MONTHS:
        return _iso(int(m.group(3)), MONTHS[m.group(1).lower()], int(m.group(2)))
    # "9 July 2025"
    m = re.search(r"(\d{1,2})\s+([A-Za-z]{3,9})\.?,?\s+(\d{4})", s)
    if m and m.group(2).lower() in MONTHS:
        return _iso(int(m.group(3)), MONTHS[m.group(2).lower()], int(m.group(1)))
    # "October 2013"
    m = re.search(r"([A-Za-z]{3,9})\.?,?\s+(\d{4})", s)
    if m and m.group(1).lower() in MONTHS:
        return _iso(int(m.group(2)), MONTHS[m.group(1).lower()], None)
    return None


def _iso(y, mo, d):
    try:
        if d is None:
            dt.date(y, mo, 1)
            return "%04d-%02d" % (y, mo)
        return dt.date(y, mo, d).isoformat()
    except ValueError:
        return None


# Things that show up in xml2rfc header cells but are not people.
NOT_AUTHOR = re.compile(
    r"^(draft|final|implementor'?s draft|implementer'?s draft|pre-draft|internet-draft|"
    r"network working group|intended status|expires|obsoletes|updates|category|issn|"
    r"published|status|workgroup|[a-z]+ \d{1,2}, \d{4}|\d{1,2} [a-z]+ \d{4}|"
    r"[a-z]+ \d{4}|\d{4}-\d{2}-\d{2}|draft-\d+)",
    re.I,
)


def looks_like_date(s):
    return parse_date(s) is not None and len(s) < 30


REDIRECT = re.compile(r'<meta[^>]+http-equiv="?refresh"?[^>]*>', re.I)


def parse_document(raw):
    """Extract metadata from one spec HTML file. Returns a dict."""
    t = raw
    out = {"title": None, "date": None, "authors": [], "workgroup": None,
           "doc_status": None, "redirect": None, "generator": None}

    m = re.search(r'name="generator"\s+content="([^"]*)"|content="([^"]*)"\s+name="generator"', t, re.I)
    if m:
        out["generator"] = m.group(1) or m.group(2)

    # Redirect / tombstone pages ("Renamed Specification", "Obsolete Specification").
    body_len = len(TAG.sub("", t[t.find("<body"):] if "<body" in t else t))
    if REDIRECT.search(t) and body_len < 2500:
        h = re.search(r"<h2>(.*?)</h2>", t, re.S | re.I)
        out["redirect"] = {
            "reason": text_of(h.group(1)) if h else "Redirect",
            "target": None,
            "message": text_of(re.search(r"<body[^>]*>(.*)</body>", t, re.S | re.I).group(1))
            if re.search(r"<body", t, re.I) else None,
        }
        a = re.search(r'<a\s+href="([^"]+)"', t[t.find("<body"):], re.I)
        if a:
            out["redirect"]["target"] = a.group(1).rsplit("/", 1)[-1]
        return out

    v3 = re.search(r'<dl id="identifiers">(.*?)</dl>', t, re.S)
    if v3 and 'class="author' in v3.group(1) or (v3 and 'class="workgroup"' in v3.group(1)):
        _parse_v3(t, v3.group(1), out)
    elif re.search(r'<table summary="layout"', t) and 'class="header"' in t:
        _parse_v1(t, out)
    elif re.search(r'<table class="header">', t):
        _parse_v2(t, out)
    elif re.search(r'<div id="rfc.title">', t):
        _parse_greenbytes(t, out)
    elif "Word.Document" in t[:2000]:
        _parse_word(t, out)

    if not out["title"]:
        m = re.search(r'<h1[^>]*id="title"[^>]*>(.*?)</h1>', t, re.S) or \
            re.search(r"<title>(.*?)</title>", t, re.S | re.I) or \
            re.search(r'<p class=MsoTitle[^>]*>(.*?)</p>', t, re.S | re.I) or \
            re.search(r"<h1[^>]*>(.*?)</h1>", t, re.S | re.I)
        if m:
            out["title"] = text_of(m.group(1))

    if out["workgroup"]:
        out["workgroup_from"] = "header"
    else:
        out["workgroup"] = _workgroup_from_text(t)
        if out["workgroup"]:
            out["workgroup_from"] = "mailing-list" if "@" in out["workgroup"] else "change-controller"
    return out


def _parse_v3(t, dl, out):
    m = re.search(r'<dd class="workgroup">(.*?)</dd>', dl, re.S)
    if m:
        out["workgroup"] = text_of(m.group(1))
    m = re.search(r'<time datetime="([^"]+)"', dl) or \
        re.search(r'<dd class="published">(.*?)</dd>', dl, re.S)
    if m:
        out["date"] = parse_date(text_of(m.group(1)))
    m = re.search(r'<dd class="(?:intended-)?status">(.*?)</dd>', dl, re.S)
    if m:
        out["doc_status"] = text_of(m.group(1))
    # Full author names from <meta name="author"> when present; else the dl.
    metas = re.findall(r'<meta content="([^"]+)" name="author"', t) + \
        re.findall(r'<meta name="author" content="([^"]+)"', t)
    orgs = [text_of(o) for o in re.findall(
        r'<div class="author">.*?(?:<div class="org">(.*?)</div>|</div>\s*</div>)', dl, re.S)]
    names = [text_of(n) for n in re.findall(r'<div class="author-name">(.*?)</div>', dl, re.S)]
    if metas and len(metas) == len(names):
        names = [html.unescape(x) for x in metas]
    elif metas and not names:
        names = [html.unescape(x) for x in metas]
    out["authors"] = [{"name": n, "org": (orgs[i] if i < len(orgs) else "") or None}
                      for i, n in enumerate(names)]
    m = re.search(r'<h1 id="title">(.*?)</h1>', t, re.S)
    if m:
        out["title"] = text_of(m.group(1))


def _parse_v1(t, out):
    rows = re.findall(r'<tr><td class="header">(.*?)</td><td class="header">(.*?)</td></tr>', t, re.S)
    left = [text_of(a) for a, _ in rows]
    right = [text_of(b) for _, b in rows]
    for cell in left:
        if cell and not NOT_AUTHOR.match(cell) and "working group" in cell.lower():
            out["workgroup"] = cell
    for cell in left:
        if cell and re.match(r"(draft|final|implement|pre-draft)", cell, re.I):
            out["doc_status"] = cell
            break
    # Right column: Name / Org / Name / Org ... / Date
    cells = [c for c in right if c]
    if cells and looks_like_date(cells[-1]):
        out["date"] = parse_date(cells.pop())
    out["authors"] = _pair_authors(cells)
    _full_names(t, out)
    m = re.search(r"<h1>(.*?)</h1>", t, re.S)
    if m:
        title = re.sub(r"<span class=\"filename\">.*?</span>", "", m.group(1), flags=re.S)
        out["title"] = text_of(title)


def _parse_v2(t, out):
    head = re.search(r'<table class="header">(.*?)</table>', t, re.S).group(1)
    left = [text_of(x) for x in re.findall(r'<td class="left">(.*?)</td>', head, re.S)]
    right = [text_of(x) for x in re.findall(r'<td class="right">(.*?)</td>', head, re.S)]
    for cell in left:
        if cell and "working group" in cell.lower():
            out["workgroup"] = cell
    cells = [c for c in right if c]
    if cells and looks_like_date(cells[-1]):
        out["date"] = parse_date(cells.pop())
    out["authors"] = _pair_authors(cells)
    m = re.search(r'<p class="title">(.*?)(?:<br\s*/?>|<span)', t, re.S)
    if m:
        out["title"] = text_of(m.group(1))
    # Full names from <meta name="author">/<link rel="author"> or the vCards.
    _upgrade_names(t, out)
    _full_names(t, out)


def _parse_greenbytes(t, out):
    m = re.search(r'<div id="rfc.title"><h1>(.*?)</h1>', t, re.S)
    if m:
        out["title"] = text_of(m.group(1))
    out["authors"] = [
        {"name": text_of(n), "org": text_of(o) or None}
        for n, o in re.findall(
            r'<div class="author-name">(.*?)</div>(?:<div class="org">(.*?)</div>)?', t, re.S)]
    m = re.search(r"<dt>Published</dt><dd>(.*?)</dd>", t, re.S)
    if m:
        out["date"] = parse_date(text_of(m.group(1)))


def _parse_word(t, out):
    """Word-exported HTML (Yadis): 'Title  Date  Name, editor' at the top of the body."""
    body = text_of(t[t.find("<body"):])[:400]
    m = re.match(r"(.+?)\s+(\d{1,2} [A-Z][a-z]+ \d{4}|[A-Z][a-z]+ \d{1,2}, \d{4})\s+(.+?), editor", body)
    if m:
        out["title"], out["date"] = m.group(1), parse_date(m.group(2))
        out["authors"] = [{"name": m.group(3), "org": None, "role": "editor"}]


def _pair_authors(cells):
    """xml2rfc header right column alternates Name, Org (org may be absent)."""
    merged = []
    for c in cells:
        # Long org names wrap onto a second header row: "Foo (was at" / "Bar)".
        if merged and merged[-1].count("(") > merged[-1].count(")"):
            merged[-1] += " " + c
        elif "@" not in c:
            merged.append(c)
    cells = merged
    people = []
    i = 0
    initial = re.compile(r"^([A-Z][a-z]?\.[ -]?)+\s*\S|^[A-Z][a-z]+ [A-Z][a-z'-]+$")
    while i < len(cells):
        c = cells[i]
        if NOT_AUTHOR.match(c):
            i += 1
            continue
        org = None
        if i + 1 < len(cells) and not initial.match(cells[i + 1]) and not NOT_AUTHOR.match(cells[i + 1]):
            org = cells[i + 1]
            i += 1
        people.append({"name": c, "org": org})
        i += 1
    return people


def _full_names(t, out):
    """Header rows carry initials ("N. Sakimura"); the Authors' Addresses section
    (v1 table / v2 vCard) carries the full name. Match them up by surname."""
    cands = [text_of(x) for x in re.findall(r'<span class="fn">(.*?)</span>', t, re.S)]
    i = t.find("Authors' Addresses</h3>")
    if i < 0:
        i = t.find("Author's Address</h3>")
    if i >= 0:
        block = t[i:i + 20000]
        # First author-text row of each address block is the person's name.
        for chunk in re.split(r'<tr cellpadding="3">|</table>', block):
            m = re.search(r'<td class="author-text">(?!&nbsp;)(.*?)</td>', chunk, re.S)
            if m:
                cands.append(text_of(m.group(1)))
    for a in out["authors"]:
        if a["name"].endswith(", Ed."):
            a["name"], a["role"] = a["name"][:-5], "editor"
        short = a["name"]
        m = re.match(r"^((?:[A-Z][a-z]?\.[ -]?)+)\s*(.+)$", short)
        if not m:
            continue
        initials, surname = m.group(1).replace(" ", ""), m.group(2).strip()
        for c in cands:
            if c.endswith(" " + surname) and c[:1] == initials[:1]:
                a["name"] = c
                break


def _upgrade_names(t, out):
    metas = re.findall(r'<meta name="author" content="([^"]+)"', t) + \
        re.findall(r'<link rel="author" href="[^"]*" title="([^"]+)"', t)
    full = []
    for x in metas:
        for part in html.unescape(x).split(","):
            part = re.sub(r"\(.*?\)", "", part).strip()
            if part:
                full.append(part)
    if full and len(full) == len(out["authors"]):
        for a, n in zip(out["authors"], full):
            a["name"] = n


CHANGE_CONTROLLER = re.compile(
    r"Change [Cc]ontroller:\s*((?:OpenID Foundation\s+)?[^-–:¶]{2,80}?Working Group)")
MAILING_LIST = re.compile(r"openid-specs-([a-z0-9-]+)@")


def _workgroup_from_text(t):
    """Fallback for documents without a WG header field.

    Uses two signals that only appear when the document itself names its WG:
    IANA "Change Controller: OpenID Foundation X Working Group" entries, and the
    WG mailing list address (openid-specs-<wg>@lists.openid.net).
    """
    body = text_of(t)
    m = CHANGE_CONTROLLER.search(body)
    if m:
        return m.group(1).strip()
    lists = MAILING_LIST.findall(t)
    if lists:
        return "openid-specs-%s@lists.openid.net" % max(set(lists), key=lists.count)
    return None


# Normalize the many spellings found in documents to the current OIDF WG names.
# Order matters: first match wins.
WG_CANON = [
    (r"artifact binding|a/?b\b|connect|openid-specs-ab@", "AB/Connect"),
    (r"fapi|financial", "FAPI"),
    (r"ekyc|identity assurance", "eKYC & IDA"),
    (r"digital credentials", "Digital Credentials Protocols"),
    (r"shared signals|risc|\bsse\b", "Shared Signals"),
    (r"modrna|mobile profile", "MODRNA"),
    (r"eap|extended authentication|enhanced authentication", "EAP"),
    (r"igov", "iGov"),
    (r"heart", "HEART"),
    (r"authzen", "AuthZEN"),
    (r"ipsie", "IPSIE"),
    (r"fastfed", "FastFed"),
]
# Spec families whose documents never state a WG, keyed by filename prefix.
# Used only as a last resort and flagged as inferred in the output.
WG_BY_PREFIX = [
    ("fastfed-", "FastFed"),
    ("openid-heart-", "HEART"),
    ("openid-risc-", "Shared Signals"),
    ("openid-financial-api-", "FAPI"),
    ("fapi-", "FAPI"),
    ("openid-connect-modrna-", "MODRNA"),
    ("openid-igov-", "iGov"),
    ("openid-caep-", "Shared Signals"),
    ("openid-sse-", "Shared Signals"),
    ("openid-ida-", "eKYC & IDA"),
    ("openid-connect-", "AB/Connect"),
    ("openid-federation-", "AB/Connect"),
]


def canonical_wg(raw):
    if not raw:
        return None
    low = raw.lower()
    if low in ("individual", "final", "draft"):
        return None
    for rx, name in WG_CANON:
        if re.search(rx, low):
            return name
    return re.sub(r"^OpenID (Foundation )?|\s*(Working Group|WG)$", "", raw).strip() or None


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------


def cache_path(cache_dir, name):
    """Path of a listed file in the cache; refuses anything that could leave it."""
    if not safe_name(name):
        raise ValueError("unsafe filename %r" % name)
    root = os.path.realpath(cache_dir)
    path = os.path.join(root, name)
    if os.path.dirname(path) != root or os.path.islink(path):
        raise ValueError("refusing cache path %r" % name)
    return path


def write_atomic(path, data):
    """Write via a new temporary file in the same directory, then rename over `path`.

    The temporary file is created exclusively, so a planted symlink is never followed,
    and the rename replaces a symlink at `path` rather than writing through it."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path) or ".", prefix=".tmp-")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.chmod(tmp, 0o644)  # mkstemp creates 0600; the output is served by a web server
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def read_cached(path, binary=False):
    """Read a cache file, refusing symlinks."""
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(fd, "rb") as f:
        data = f.read()
    return data if binary else data.decode("utf-8", "replace")


class Budget:
    """Crawl-wide limits on the number and total size of downloads."""

    def __init__(self, max_files=MAX_DOWNLOADS, max_bytes=MAX_TOTAL_BYTES):
        self.max_files, self.max_bytes = max_files, max_bytes
        self.files = self.bytes = 0
        self._lock = threading.Lock()

    def reserve(self):
        with self._lock:
            if self.files >= self.max_files:
                raise FetchError("download budget of %d files used up" % self.max_files)
            self.files += 1

    def spend(self, n):
        with self._lock:
            self.bytes += n
            if self.bytes > self.max_bytes:
                raise FetchError("download budget of %d bytes used up" % self.max_bytes)


def fetch_all(names, cache_dir, listing, workers=8, offline=False, budget=None):
    """Bring the cache up to date. Returns counts: fetched, cached, failed, missing."""
    os.makedirs(cache_dir, exist_ok=True)
    budget = budget or Budget()
    stamp_path = os.path.join(os.path.realpath(cache_dir), ".stamps.json")
    stamps = {}
    if os.path.exists(stamp_path):
        try:
            stamps = json.loads(read_cached(stamp_path))
        except (OSError, ValueError):
            stamps = {}
        if not isinstance(stamps, dict):
            stamps = {}

    def one(name):
        path = cache_path(cache_dir, name)
        have = os.path.exists(path)
        if offline or (have and stamps.get(name) == listing.get(name, {}).get("modified")):
            return "cached" if have else "missing"
        try:
            budget.reserve()
            data = http_get(BASE_URL + urllib.parse.quote(name))
            budget.spend(len(data))
        except Exception as e:  # stale cache is better than nothing, but it is counted
            print("  ! %s: %s" % (name, e), file=sys.stderr)
            return "failed"
        write_atomic(path, data)
        stamps[name] = listing.get(name, {}).get("modified")
        return "fetched"

    with concurrent.futures.ThreadPoolExecutor(workers) as ex:
        results = list(ex.map(one, names))
    write_atomic(stamp_path, json.dumps(stamps, indent=0, sort_keys=True))
    return {k: results.count(k) for k in ("fetched", "cached", "failed", "missing")}


def check_fetch(stats):
    """Raise when too many downloads failed for the result to be trusted."""
    attempted = stats["fetched"] + stats["failed"]
    if stats["failed"] > max(3, MAX_FAILURE_RATIO * attempted):
        raise FetchError("%d of %d downloads failed" % (stats["failed"], attempted))


def check_complete(specs, last_good):
    """Raise when this build lost a large share of specs or revisions."""
    now = {"specs": len(specs), "revisions": sum(len(s["revisions"]) for s in specs)}
    if now["specs"] < MIN_SPECS:
        raise FetchError("only %d specs found (expected at least %d)" % (now["specs"], MIN_SPECS))
    for k in ("specs", "revisions"):
        if last_good.get(k) and now[k] < MIN_SHARE_OF_LAST_GOOD * last_good[k]:
            raise FetchError("%s dropped from %d to %d since the last good build" % (k, last_good[k], now[k]))
    return now


def build(listing, cache_dir, renamed_to=None):
    stems = {}
    for name in listing:
        stem, _, ext = name.rpartition(".")
        if ext.lower() in FORMATS:
            stems.setdefault(stem, set()).add(ext.lower())

    specs = {}
    aliases = {}
    for stem, exts in stems.items():
        if "html" not in exts:
            continue
        c = classify(stem)
        if c is None or stem.endswith("_orig"):
            aliases[stem] = exts
            continue
        key, kind, n = c
        specs.setdefault(key, {"key": key, "revisions": []})["revisions"].append(
            {"stem": stem, "kind": kind, "n": n, "formats": sorted(exts)})

    # Unversioned names whose key has no numbered revisions are specs in their own right
    # (e.g. openid-authentication-2_0.html), or redirect stubs.
    for stem, exts in aliases.items():
        if stem in specs:
            specs[stem]["alias"] = {"stem": stem, "formats": sorted(exts)}
        elif not stem.endswith("_orig"):
            specs[stem] = {"key": stem, "revisions": [], "alias": {"stem": stem, "formats": sorted(exts)}}
    for stem in aliases:
        if stem.endswith("_orig"):
            base = re.sub(r"-\d{2}_orig$|_orig$", "", stem)
            if base in specs:
                specs[base].setdefault("extras", []).append(stem)

    def load(stem):
        path = cache_path(cache_dir, stem + ".html")
        if not os.path.exists(path):
            return {}
        return parse_document(read_cached(path))

    loaded = {}
    for key, spec in sorted(specs.items()):
        revs = []
        for r in spec["revisions"]:
            meta = load(r["stem"])
            if meta.get("redirect"):
                continue
            revs.append(_revision(r, meta, listing))
        alias_meta = load(spec["alias"]["stem"]) if spec.get("alias") else {}

        if alias_meta and not alias_meta.get("redirect"):
            # The unversioned URL is itself the published edition when nothing else is,
            # or when the document says it is Final but no -final file exists
            # (OpenID 2.0-era specs were published this way).
            kind = _kind_from_doc(alias_meta)
            has_final = any(r["kind"] in ("final", "errata") for r in revs)
            if not revs or (kind in ("final", "errata") and not has_final):
                r = {"stem": key, "kind": kind, "n": None, "formats": spec["alias"]["formats"]}
                revs.append(_revision(r, alias_meta, listing))

        if not revs and not alias_meta.get("redirect"):
            continue
        for r in revs:
            r["published_as"] = key
        loaded[key] = (spec, revs, alias_meta)

    # A spec that changed its filename is still one spec: fold every earlier name
    # into the name it ended up with, so Draft -> ID -> Final reads as one history.
    parent = _rename_parents(loaded, renamed_to or {})

    def root(k):
        seen = set()
        while k in parent and k not in seen:
            seen.add(k)
            k = parent[k]
        return k

    groups = {}
    for key in loaded:
        groups.setdefault(root(key), []).append(key)

    result = []
    for key, members in sorted(groups.items()):
        spec, _, alias_meta = loaded[key]
        revs = [r for m in members for r in loaded[m][1]]
        if not revs and not alias_meta.get("redirect"):
            continue
        revs.sort(key=lambda r: (r["date"] or r["listed"] or "", KIND_RANK[r["kind"]], r["number"] or ""))
        entry = _summarize(key, revs, spec, alias_meta)
        former = [m for m in members if m != key]
        if former:
            entry["former_names"] = sorted(
                ({"key": m, "title": _member_title(loaded[m][1]), "how": parent_how[m],
                  # The old unversioned URL still serves the old document (no redirect stub).
                  "old_url_live": bool(loaded[m][0].get("alias")) and not loaded[m][2].get("redirect")}
                 for m in former),
                key=lambda f: min((r["date"] or r["listed"] or "" for r in loaded[f["key"]][1]), default=""))
        result.append(entry)

    _resolve_redirects(result)
    _inherit_workgroups(result)
    return result


# Filled in by _rename_parents: former key -> how the rename was established.
parent_how = {}


def _norm_title(t, drop_versions=False):
    t = (clean_title(t) or "").lower()
    if drop_versions:
        t = re.sub(r"\b\d+(\.\d+)*\b", " ", t)
        t = re.sub(r"\bconnect\b", " ", t)
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def _member_title(revs):
    for r in reversed(revs):
        if r["title"]:
            return clean_title(r["title"])
    return None


def _rename_parents(loaded, renamed_to):
    """Map an old spec key to the key it was renamed to.

    Evidence, strongest first (all of it published on openid.net, none guessed from filenames):
    1. A redirect stub saying "Renamed" or "Redirection to Correct Specification URL".
    2. A redirect stub saying "Obsolete" whose target has the same title once version
       numbers and the word "Connect" are ignored (e.g. "OpenID Connect for Verifiable
       Credential Issuance" -> "OpenID for Verifiable Credential Issuance 1.0").
       Obsolete stubs to a different title (Messages -> Core) are real replacements and stay separate.
    3. No stub, but an older key whose documents carry exactly the same title as a newer key.
    4. Curated: "renamed_to" in overrides.json, for renames with no stub and a changed title.
    """
    parent_how.clear()
    parent = {}
    for old, new in renamed_to.items():
        if old in loaded and new in loaded:
            parent[old], parent_how[old] = new, "curated (overrides.json)"
        else:
            print("  ! renamed_to: unknown spec %r -> %r" % (old, new), file=sys.stderr)
    title_of = {k: _member_title(v[1]) for k, v in loaded.items()}

    for key, (spec, revs, alias_meta) in loaded.items():
        red = alias_meta.get("redirect") if alias_meta else None
        if not red or not red.get("target"):
            continue
        tgt = red["target"].rsplit(".", 1)[0]
        tgt_key = tgt if tgt in loaded else None
        if not tgt_key or tgt_key == key:
            continue
        reason = red["reason"].lower()
        if "renamed" in reason or "redirection" in reason:
            parent[key], parent_how[key] = tgt_key, "redirect: " + red["reason"]
        elif title_of.get(key) and title_of.get(tgt_key) and \
                _norm_title(title_of[key], True) == _norm_title(title_of[tgt_key], True):
            parent[key], parent_how[key] = tgt_key, "redirect: " + red["reason"] + " (same title)"

    by_title = {}
    for key, (_, revs, _) in loaded.items():
        if revs and title_of.get(key):
            by_title.setdefault(_norm_title(title_of[key]), []).append(key)
    for keys in by_title.values():
        if len(keys) < 2:
            continue
        last = lambda k: max(r["date"] or r["listed"] or "" for r in loaded[k][1])
        keys.sort(key=last)
        newest = keys[-1]
        for k in keys[:-1]:
            if k not in parent:
                parent[k], parent_how[k] = newest, "same title in documents"
    return parent


def _kind_from_doc(meta):
    s = " ".join(filter(None, [meta.get("doc_status"), meta.get("title")])).lower()
    if "errata" in s:
        return "errata"
    if "final" in s:
        return "final"
    if "implementer" in s or "implementor" in s:
        return "implementers"
    return "draft"


def _revision(r, meta, listing):
    listed = listing.get(r["stem"] + ".html", {}).get("modified")
    return {
        "file": r["stem"],
        "kind": r["kind"],
        "number": r["n"],
        "label": revision_label(r["kind"], r["n"]),
        "title": meta.get("title"),
        "date": meta.get("date"),
        "date_source": "document" if meta.get("date") else "listing",
        "listed": listed[:10] if listed else None,
        "authors": meta.get("authors") or [],
        "workgroup": meta.get("workgroup"),
        "workgroup_from": meta.get("workgroup_from"),
        "doc_status": meta.get("doc_status"),
        "formats": r["formats"],
    }


DRAFT_SUFFIX = re.compile(
    r"\s*(?:[-–—:]\s*|\()?\s*(?:draft\s*\d+|implementer'?s draft\s*\d*|implementors? draft\s*\d*|"
    r"final|errata set \d+|incorporating errata set \d+|draft \d+ incorporating errata set \d+|"
    r"wd\s*\d+|working draft\s*\d*|draft|draft-[\w.-]+)\)?\s*$",
    re.I,
)
STATUS_PREFIX = re.compile(r"^(?:final|draft|implementer'?s draft|implementors? draft)\s*:\s*", re.I)


def clean_title(t):
    if not t:
        return t
    t = STATUS_PREFIX.sub("", t)
    prev = None
    while prev != t:
        prev = t
        t = DRAFT_SUFFIX.sub("", t).strip()
    return t


def _summarize(key, revs, spec, alias_meta):
    latest = revs[-1] if revs else None
    by_kind = lambda k: [r for r in revs if r["kind"] == k]
    finals = by_kind("final")
    erratas = by_kind("errata")
    ids = by_kind("implementers")

    milestone = None
    for k in ("errata", "final", "implementers"):
        hits = by_kind(k)
        if hits:
            milestone = max(hits, key=lambda r: (r["date"] or r["listed"] or "", int(r["number"] or 0)))
            break

    if erratas or finals:
        status = "final"
    elif ids:
        status = "implementers"
    elif revs:
        status = "draft"
    else:
        status = "redirect"

    # Work after the milestone = drafts dated after it (towards next ID / errata).
    in_progress = False
    if milestone and latest and latest is not milestone and latest["kind"] == "draft":
        in_progress = (latest["date"] or "") > (milestone["date"] or "")

    title_src = milestone or latest
    title = clean_title(title_src["title"]) if title_src and title_src["title"] else None
    if not title and alias_meta and alias_meta.get("title"):
        title = clean_title(alias_meta["title"])

    wg = wg_raw = None
    for r in reversed(revs):
        if canonical_wg(r["workgroup"]):
            wg_raw = r["workgroup"]
            wg = canonical_wg(wg_raw)
            break

    entry = {
        "key": key,
        "title": title,
        "status": status,
        "status_label": {"final": "Final", "implementers": "Implementer's Draft",
                         "draft": "Draft", "redirect": "Renamed / Obsolete"}[status],
        "in_progress": in_progress,
        "workgroup": wg,
        "workgroup_raw": wg_raw,
        "workgroup_source": "document" if wg else None,
        "latest": latest["file"] if latest else None,
        "milestone": milestone["file"] if milestone else None,
        "current_url": spec["alias"]["stem"] if spec.get("alias") else None,
        "updated": (latest["date"] or latest["listed"]) if latest else None,
        "authors": (title_src or {}).get("authors", []),
        "counts": {"draft": len(by_kind("draft")), "implementers": len(ids),
                   "final": len(finals), "errata": len(erratas)},
        "revisions": revs,
    }
    if alias_meta.get("redirect"):
        # The unversioned URL now points elsewhere: the spec was renamed or obsoleted.
        entry["redirect"] = alias_meta["redirect"]
        entry["current_url"] = None
    if spec.get("extras"):
        entry["extras"] = sorted(spec["extras"])
    return entry


def _resolve_redirects(result):
    by_alias = {e["current_url"]: e for e in result if e.get("current_url")}
    for e in result:
        r = e.get("redirect")
        if r and r.get("target"):
            tgt = r["target"].rsplit(".", 1)[0]
            r["target_key"] = by_alias[tgt]["key"] if tgt in by_alias else None
            if not e["title"] and tgt in by_alias:
                e["redirect_title"] = by_alias[tgt]["title"]


def _family(key):
    k = re.sub(r"-\d+_\d+$", "", key)
    return k


def _inherit_workgroups(result):
    """Older revisions often lack a WG field; borrow it from the same spec family,
    then fall back to the filename-prefix table. Both are flagged as inferred."""
    fam = {}
    for e in result:
        if e["workgroup"]:
            fam.setdefault(_family(e["key"]), e["workgroup"])
    for e in result:
        if e["workgroup"]:
            continue
        if _family(e["key"]) in fam:
            e["workgroup"], e["workgroup_source"] = fam[_family(e["key"])], "family"
            continue
        for prefix, name in WG_BY_PREFIX:
            if e["key"].startswith(prefix):
                e["workgroup"], e["workgroup_source"] = name, "prefix"
                break


OVERRIDABLE = {"title", "workgroup", "status", "note"}


def load_overrides(path):
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return {k: v for k, v in json.load(f).items() if not k.startswith("_")}


def renames_from(overrides):
    return {k: v["renamed_to"] for k, v in overrides.items() if v.get("renamed_to")}
STATUS_LABEL = {"final": "Final", "implementers": "Implementer's Draft", "draft": "Draft"}


def apply_overrides(specs, overrides):
    """Apply staff corrections for facts a document does not state (or states wrongly).
    Keys may be a spec's current key or any former name. Every overridden field is
    listed in entry["curated"]. Returns {current key: fields} for what was applied."""
    by_key = {}
    for e in specs:
        by_key[e["key"]] = e
        for f in e.get("former_names", []):
            by_key[f["key"]] = e
    applied = {}
    for key, fields in overrides.items():
        e = by_key.get(key)
        if e is None:
            print("  ! override for unknown spec %r" % key, file=sys.stderr)
            continue
        for field, value in fields.items():
            if field == "renamed_to":
                continue  # handled during build
            if field not in OVERRIDABLE:
                print("  ! %s: field %r cannot be overridden" % (key, field), file=sys.stderr)
                continue
            e[field] = value
            if field not in e.setdefault("curated", []):
                e["curated"].append(field)
            if field == "workgroup":
                e["workgroup_source"] = "curated"
            if field == "status":
                e["status_label"] = STATUS_LABEL[value]
            applied.setdefault(e["key"], {})[field] = value
    return applied


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cache", default=DEFAULT_CACHE)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--offline", action="store_true", help="use cached listing and files only")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--overrides", default=DEFAULT_OVERRIDES, help="curated corrections (JSON)")
    ap.add_argument("--report", default=DEFAULT_REPORT, help="where to write the source-fixes report")
    args = ap.parse_args()

    os.makedirs(args.cache, exist_ok=True)
    cache_root = os.path.realpath(args.cache)
    listing_path = os.path.join(cache_root, ".listing.html")
    last_good_path = os.path.join(cache_root, ".last-good.json")
    if args.offline:
        text = read_cached(listing_path)
    else:
        text = http_get(BASE_URL, max_bytes=MAX_LISTING_BYTES).decode("utf-8", "replace")
        write_atomic(listing_path, text)
    listing = parse_listing(text)
    print("listing: %d files" % len(listing), file=sys.stderr)

    # Nothing below writes output until the crawl has passed these checks, so a broken
    # or tampered source fails the run and the last good deployment stays up.
    try:
        htmls = [n for n in listing if n.lower().endswith(".html")]
        stats = fetch_all(htmls, args.cache, listing, args.workers, args.offline)
        print("documents: %(fetched)d fetched, %(cached)d cached, %(failed)d failed, %(missing)d missing" % stats,
              file=sys.stderr)
        check_fetch(stats)

        overrides = load_overrides(args.overrides)
        specs = build(listing, args.cache, renames_from(overrides))
        last_good = {}
        if os.path.exists(last_good_path):
            try:
                last_good = json.loads(read_cached(last_good_path))
            except (OSError, ValueError):
                pass
        totals = check_complete(specs, last_good if isinstance(last_good, dict) else {})
    except FetchError as e:
        sys.exit("crawl rejected: %s; not writing output" % e)
    generated = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()

    # Check the documents before overrides are applied, so the report reflects the sources.
    import source_issues
    issues = source_issues.find_issues(specs)
    overrides = apply_overrides(specs, overrides)
    os.makedirs(os.path.dirname(args.report), exist_ok=True)
    write_atomic(args.report, source_issues.render_markdown(issues, generated[:10], overrides))
    print("wrote %d source issues -> %s" % (len(issues), args.report), file=sys.stderr)

    data = {
        "generated": generated,
        "source": BASE_URL,
        "specs": specs,
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    write_atomic(args.out, json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    write_atomic(last_good_path, json.dumps(dict(totals, generated=generated)))
    print("wrote %d specs -> %s" % (len(specs), args.out), file=sys.stderr)


if __name__ == "__main__":
    main()

"""Unit tests for the parser: python3 -m unittest discover -s crawler"""
import io
import os
import tempfile
import unittest
import urllib.request
from unittest import mock

import build_data as b
import source_issues


class Classify(unittest.TestCase):
    def test_suffixes(self):
        self.assertEqual(b.classify("openid-connect-core-1_0-36"), ("openid-connect-core-1_0", "draft", "36"))
        self.assertEqual(b.classify("openid-connect-core-1_0-final"), ("openid-connect-core-1_0", "final", None))
        self.assertEqual(b.classify("openid-connect-core-1_0-errata2"), ("openid-connect-core-1_0", "errata", "2"))
        self.assertEqual(b.classify("fapi-2_0-attacker-model-ID2"), ("fapi-2_0-attacker-model", "implementers", "2"))
        self.assertEqual(b.classify("oauth-v2-jarm-final"), ("oauth-v2-jarm", "final", None))
        self.assertEqual(b.classify("openid-financial-api-ciba-wd-02"), ("openid-financial-api-ciba", "draft", "02"))
        self.assertEqual(b.classify("openid-heart-oauth2-1_0-2017-05-31"),
                         ("openid-heart-oauth2-1_0", "draft", "2017-05-31"))

    def test_unversioned_is_alias(self):
        self.assertIsNone(b.classify("openid-connect-core-1_0"))


class Dates(unittest.TestCase):
    def test_formats(self):
        self.assertEqual(b.parse_date("February 25, 2014"), "2014-02-25")
        self.assertEqual(b.parse_date("9 July 2025"), "2025-07-09")
        self.assertEqual(b.parse_date("2026-03-27"), "2026-03-27")
        self.assertEqual(b.parse_date("May\xa02, 2017"), "2017-05-02")
        self.assertEqual(b.parse_date("October 2013"), "2013-10")
        self.assertIsNone(b.parse_date("N. Sakimura"))


class Titles(unittest.TestCase):
    def test_clean(self):
        self.assertEqual(b.clean_title("Final: OpenID Authentication 2.0 - Final"), "OpenID Authentication 2.0")
        self.assertEqual(b.clean_title("Authorization API 1.0 – draft 02"), "Authorization API 1.0")
        self.assertEqual(b.clean_title("FAPI 2.0 Message Signing (Draft)"), "FAPI 2.0 Message Signing")
        self.assertEqual(b.clean_title("JSON Web Token (JWT) draft-jones-json-web-token-07"), "JSON Web Token (JWT)")


class Workgroups(unittest.TestCase):
    def test_canonical(self):
        self.assertEqual(b.canonical_wg("OpenID Foundation Artifact Binding Working Group"), "AB/Connect")
        self.assertEqual(b.canonical_wg("connect"), "AB/Connect")
        self.assertEqual(b.canonical_wg("eKYC-IDA"), "eKYC & IDA")
        self.assertEqual(b.canonical_wg("Shared Signals and Events Working Group"), "Shared Signals")
        self.assertIsNone(b.canonical_wg("individual"))


V1 = """<html><head><title>Final: Example 1.0</title></head><body>
<table summary="layout" width="66%"><tr><td><table summary="layout">
<tr><td class="header">Final</td><td class="header">N. Sakimura</td></tr>
<tr><td class="header">&nbsp;</td><td class="header">NAT.Consulting</td></tr>
<tr><td class="header">&nbsp;</td><td class="header">M. Jones</td></tr>
<tr><td class="header">&nbsp;</td><td class="header">Self-Issued Consulting (was at</td></tr>
<tr><td class="header">&nbsp;</td><td class="header">Microsoft)</td></tr>
<tr><td class="header">&nbsp;</td><td class="header">December 15, 2023</td></tr>
</table></td></tr></table>
<h1><br />Example 1.0</h1>
<h3>Authors' Addresses</h3>
<table><tr><td class="author-text">&nbsp;</td><td class="author-text">Nat Sakimura</td></tr>
<tr cellpadding="3"><td>&nbsp;</td><td>&nbsp;</td></tr>
<tr><td class="author-text">&nbsp;</td><td class="author-text">Michael B. Jones</td></tr></table>
</body></html>"""


class ParseV1(unittest.TestCase):
    def test_header(self):
        m = b.parse_document(V1)
        self.assertEqual(m["title"], "Example 1.0")
        self.assertEqual(m["date"], "2023-12-15")
        self.assertEqual(m["doc_status"], "Final")
        self.assertEqual([a["name"] for a in m["authors"]], ["Nat Sakimura", "Michael B. Jones"])
        self.assertEqual(m["authors"][1]["org"], "Self-Issued Consulting (was at Microsoft)")


def _spec(title, date, redirect=None):
    rev = {"title": title, "date": date, "listed": date}
    return ({"alias": {"stem": "x"}} if redirect else {}, [rev] if title else [], {"redirect": redirect} if redirect else {})


class Renames(unittest.TestCase):
    def test_evidence(self):
        loaded = {
            "fapi-2_0-baseline": _spec("FAPI 2.0 Baseline Profile", "2021-07-01",
                                       {"reason": "Renamed Specification", "target": "fapi-2_0-security-profile.html"}),
            "fapi-2_0-security-profile": _spec("FAPI 2.0 Security Profile", "2022-12-07",
                                               {"reason": "Renamed Specification", "target": "fapi-security-profile-2_0.html"}),
            "fapi-security-profile-2_0": _spec("FAPI 2.0 Security Profile", "2025-02-22"),
            # Obsolete, different title: a real replacement, kept separate.
            "openid-connect-messages-1_0": _spec("OpenID Connect Messages 1.0", "2013-01-01",
                                                 {"reason": "Obsolete Specification", "target": "openid-connect-core-1_0.html"}),
            "openid-connect-core-1_0": _spec("OpenID Connect Core 1.0", "2014-02-25"),
            # Obsolete, same title once versions and "Connect" are ignored: a rename.
            "openid-connect-4-verifiable-credential-issuance-1_0": _spec(
                "OpenID Connect for Verifiable Credential Issuance", "2022-01-01",
                {"reason": "Obsolete Specification", "target": "openid-4-verifiable-credential-issuance-1_0.html"}),
            "openid-4-verifiable-credential-issuance-1_0": _spec("OpenID for Verifiable Credential Issuance 1.0", "2025-09-16"),
            # Same title, no stub.
            "openid-caep-specification-1_0": _spec("OpenID Continuous Access Evaluation Profile 1.0", "2021-06-01"),
            "openid-caep-1_0": _spec("OpenID Continuous Access Evaluation Profile 1.0", "2025-08-29"),
            # Different versions are different specs.
            "openid-federation-1_0": _spec("OpenID Federation 1.0", "2025-01-01"),
            "openid-federation-1_1": _spec("OpenID Federation 1.1", "2026-01-01"),
        }
        p = b._rename_parents(loaded, {})
        self.assertEqual(p["fapi-2_0-baseline"], "fapi-2_0-security-profile")
        self.assertEqual(p["fapi-2_0-security-profile"], "fapi-security-profile-2_0")
        self.assertNotIn("openid-connect-messages-1_0", p)
        self.assertEqual(p["openid-connect-4-verifiable-credential-issuance-1_0"], "openid-4-verifiable-credential-issuance-1_0")
        self.assertEqual(p["openid-caep-specification-1_0"], "openid-caep-1_0")
        self.assertNotIn("openid-federation-1_0", p)


def _row(href):
    return '<tr><td><a href="%s">x</a></td><td align="right">2025-01-01 10:00  </td><td align="right"> 12K</td></tr>' % href


class UntrustedListing(unittest.TestCase):
    def test_real_names_accepted(self):
        names = ["openid-connect-core-1_0-final.html", "fapi-2_0-attacker-model-ID2.html",
                 "openid-heart-oauth2-1_0-2017-05-31.html", "draft-jones-json-web-token-07.txt"]
        self.assertEqual(sorted(b.parse_listing("".join(_row(n) for n in names))), sorted(names))

    def test_path_names_rejected(self):
        hostile = ["..%2F..%2Fetc%2Fpasswd", "a/../../x.html", "%2Ftmp%2Fx.html", "..", ".hidden.html",
                   "x%00.html", "a%5C..%5Cb.html", "&#46;&#46;%2Fx.html", 'x" onmouseover="alert(1).html',
                   "x%22%3E%3Cimg%20src%3Dx%3E.html"]
        self.assertEqual(b.parse_listing("".join(_row(n) for n in hostile)), {})

    def test_cache_path_contained(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(b.cache_path(d, "a-1_0.html"), os.path.join(os.path.realpath(d), "a-1_0.html"))
            for bad in ["../x.html", "/tmp/x.html", "a/b.html", "..", ""]:
                with self.assertRaises(ValueError):
                    b.cache_path(d, bad)
            os.symlink("/etc/hosts", os.path.join(d, "link.html"))
            with self.assertRaises(ValueError):
                b.cache_path(d, "link.html")


class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()


class Fetch(unittest.TestCase):
    def test_only_openid_net_https(self):
        for url in ["http://openid.net/specs/", "https://evil.example/specs/", "https://openid.net.evil.example/",
                    "file:///etc/passwd", "https://openid.net:8443/specs/"]:
            with self.assertRaises(b.FetchError):
                b.http_get(url)

    def test_redirect_off_host_refused(self):
        h = b._SameHostRedirects()
        req = urllib.request.Request(b.BASE_URL)
        with self.assertRaises(b.FetchError):
            h.redirect_request(req, None, 302, "Found", {}, "https://evil.example/x.html")
        self.assertIsNotNone(h.redirect_request(req, None, 302, "Found", {}, "https://openid.net/specs/x.html"))

    def test_size_cap(self):
        with mock.patch.object(b._opener, "open", return_value=_Resp(b"x" * 101)):
            with self.assertRaises(b.FetchError):
                b.http_get(b.BASE_URL, max_bytes=100)
        with mock.patch.object(b._opener, "open", return_value=_Resp(b"x" * 100)):
            self.assertEqual(len(b.http_get(b.BASE_URL, max_bytes=100)), 100)

    def test_listing_entry_cap(self):
        with mock.patch.object(b, "MAX_LISTING_ENTRIES", 3):
            with self.assertRaises(b.FetchError):
                b.parse_listing("".join(_row("s-%d.html" % i) for i in range(5)))


def _specs(n, revs=2, prefix="spec"):
    return [{"key": "%s-%d" % (prefix, i), "revisions": [{"file": "%s-%d-%02d" % (prefix, i, j)} for j in range(revs)]}
            for i in range(n)]


class CrawlLimits(unittest.TestCase):
    def test_budget_files_and_bytes(self):
        bud = b.Budget(max_files=2, max_bytes=10)
        bud.reserve(); bud.reserve()
        with self.assertRaises(b.FetchError):
            bud.reserve()
        bud = b.Budget(max_files=10, max_bytes=10)
        bud.spend(10)
        with self.assertRaises(b.FetchError):
            bud.spend(1)

    def test_fetch_all_counts_failures_and_stops_at_budget(self):
        names = ["s-%d.html" % i for i in range(5)]
        listing = {n: {"modified": "2025-01-01T00:00"} for n in names}
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(b, "http_get", return_value=b"x" * 4), mock.patch("sys.stderr"):
            stats = b.fetch_all(names, d, listing, workers=1, budget=b.Budget(max_files=10, max_bytes=8))
            self.assertEqual((stats["fetched"], stats["failed"]), (2, 3))
        b.check_fetch({"fetched": 100, "failed": 3, "cached": 0, "missing": 0})
        with self.assertRaises(b.FetchError):
            b.check_fetch({"fetched": 100, "failed": 6, "cached": 0, "missing": 0})

    def test_completeness_against_last_good(self):
        specs = _specs(60)
        self.assertEqual({k: v for k, v in b.check_complete(specs, {"specs": 60, "revisions": 120}).items()
                          if k in ("specs", "revisions")}, {"specs": 60, "revisions": 120})
        with self.assertRaises(b.FetchError):
            b.check_complete(specs[:10], {})
        with self.assertRaises(b.FetchError):
            b.check_complete(specs[:53], {"specs": 60, "revisions": 106})
        with self.assertRaises(b.FetchError):
            b.check_complete(_specs(60, revs=1), {"specs": 60, "revisions": 120})

    def test_same_totals_but_different_items_rejected(self):
        last = b.check_complete(_specs(60), {})
        swapped = _specs(55) + _specs(5, prefix="other")
        with mock.patch("sys.stderr"), self.assertRaises(b.FetchError):
            b.check_complete(swapped, last)
        # One or two withdrawn items is normal.
        with mock.patch("sys.stderr"):
            b.check_complete(_specs(59) + _specs(1, prefix="other"), last)
        # A rename keeps the old name in former_names, so it is not a loss.
        renamed = _specs(60)
        renamed[0] = dict(renamed[0], key="spec-new", former_names=[{"key": "spec-0"}])
        with mock.patch("sys.stderr"):
            b.check_complete(renamed, last)


class SafeCacheWrites(unittest.TestCase):
    def test_write_replaces_symlink_instead_of_following_it(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as outside:
            victim = os.path.join(outside, "victim")
            with open(victim, "w") as f:
                f.write("untouched")
            for name in (".stamps.json", ".listing.html", "x.html.part"):
                os.symlink(victim, os.path.join(d, name))
                b.write_atomic(os.path.join(d, name), "new")
                self.assertFalse(os.path.islink(os.path.join(d, name)))
            with open(victim) as f:
                self.assertEqual(f.read(), "untouched")
            self.assertEqual(sorted(os.listdir(d)), [".listing.html", ".stamps.json", "x.html.part"])

    def test_read_refuses_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            os.symlink("/etc/hosts", os.path.join(d, ".listing.html"))
            with self.assertRaises(OSError):
                b.read_cached(os.path.join(d, ".listing.html"))


class MovedTo(unittest.TestCase):
    def test_clean(self):
        self.assertEqual(b.clean_moved_to({"body": "IETF", "via": "draft-ietf-oauth-json-web-token", "rfc": 7519,
                                           "rfc_title": "JSON Web Token (JWT)", "rfc_date": "2015-05"}),
                         {"body": "IETF", "via": "draft-ietf-oauth-json-web-token", "rfc": 7519,
                          "rfc_title": "JSON Web Token (JWT)", "rfc_date": "2015-05"})
        self.assertEqual(b.clean_moved_to({"body": "IETF", "note": "Expired."}), {"body": "IETF", "note": "Expired."})
        for bad in [None, {}, {"body": ""}, {"body": "IETF", "rfc": "7519"}, {"body": "IETF", "rfc": True},
                    {"body": "IETF", "via": "javascript:alert(1)"}, {"body": "IETF", "via": "../x"},
                    {"body": "IETF", "rfc": 7519, "rfc_date": "May 2015"}]:
            with self.assertRaises(ValueError):
                b.clean_moved_to(bad)

    def test_override_applies_and_bad_one_is_skipped(self):
        specs = [{"key": "draft-jones-jwt"}, {"key": "draft-jones-x"}]
        with mock.patch("sys.stderr"):
            b.apply_overrides(specs, {"draft-jones-jwt": {"moved_to": {"body": "IETF", "rfc": 7519}},
                                      "draft-jones-x": {"moved_to": {"body": "IETF", "via": "<script>"}}})
        self.assertEqual(specs[0]["moved_to"]["rfc"], 7519)
        self.assertEqual(specs[0]["curated"], ["moved_to"])
        self.assertNotIn("moved_to", specs[1])


class Sitemap(unittest.TestCase):
    def test_one_url_per_live_spec(self):
        specs = [
            {"key": "core-1_0", "current_url": "core-1_0", "milestone": "core-1_0-errata2", "latest": "core-1_0-36"},
            {"key": "x-1_0", "current_url": None, "milestone": "x-1_0-final", "latest": "x-1_0-03"},
            {"key": "y-1_0", "current_url": None, "milestone": None, "latest": "y-1_0-02", "status": "draft",
             "updated": "2024-05-01"},
            # Abandoned: never approved, numbered drafts only, last revised before 2012.
            {"key": "draft-jones-jwt", "current_url": None, "milestone": None, "latest": "draft-jones-jwt-07",
             "status": "draft", "updated": "2011-12-13"},
            # Old but with a stable URL (e.g. Simple Registration 1.0): kept.
            {"key": "sreg-1_0", "current_url": "sreg-1_0", "milestone": None, "latest": "sreg-1_0",
             "status": "draft", "updated": "2006-06-30"},
            {"key": "moved-1_0", "current_url": "moved-1_0", "milestone": None, "latest": "moved-1_0",
             "status": "draft", "updated": "2020-01-01", "moved_to": {"body": "IETF"}},
            {"key": "old-1_0", "current_url": "old-1_0", "milestone": None, "latest": "old-1_0-01",
             "redirect": {"reason": "Obsolete Specification"}},
        ]
        listing = {"core-1_0.html": {"modified": "2023-12-16T05:56"}, "x-1_0-final.html": {"modified": "2024-01-02T00:00"}}
        e = b.sitemap_entries(specs, listing)
        self.assertEqual([(x["loc"].rsplit("/", 1)[1], x["lastmod"]) for x in e],
                         [("core-1_0.html", "2023-12-16"), ("sreg-1_0.html", None), ("x-1_0-final.html", "2024-01-02"),
                          ("y-1_0-02.html", None)])

    def test_render_is_valid_xml(self):
        import xml.etree.ElementTree as ET
        xml = b.render_sitemap([{"loc": b.BASE_URL + "a-1_0.html", "lastmod": "2025-01-01"},
                                {"loc": b.BASE_URL + "b-1_0.html", "lastmod": None}])
        root = ET.fromstring(xml)
        ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
        self.assertEqual([u.find(ns + "loc").text for u in root], [b.BASE_URL + "a-1_0.html", b.BASE_URL + "b-1_0.html"])
        self.assertIsNone(root[1].find(ns + "lastmod"))


class CuratedWorkgroupIssue(unittest.TestCase):
    def issue(self, curated):
        rev = {"file": "x-1_0-ID1", "kind": "implementers", "workgroup": None, "date": "2020-07-15", "authors": []}
        spec = {"key": "x-1_0", "title": "X", "workgroup": "AB/Connect", "latest": "x-1_0-ID1",
                "milestone": "x-1_0-ID1", "revisions": [rev]}
        return source_issues.find_issues([spec], curated)[0]

    def test_inferred_workgroup(self):
        self.assertEqual(self.issue(None)["expected"], "AB/Connect")
        self.assertIn("infers AB/Connect", self.issue(None)["detail"])

    def test_curated_workgroup_replaces_the_inferred_one(self):
        issue = self.issue({"x-1_0": "MODRNA"})
        self.assertEqual(issue["expected"], "MODRNA")
        self.assertIn("MODRNA, set in overrides.json", issue["detail"])
        self.assertNotIn("AB/Connect", issue["detail"])


if __name__ == "__main__":
    unittest.main()

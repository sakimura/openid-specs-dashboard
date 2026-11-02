"""Unit tests for the parser: python3 -m unittest discover -s crawler"""
import unittest

import build_data as b


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


if __name__ == "__main__":
    unittest.main()

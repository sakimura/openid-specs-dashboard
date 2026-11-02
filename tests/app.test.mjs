// Tests for the page's data handling: node --test tests/*.test.mjs
// Uses the real public/app.js, which exports its helpers when loaded under Node.
import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const app = createRequire(import.meta.url)("../public/app.js");

const rev = (file, kind = "final", extra = {}) => ({ file, kind, label: "Final", date: "2025-01-01", formats: ["html"], authors: [{ name: "A" }], ...extra });
const spec = (extra = {}) => ({
  key: "example-1_0", title: "Example 1.0", status: "final", workgroup: "AB/Connect",
  latest: "example-1_0-final", milestone: "example-1_0-final", updated: "2025-01-01",
  counts: { draft: 0, implementers: 0, final: 1, errata: 0 }, revisions: [rev("example-1_0-final")], ...extra,
});
const data = (...specs) => ({ generated: "2026-11-02T03:17:00+00:00", source: "https://openid.net/specs/", specs });
const protoSnapshot = () => Object.getOwnPropertyNames(Object.prototype).sort().join(",");

test("real-shaped data passes through", () => {
  const out = app.validate(data(spec()));
  assert.equal(out.specs.length, 1);
  assert.equal(out.specs[0].revisions[0].file, "example-1_0-final");
});

test("hostile workgroup names do not touch Object.prototype", () => {
  const before = protoSnapshot();
  for (const wg of ["__proto__", "constructor", "toString", "hasOwnProperty"]) {
    const specs = app.prepare(app.validate(data(spec({ workgroup: wg }), spec({ key: "b-1_0" }))));
    const rows = app.wgTotals(specs);
    assert.equal(rows.find((r) => r.wg === wg).c.final, 1, wg);
  }
  assert.equal(protoSnapshot(), before);
  assert.equal({}.final, undefined);
});

test("__proto__ keys in the JSON are not copied", () => {
  const raw = JSON.parse('{"generated":"2026-11-02","specs":[{"key":"x-1_0","status":"final","__proto__":{"polluted":1},' +
    '"revisions":[{"file":"x-1_0-final","kind":"final","__proto__":{"polluted":1}}]}]}');
  const s = app.validate(raw).specs[0];
  assert.equal(s.polluted, undefined);
  assert.equal(s.revisions[0].polluted, undefined);
  assert.equal(Object.getPrototypeOf(s), Object.prototype);
});

test("status must be one of the three statuses, not any inherited property", () => {
  for (const status of ["constructor", "toString", "__proto__", "redirect", "", null]) {
    assert.equal(app.validate(data(spec({ status }))).specs.length, 0, String(status));
  }
  for (const status of ["draft", "implementers", "final"]) {
    assert.equal(app.validate(data(spec({ status }))).specs.length, 1, status);
  }
  assert.equal(app.parseHash("#status=constructor").status, "");
  assert.equal(app.parseHash("#status=final").status, "final");
});

test("records without a usable revision are dropped, not rendered", () => {
  const out = app.validate(data(spec({ revisions: [], current_url: null, latest: null, milestone: null }), spec({ key: "ok-1_0" })));
  assert.deepEqual(out.specs.map((s) => s.key), ["ok-1_0"]);
  const bad = app.validate(data(spec({ revisions: [rev('x" onmouseover="a'), rev("../x")] })));
  assert.equal(bad.specs.length, 0);
});

test("unknown latest/milestone fall back safely", () => {
  const [s] = app.prepare(app.validate(data(spec({ latest: "nope", milestone: "nope" }))));
  assert.equal(s.latestRev.file, "example-1_0-final");
  assert.equal(s.milestoneRev, null);
});

test("unsafe file names, formats, dates and URLs are dropped", () => {
  const [s] = app.validate(data(spec({
    current_url: "javascript:alert(1)",
    revisions: [rev("example-1_0-final", "final", { date: '2024"><img src=x>', formats: ["html", "javascript:x"] }), rev("../evil")],
  }))).specs;
  assert.equal(s.current_url, null);
  assert.equal(s.revisions.length, 1);
  assert.equal(s.revisions[0].date, null);
  assert.deepEqual(s.revisions[0].formats, ["html"]);
  assert.equal(app.fmtDate('2024"><img'), "—");
  assert.equal(app.specUrl('a"b', "html"), "https://openid.net/specs/a%22b.html");
});

test("malformed top level is rejected", () => {
  for (const bad of [null, [], {}, { specs: {} }, { specs: [], generated: "yesterday" }]) {
    assert.throws(() => app.validate(bad));
  }
});

test("moved_to keeps only a body, a draft name and an RFC number", () => {
  const ok = app.prepare(app.validate(data(spec({ moved_to: { body: "IETF", via: "draft-ietf-oauth-json-web-token", rfc: 7519 } }))))[0];
  assert.deepEqual([ok.moved_to.via, ok.moved_to.rfc, ok.superseded], ["draft-ietf-oauth-json-web-token", 7519, true]);
  const bad = app.validate(data(spec({ moved_to: { body: "IETF", via: "javascript:alert(1)", rfc: "7519", url: "https://evil.example" } }))).specs[0];
  assert.deepEqual(bad.moved_to, { body: "IETF", via: null, rfc: null, rfc_title: null, note: null });
  assert.equal(app.validate(data(spec({ moved_to: { body: "" } }))).specs[0].moved_to, null);
});

test("hash parameters fall back to defaults", () => {
  assert.deepEqual([app.parseHash("#sort=bogus:bad").sort, app.parseHash("#sort=bogus:bad").dir], ["updated", "desc"]);
  assert.deepEqual([app.parseHash("#sort=title").sort, app.parseHash("#sort=title").dir], ["title", "asc"]);
  assert.equal(app.parseHash("#sort=__proto__:asc").sort, "updated");
});

test("CSV cells that a spreadsheet could evaluate are kept as text", () => {
  const risky = ["=1+1", "+1", "-1", "@SUM(A1)", " =HYPERLINK(\"https://x.invalid\")", "\t=1", "\r=1", "\n=1",
    " =1", "　=1", "﻿=1", "＝1+1", "＋1", "－1", "＠SUM(A1)"];
  for (const v of risky) {
    const cell = app.csvCell(v);
    assert.ok(cell.startsWith("\"'"), JSON.stringify(v) + " -> " + cell);
    assert.ok(!/[\r\n]/.test(cell), "line break kept in " + JSON.stringify(v));
  }
  assert.equal(app.csvCell("OpenID Connect Core 1.0"), '"OpenID Connect Core 1.0"');
  assert.equal(app.csvCell('a "quoted", value'), '"a ""quoted"", value"');
  assert.equal(app.csvCell("line one\nline two"), '"line one line two"');
  assert.equal(app.csvCell(null), '""');
});

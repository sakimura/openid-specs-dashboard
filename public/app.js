/* OpenID Specifications Dashboard — no build step, no dependencies. */
(function () {
  "use strict";

  const SPECS_BASE = "https://openid.net/specs/";
  const DATA_URL = "data/specs.json";
  const KINDS = ["draft", "implementers", "final", "errata"];
  const KIND_NAME = { draft: "Draft", implementers: "Implementer's Draft", final: "Final", errata: "Errata" };
  const KIND_VAR = { draft: "--m-draft", implementers: "--m-id", final: "--m-final", errata: "--m-errata" };
  const STATUS_RANK = { final: 3, implementers: 2, draft: 1 };
  const NOT_STATED = "Not stated";
  const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

  const $ = (s, el = document) => el.querySelector(s);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const cssVar = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  const kindColor = (k) => `var(${KIND_VAR[k]})`;
  const specUrl = (file, ext = "html") => SPECS_BASE + encodeURIComponent(file) + "." + encodeURIComponent(ext);
  // specs.json is built from documents we do not control: check every field that
  // ends up in a URL, class name or markup before rendering.
  const SAFE_FILE = /^[A-Za-z0-9][A-Za-z0-9._-]*$/;
  const ISO_DATE = /^\d{4}(-\d{2}(-\d{2})?)?$/;
  const FORMATS = new Set(["html", "txt", "xml", "md", "pdf"]);
  const SEVERITIES = new Set(["error", "check", "rename", "stub", "missing", "naming", "other", "historical"]);
  const SORTS = new Set(["updated", "title", "workgroup", "status"]);

  const state = { q: "", status: "", wg: "", active: false, superseded: false, sort: "updated", dir: "desc", open: null };
  let DATA = null, SPECS = [], NOW = new Date();

  // ---------------------------------------------------------------- utilities
  function fmtDate(d) {
    if (!d || !ISO_DATE.test(d)) return "—";
    const [y, m, day] = d.split("-");
    if (!m) return y;
    return (day ? +day + " " : "") + MONTHS[+m - 1] + " " + y;
  }
  function monthsAgo(d) {
    if (!d) return Infinity;
    const [y, m] = d.split("-").map(Number);
    return (NOW.getFullYear() - y) * 12 + (NOW.getMonth() + 1 - (m || 1));
  }
  function relTime(d) {
    const m = monthsAgo(d);
    if (m === Infinity) return "";
    if (m < 1) return "this month";
    if (m < 12) return m + " mo ago";
    const y = Math.floor(m / 12);
    return y + (y === 1 ? " yr ago" : " yrs ago");
  }
  function editorsShort(authors, n = 3) {
    if (!authors || !authors.length) return "—";
    const names = authors.map((a) => a.name);
    return names.slice(0, n).join(", ") + (names.length > n ? ` +${names.length - n}` : "");
  }
  function rev(spec, file) { return spec.revisions.find((r) => r.file === file) || null; }

  // ---------------------------------------------------------------- validate
  // Only known fields are copied, into fresh objects, so keys such as "__proto__"
  // in the data never reach an object's prototype. Enum checks use Sets, not `in`.
  const STATUSES = new Set(["draft", "implementers", "final"]);
  const WG_SOURCES = new Set(["document", "inferred", "curated"]);
  const okDate = (d) => (typeof d === "string" && ISO_DATE.test(d) ? d : null);
  const okFile = (f) => typeof f === "string" && SAFE_FILE.test(f);
  const str = (t) => (t == null ? null : String(t));
  const list = (v) => (Array.isArray(v) ? v : []);
  const isObj = (v) => v !== null && typeof v === "object" && !Array.isArray(v);
  function cleanAuthors(v) {
    return list(v).filter(isObj).map((a) => ({ name: String(a.name || ""), org: str(a.org) })).filter((a) => a.name);
  }
  function cleanRevision(r) {
    if (!isObj(r) || !okFile(r.file) || !KINDS.includes(r.kind)) return null;
    return {
      file: r.file, kind: r.kind,
      number: typeof r.number === "string" && /^[\d-]+$/.test(r.number) ? r.number : null,
      label: String(r.label || r.file), title: str(r.title),
      date: okDate(r.date), listed: okDate(r.listed),
      formats: list(r.formats).filter((f) => FORMATS.has(f)),
      authors: cleanAuthors(r.authors),
    };
  }
  function cleanIssue(i) {
    if (!isObj(i) || !SEVERITIES.has(i.severity)) return null;
    return { severity: i.severity, category: str(i.category), detail: str(i.detail), expected: str(i.expected),
      found: str(i.found), files: list(i.files).filter(okFile) };
  }
  function cleanSpec(s) {
    if (!isObj(s) || !okFile(s.key) || !STATUSES.has(s.status)) return null;
    const revisions = list(s.revisions).map(cleanRevision).filter(Boolean);
    // Every link and date on a row comes from a revision; a spec without one cannot be shown.
    if (!revisions.length) return null;
    const files = new Set(revisions.map((r) => r.file));
    const former = list(s.former_names).filter((f) => isObj(f) && okFile(f.key))
      .map((f) => ({ key: f.key, title: str(f.title), how: String(f.how || "") }));
    const r = isObj(s.redirect) ? s.redirect : null;
    return {
      key: s.key, title: str(s.title), status: s.status, status_label: String(s.status_label || ""),
      in_progress: s.in_progress === true,
      workgroup: str(s.workgroup), workgroup_raw: str(s.workgroup_raw),
      workgroup_source: WG_SOURCES.has(s.workgroup_source) ? s.workgroup_source : null,
      latest: files.has(s.latest) ? s.latest : revisions[revisions.length - 1].file, milestone: files.has(s.milestone) ? s.milestone : null,
      current_url: okFile(s.current_url) ? s.current_url : null,
      updated: okDate(s.updated), authors: cleanAuthors(s.authors), revisions,
      counts: Object.fromEntries(KINDS.map((k) => [k, Math.max(0, Number(isObj(s.counts) && s.counts[k]) || 0)])),
      former_names: former.length ? former : undefined,
      issues: list(s.issues).map(cleanIssue).filter(Boolean),
      redirect: r ? { reason: String(r.reason || "Obsolete Specification"), message: str(r.message),
        target: okFile(r.target) ? r.target : null, target_key: okFile(r.target_key) ? r.target_key : null } : null,
      note: str(s.note), curated: list(s.curated).length ? list(s.curated).map(String) : null,
    };
  }
  function validate(data) {
    if (!isObj(data) || !Array.isArray(data.specs) || !okDate(String(data.generated || "").slice(0, 10))) throw new Error("unexpected data format");
    return { generated: String(data.generated), source: str(data.source), specs: data.specs.map(cleanSpec).filter(Boolean) };
  }

  // ---------------------------------------------------------------- derive
  function prepare(data) {
    NOW = new Date(data.generated);
    return data.specs.map((s) => {
      const milestone = rev(s, s.milestone);
      const latest = rev(s, s.latest);
      const superseded = !!s.redirect;
      const wg = s.workgroup || NOT_STATED;
      const displayKind = milestone ? milestone.kind : "draft";
      const hay = [s.title, s.key, wg, ...(s.former_names || []).flatMap((f) => [f.key, f.title]), ...(s.revisions.flatMap((r) => r.authors.map((a) => a.name)))].join(" ").toLowerCase();
      // A draft dated after the latest approved document (Final, errata set or ID). What it is
      // heading toward (errata, a revision, the next ID) is not stated anywhere, so it isn't claimed.
      const newerDraft = s.in_progress && !!milestone;
      const recentNewerDraft = newerDraft && !!latest && monthsAgo(latest.date || latest.listed) <= 12;
      return Object.assign({}, s, { milestoneRev: milestone, latestRev: latest, superseded, wg, displayKind, hay,
        newerDraft, recentNewerDraft, active: monthsAgo(s.updated) <= 12 });
    });
  }

  function filtered() {
    const q = state.q.trim().toLowerCase();
    const out = SPECS.filter((s) =>
      (state.superseded || !s.superseded) &&
      (!state.status || s.status === state.status) &&
      (!state.wg || s.wg === state.wg) &&
      (!state.active || s.active) &&
      (!q || q.split(/\s+/).every((t) => s.hay.includes(t))));
    const dir = state.dir === "asc" ? 1 : -1;
    const key = {
      title: (s) => (s.title || s.key).toLowerCase(),
      workgroup: (s) => (s.wg === NOT_STATED ? "~" : s.wg.toLowerCase()),
      status: (s) => STATUS_RANK[s.status] * 10 + (s.counts.errata ? 1 : 0),
      updated: (s) => s.updated || "",
    }[state.sort];
    return out.sort((a, b) => {
      const x = key(a), y = key(b);
      return (x < y ? -1 : x > y ? 1 : 0) * dir || (a.title || "").localeCompare(b.title || "");
    });
  }

  // ---------------------------------------------------------------- KPIs
  function renderKpis() {
    const live = SPECS.filter((s) => !s.superseded);
    const n = (st) => live.filter((s) => s.status === st).length;
    const tiles = [
      { key: "", label: "Specifications", value: live.length, note: `${SPECS.length - live.length} obsolete not counted` },
      { key: "final", label: "Final", value: n("final"), note: `${live.filter((s) => s.counts.errata).length} with errata`, color: "final" },
      { key: "implementers", label: "Implementer's Drafts", value: n("implementers"), note: "highest level reached", color: "implementers" },
      { key: "draft", label: "Drafts", value: n("draft"), note: "no ID or Final yet", color: "draft" },
      { key: "active", label: "Active in last 12 months", value: live.filter((s) => s.active).length, note: `${live.filter((s) => s.recentNewerDraft).length} with drafts after their latest approved document` },
    ];
    $("#kpis").innerHTML = tiles.map((t) => {
      const on = t.key === "active" ? state.active : (t.key === state.status && !state.active && (t.key || !state.status));
      return `<button type="button" class="kpi${on && t.key !== "" ? " on" : ""}" data-kpi="${t.key}">
        <div class="kpi-value">${t.value}</div>
        <div class="kpi-label">${t.color ? `<span class="swatch k-${t.color}"></span>` : ""}${esc(t.label)}</div>
        <div class="kpi-note">${esc(t.note)}</div></button>`;
    }).join("");
  }

  // ---------------------------------------------------------------- headline
  // Design system rule 1: the title states the point.
  function renderHeadline() {
    const live = SPECS.filter((s) => !s.superseded);
    const fin = live.filter((s) => s.status === "final").length;
    const active = live.filter((s) => s.active).length;
    const newer = live.filter((s) => s.recentNewerDraft).length;
    $("#headline").textContent = `${fin} of ${live.length} OpenID specifications have reached Final`;
    $("#lead").textContent = `${active} were revised in the last 12 months; ${newer} of them have a draft newer than their latest approved document.`;
  }

  // ---------------------------------------------------------------- charts
  function legend(el, kinds) {
    el.innerHTML = kinds.map((k) => `<span><i class="swatch k-${k}"></i>${KIND_NAME[k]}</span>`).join("");
  }

  function niceMax(v) {
    const step = Math.pow(10, Math.floor(Math.log10(Math.max(v, 1))));
    for (const m of [1, 2, 2.5, 5, 10]) if (m * step >= v) return m * step;
    return 10 * step;
  }

  function renderActivity() {
    const el = $("#chart-activity");
    const counts = Object.create(null);
    SPECS.forEach((s) => s.revisions.forEach((r) => {
      const y = (r.date || r.listed || "").slice(0, 4);
      if (!y) return;
      (counts[y] = counts[y] || { draft: 0, implementers: 0, final: 0, errata: 0 })[r.kind]++;
    }));
    const years = Object.keys(counts).sort();
    const first = +years[0], last = Math.max(+years[years.length - 1], NOW.getFullYear());
    const all = [];
    for (let y = first; y <= last; y++) all.push({ y, c: counts[y] || { draft: 0, implementers: 0, final: 0, errata: 0 } });
    const total = (c) => KINDS.reduce((a, k) => a + c[k], 0);
    const peak = all.reduce((a, d) => (total(d.c) > total(a.c) ? d : a));
    const recent = all.filter((d) => d.y >= NOW.getFullYear() - 4).reduce((a, d) => a + d.c.final + d.c.errata, 0);
    $("#activity-title").textContent = `Activity peaked in ${peak.y} with ${total(peak.c)} revisions; ${recent} Finals and errata sets approved since ${NOW.getFullYear() - 4}`;
    const W = Math.max(el.clientWidth, 320), H = 240, m = { t: 10, r: 8, b: 26, l: 34 };
    const iw = W - m.l - m.r, ih = H - m.t - m.b;
    const max = niceMax(Math.max(...all.map((d) => total(d.c))));
    const band = iw / all.length, bw = Math.max(4, Math.min(28, band * 0.7));
    const ys = (v) => ih - (v / max) * ih;
    let svg = `<svg viewBox="0 0 ${W} ${H}" width="${W}" height="${H}"><g transform="translate(${m.l},${m.t})">`;
    for (let i = 0; i <= 4; i++) {
      const v = (max / 4) * i, y = ys(v);
      svg += `<line class="grid" x1="0" x2="${iw}" y1="${y}" y2="${y}"/><text x="-8" y="${y + 4}" text-anchor="end">${Math.round(v)}</text>`;
    }
    const every = band < 22 ? (band < 12 ? 5 : 2) : 1;
    all.forEach((d, i) => {
      const x = i * band + (band - bw) / 2;
      let acc = 0;
      svg += `<g data-i="${i}">`;
      KINDS.forEach((k) => {
        const v = d.c[k]; if (!v) return;
        const y0 = ys(acc), y1 = ys(acc + v);
        const h = Math.max(0, y0 - y1 - (acc > 0 ? 2 : 0)); // 2px surface gap between segments
        svg += `<rect x="${x}" y="${y1}" width="${bw}" height="${h}" rx="${acc + v === total(d.c) ? 3 : 0}" fill="${kindColor(k)}"/>`;
        acc += v;
      });
      svg += `</g>`;
      if (d.y % every === 0) svg += `<text x="${x + bw / 2}" y="${ih + 18}" text-anchor="middle">${d.y}</text>`;
      svg += `<rect class="hit" data-i="${i}" x="${i * band}" y="0" width="${band}" height="${ih}"/>`;
    });
    svg += `<line class="axis-line" x1="0" x2="${iw}" y1="${ih}" y2="${ih}"/></g></svg>`;
    el.innerHTML = svg;
    el.querySelectorAll(".hit").forEach((h) => {
      const d = all[+h.dataset.i];
      h.addEventListener("mousemove", (e) => showTip(e, String(d.y),
        KINDS.slice().reverse().map((k) => [KIND_NAME[k], d.c[k], k]).concat([["Total", total(d.c)]])));
      h.addEventListener("mouseleave", hideTip);
    });
  }

  // WG names come from the documents, so they are Map keys, never object properties.
  function wgTotals(specs) {
    const groups = new Map();
    specs.filter((s) => !s.superseded).forEach((s) => {
      if (!groups.has(s.wg)) groups.set(s.wg, { final: 0, implementers: 0, draft: 0 });
      groups.get(s.wg)[s.status]++;
    });
    return [...groups].map(([wg, c]) => ({ wg, c, t: c.final + c.implementers + c.draft }))
      .sort((a, b) => (a.wg === NOT_STATED) - (b.wg === NOT_STATED) || b.t - a.t);
  }

  function renderWg() {
    const el = $("#chart-wg");
    const order = ["final", "implementers", "draft"];
    const rows = wgTotals(SPECS);
    const top = rows.find((r) => r.wg !== NOT_STATED);
    if (top) $("#wg-title").textContent = `${top.wg} maintains the most specifications (${top.t}, ${top.c.final} Final)`;
    const W = Math.max(el.clientWidth, 300), row = 22, m = { t: 4, r: 30, b: 4, l: 168 };
    const H = m.t + m.b + rows.length * row, iw = W - m.l - m.r;
    const max = Math.max(...rows.map((r) => r.t));
    let svg = `<svg viewBox="0 0 ${W} ${H}" width="${W}" height="${H}"><g transform="translate(${m.l},${m.t})">`;
    rows.forEach((r, i) => {
      const y = i * row, bh = 14;
      svg += `<text class="wg-label" x="-10" y="${y + bh - 2}" text-anchor="end">${esc(r.wg)}</text>`;
      let acc = 0;
      order.forEach((k) => {
        const v = r.c[k]; if (!v) return;
        const x = (acc / max) * iw, w = (v / max) * iw - (acc + v < r.t ? 2 : 0);
        svg += `<rect x="${x}" y="${y}" width="${Math.max(w, 1)}" height="${bh}" rx="${acc + v === r.t ? 3 : 0}" fill="${kindColor(k)}"/>`;
        acc += v;
      });
      svg += `<text class="total" x="${(r.t / max) * iw + 6}" y="${y + bh - 2}">${r.t}</text>`;
      svg += `<rect class="hit" data-i="${i}" x="${-m.l}" y="${y - 3}" width="${W}" height="${row}"/>`;
    });
    svg += `</g></svg>`;
    el.innerHTML = svg;
    el.querySelectorAll(".hit").forEach((h) => {
      const r = rows[+h.dataset.i];
      h.addEventListener("mousemove", (e) => showTip(e, r.wg,
        order.map((k) => [KIND_NAME[k], r.c[k], k]).concat([["Total", r.t], ["", "Click to filter"]])));
      h.addEventListener("mouseleave", hideTip);
      h.addEventListener("click", () => { state.wg = state.wg === r.wg ? "" : r.wg; $("#wg").value = state.wg; update(); });
    });
  }

  function showTip(e, title, rows) {
    const tt = $("#tooltip");
    tt.innerHTML = `<div class="tt-title">${esc(title)}</div>` + rows.map(([l, v, k]) =>
      `<div class="tt-row"><span>${k ? `<i class="swatch k-${k}"></i>` : ""}${esc(l)}</span><strong>${esc(v)}</strong></div>`).join("");
    tt.hidden = false;
    const r = tt.getBoundingClientRect();
    let x = e.clientX + 14, y = e.clientY + 14;
    if (x + r.width > innerWidth - 8) x = e.clientX - r.width - 14;
    if (y + r.height > innerHeight - 8) y = e.clientY - r.height - 14;
    tt.style.left = x + "px"; tt.style.top = y + "px";
  }
  function hideTip() { $("#tooltip").hidden = true; }

  // ---------------------------------------------------------------- table
  function statusBadge(s) {
    if (s.superseded && !s.milestoneRev && !s.latestRev) return `<span class="badge renamed">${esc(s.redirect.reason)}</span>`;
    const k = s.status === "final" && s.counts.errata ? "errata" : s.status;
    let label = s.status_label;
    if (k === "errata") label = "Final · Errata " + s.milestoneRev.number;
    else if (s.status === "implementers" && s.milestoneRev) label = "Implementer's Draft " + s.milestoneRev.number;
    return `<span class="badge ${k}">${esc(label)}</span>`;
  }
  function track(s) {
    // Three maturity stages. Errata corrects a Final; it is not a further stage, so it
    // appears in the chip label ("Final · Errata 2"), not as a fourth dot.
    const lvl = { draft: 1, implementers: 2, final: 3 }[s.status];
    return `<div class="track" title="Draft · Implementer's Draft · Final" aria-hidden="true">${["draft", "implementers", "final"].map((k, i) =>
      `${i ? "<b></b>" : ""}<i class="${i < lvl ? "on" : ""}"></i>`).join("")}</div>`;
  }
  // Short name of the latest approved document: "Final", "Errata Set 2", "ID2".
  function approvedShort(r) {
    if (!r) return "";
    return r.kind === "implementers" ? "ID" + (r.number || "") : r.kind === "errata" ? "Errata Set " + (r.number || "") : "Final";
  }
  function flags(s) {
    const f = [];
    if (s.superseded) f.push(`<span class="badge renamed">${esc(s.redirect.reason.replace(/ ?Specification ?/, "")) || "Obsolete"}</span>`);
    if (s.issues && s.issues.some((i) => i.severity === "error")) f.push(`<span class="flag flag-issue" title="The published document has a metadata error; see details">Metadata error in source</span>`);
    if (s.newerDraft) f.push(`<span class="flag" title="A draft has been published after the latest approved document. The dashboard cannot tell whether it is errata, a revision or the next approval step.">Drafts after ${esc(approvedShort(s.milestoneRev))}</span>`);
    return f.length ? `<div class="flags">${f.join("")}</div>` : "";
  }
  const ISSUE_LABEL = { error: "Fix in source", check: "Confirm", rename: "Possible rename", stub: "Add redirect", missing: "Add to source", historical: "Missing (historical)", naming: "Harmonise", other: "Check" };
  function issuesBlock(s) {
    if (!s.issues || !s.issues.length) return "";
    return `<div class="d-section kicker">Source metadata issues</div><ul class="issues">${s.issues.map((i) =>
      `<li class="issue ${i.severity}"><span class="issue-tag">${ISSUE_LABEL[i.severity]}</span>
        <div><strong>${esc(i.category)}:</strong> document says “${esc(i.found)}”, expected ${esc(i.expected)}.
        <div class="issue-detail">${esc(i.detail)}</div>
        <div class="issue-files">${i.files.map((f) => `<a class="mono" href="${specUrl(f)}" target="_blank" rel="noopener">${esc(f)}</a>`).join(" ")}</div></div></li>`).join("")}</ul>`;
  }
  function wgMark(s) {
    if (!s.workgroup_source || s.workgroup_source === "document") return "";
    const why = s.workgroup_source === "curated" ? "Set by OIDF staff — not stated in the document" : "Inferred — not stated in the document";
    return ` <span class="inferred-mark" title="${why}">*</span>`;
  }
  function formerLine(s) {
    if (!s.former_names) return "";
    return `<span class="formerly">Formerly ${s.former_names.map((f) =>
      f.title && f.title !== s.title ? `${esc(f.title)} (<span class="mono">${esc(f.key)}</span>)` : `<span class="mono">${esc(f.key)}</span>`).join(", ")}</span>`;
  }
  function revCell(r) {
    if (!r) return `<span class="spec-key">—</span>`;
    return `<a class="rev-link" href="${specUrl(r.file)}" target="_blank" rel="noopener" data-stop>${esc(r.label)}</a><span class="rev-date">${fmtDate(r.date || r.listed)}</span>`;
  }

  function renderTable() {
    const rows = filtered();
    $("#count").textContent = `${rows.length} of ${SPECS.filter((s) => state.superseded || !s.superseded).length}`;
    $("#empty").hidden = rows.length > 0;
    $("#specs tbody").innerHTML = rows.map((s) => {
      const rev = s.milestoneRev || s.latestRev;
      const href = s.current_url ? specUrl(s.current_url) : rev ? specUrl(rev.file) : SPECS_BASE;
      const latestDiff = s.latestRev && s.latestRev !== s.milestoneRev;
      return `<tr data-key="${esc(s.key)}" class="${s.superseded ? "superseded" : ""}" tabindex="0">
        <td data-label="Specification"><a class="spec-title" href="${href}" target="_blank" rel="noopener" data-stop>${esc(s.title || s.key)}</a>
          <span class="spec-key mono">${esc(s.key)}</span>${formerLine(s)}</td>
        <td class="td-wg" data-label="Working group">${esc(s.wg)}${wgMark(s)}</td>
        <td data-label="Status">${statusBadge(s)}${track(s)}${flags(s)}</td>
        <td data-label="Latest approved">${revCell(s.milestoneRev)}</td>
        <td data-label="Latest revision">${latestDiff || !s.milestoneRev ? revCell(s.latestRev) : `<span class="spec-key">same</span>`}</td>
        <td class="td-date" data-label="Updated">${fmtDate(s.updated)}<span class="rev-date">${relTime(s.updated)}</span></td>
        <td class="td-ed" data-label="Editors">${esc(editorsShort(s.authors))}</td>
      </tr>`;
    }).join("");
    document.querySelectorAll("#specs th.sortable").forEach((th) => {
      th.classList.toggle("sorted", th.dataset.sort === state.sort);
      th.classList.toggle("asc", th.dataset.sort === state.sort && state.dir === "asc");
      th.classList.toggle("desc", th.dataset.sort === state.sort && state.dir === "desc");
    });
  }

  // ---------------------------------------------------------------- drawer
  function openDrawer(key, push = true) {
    const s = SPECS.find((x) => x.key === key);
    if (!s) return;
    state.open = key;
    const m = s.milestoneRev, l = s.latestRev;
    const k = s.status === "final" && s.counts.errata ? "errata" : s.status;
    const allAuthors = (m || l || { authors: [] }).authors;
    const revs = s.revisions.slice().reverse();
    const target = s.redirect && s.redirect.target_key ? SPECS.find((x) => x.key === s.redirect.target_key) : null;
    const LIMIT = 15;
    const revItem = (r, i) => {
      const isMs = r.kind !== "draft";
      const fmts = r.formats.map((f) => `<a href="${specUrl(r.file, f)}" target="_blank" rel="noopener">${f}</a>`).join("");
      const titleNote = r.title && s.title && !r.title.startsWith(s.title) ? `<span class="t-title">Published as “${esc(r.title)}”</span>` : "";
      return `<li class="${isMs ? "milestone" : ""}" ${i >= LIMIT ? 'data-more hidden' : ""}>
        <span class="dot"></span>
        <a class="t-label" href="${specUrl(r.file)}" target="_blank" rel="noopener">${esc(r.label)}</a>
        <span class="t-date">${fmtDate(r.date || r.listed)}${r.date ? "" : ' <span title="Date not found in document; directory listing date shown">†</span>'}</span>
        ${titleNote}
        <span class="t-meta"><span class="mono">${esc(r.file)}</span>${fmts}</span></li>`;
    };
    $("#drawer-body").innerHTML = `
      <div class="kicker">${esc(s.wg)}${s.workgroup_source && s.workgroup_source !== "document" ? ` (${s.workgroup_source === "curated" ? "curated" : "inferred"})` : ""}&nbsp;&nbsp;·&nbsp;&nbsp;${esc(s.status_label)}</div>
      <h2 class="d-title" id="d-title">${esc(s.title || s.key)}</h2>
      <div class="d-badges">${statusBadge(s)}${flags(s).replace(/<\/?div[^>]*>/g, "")}</div>
      ${s.redirect ? `<div class="callout"><span class="callout-label">${esc(s.redirect.reason)}:</span> ${esc((s.redirect.message || "").replace(s.redirect.reason, "").replace(/Your browser should load[^.]*\.\s*/, "").trim())}
        ${target ? ` <button class="linkbtn" data-goto="${esc(target.key)}">Open ${esc(target.title)} →</button>` : ""}</div>` : ""}
      <dl class="d-grid">
        <dt>Filename stem</dt><dd class="mono">${esc(s.key)}</dd>
        ${s.current_url ? `<dt>Canonical URL</dt><dd><a href="${specUrl(s.current_url)}" target="_blank" rel="noopener">${esc(specUrl(s.current_url))}</a></dd>` : ""}
        <dt>Latest approved</dt><dd>${m ? `<a href="${specUrl(m.file)}" target="_blank" rel="noopener">${esc(m.label)}</a> · ${fmtDate(m.date || m.listed)}` : "No Implementer's Draft or Final yet"}</dd>
        <dt>Latest revision</dt><dd>${l ? `<a href="${specUrl(l.file)}" target="_blank" rel="noopener">${esc(l.label)}</a> · ${fmtDate(l.date || l.listed)} <span class="spec-key">(${relTime(l.date || l.listed)})</span>` : "—"}</dd>
        <dt>Revisions</dt><dd>${s.counts.draft} drafts · ${s.counts.implementers} Implementer's Drafts · ${s.counts.final} Final · ${s.counts.errata} errata</dd>
        ${s.workgroup_raw && s.workgroup_raw !== s.wg ? `<dt>WG as stated</dt><dd>${esc(s.workgroup_raw)}</dd>` : ""}
        ${s.note ? `<dt>Note</dt><dd>${esc(s.note)}</dd>` : ""}
        ${s.curated ? `<dt>Curated fields</dt><dd>${esc(s.curated.join(", "))}</dd>` : ""}
      </dl>
      ${s.former_names ? `<div class="d-section kicker">Published earlier as</div><ul class="former">${s.former_names.map((f) =>
        `<li><span class="mono">${esc(f.key)}</span>${f.title && f.title !== s.title ? `<span>${esc(f.title)}</span>` : ""}<span class="how">${esc(f.how.startsWith("redirect") ? "redirect page on openid.net" : f.how)}</span></li>`).join("")}</ul>` : ""}
      ${issuesBlock(s)}
      <div class="d-section kicker">Editors${m ? ` of ${esc(m.label)}` : ""}</div>
      <div class="authors">${allAuthors.length ? allAuthors.map((a) => `<div class="author"><div>${esc(a.name)}</div>${a.org ? `<div class="org">${esc(a.org)}</div>` : ""}</div>`).join("") : '<span class="spec-key">Not stated</span>'}</div>
      <div class="d-section kicker">Revision history</div>
      <ol class="timeline">${revs.map(revItem).join("")}</ol>
      ${revs.length > LIMIT ? `<p class="collapsed-note"><button class="linkbtn" id="more">Show all ${revs.length} revisions</button></p>` : ""}
    `;
    const more = $("#more");
    if (more) more.onclick = () => { document.querySelectorAll("#drawer [data-more]").forEach((li) => (li.hidden = false)); more.remove(); };
    const go = $("#drawer [data-goto]");
    if (go) go.onclick = () => { if (!state.superseded && target.superseded) state.superseded = true; openDrawer(go.dataset.goto); };
    const d = $("#drawer");
    d.setAttribute("aria-hidden", "false");
    $(".drawer-panel").scrollTop = 0;
    $(".drawer-close").focus();
    if (push) writeHash();
  }
  function closeDrawer() {
    $("#drawer").setAttribute("aria-hidden", "true");
    state.open = null;
    writeHash();
  }

  // ---------------------------------------------------------------- state <-> URL
  function writeHash() {
    const p = new URLSearchParams();
    if (state.q) p.set("q", state.q);
    if (state.status) p.set("status", state.status);
    if (state.wg) p.set("wg", state.wg);
    if (state.active) p.set("active", "1");
    if (state.superseded) p.set("all", "1");
    if (state.sort !== "updated" || state.dir !== "desc") p.set("sort", state.sort + ":" + state.dir);
    if (state.open) p.set("spec", state.open);
    const h = p.toString();
    history.replaceState(null, "", h ? "#" + h : location.pathname + location.search);
  }
  function parseHash(hash) {
    const p = new URLSearchParams(hash.replace(/^#/, ""));
    const [sort, dir] = (p.get("sort") || "").split(":");
    const out = {
      q: p.get("q") || "", status: STATUSES.has(p.get("status")) ? p.get("status") : "", wg: p.get("wg") || "",
      active: p.get("active") === "1", superseded: p.get("all") === "1",
      sort: SORTS.has(sort) ? sort : "updated", open: p.get("spec"),
    };
    out.dir = dir === "asc" || dir === "desc" ? dir : out.sort === "title" || out.sort === "workgroup" ? "asc" : "desc";
    return out;
  }
  function readHash() { Object.assign(state, parseHash(location.hash)); }
  function syncControls() {
    $("#q").value = state.q;
    $("#wg").value = state.wg;
    $("#active").checked = state.active;
    $("#superseded").checked = state.superseded;
    document.querySelectorAll("#status-seg button").forEach((b) => b.classList.toggle("on", b.dataset.v === state.status));
  }

  function update() {
    syncControls();
    renderKpis();
    renderTable();
    writeHash();
  }

  // ---------------------------------------------------------------- CSV
  // Spreadsheets evaluate a cell that starts with = + - @ (or the full-width forms), and
  // some trim leading whitespace or control characters first. Any such cell gets a leading
  // ' so it stays text; line breaks become spaces so every record is one line.
  const CSV_RISKY = /^[\s\u0000-\u001f\u007f-\u009f\u00a0\u1680\u2000-\u200f\u2028-\u202f\u205f\u3000\ufeff=+\-@\uff1d\uff0b\uff0d\uff20]/;
  function csvCell(v) {
    let t = String(v ?? "").replace(/[\r\n\u2028\u2029]+/g, " ");
    if (CSV_RISKY.test(t)) t = "'" + t;
    return `"${t.replace(/"/g, '""')}"`;
  }
  function exportCsv() {
    const cols = ["title", "key", "working_group", "status", "latest_approved", "latest_approved_date", "latest_revision", "latest_revision_date", "editors", "url"];
    const q = csvCell;
    const lines = [cols.join(",")].concat(filtered().map((s) => [
      s.title, s.key, s.wg, s.status_label + (s.counts.errata && s.milestoneRev ? " (errata " + s.milestoneRev.number + ")" : ""),
      s.milestoneRev && s.milestoneRev.file, s.milestoneRev && (s.milestoneRev.date || s.milestoneRev.listed),
      s.latestRev && s.latestRev.file, s.latestRev && (s.latestRev.date || s.latestRev.listed),
      (s.authors || []).map((a) => a.name).join("; "),
      s.current_url ? specUrl(s.current_url) : "",
    ].map(q).join(",")));
    const blob = new Blob([lines.join("\n")], { type: "text/csv" });
    const a = Object.assign(document.createElement("a"), { href: URL.createObjectURL(blob), download: "openid-specs.csv" });
    a.click();
    URL.revokeObjectURL(a.href);
  }

  // ---------------------------------------------------------------- wire up
  function bind() {
    let t;
    $("#q").addEventListener("input", (e) => { clearTimeout(t); t = setTimeout(() => { state.q = e.target.value; update(); }, 120); });
    $("#wg").addEventListener("change", (e) => { state.wg = e.target.value; update(); });
    $("#active").addEventListener("change", (e) => { state.active = e.target.checked; update(); });
    $("#superseded").addEventListener("change", (e) => { state.superseded = e.target.checked; update(); });
    $("#status-seg").addEventListener("click", (e) => { const b = e.target.closest("button"); if (b) { state.status = b.dataset.v; update(); } });
    $("#kpis").addEventListener("click", (e) => {
      const b = e.target.closest(".kpi"); if (!b) return;
      const k = b.dataset.kpi;
      if (k === "active") state.active = !state.active;
      else { state.status = state.status === k ? "" : k; state.active = false; }
      update();
    });
    document.querySelectorAll("#specs th.sortable").forEach((th) => th.addEventListener("click", () => {
      const k = th.dataset.sort;
      if (state.sort === k) state.dir = state.dir === "asc" ? "desc" : "asc";
      else { state.sort = k; state.dir = k === "title" || k === "workgroup" ? "asc" : "desc"; }
      update();
    }));
    const tbody = $("#specs tbody");
    tbody.addEventListener("click", (e) => {
      if (e.target.closest("[data-stop]")) return;
      const tr = e.target.closest("tr"); if (tr) openDrawer(tr.dataset.key);
    });
    tbody.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && e.target.matches("tr")) openDrawer(e.target.dataset.key);
    });
    $("#drawer").addEventListener("click", (e) => { if (e.target.closest("[data-close]")) closeDrawer(); });
    document.addEventListener("keydown", (e) => { if (e.key === "Escape" && state.open) closeDrawer(); });
    $("#export").addEventListener("click", exportCsv);
    let rz;
    addEventListener("resize", () => { clearTimeout(rz); rz = setTimeout(() => { renderActivity(); renderWg(); }, 150); });
  }

  async function main() {
    try {
      const res = await fetch(DATA_URL, { cache: "no-cache" });
      if (!res.ok) throw new Error(res.status + " " + res.statusText);
      DATA = validate(await res.json());
    } catch (err) {
      $("#generated").textContent = "Could not load data";
      $("#specs tbody").innerHTML = `<tr><td colspan="7" class="empty">Failed to load ${esc(DATA_URL)}: ${esc(err.message)}</td></tr>`;
      return;
    }
    SPECS = prepare(DATA);
    $("#generated").textContent = "Data as of " + fmtDate(DATA.generated.slice(0, 10));
    $("#foot-date").textContent = fmtDate(DATA.generated.slice(0, 10));
    renderHeadline();
    const wgs = [...new Set(SPECS.map((s) => s.wg))].sort((a, b) => (a === NOT_STATED) - (b === NOT_STATED) || a.localeCompare(b));
    $("#wg").insertAdjacentHTML("beforeend", wgs.map((w) => `<option>${esc(w)}</option>`).join(""));
    legend($("#legend-activity"), KINDS);
    legend($("#legend-wg"), ["final", "implementers", "draft"]);
    readHash();
    bind();
    update();
    renderActivity();
    renderWg();
    if (state.open) openDrawer(state.open, false);
    addEventListener("hashchange", () => { readHash(); update(); if (state.open) openDrawer(state.open, false); else $("#drawer").setAttribute("aria-hidden", "true"); });
  }

  // Under Node (tests/app.test.mjs) expose the data-handling functions instead of rendering.
  if (typeof module === "object" && module.exports) module.exports = { validate, prepare, wgTotals, csvCell, parseHash, specUrl, fmtDate };
  else main();
})();

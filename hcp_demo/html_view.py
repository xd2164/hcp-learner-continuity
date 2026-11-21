"""Build a self-contained HTML view of the Track A results.

    python -m hcp_demo.html_view            # writes docs/index.html

The page embeds the results as JSON and renders with plain DOM APIs (no
external scripts, fonts or styles), so it opens from disk or GitHub Pages.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from . import track_a
from .check_scenarios import check_bundle

ROOT = Path(__file__).resolve().parent.parent

TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>HCP Learner Continuity: Track A</title>
<style>
.viz-root {
  color-scheme: light;
  --page: #f9f9f7; --surface-1: #fcfcfb; --text-primary: #0b0b0b; --text-secondary: #52514e;
  --muted: #898781; --grid: #e1e0d9; --baseline: #c3c2b7; --border: rgba(11,11,11,0.10);
  --series-1: #2a78d6; --series-2: #eb6834; --series-3: #1baf7a;
  --good-text: #006300; --critical: #d03b3b; --hover: rgba(11,11,11,0.04);
}
@media (prefers-color-scheme: dark) {
  :root:where(:not([data-theme="light"])) .viz-root {
    color-scheme: dark;
    --page: #0d0d0d; --surface-1: #1a1a19; --text-primary: #f0efec; --text-secondary: #c3c2b7;
    --muted: #898781; --grid: #2c2c2a; --baseline: #383835; --border: rgba(255,255,255,0.10);
    --series-1: #3987e5; --series-2: #d95926; --series-3: #199e70;
    --good-text: #0ca30c; --critical: #d03b3b; --hover: rgba(255,255,255,0.05);
  }
}
:root[data-theme="dark"] .viz-root {
  color-scheme: dark;
  --page: #0d0d0d; --surface-1: #1a1a19; --text-primary: #f0efec; --text-secondary: #c3c2b7;
  --muted: #898781; --grid: #2c2c2a; --baseline: #383835; --border: rgba(255,255,255,0.10);
  --series-1: #3987e5; --series-2: #d95926; --series-3: #199e70;
  --good-text: #0ca30c; --critical: #d03b3b; --hover: rgba(255,255,255,0.05);
}
* { box-sizing: border-box; }
body { margin: 0; }
.viz-root { background: var(--page); color: var(--text-primary); min-height: 100vh;
  font: 15px/1.5 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
.wrap { max-width: 1080px; margin: 0 auto; padding: 32px 20px 64px; }
header { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; }
h1 { font-size: 28px; margin: 0 0 4px; letter-spacing: -0.01em; }
h2 { font-size: 18px; margin: 0 0 4px; }
h3 { font-size: 15px; margin: 0 0 6px; }
.sub { color: var(--text-secondary); margin: 0; }
.note { color: var(--muted); font-size: 13px; }
.card { background: var(--surface-1); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-top: 20px; }
.tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-top: 20px; }
.tile { background: var(--surface-1); border: 1px solid var(--border); border-radius: 12px; padding: 16px; }
.tile .label { color: var(--text-secondary); font-size: 13px; }
.tile .value { font-size: 28px; font-weight: 600; margin-top: 2px; }
.tile .delta { font-size: 13px; color: var(--muted); }
button { font: inherit; color: inherit; background: var(--surface-1); border: 1px solid var(--border);
  border-radius: 8px; padding: 6px 12px; cursor: pointer; }
button:hover { background: var(--hover); }
button[aria-pressed="true"] { border-color: var(--text-secondary); font-weight: 600; }
.row { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
.chart-head { display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; flex-wrap: wrap; }
.legend { display: flex; gap: 6px 16px; flex-wrap: wrap; color: var(--text-secondary); font-size: 13px; margin: 8px 0; }
.legend span { display: inline-flex; align-items: center; gap: 6px; }
.sw { width: 12px; height: 12px; border-radius: 3px; display: inline-block; }
svg text { fill: var(--text-secondary); font-size: 12px; }
svg .muted { fill: var(--muted); }
.bar { cursor: default; outline: none; }
.bar:hover path, .bar:focus path { filter: brightness(1.12); }
.bar:focus-visible .hit { stroke: var(--text-primary); stroke-width: 1; }
table { border-collapse: collapse; width: 100%; font-size: 14px; }
th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--grid); vertical-align: top; }
th { color: var(--text-secondary); font-weight: 600; font-size: 13px; }
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
.tip { position: fixed; pointer-events: none; background: var(--surface-1); border: 1px solid var(--border);
  border-radius: 8px; padding: 8px 10px; font-size: 13px; box-shadow: 0 4px 16px rgba(0,0,0,0.12); display: none; z-index: 10; }
.tip .t { color: var(--text-secondary); margin-bottom: 4px; }
.tip .r { display: flex; align-items: center; gap: 8px; }
.tip .k { width: 12px; height: 2px; display: inline-block; }
.tip strong { font-variant-numeric: tabular-nums; }
.learners { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 12px; }
.steps { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 12px; margin-top: 16px; }
.step { border: 1px solid var(--border); border-radius: 10px; padding: 12px; }
.step .n { color: var(--muted); font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; }
.step ul { margin: 6px 0 0; padding-left: 18px; color: var(--text-secondary); font-size: 13px; }
.step p { margin: 4px 0; font-size: 14px; }
.pill { display: inline-block; font-size: 12px; padding: 1px 8px; border-radius: 999px; border: 1px solid var(--border); color: var(--text-secondary); }
.ok { color: var(--good-text); font-weight: 600; }
.seg { display: flex; gap: 2px; height: 16px; margin: 8px 0; }
.seg div { height: 100%; }
.seg div:first-child { border-radius: 4px 0 0 4px; }
.seg div:last-child { border-radius: 0 4px 4px 0; }
.seg div:only-child { border-radius: 4px; }
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
@media (max-width: 760px) { .grid2 { grid-template-columns: 1fr; } }
footer { margin-top: 28px; color: var(--muted); font-size: 13px; }
a { color: var(--series-1); }
</style>
</head>
<body>
<div class="viz-root">
<div class="wrap">
  <header>
    <div>
      <h1>One learner. Two AI tutors. No starting over.</h1>
      <p class="sub">Track A of HCP Learner Continuity: a tutor handoff through the Human Context Protocol (2.0-draft-3), run on ten synthetic learners.</p>
    </div>
    <button id="theme" type="button" aria-label="Toggle light or dark theme">Theme</button>
  </header>

  <div class="tiles" id="tiles"></div>

  <section class="card" aria-labelledby="c1">
    <div class="chart-head">
      <div>
        <h2 id="c1">Intake questions Tutor B needs before targeted practice</h2>
        <p class="sub">Per learner, with the context HCP hands over versus starting cold.</p>
      </div>
      <button id="tableToggle" type="button" aria-pressed="false">Show table</button>
    </div>
    <div class="legend" id="legend1"></div>
    <div id="chart1"></div>
    <div id="table1" hidden></div>
    <p class="note">Two diagnostic questions per standard Tutor B has no evidence for. With HCP, only standards that are unassessed, or where Tutor A's model-inferred evidence needs confirming, need questions.</p>
  </section>

  <section class="card" aria-labelledby="c2">
    <h2 id="c2">Follow one learner through the handoff</h2>
    <p class="sub">Pick a learner. Every step below is computed from their HCP record.</p>
    <div class="learners" id="learners" role="group" aria-label="Learners"></div>
    <div id="detail"></div>
  </section>

  <footer>
    <p>All learners, schools and records are synthetic (Understudy, seed 2368342781). No real student data. The tutors are rule-based stand-ins and session results are simulated, so these figures show what the context makes possible, not measured learning gains.</p>
    <p>The demo provider is not a conformant HCP implementation. It models the access decisions and passes the fixture's scenarios. HCP is a working draft and its format will change. Generated by <code>python -m hcp_demo.html_view</code>.</p>
  </footer>
</div>
<div class="tip" id="tip" role="status" aria-live="polite"></div>
</div>

<script type="application/json" id="data">__DATA__</script>
<script>
(function () {
  "use strict";
  const D = JSON.parse(document.getElementById("data").textContent);
  const R = D.results;
  const NS = "http://www.w3.org/2000/svg";
  const $ = (id) => document.getElementById(id);
  function el(tag, attrs, text) {
    const n = document.createElement(tag);
    for (const k in (attrs || {})) n.setAttribute(k, attrs[k]);
    if (text != null) n.textContent = text;
    return n;
  }
  function svg(tag, attrs) {
    const n = document.createElementNS(NS, tag);
    for (const k in (attrs || {})) n.setAttribute(k, attrs[k]);
    return n;
  }
  const fmt = (n) => Number(n).toLocaleString("en-US");

  // Theme toggle: explicit stamp wins over the OS setting both ways.
  $("theme").addEventListener("click", () => {
    const root = document.documentElement;
    const dark = root.dataset.theme ? root.dataset.theme === "dark"
      : window.matchMedia("(prefers-color-scheme: dark)").matches;
    root.dataset.theme = dark ? "light" : "dark";
  });

  // ---- Tiles
  const withSum = R.reduce((a, r) => a + r.metrics.intakeItemsWithHCP, 0);
  const withoutSum = R.reduce((a, r) => a + r.metrics.intakeItemsWithoutHCP, 0);
  const minutes = R.reduce((a, r) => a + r.metrics.intakeMinutesSaved, 0);
  const sessions = R.filter((r) => r.tutorA.session);
  const handed = sessions.filter((r) => r.hcp.tutorBSawTutorAEvidence).length;
  const tiles = [
    ["Fixture scenarios passed", D.check.passed + " / " + D.check.total, "access decisions match the fixture"],
    ["Intake questions, all learners", fmt(withSum) + " vs " + fmt(withoutSum), "with HCP vs without"],
    ["Learner time saved", fmt(Math.round(minutes / 60 * 10) / 10) + " h", fmt(minutes) + " minutes at 1.5 min per question"],
    ["Tutor A evidence reached Tutor B", handed + " / " + sessions.length, "sessions handed over"],
    ["Off-limits entries disclosed", String(D.check.leaks), "across all fixture scenarios"],
  ];
  for (const [l, v, d] of tiles) {
    const t = el("div", { class: "tile" });
    t.append(el("div", { class: "label" }, l), el("div", { class: "value" }, v), el("div", { class: "delta" }, d));
    $("tiles").append(t);
  }

  // ---- Tooltip
  const tip = $("tip");
  function showTip(evt, title, rows) {
    tip.replaceChildren(el("div", { class: "t" }, title));
    for (const [color, value, name] of rows) {
      const r = el("div", { class: "r" });
      const k = el("span", { class: "k" }); k.style.background = color;
      r.append(k, el("strong", {}, value), el("span", { class: "note" }, name));
      tip.append(r);
    }
    tip.style.display = "block";
    let x, y;
    if (evt.clientX != null && evt.type !== "focus") { x = evt.clientX; y = evt.clientY; }
    else { const b = evt.target.getBoundingClientRect(); x = b.right; y = b.top; }
    const w = tip.offsetWidth, h = tip.offsetHeight;
    tip.style.left = Math.min(x + 14, window.innerWidth - w - 8) + "px";
    tip.style.top = Math.max(8, y - h - 10) + "px";
  }
  const hideTip = () => { tip.style.display = "none"; };

  // ---- Chart 1: grouped horizontal bars
  const S1 = { key: "intakeItemsWithHCP", name: "With HCP", color: "var(--series-1)" };
  const S2 = { key: "intakeItemsWithoutHCP", name: "Without HCP (cold start)", color: "var(--series-2)" };
  for (const s of [S1, S2]) {
    const sp = el("span"); const sw = el("span", { class: "sw" }); sw.style.background = s.color;
    sp.append(sw, document.createTextNode(s.name)); $("legend1").append(sp);
  }
  function barPath(x0, y, len, h) {
    // square at the baseline, 4px rounded data-end
    const r = Math.min(4, len / 2, h / 2);
    if (len <= 0) return "";
    return `M${x0},${y} H${x0 + len - r} Q${x0 + len},${y} ${x0 + len},${y + r} V${y + h - r} Q${x0 + len},${y + h} ${x0 + len - r},${y + h} H${x0} Z`;
  }
  function drawChart() {
    const host = $("chart1"); host.replaceChildren();
    const W = Math.max(host.clientWidth, 320);
    const labelW = W < 520 ? 110 : 170, right = 40, top = 8, barH = 10, pair = 2, rowH = 36;
    const H = top + R.length * rowH + 28;
    const max = Math.ceil(Math.max(...R.map((r) => r.metrics[S2.key])) / 20) * 20;
    const plotW = W - labelW - right;
    const sx = (v) => (v / max) * plotW;
    const s = svg("svg", { width: W, height: H, role: "img",
      "aria-label": "Intake questions per learner, with HCP versus without. Values are in the table view." });
    for (let t = 0; t <= max; t += 20) {
      const x = labelW + sx(t);
      s.append(svg("line", { x1: x, x2: x, y1: top - 4, y2: H - 24, stroke: t === 0 ? "var(--baseline)" : "var(--grid)", "stroke-width": 1 }));
      const tx = svg("text", { x: x, y: H - 8, "text-anchor": "middle", class: "muted" }); tx.textContent = t; s.append(tx);
    }
    R.forEach((r, i) => {
      const y0 = top + i * rowH + (rowH - (2 * barH + pair)) / 2;
      const name = svg("text", { x: labelW - 10, y: y0 + barH + 4, "text-anchor": "end" });
      name.textContent = r.learner.name + " (Gr " + r.learner.grade + ")"; s.append(name);
      [S1, S2].forEach((ser, j) => {
        const v = r.metrics[ser.key];
        const y = y0 + j * (barH + pair);
        const g = svg("g", { class: "bar", tabindex: 0, role: "img",
          "aria-label": `${r.learner.name}: ${ser.name} ${v} questions` });
        g.append(svg("rect", { class: "hit", x: labelW, y: y - 2, width: Math.max(sx(v), 8) + 30, height: barH + 4, fill: "transparent" }));
        if (v > 0) g.append(svg("path", { d: barPath(labelW, y, sx(v), barH), fill: ser.color }));
        else g.append(svg("rect", { x: labelW, y: y, width: 2, height: barH, fill: ser.color }));
        const lab = svg("text", { x: labelW + sx(v) + 6, y: y + barH - 1, class: "muted", "font-size": 11 });
        lab.textContent = v; g.append(lab);
        const rows = [[S1.color, fmt(r.metrics[S1.key]), S1.name], [S2.color, fmt(r.metrics[S2.key]), S2.name]];
        const title = r.learner.name + ", grade " + r.learner.grade;
        g.addEventListener("pointermove", (e) => showTip(e, title, rows));
        g.addEventListener("focus", (e) => showTip(e, title, rows));
        g.addEventListener("pointerleave", hideTip); g.addEventListener("blur", hideTip);
        g.addEventListener("click", () => select(i, true));
        s.append(g);
      });
    });
    host.append(s);
  }
  function drawTable() {
    const t = el("table");
    const hr = el("tr");
    for (const [h, c] of [["Learner", ""], ["Grade", ""], ["With HCP", "num"], ["Without HCP", "num"], ["Minutes saved", "num"], ["Preference signals", "num"]])
      hr.append(el("th", { class: c, scope: "col" }, h));
    { const th = el("thead"); th.append(hr); t.append(th); }
    const tb = el("tbody"); t.append(tb);
    for (const r of R) {
      const tr = el("tr"); const m = r.metrics;
      for (const [v, c] of [[r.learner.name, ""], [r.learner.grade, ""], [m.intakeItemsWithHCP, "num"], [m.intakeItemsWithoutHCP, "num"], [m.intakeMinutesSaved, "num"], [m.personalizationSignalsWithHCP, "num"]])
        tr.append(el("td", { class: c }, String(v)));
      tb.append(tr);
    }
    $("table1").replaceChildren(t);
  }
  $("tableToggle").addEventListener("click", (e) => {
    const on = e.currentTarget.getAttribute("aria-pressed") !== "true";
    e.currentTarget.setAttribute("aria-pressed", on);
    e.currentTarget.textContent = on ? "Show chart" : "Show table";
    $("table1").hidden = !on; $("chart1").hidden = on; $("legend1").hidden = on;
  });

  // ---- Learner detail
  const SRC = [
    ["issuer-attested", "Issuer-attested (school credentials)", "var(--series-1)"],
    ["person-declared", "Person-declared (learner's own words)", "var(--series-2)"],
    ["model-inferred", "Model-inferred (practice systems, Tutor A)", "var(--series-3)"],
  ];
  function step(n, title, lines, extra) {
    const c = el("div", { class: "step" });
    c.append(el("div", { class: "n" }, "Step " + n), el("h3", {}, title));
    if (extra) c.append(extra);
    if (lines.length) { const ul = el("ul"); for (const l of lines) ul.append(el("li", {}, l)); c.append(ul); }
    return c;
  }
  function p(text, cls) { return el("p", cls ? { class: cls } : {}, text); }

  function detail(r) {
    const box = $("detail"); box.replaceChildren();
    const L = r.learner, a = r.tutorA, b = r.tutorB, c = r.coldStart, h = r.hcp, m = r.metrics, ctx = r.context;
    const head = el("div", { style: "margin-top:16px" });
    head.append(el("h3", { style: "font-size:18px;margin:0" }, L.name),
      p(`Grade ${L.grade} · ${L.school}, ${L.state} · ${L.id} · synthetic`, "note"));
    box.append(head);

    const steps = el("div", { class: "steps" });
    steps.append(step(1, "Starting record", [
      `${h.entriesAtStart} HCP entries`,
      `${ctx.course || "Math course n/a"}`,
      `${ctx.mastered} of ${ctx.totalStandards} standards mastered`,
      `Not yet mastered: ${ctx.notYetMastered.join(", ") || "none"}`,
      `Not yet assessed: ${ctx.notAssessed}`,
    ]));
    steps.append(step(2, "Tutor A personalizes", a.approach.slice(0, 3),
      (() => { const d = el("div"); d.append(p("Target: " + (a.target || "none")), p(a.reason, "note"), p(`${a.session_minutes}-minute sessions`, "note")); return d; })()));
    steps.append(step(3, "New evidence written", a.session ? ["Recorded as model-inferred, medium confidence, under Tutor A's grant"] : [],
      p(a.session ? a.session.summary : "No targeted session: nothing to remediate yet.")));
    steps.append(step(4, "Switch to Tutor B", [
      `Tutor A's next request is refused: ${h.tutorAAfterRevocation}`,
      `Tutor B receives ${h.tutorBDisclosed} entries`,
    ], (() => { const d = el("div"); d.append(p("Learner revokes Tutor A, grants Tutor B."));
      const s = el("p"); s.append(document.createTextNode("Tutor A's evidence reached Tutor B: "));
      s.append(el("span", { class: h.tutorBSawTutorAEvidence ? "ok" : "" }, h.tutorBSawTutorAEvidence ? "yes" : (a.session ? "no" : "n/a")));
      d.append(s); return d; })()));
    steps.append(step(5, "Tutor B continues", b.approach.filter((x) => /^[A-Z0-9]+[.-]/.test(x)).slice(0, 2)
        .concat(b.asks_first.map((x) => "Honors directive: " + x)),
      (() => { const d = el("div"); d.append(p("Target: " + (b.target || "short check")), p(b.reason, "note")); return d; })()));
    box.append(steps);

    const g2 = el("div", { class: "grid2", style: "margin-top:20px" });
    // What Tutor B received, by source
    const left = el("div");
    left.append(el("h3", {}, "What Tutor B received, by who asserted it"));
    const total = SRC.reduce((s, [k]) => s + (h.tutorBByDeclaration[k] || 0), 0);
    const seg = el("div", { class: "seg", role: "img",
      "aria-label": SRC.map(([k, n]) => `${n}: ${h.tutorBByDeclaration[k] || 0}`).join("; ") });
    const lg = el("div", { class: "legend" });
    for (const [k, n, col] of SRC) {
      const v = h.tutorBByDeclaration[k] || 0;
      if (v) {
        const s = el("div", { tabindex: 0 }); s.style.flex = String(v); s.style.background = col;
        const rows = [[col, String(v), n]];
        s.addEventListener("pointermove", (e) => showTip(e, "Entries Tutor B received", rows));
        s.addEventListener("focus", (e) => showTip(e, "Entries Tutor B received", rows));
        s.addEventListener("pointerleave", hideTip); s.addEventListener("blur", hideTip);
        seg.append(s);
      }
      const sp = el("span"); const sw = el("span", { class: "sw" }); sw.style.background = col;
      sp.append(sw, document.createTextNode(`${n}: ${v}`)); lg.append(sp);
    }
    left.append(seg, lg);
    left.append(el("h3", { style: "margin-top:14px" }, "Not given to Tutor B"));
    const wl = el("ul", { style: "margin:0;padding-left:18px;color:var(--text-secondary);font-size:14px" });
    const w = Object.entries(h.withheldFromTutorB);
    if (!w.length) wl.append(el("li", {}, "Nothing: Tutor B received every entry."));
    for (const [k, v] of w.sort()) wl.append(el("li", {}, `${v} ${v === 1 ? "entry" : "entries"}: ${k}`));
    left.append(wl);
    // Comparison
    const right = el("div");
    right.append(el("h3", {}, "Tutor B with and without HCP"));
    const t = el("table");
    const hr = el("tr"); for (const x of ["", "With HCP", "Without HCP"]) hr.append(el("th", { scope: "col" }, x));
    { const th = el("thead"); th.append(hr); t.append(th); }
    const tb = el("tbody"); t.append(tb);
    const rows = [
      ["Intake questions", m.intakeItemsWithHCP, m.intakeItemsWithoutHCP],
      ["Intake minutes saved", m.intakeMinutesSaved, "-"],
      ["Known learner preferences", m.personalizationSignalsWithHCP, 0],
      ["Course already mastered", m.shareOfPoolAlreadyMastered == null ? "n/a" : "known, skipped",
        m.shareOfPoolAlreadyMastered == null ? "n/a" : Math.round(m.shareOfPoolAlreadyMastered * 100) + "% at risk of re-teaching"],
      ["Builds on Tutor A", m.buildsOnTutorA ? "yes" : "n/a", "no"],
      ["First step", b.target || "short check", "diagnostic across " + ctx.totalStandards + " standards"],
    ];
    for (const row of rows) { const tr = el("tr"); row.forEach((v, i) => tr.append(el(i ? "td" : "th", i ? {} : { scope: "row" }, String(v)))); tb.append(tr); }
    right.append(t);
    if (Object.keys(ctx.statements).length || ctx.interests) {
      right.append(el("h3", { style: "margin-top:14px" }, "In the learner's own words"));
      const ul = el("ul", { style: "margin:0;padding-left:18px;color:var(--text-secondary);font-size:14px" });
      for (const [k, v] of Object.entries(ctx.statements)) ul.append(el("li", {}, `${k.replace(/_/g, " ")}: "${v}"`));
      if (ctx.interests) ul.append(el("li", {}, `interests: "${ctx.interests}"`));
      right.append(ul);
    }
    g2.append(left, right);
    box.append(g2);
  }
  const btns = [];
  function select(i, scroll) {
    btns.forEach((b, j) => b.setAttribute("aria-pressed", String(i === j)));
    detail(R[i]);
    if (scroll) $("c2").scrollIntoView({ behavior: "smooth", block: "start" });
  }
  R.forEach((r, i) => {
    const b = el("button", { type: "button", "aria-pressed": "false" }, `${r.learner.name} · Gr ${r.learner.grade}`);
    b.addEventListener("click", () => select(i));
    btns.push(b); $("learners").append(b);
  });

  drawChart(); drawTable(); select(0);
  let rt; window.addEventListener("resize", () => { clearTimeout(rt); rt = setTimeout(drawChart, 120); });
})();
</script>
</body>
</html>
"""


def build(out: Path) -> Path:
    bundle = track_a.DEFAULT_BUNDLE
    results = [track_a.run_learner(d) for d in sorted((bundle / "learners").iterdir())]
    passed, total, failures, _ = check_bundle(bundle)
    leaks = sum(1 for f in failures if "mustNotDisclose" in f)
    payload = json.dumps({"results": results,
                          "check": {"passed": passed, "total": total, "leaks": leaks}},
                         ensure_ascii=False)
    # Keep the embedded JSON from closing its <script> element.
    payload = payload.replace("</", "<\\/")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(TEMPLATE.replace("__DATA__", payload), encoding="utf-8")
    return out


def main(argv: list[str]) -> int:
    out = Path(argv[1]) if len(argv) > 1 else ROOT / "docs" / "index.html"
    print(f"wrote {build(out)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

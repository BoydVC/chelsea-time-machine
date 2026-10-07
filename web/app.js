"use strict";
// Blue Since Boyhood: everything rendered from data/chelsea.json (built from saved Wikipedia pages by build_data.py).
const $ = (s, r = document) => r.querySelector(s);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
let D, SRC_ORDER = [];
const TABS = [["timeline", "Era timeline"], ["chart", "League finishes"], ["today", "This day"], ["finals", "Finals & legends"], ["quiz", "Quiz"], ["sources", "Sources"]];
const params = new URLSearchParams(location.search);
let tab = params.get("tab") || "timeline";

function cite(id) {
  const s = D.sources[id]; if (!s) return "";
  let n = SRC_ORDER.indexOf(id); if (n < 0) { SRC_ORDER.push(id); n = SRC_ORDER.length - 1; }
  return `<a class="cite" href="${esc(s.url)}" target="_blank" rel="noopener" title="${esc(s.title)} (fetched ${esc(s.fetched)})">[${n + 1}]</a>`;
}
const yearOf = (s) => +((String(s).match(/\d{4}/) || [0])[0]);
const seasonOfDate = (iso) => { const y = +iso.slice(0, 4), m = +iso.slice(5, 7); return m >= 7 ? y : y - 1; };
const fmtDate = (iso) => new Date(iso + "T12:00:00").toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" });
const yrsRange = (s) => { const ys = (String(s).match(/\d{4}/g) || []).map(Number); return [Math.min(...ys), Math.max(...ys)]; };

function nav() {
  if ($("#nav").children.length) { [...$("#nav").children].forEach((b) => b.classList.toggle("on", b.dataset.tab === tab)); return; }
  $("#nav").innerHTML = TABS.map(([id, label]) => `<button data-tab="${id}" class="${id === tab ? "on" : ""}">${label}</button>`).join("");
  $("#nav").onclick = (e) => { const b = e.target.closest("button[data-tab]"); if (!b) return; tab = b.dataset.tab; render(); history.replaceState(null, "", "?tab=" + tab); window.scrollTo(0, 0); };
}

function matchCard(m) {
  const pens = m.penalties ? ` <span class="tiny">(${esc(m.penalties)} pens)</span>` : (m.aet ? ` <span class="tiny">(a.e.t.)</span>` : "");
  return `<div class="match"><div class="tiny">${esc(fmtDate(m.date))} · ${esc(m.competition)}</div>
    <div class="score">${esc(m.team1)} ${esc(m.score)} ${esc(m.team2)}${pens}</div>
    <div><span class="pill ${m.result === "W" ? "w" : "l"}">${m.result === "W" ? "Won" : "Lost"}</span><span class="tiny">${esc(m.stadium)}</span></div>
    ${m.chelseaScorers.length ? `<div class="tiny">Chelsea: ${esc(m.chelseaScorers.join(", "))}</div>` : ""}
    ${m.opponentScorers.length ? `<div class="tiny">${esc(m.opponent)}: ${esc(m.opponentScorers.join(", "))}</div>` : ""}
    <div class="tiny">${cite(m.src)}</div></div>`;
}

function timeline() {
  const eras = D.eras.map((e) => {
    const [a, b] = e.range;
    const mgrs = D.managers.filter((m) => { const f = yearOf(m.from), t = m.to === "Present" ? 9999 : yearOf(m.to); return (f >= a && f <= b) || (f < a && t > a); });
    const seasons = D.seasons.filter((s) => s.start >= a && s.start <= b);
    const tro = seasons.filter((s) => s.trophies.length);
    const ms = D.matches.filter((m) => { const s = seasonOfDate(m.date); return s >= a && s <= b; });
    const legs = D.legends.filter((l) => { const [x, y] = yrsRange(l.years); return y >= a && x <= b; });
    const best = seasons.reduce((p, s) => (s.pos && (!p || s.pos < p.pos) ? s : p), null);
    return `<section class="era" id="era-${e.id}">
      <div class="era-rail"><div class="era-years">${esc(e.years)}</div><div class="era-title">${esc(e.title)}</div>
        <div class="tiny">${seasons.length} seasons · ${tro.reduce((n, s) => n + s.trophies.length, 0)} trophies${cite("seasons")}</div></div>
      <div class="era-body">
        <p class="era-sum">${esc(e.summary)}</p>
        <ul class="ev">${e.evidence.map((x) => `<li>${esc(x)}${cite(e.src)}</li>`).join("")}</ul>
        <h3>Managers</h3>
        <div class="row">${mgrs.map((m) => `<div class="mgr"><b>${esc(m.name)}</b><span class="tiny">${esc(m.from)} – ${esc(m.to)} · ${m.games} games · ${m.winPct.toFixed(1)}% won</span>${m.honours.length ? `<div class="tiny" style="color:#ffd866">${esc(m.honours.join("; "))}</div>` : ""}${cite(m.src)}</div>`).join("")}</div>
        <h3>Trophies</h3>
        <div class="trophy-strip">${tro.map((s) => `<div class="tro">🏆 <b>${esc(s.season)}</b> ${esc(s.trophies.join(" · "))}</div>`).join("") || `<span class="tiny">None in these seasons.</span>`}${cite("seasons")}</div>
        ${best ? `<p class="tiny">Best league finish: ${esc(best.posText)} in ${esc(best.season)}${cite("seasons")}</p>` : ""}
        ${ms.length ? `<h3>Iconic matches</h3><div class="row">${ms.map(matchCard).join("")}</div>` : ""}
        <h3>Player of the Season (fans' vote)</h3>
        <div class="trophy-strip">${D.playerOfSeason.filter((p) => p.year - 1 >= a && p.year - 1 <= b).map((p) => `<div class="tro" style="background:rgba(10,91,196,.18);border-color:rgba(143,193,255,.35)"><b>${p.year}</b> ${esc(p.player)}</div>`).join("")}${cite("pots")}</div>
        ${legs.length ? `<h3>Legends of the era</h3><div class="row">${legs.map(legendCard).join("")}</div>` : ""}
      </div></section>`;
  }).join("");
  return `<h2>The era timeline</h2><p class="lede">Scroll from the Bates-era survival years to the Club World Cup. Quotes are verbatim from Wikipedia's Chelsea F.C. article; stats come from its season and manager lists.</p>${eras}`;
}

function legendCard(l) {
  return `<div class="legend"><b>${esc(l.name)}</b><div class="tiny">${esc(l.years)}</div>
    <div><span class="big">${l.apps}</span> <span class="tiny">games${l.appsRank ? ` · #${l.appsRank} all-time` : ""}</span></div>
    ${l.goals != null ? `<div><span class="big">${l.goals}</span> <span class="tiny">goals · #${l.goalsRank} all-time</span></div>` : ""}${cite(l.src)}</div>`;
}

let selSeason = null;
function chart() {
  const S = D.seasons, n = S.length, W = 1100, H = 400, L = 44, R = 16, T = 34, B = 54;
  const maxPos = Math.max(...S.map((s) => s.pos || 0), 20);
  const x = (i) => L + (i * (W - L - R)) / (n - 1), y = (p) => T + ((p - 1) * (H - T - B)) / (maxPos - 1);
  const bands = D.eras.map((e, k) => { const i0 = S.findIndex((s) => s.start >= e.range[0]); let i1 = S.map((s) => s.start <= e.range[1]).lastIndexOf(true); if (i0 < 0 || i1 < 0) return ""; const x0 = x(i0) - (W - L - R) / (n - 1) / 2, x1 = x(i1) + (W - L - R) / (n - 1) / 2;
    return `<rect x="${Math.max(L - 10, x0)}" y="${T - 22}" width="${Math.min(W - R, x1) - Math.max(L - 10, x0)}" height="${H - T - B + 30}" fill="${k % 2 ? "rgba(255,255,255,.03)" : "rgba(10,91,196,.10)"}"/><text x="${(Math.max(L, x0) + Math.min(W - R, x1)) / 2}" y="${T - 10}" text-anchor="middle" style="fill:#ffd866;font-weight:700">${esc(e.title)}</text>`; }).join("");
  const grid = [1, 4, 6, 10, 15, 20].filter((p) => p <= maxPos).map((p) => `<line x1="${L}" x2="${W - R}" y1="${y(p)}" y2="${y(p)}" stroke="rgba(255,255,255,${p === 1 ? .25 : .08})"/><text x="${L - 8}" y="${y(p) + 4}" text-anchor="end">${p}${p === 1 ? "st" : "th"}</text>`).join("");
  const path = S.map((s, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(s.pos).toFixed(1)}`).join("");
  const pts = S.map((s, i) => {
    const title = s.trophies.includes("League title"), any = s.trophies.length;
    const mk = title ? `<text x="${x(i)}" y="${y(s.pos) - 12}" text-anchor="middle" style="font-size:16px">🏆</text>` : any ? `<text x="${x(i)}" y="${y(s.pos) - 10}" text-anchor="middle" style="font-size:12px;fill:#ffd866">★${any > 1 ? any : ""}</text>` : "";
    return `${mk}<circle class="pt" data-i="${i}" cx="${x(i)}" cy="${y(s.pos)}" r="${selSeason === i ? 7 : 5}" fill="${title ? "#dba111" : "#0a5bc4"}" stroke="#fff" stroke-width="${selSeason === i ? 2.5 : 1.2}"/>
      ${i % 2 === 0 || i === n - 1 ? `<text x="${x(i)}" y="${H - B + 18}" text-anchor="end" transform="rotate(-45 ${x(i)} ${H - B + 18})">${esc(s.season)}</text>` : ""}`;
  }).join("");
  const svg = `<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="Chelsea league finishing position by season">${bands}${grid}<path d="${path}" fill="none" stroke="#8fc1ff" stroke-width="2"/>${pts}</svg>`;
  const s = selSeason != null ? S[selSeason] : null;
  const det = s ? `<div class="card detail"><h3>${esc(s.season)}: ${esc(s.posText)} in the ${s.division === "Prem" ? "Premier League" : "First Division"}${cite(s.src)}</h3>
    <div>${s.w}W ${s.d}D ${s.l}L · ${s.gf} scored, ${s.ga} conceded · ${s.pts} pts</div>
    <div>FA Cup: ${esc(s.faCup || "–")} · League Cup: ${esc(s.leagueCup || "–")}${Object.entries(s.other).map(([k, v]) => ` · ${esc(k)}: ${esc(v)}`).join("")}</div>
    <div>Top goalscorer: ${esc(s.topScorer)} (${s.topGoals})</div>
    ${s.trophies.length ? `<div style="margin-top:6px">${s.trophies.map((t) => `<span class="pill gold">🏆 ${esc(t)}</span>`).join("")}</div>` : ""}</div>` : `<p class="tiny">Click or tap a point for that season's record.</p>`;
  const rows = S.map((r, i) => `<tr data-i="${i}" class="${selSeason === i ? "sel" : ""}"><td>${esc(r.season)}</td><td>${esc(r.division)}</td><td class="n">${esc(r.posText)}</td><td class="n">${r.pld}</td><td class="n">${r.w}-${r.d}-${r.l}</td><td class="n">${r.gf}:${r.ga}</td><td class="n">${r.pts}</td><td>${esc(r.faCup)}</td><td>${esc(r.leagueCup)}</td><td>${esc(r.topScorer)} (${r.topGoals})</td><td>${r.trophies.map((t) => `<span class="pill gold">${esc(t)}</span>`).join("")}</td></tr>`).join("");
  return `<h2>League finish, season by season</h2><p class="lede">${S[0].season} to ${S[n - 1].season}: final league position (1st at the top). 🏆 = league champions, ★ = other trophies that season.${cite("seasons")}</p>
    <div class="card"><div class="chart-wrap">${svg}</div><p class="tiny swipe">Swipe the chart sideways to see every season.</p>${det}</div>
    <h3 style="margin-top:20px">Every season${cite("seasons")}</h3>
    <div class="card table-wrap"><table><thead><tr><th>Season</th><th>Div</th><th class="n">Pos</th><th class="n">P</th><th class="n">W-D-L</th><th class="n">Goals</th><th class="n">Pts</th><th>FA Cup</th><th>Lg Cup</th><th>Top goalscorer</th><th>Trophies</th></tr></thead><tbody>${rows}</tbody></table>
    <p class="tiny">Cup codes as in the source: W = won, RU = runners-up, SF = semi-final, QF = quarter-final, R3/R4… = round reached. Division "Div 1" = old First Division (before 1992–93).</p></div>`;
}

function today() {
  const now = new Date(), isDay = now.getMonth() + 1 === D.thisDay.month && now.getDate() === D.thisDay.day;
  const items = D.thisDay.items.slice().reverse();
  return `<div class="today"><div class="date">${isDay ? "TODAY · " : ""}7 OCTOBER</div><h2>This day in Chelsea history</h2>
    <p class="tiny" style="color:#cfe0ff;margin-top:-6px">Every 7 October fixture in Wikipedia's season pages from 1990–91 to 2026–27. Most years 7 October fell in an international break, so there are ${items.length} matches.</p>
    ${items.map((m) => { const ch = m.team1 === "Chelsea"; const [a, b] = m.score.match(/\d+/g).map(Number); const res = (ch ? a - b : b - a) > 0 ? "Won" : (a === b ? "Drew" : "Lost");
      return `<div class="tday"><div class="yr">${m.date.slice(0, 4)}</div><div><div class="score" style="font-size:19px">${esc(m.team1)} ${esc(m.score)} ${esc(m.team2)}</div>
      <div><span class="pill ${res === "Won" ? "w" : "l"}">${res}</span><span class="tiny" style="color:#cfe0ff">${esc(m.competition === "Matches" ? "Premier League" : m.competition)}${m.round ? ` · ${/^\d+$/.test(m.round) ? "Matchweek " + m.round : esc(m.round)}` : ""} · ${esc(m.season)}${m.stadium ? " · " + esc(m.stadium) : ""}${m.attendance ? " · attendance " + esc(m.attendance) : ""}</span></div>
      ${m.chelseaScorers.length ? `<div class="tiny" style="color:#e8eefb">Chelsea goals: ${esc(m.chelseaScorers.join(", "))}</div>` : ""}<div class="tiny">${cite(m.src)}</div></div></div>`; }).join("")}
  </div>
  <div class="grid g2" style="margin-top:16px">
    <div class="card"><h3>Record on 7 October since 1990</h3><p>${items.length} played, ${items.length} won, ${items.reduce((n, m) => n + (m.team1 === "Chelsea" ? +m.score.match(/\d+/g)[0] : +m.score.match(/\d+/g)[1]), 0)} goals scored, ${items.reduce((n, m) => n + (m.team1 === "Chelsea" ? +m.score.match(/\d+/g)[1] : +m.score.match(/\d+/g)[0]), 0)} conceded. Counted from the matches listed above.</p></div>
    <div class="card"><h3>How this card is built</h3><p class="tiny">build_data.py scans every saved season page for fixtures dated 7 October (match boxes and results tables). Nothing is added by hand. A match on another date that a page leaves out won't appear here.</p></div>
  </div>`;
}

function finals() {
  const hon = D.honours.map((h) => `<tr><td>${esc(h.honour)}</td><td class="n"><b>${h.count}</b></td><td>${esc(h.years)}</td></tr>`).join("");
  return `<h2>Finals that defined it</h2><p class="lede">${D.matches.length} finals from 1997 to 2025. Score, scorers and venue come from each final's own Wikipedia page.</p>
    <div class="row">${D.matches.map(matchCard).join("")}</div>
    <h2 style="margin-top:26px">Legends Boyd watched</h2><p class="lede">Players in the club's all-time top-10 for appearances or goals whose Chelsea careers ran into the 1990s or later.${cite("records")}</p>
    <div class="row">${D.legends.map(legendCard).join("")}</div>
    <h2 style="margin-top:26px">Player of the Season, ${D.playerOfSeason[0].year}–${D.playerOfSeason[D.playerOfSeason.length - 1].year}${cite("pots")}</h2>
    <p class="lede">The supporters' award, given at the end of each season. Most wins since ${D.playerOfSeason[0].year}: ${(() => { const c = {}; D.playerOfSeason.forEach((p) => (c[p.player] = (c[p.player] || 0) + 1)); return Object.entries(c).sort((x, y) => y[1] - x[1]).slice(0, 3).map(([k, v]) => `${esc(k)} (${v})`).join(", "); })()}.</p>
    <div class="row">${D.playerOfSeason.map((p) => `<div class="legend" style="flex:1 1 150px"><div class="tiny">${p.year}</div><b>${esc(p.player)}</b><div class="tiny">${esc(p.position)} · ${esc(p.nationality)}</div></div>`).join("")}</div>
    <h2 style="margin-top:26px">Major honours, all time${cite("records")}</h2>
    <div class="card table-wrap"><table><thead><tr><th>Honour</th><th class="n">No.</th><th>Years</th></tr></thead><tbody>${hon}</tbody></table></div>`;
}

let Q = { i: 0, score: 0, picked: null, done: false };
function quiz() {
  const qs = D.quiz;
  if (Q.done) return `<div class="quiz card"><h2>Full time: ${Q.score} / ${qs.length}</h2><p>${Q.score >= 13 ? "Proper Blue. Stamford Bridge legend status." : Q.score >= 9 ? "Solid season. Top-four finish." : "Mid-table. A rewatch of the 2012 final is prescribed."}</p><button class="btn" data-q="restart">Play again</button></div>`;
  const q = qs[Q.i];
  return `<div class="quiz"><div class="qhead"><h2>Chelsea quiz</h2><span class="tiny">Question ${Q.i + 1} of ${qs.length} · score ${Q.score}</span></div>
    <div class="bar"><i style="width:${(Q.i / qs.length) * 100}%"></i></div>
    <div class="card"><p class="qtext">${esc(q.q)}</p>
    ${q.options.map((o, k) => `<button class="opt ${Q.picked != null ? (k === q.answer ? "right" : k === Q.picked ? "wrong" : "") : ""}" data-opt="${k}" ${Q.picked != null ? "disabled" : ""}>${esc(o)}</button>`).join("")}
    ${Q.picked != null ? `<div class="why">${Q.picked === q.answer ? "✅ Correct." : "❌ Not quite."} ${esc(q.why)}${cite(q.src)}</div><div style="margin-top:12px"><button class="btn" data-q="next">${Q.i + 1 < qs.length ? "Next question" : "See score"}</button></div>` : ""}
    </div><p class="tiny">All 15 questions are generated from the cited data above. The wrong options are plausible distractors.</p></div>`;
}

function sources() {
  const ids = Object.keys(D.sources);
  return `<h2>Sources</h2><p class="lede">Free public pages, fetched ${esc(D.sourcesFetched)} and saved under data/raw/. The app runs offline from those copies. Data built ${esc(D.generatedAt)}.</p>
    <div class="card"><ol class="srcs">${ids.map((id) => `<li><a href="${esc(D.sources[id].url)}" target="_blank" rel="noopener">${esc(D.sources[id].title)}</a> <span class="tiny">· fetched ${esc(D.sources[id].fetched)}</span></li>`).join("")}</ol>
    <p class="tiny">Wikipedia text is CC BY-SA 4.0. Quotes in the era timeline are verbatim, and the smoke test checks each one against the saved page. Numbers come straight from the parsed tables, and the smoke test re-parses the tables to check them.</p></div>`;
}

function render() {
  SRC_ORDER = Object.keys(D.sources);
  nav();
  const f = { timeline, chart, today, finals, quiz, sources }[tab] || timeline;
  $("#main").innerHTML = f();
  if (tab === "chart" && selSeason != null) { const w = $(".chart-wrap"), c = $(`circle.pt[data-i="${selSeason}"]`); if (w && c && w.scrollWidth > w.clientWidth) { const r = c.getBoundingClientRect(), wr = w.getBoundingClientRect(); w.scrollLeft += r.left - wr.left - wr.width / 2; } }
  $("#foot").innerHTML = `Blue Since Boyhood · built ${esc(D.generatedAt)} from Wikipedia (fetched ${esc(D.sourcesFetched)}) · ${window.CHELSEA_SNAPSHOT ? "offline snapshot" : "live on this box"} · bracketed numbers link to sources`;
}

document.addEventListener("click", (e) => {
  const pt = e.target.closest("[data-i]");
  if (pt && tab === "chart") { selSeason = +pt.dataset.i; render(); return; }
  const o = e.target.closest("[data-opt]");
  if (o && Q.picked == null) { Q.picked = +o.dataset.opt; if (Q.picked === D.quiz[Q.i].answer) Q.score++; render(); return; }
  const qb = e.target.closest("[data-q]");
  if (qb) { if (qb.dataset.q === "restart") Q = { i: 0, score: 0, picked: null, done: false }; else { Q.picked = null; if (++Q.i >= D.quiz.length) Q.done = true; } render(); }
});
document.addEventListener("mousemove", (e) => {
  const pt = e.target.closest && e.target.closest("circle.pt"); const tip = $("#tip");
  if (!pt) { tip.hidden = true; return; }
  const s = D.seasons[+pt.dataset.i];
  tip.innerHTML = `<b>${esc(s.season)}</b>: ${esc(s.posText)} · ${s.pts} pts${s.trophies.length ? "<br>🏆 " + esc(s.trophies.join(", ")) : ""}`;
  tip.hidden = false; tip.style.left = Math.min(e.clientX + 14, innerWidth - 270) + "px"; tip.style.top = e.clientY + 14 + "px";
});

(async () => {
  D = window.CHELSEA_SNAPSHOT || (await (await fetch("/api/data")).json());
  if (params.has("season")) selSeason = D.seasons.findIndex((s) => s.season === params.get("season"));
  render();
})();

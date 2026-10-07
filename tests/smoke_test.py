#!/usr/bin/env python3
"""Smoke test for Blue Since Boyhood.
1. Re-parses the fetched seasons table (data/raw, BeautifulSoup, independent of build_data.py's pandas path)
   and checks every chart point (position, W/D/L, goals, points, cup results) against it.
2. Checks managers, honours and legends against their fetched tables, finals against the fetched final pages,
   era quotes verbatim against the fetched Chelsea F.C. article, and every quiz answer against the data.
3. Checks the live server (GET only) and the offline snapshot.
Usage: python3 tests/smoke_test.py"""
import json, os, re, sys, urllib.request
from bs4 import BeautifulSoup
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
PORT = os.environ.get("CHELSEA_TM_PORT", "4247")
D = json.load(open(os.path.join(ROOT, "data", "chelsea.json"), encoding="utf-8"))
ok = fail = 0
def check(name, cond, detail=""):
    global ok, fail
    if cond: ok += 1
    else: fail += 1; print("FAIL", name, detail)
    return cond
def txt(el): return re.sub(r"\s+", " ", re.sub(r"\[[^\]]*\]", "", el.get_text(" "))).replace("↑", "").replace("↓", "").strip()

# ---- 1. chart data vs the fetched seasons table ----
soup = BeautifulSoup(open(os.path.join(RAW, "List_of_Chelsea_F.C._seasons.html"), encoding="utf-8"), "lxml")
tbl = max(soup.find_all("table"), key=lambda t: len(t.find_all("tr")))
raw = {}
for tr in tbl.find_all("tr"):
    cells = tr.find_all(["td", "th"])
    if len(cells) < 12: continue
    c = [txt(x) for x in cells]
    if not re.match(r"\d{4}–\d{2,4}$", c[0]): continue
    raw[c[0]] = c
check("seasons table parsed", len(raw) > 100, len(raw))
chart_seasons = [s["season"] for s in D["seasons"]]
expected = [k for k in raw if int(k[:4]) >= 1990]
check("chart covers every 1990+ season in the table", chart_seasons == expected, set(expected) ^ set(chart_seasons))
for s in D["seasons"]:
    c = raw.get(s["season"])
    if not check(f"{s['season']} present in table", c is not None): continue
    # columns: Season, Division, Pld, W, D, L, GF, GA, Pts, Pos, FA Cup, League Cup, ...
    nums = [int(x) for x in c[2:9]]
    check(f"{s['season']} P/W/D/L/GF/GA/Pts", nums == [s["pld"], s["w"], s["d"], s["l"], s["gf"], s["ga"], s["pts"]], (nums, s))
    check(f"{s['season']} position", int(re.match(r"\d+", c[9]).group(0)) == s["pos"], (c[9], s["pos"]))
    check(f"{s['season']} FA Cup / League Cup", (c[10], c[11]) == (s["faCup"], s["leagueCup"]), (c[10:12], s["faCup"], s["leagueCup"]))
    check(f"{s['season']} W-D-L adds to played", s["w"] + s["d"] + s["l"] == s["pld"])
    check(f"{s['season']} points rule", s["pts"] == 3 * s["w"] + s["d"])
    check(f"{s['season']} league title marker only when 1st", ("League title" in s["trophies"]) == (s["pos"] == 1))
titles = [s["season"] for s in D["seasons"] if "League title" in s["trophies"]]
check("league titles 1990+ = 2004–05, 2005–06, 2009–10, 2014–15, 2016–17", titles == ["2004–05", "2005–06", "2009–10", "2014–15", "2016–17"], titles)
fa = [s["season"] for s in D["seasons"] if "FA Cup" in s["trophies"]]
hon = {h["honour"]: h for h in D["honours"]}
fa_years = [y for y in re.findall(r"\d{4}", hon["FA Cup"]["years"]) if int(y) >= 1991]
check("FA Cup wins match records page", [str(int(s[:4]) + 1) for s in fa] == fa_years, (fa, fa_years))

# ---- 2. managers / honours / legends / finals / eras / quiz ----
msoup = BeautifulSoup(open(os.path.join(RAW, "List_of_Chelsea_F.C._managers.html"), encoding="utf-8"), "lxml")
mtext = re.sub(r"\s+", " ", msoup.get_text(" "))
for m in D["managers"]:
    base = re.sub(r" \(\d\)$", "", m["name"])
    check(f"manager {m['name']} on managers page", base in mtext)
    check(f"manager {m['name']} dates on page", m["from"] in mtext and (m["to"] == "Present" or m["to"] in mtext))
check("current manager is last row", D["managers"][-1]["to"] == "Present")
rsoup = re.sub(r"\s+", " ", BeautifulSoup(open(os.path.join(RAW, "List_of_Chelsea_F.C._records_and_statistics.html"), encoding="utf-8"), "lxml").get_text(" "))
for l in D["legends"]:
    check(f"legend {l['name']} on records page", l["name"] in rsoup)
    check(f"legend {l['name']} apps {l['apps']} on records page", re.search(rf"\b{l['apps']}\b", rsoup) is not None)
psoup = re.sub(r"\s+", " ", BeautifulSoup(open(os.path.join(RAW, "Chelsea_F.C._Player_of_the_Season.html"), encoding="utf-8"), "lxml").get_text(" "))
check("player of the season covers 1991 to latest", [p["year"] for p in D["playerOfSeason"]] == list(range(1991, D["playerOfSeason"][-1]["year"] + 1)))
for p in D["playerOfSeason"]:
    check(f"POTS {p['year']} {p['player']} on page", re.search(rf"{p['year']} {re.escape(p['player'])}", psoup) is not None)
for m in D["matches"]:
    w = open(os.path.join(RAW, "finals", m["id"] + ".wiki"), encoding="utf-8").read()
    check(f"final {m['id']} score in page", m["score"] in w, m["score"])
    for sc in m["chelseaScorers"]:
        check(f"final {m['id']} scorer {sc} in page", sc.split(" ")[0] in w)
    if m["penalties"]: check(f"final {m['id']} penalties in page", m["penalties"] in w)
club = BeautifulSoup(open(os.path.join(RAW, "Chelsea_F.C..html"), encoding="utf-8"), "lxml").get_text("")
club = re.sub(r"\s+", " ", re.sub(r"\[\d+\]|\[[a-z]\]", "", club))
for e in D["eras"]:
    for ev in e["evidence"]:
        check(f"era quote verbatim: {ev[:50]}", ev in club)
for it in D["thisDay"]["items"]:
    check(f"this-day {it['date']} is 7 October", it["date"][5:] == "10-07")
    w = open(os.path.join(RAW, "seasons", it["season"] + ".wiki"), encoding="utf-8").read()
    check(f"this-day {it['date']} score in season page", it["score"].split(" ")[0] in w)
check("quiz has 15 questions", len(D["quiz"]) == 15)
for q in D["quiz"]:
    check(f"quiz source exists: {q['q'][:40]}", q["src"] in D["sources"])
    check(f"quiz answer index valid: {q['q'][:40]}", 0 <= q["answer"] < len(q["options"]) and len(set(q["options"])) == len(q["options"]))
    ans = q["options"][q["answer"]]
    blob = json.dumps({k: D[k] for k in ("seasons", "managers", "honours", "legends", "matches")}, ensure_ascii=False)
    check(f"quiz answer appears in data: {ans}", ans in blob or ans.split(" ")[-1] in blob, ans)
for s in D["sources"].values():
    check(f"source has url+fetched: {s['title'][:40]}", s["url"].startswith("https://") and s.get("fetched"))

# ---- 3. server + snapshot ----
try:
    with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/health", timeout=30) as r: check("server health", json.load(r).get("ok") is True)
    with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/data", timeout=30) as r: check("server serves current data", json.load(r)["generatedAt"] == D["generatedAt"])
    with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/", timeout=30) as r: check("server serves app", b"app.js" in r.read())
except Exception as ex:
    check("server reachable", False, repr(ex))
snap = os.path.join(ROOT, "dist", "chelsea-time-machine-snapshot.html")
html = open(snap, encoding="utf-8").read() if os.path.exists(snap) else ""
check("snapshot exists", bool(html))
check("snapshot self-contained", "window.CHELSEA_SNAPSHOT" in html and not re.search(r'<(script|link)[^>]+(src|href)=["\']', html))
check("snapshot data current", json.dumps(D["generatedAt"]) in html)
print(f"\n{ok} checks passed, {fail} failed")
sys.exit(1 if fail else 0)

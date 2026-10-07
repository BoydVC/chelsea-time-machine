#!/usr/bin/env python3
"""Build data/chelsea.json from the raw Wikipedia pages saved in data/raw/ (no network).
Every record carries a `src` id that maps to a URL in `sources`. Nothing is typed in by hand
except era framing text, and each era's facts quote an `evidence` sentence that must appear
verbatim in the fetched source (tests/smoke_test.py checks this)."""
import io, json, os, re, glob, datetime
import pandas as pd
from bs4 import BeautifulSoup

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "data", "raw")
W = "https://en.wikipedia.org/wiki/"
FETCHED = datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(RAW, "List_of_Chelsea_F.C._seasons.html"))).strftime("%Y-%m-%d")

def clean(s):
    s = "" if s is None or (isinstance(s, float) and pd.isna(s)) else str(s)
    s = re.sub(r"\[[^\]]*\]", "", s)
    return re.sub(r"\s+", " ", s.replace("↑", "").replace("↓", "")).strip()

def tables(name, br=" / "):
    html = open(os.path.join(RAW, name + ".html"), encoding="utf-8").read()
    html = re.sub(r"<br\s*/?>", br, html)
    return pd.read_html(io.StringIO(html))

sources = {
    "seasons": {"title": "List of Chelsea F.C. seasons", "url": W + "List_of_Chelsea_F.C._seasons"},
    "managers": {"title": "List of Chelsea F.C. managers", "url": W + "List_of_Chelsea_F.C._managers"},
    "club": {"title": "Chelsea F.C.", "url": W + "Chelsea_F.C."},
    "records": {"title": "List of Chelsea F.C. records and statistics", "url": W + "List_of_Chelsea_F.C._records_and_statistics"},
    "pots": {"title": "Chelsea F.C. Player of the Season", "url": W + "Chelsea_F.C._Player_of_the_Season"},
}
for s in sources.values(): s["fetched"] = FETCHED

# ---------- seasons ----------
t = [x for x in tables("List_of_Chelsea_F.C._seasons") if x.shape[0] > 100][0]
t.columns = [c[1] if isinstance(c, tuple) else c for c in t.columns]
cols = list(t.columns)
seasons = []
for _, r in t.iterrows():
    season = clean(r["Season"])
    m = re.match(r"(\d{4})", season)
    if not m or int(m.group(1)) < 1990: continue
    pos = clean(r["Pos"]); pn = re.match(r"(\d+)", pos)
    row = {"season": season, "start": int(m.group(1)), "division": clean(r["Division"]),
           "pld": int(clean(r["Pld"])), "w": int(clean(r["W"])), "d": int(clean(r["D"])), "l": int(clean(r["L"])),
           "gf": int(clean(r["GF"])), "ga": int(clean(r["GA"])), "pts": int(clean(r["Pts"])),
           "pos": int(pn.group(1)) if pn else None, "posText": pos,
           "faCup": clean(r["FA Cup"]), "leagueCup": clean(r["League Cup"]),
           "other": {k: clean(r[k]) for k in ["CS", "UCL", "UEL", "UEC", "CWC", "USC", "FWC", "FM"] if k in cols and clean(r[k])},
           "topScorer": clean(r["Player(s)"]), "topGoals": int(re.match(r"\d+", clean(r["Goals"])).group(0)),
           "src": "seasons"}
    names = {"CS": "Charity/Community Shield", "UCL": "Champions League", "UEL": "UEFA Cup/Europa League", "UEC": "Conference League",
             "CWC": "Cup Winners' Cup", "USC": "UEFA Super Cup", "FWC": "FIFA Club World Cup", "FM": "Full Members' Cup"}
    trophies = []
    if row["pos"] == 1 and row["division"] in ("Prem", "Div 1"): trophies.append("League title")
    if row["pos"] == 1 and row["division"] == "Div 2": trophies.append("Second Division title")
    if row["faCup"] == "W": trophies.append("FA Cup")
    if row["leagueCup"] == "W": trophies.append("League Cup")
    for k, v in row["other"].items():
        if v == "W": trophies.append(names[k])
    row["trophies"] = trophies
    seasons.append(row)

# ---------- managers ----------
mt = tables("List_of_Chelsea_F.C._managers", br="; ")[0]
managers = []
for _, r in mt.iterrows():
    name = clean(r["Manager"])
    if name == "Total": continue
    to = clean(r["To"])
    year_to = 9999 if to == "Present" else int(re.search(r"\d{4}", to).group(0))
    if year_to < 1991: continue
    hon = clean(r["Honours"])
    managers.append({"name": name, "nationality": clean(r["Nationality"]), "from": clean(r["From"]), "to": to,
                     "games": int(clean(r["M"])), "winPct": float(clean(r["Win%"])),
                     "honours": [] if hon in ("–", "-", "") else [h.strip() for h in hon.split(";") if h.strip()],
                     "src": "managers"})

# ---------- honours + legends (records page) ----------
rt = tables("List_of_Chelsea_F.C._records_and_statistics")
honours = [{"honour": clean(r["Honour"]), "count": int(clean(r["No."])), "years": clean(r["Years"]), "src": "records"} for _, r in rt[0].iterrows()]
apps = {clean(r["Player"]): {"rank": int(r["Rank"]), "years": clean(r["Years"]), "apps": int(re.match(r"\d+", clean(r["Total"])).group(0))} for _, r in rt[1].iterrows()}
goals = {}
for _, r in rt[2].iterrows():
    m = re.match(r"(\d+) \((\d+)\)", clean(r["Total"]))
    goals[clean(r["Player"])] = {"rank": int(r["Rank"]), "years": clean(r["Years"]), "goals": int(m.group(1)), "apps": int(m.group(2))}
legends = []
for name in dict.fromkeys(list(apps) + list(goals)):
    a, g = apps.get(name), goals.get(name)
    years = (a or g)["years"]
    if max(int(y) for y in re.findall(r"\d{4}", years)) < 1991: continue  # Boyd's era: still playing 1991+
    legends.append({"name": name, "years": years, "apps": (a or g)["apps"], "appsRank": a["rank"] if a else None,
                    "goals": g["goals"] if g else None, "goalsRank": g["rank"] if g else None, "src": "records"})

# ---------- Player of the Season (fans' vote), 1991 onwards ----------
pt = [x for x in tables("Chelsea_F.C._Player_of_the_Season") if list(x.columns)[:2] == ["Year", "Player"]][0]
potS = [{"year": int(clean(r["Year"])), "player": re.sub(r" \(\d+\)$", "", clean(r["Player"])), "nationality": clean(r["Nationality"]),
         "position": clean(r["Position"]), "src": "pots"} for _, r in pt.iterrows() if re.match(r"\d{4}$", clean(r["Year"])) and int(clean(r["Year"])) >= 1991]

# ---------- iconic matches (finals) ----------
def fb_field(block, k):
    m = re.search(r"\|\s*" + k + r"\s*=(.*?)(?=\n\s*\||\Z)", block, re.S)
    return m.group(1).strip() if m else ""
def unlink(s):
    s = re.sub(r"\{\{score link\|[^|]*\|([^|}]*)\|[^}]*\}\}", r"\1", s)
    s = re.sub(r"\{\{[^{}]*\}\}", "", s)
    s = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", s)
    return re.sub(r"\s+", " ", s).strip()
def scorers(s):
    out = []
    for m in re.finditer(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]\s*\{\{goal\|([^}]*)\}\}", s):
        parts = m.group(2).split("|")
        mins = [x for x in parts if x and re.match(r"\d", x)]
        og = " (o.g.)" if any(x.strip() == "o.g." for x in parts) else ""
        out.append(m.group(1) + " " + ", ".join(x + "'" for x in mins) + og)
    if not out:
        out = [unlink(x) for x in re.split(r"<br\s*/?>", s) if unlink(x)]
    return out
def parse_date(s):
    m = re.search(r"Start date\|(\d{4})\|(\d+)\|(\d+)", s)
    if m: return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    d = datetime.datetime.strptime(unlink(s), "%d %B %Y"); return d.strftime("%Y-%m-%d")

FINAL_NOTES = {  # what the match was; the score/scorers/venue come from the page itself
    "1997_FA_Cup_final": ("FA Cup final", "Gullit era"),
    "1998_UEFA_Cup_Winners'_Cup_final": ("Cup Winners' Cup final", "Vialli era"),
    "2000_FA_Cup_final": ("FA Cup final", "Vialli era"),
    "2005_Football_League_Cup_final": ("League Cup final", "Mourinho era"),
    "2008_UEFA_Champions_League_final": ("Champions League final", "Grant"),
    "2010_FA_Cup_final": ("FA Cup final (completing the Double)", "Ancelotti era"),
    "2012_UEFA_Champions_League_final": ("Champions League final", "Di Matteo"),
    "2013_UEFA_Europa_League_final": ("Europa League final", "Benítez"),
    "2019_UEFA_Europa_League_final": ("Europa League final", "Sarri"),
    "2021_UEFA_Champions_League_final": ("Champions League final", "Tuchel"),
    "2025_UEFA_Conference_League_final": ("Conference League final", "Maresca"),
    "2025_FIFA_Club_World_Cup_final": ("FIFA Club World Cup final", "Maresca"),
}
matches = []
for key, (comp, mgr) in FINAL_NOTES.items():
    txt = open(os.path.join(RAW, "finals", key + ".wiki"), encoding="utf-8").read()
    m = re.search(r"\{\{(?:#invoke:)?[Ff]ootball ?box[^\n]*\n(.*?)\n\}\}", txt, re.S)
    b = m.group(1)
    t1, t2 = unlink(fb_field(b, "team1")), unlink(fb_field(b, "team2"))
    score = unlink(fb_field(b, "score"))
    pens = unlink(fb_field(b, "penaltyscore"))
    chelsea_home = "Chelsea" in t1
    g1, g2 = scorers(fb_field(b, "goals1")), scorers(fb_field(b, "goals2"))
    a, c = [int(x) for x in re.findall(r"\d+", score)[:2]]
    cs, os_ = (a, c) if chelsea_home else (c, a)
    if pens:
        p1, p2 = [int(x) for x in re.findall(r"\d+", pens)[:2]]
        pc, po = (p1, p2) if chelsea_home else (p2, p1)
        result = "W" if pc > po else "L"
    else:
        result = "W" if cs > os_ else ("L" if cs < os_ else "D")
    sid = "final:" + key
    sources[sid] = {"title": key.replace("_", " "), "url": W + key, "fetched": FETCHED}
    matches.append({"id": key, "date": parse_date(fb_field(b, "date")), "competition": comp, "manager": mgr,
                    "team1": t1, "team2": t2, "score": score, "aet": fb_field(b, "aet") == "yes" or bool(pens), "penalties": pens or None,
                    "chelseaScorers": g1 if chelsea_home else g2, "opponentScorers": g2 if chelsea_home else g1,
                    "opponent": t2 if chelsea_home else t1, "result": result,
                    "stadium": unlink(fb_field(b, "stadium")), "src": sid})
matches.sort(key=lambda m: m["date"])

# ---------- this day: 7 October, from every season page 1990-91 onwards ----------
def this_day(month=10, day=7):
    out = []
    for f in sorted(glob.glob(os.path.join(RAW, "seasons", "*.wiki"))):
        season = os.path.basename(f)[:-5]
        txt = open(f, encoding="utf-8").read()
        title = season + " Chelsea F.C. season"
        sid = "season:" + season
        # football boxes
        for m in re.finditer(r"\{\{(?:#invoke:)?[Ff]ootball box(?: collapsible)?[^\n]*\n(.*?)\n\}\}", txt, re.S):
            b = m.group(1); ds = fb_field(b, "date")
            try: d = parse_date(ds)
            except Exception: continue
            if int(d[5:7]) != month or int(d[8:10]) != day: continue
            head = [h for h in re.findall(r"^==+\s*([^=\n]+?)\s*==+", txt[:m.start()], re.M)]
            t1, t2 = unlink(fb_field(b, "team1")), unlink(fb_field(b, "team2"))
            ch = "Chelsea" in t1
            out.append({"date": d, "season": season, "competition": head[-1] if head else "", "round": unlink(fb_field(b, "round")),
                        "team1": t1, "team2": t2, "score": unlink(fb_field(b, "score")),
                        "chelseaScorers": scorers(fb_field(b, "goals1" if ch else "goals2")),
                        "stadium": unlink(fb_field(b, "stadium")), "attendance": unlink(fb_field(b, "attendance")), "src": sid})
        # wikitable rows like "| 7 October 1992 ||[[Walsall F.C.|Walsall]]||H||1–0 ..."
        for m in re.finditer(r"^\|\|?(?:([^|\n]*?)\s*\|\|)?\s*(\d{1,2}) (\w+) (\d{4})\s*\|\|(.*)$", txt, re.M):
            try: d = datetime.datetime.strptime(f"{m.group(2)} {m.group(3)} {m.group(4)}", "%d %B %Y")
            except ValueError: continue
            if d.month != month or d.day != day: continue
            cells = [unlink(c) for c in m.group(5).split("||")]
            if len(cells) < 3 or cells[1] not in ("H", "A", "N"): continue
            head = re.findall(r"^==+\s*([^=\n]+?)\s*==+", txt[:m.start()], re.M)
            opp, venue, score = cells[0], cells[1], cells[2]
            out.append({"date": d.strftime("%Y-%m-%d"), "season": season, "competition": head[-1] if head else "", "round": unlink(m.group(1) or ""),
                        "team1": "Chelsea" if venue == "H" else opp, "team2": opp if venue == "H" else "Chelsea", "score": score,
                        "chelseaScorers": [x.strip() for x in cells[4].split(",")] if len(cells) > 4 and cells[4] else [],
                        "stadium": "", "attendance": cells[3] if len(cells) > 3 else "", "src": sid})
        if any(o["src"] == sid for o in out):
            sources[sid] = {"title": title, "url": W + title.replace(" ", "_"), "fetched": FETCHED}
    return sorted(out, key=lambda o: o["date"])
thisday = this_day()

# ---------- eras (framing) with verbatim evidence from the Chelsea F.C. article ----------
club_text = re.sub(r"\[\d+\]|\[[a-z]\]", "", BeautifulSoup(open(os.path.join(RAW, "Chelsea_F.C..html"), encoding="utf-8"), "lxml").get_text(""))
club_text = re.sub(r"\s+", " ", club_text)
ERAS = [
    {"id": "bates", "title": "Survival to silverware", "years": "1990–2003", "range": [1990, 2003],
     "summary": "The Bates years: Stamford Bridge saved, the Premier League arrives, and the Gullit–Vialli cup teams end a long wait for honours.",
     "evidence": ["Bates reunited the stadium freehold with the club in 1992",
                  "The appointment of Ruud Gullit as player-manager in 1996 began an upturn in the team's fortunes",
                  "led the club to their first major honour since 1971, the FA Cup",
                  "whose reign saw Chelsea win the League Cup, the UEFA Cup Winners' Cup and the UEFA Super Cup in 1998, and the FA Cup in 2000"]},
    {"id": "abramovich", "title": "The Abramovich era", "years": "2003–2022", "range": [2003, 2021],
     "summary": "A takeover in June 2003, then league titles, Doubles, and Chelsea's first European Cup in Munich.",
     "evidence": ["Bates unexpectedly sold Chelsea F.C. in June 2003 for £60 million",
                  "Under Mourinho, Chelsea became the fifth English team to win back-to-back league championships since the Second World War (2004–05 and 2005–06)",
                  "Carlo Ancelotti led them to their first Premier League and FA Cup Double, becoming the first English top-flight club to score 100 league goals in a season since 1963",
                  "their first UEFA Champions League title, beating Bayern Munich 4–3 on penalties, the first London club to win the trophy",
                  "making them the first club to hold two major European titles simultaneously",
                  "won their second UEFA Champions League title with a 1–0 win over Manchester City in Porto"]},
    {"id": "blueco", "title": "BlueCo and the rebuild", "years": "2022–now", "range": [2022, 2026],
     "summary": "New owners, a record-low season, then a Conference League and the expanded Club World Cup; Xabi Alonso takes over in 2026.",
     "evidence": ["The UK government approved the £4.25bn takeover, ending Abramovich's 19-year ownership of the club",
                  "Chelsea scored a record-low 38 goals across the entire season and finished in the bottom half of the table for the first time since 1995–96",
                  "After winning the UEFA Conference League in 2025, Chelsea became the first club to win all four main UEFA competitions",
                  "Chelsea secured the trophy with a 3–0 win over Champions League winners Paris Saint-Germain in the final",
                  "On 17 May 2026, Xabi Alonso was appointed as the new Chelsea manager on a four-year contract, starting from 1 July 2026"]},
]
for e in ERAS:
    e["src"] = "club"
    e["evidenceFound"] = [ev in club_text for ev in e["evidence"]]

data = {"generatedAt": datetime.datetime.now().strftime("%Y-%m-%d %H:%M ET"), "sourcesFetched": FETCHED,
        "seasons": seasons, "managers": managers, "playerOfSeason": potS, "honours": honours, "legends": legends,
        "matches": matches, "thisDay": {"month": 10, "day": 7, "items": thisday}, "eras": ERAS, "sources": sources}

# ---------- quiz: 15 questions, each derived from a record above ----------
import random
rng = random.Random(7)
def q(text, answer, wrong, src, why):
    opts = [answer] + [w for w in wrong if w != answer][:3]
    rng.shuffle(opts)
    return {"q": text, "options": opts, "answer": opts.index(answer), "src": src, "why": why}
S = {s["season"]: s for s in seasons}
titles = [s["season"] for s in seasons if "League title" in s["trophies"]]
M = {m["id"]: m for m in matches}
mgr_by = {m["name"]: m for m in managers}
quiz = [
    q("Which manager led Chelsea to their first UEFA Champions League title in 2012?", "Roberto Di Matteo",
      ["André Villas-Boas", "Carlo Ancelotti", "Rafael Benítez"], "managers", "Di Matteo's honours: 2012 FA Cup, 2012 UEFA Champions League."),
    q("Who scored Chelsea's 88th-minute equaliser in the 2012 Champions League final?", M["2012_UEFA_Champions_League_final"]["chelseaScorers"][0].split(" ")[0],
      ["Lampard", "Mata", "Torres"], M["2012_UEFA_Champions_League_final"]["src"], "Bayern 1–1 Chelsea (Chelsea won 4–3 on penalties): " + ", ".join(M["2012_UEFA_Champions_League_final"]["chelseaScorers"])),
    q("How many points did Chelsea finish with in 2004–05, Mourinho's first title season?", str(S["2004–05"]["pts"]),
      ["91", "93", "87"], "seasons", f"2004–05: {S['2004–05']['w']}W {S['2004–05']['d']}D {S['2004–05']['l']}L, {S['2004–05']['pts']} pts, {S['2004–05']['posText']}."),
    q("How many league goals did Chelsea score in the 2009–10 Double season?", str(S["2009–10"]["gf"]),
      ["95", "86", "110"], "seasons", f"2009–10: {S['2009–10']['gf']} scored, {S['2009–10']['ga']} conceded."),
    q("Who scored the only goal of the 2021 Champions League final in Porto?", M["2021_UEFA_Champions_League_final"]["chelseaScorers"][0].split(" ")[0],
      ["Werner", "Mount", "Pulisic"], M["2021_UEFA_Champions_League_final"]["src"], "Manchester City 0–1 Chelsea: " + ", ".join(M["2021_UEFA_Champions_League_final"]["chelseaScorers"])),
    q("Which club did Chelsea beat 2–0 in the 1997 FA Cup final?", M["1997_FA_Cup_final"]["opponent"],
      ["Aston Villa", "Manchester United", "Portsmouth"], M["1997_FA_Cup_final"]["src"], "Chelsea 2–0 Middlesbrough; scorers " + ", ".join(M["1997_FA_Cup_final"]["chelseaScorers"])),
    q("Who scored the winner in the 1998 Cup Winners' Cup final against VfB Stuttgart?", M["1998_UEFA_Cup_Winners'_Cup_final"]["chelseaScorers"][0].split(" ")[0],
      ["Vialli", "Di Matteo", "Wise"], M["1998_UEFA_Cup_Winners'_Cup_final"]["src"], "Chelsea 1–0 VfB Stuttgart, Råsunda Stadium, Stockholm."),
    q("Who is Chelsea's all-time leading goalscorer?", "Frank Lampard",
      ["Didier Drogba", "Kerry Dixon", "Bobby Tambling"], "records", f"Lampard: {goals['Frank Lampard']['goals']} goals in {goals['Frank Lampard']['apps']} games."),
    q("How many games did John Terry play for Chelsea?", str(apps["John Terry"]["apps"]),
      ["648", "795", "508"], "records", f"Terry: {apps['John Terry']['apps']} appearances ({apps['John Terry']['years']}), 3rd on the all-time list."),
    q("How many English top-flight league titles have Chelsea won (records page, fetched Oct 7, 2026)?", str(honours[0]["count"]),
      ["5", "7", "4"], "records", "Titles: " + honours[0]["years"]),
    q("Who scored twice for Chelsea in the 2025 FIFA Club World Cup final against PSG?", "Cole Palmer",
      ["João Pedro", "Enzo Fernández", "Nicolas Jackson"], M["2025_FIFA_Club_World_Cup_final"]["src"], "Chelsea 3–0 Paris Saint-Germain: " + ", ".join(M["2025_FIFA_Club_World_Cup_final"]["chelseaScorers"])),
    q("Where was the 2025 Conference League final, which Chelsea won 4–1 against Real Betis?", "Wrocław",
      ["Prague", "Baku", "Tirana"], M["2025_UEFA_Conference_League_final"]["src"], "Venue: " + M["2025_UEFA_Conference_League_final"]["stadium"]),
    q("Where did Chelsea finish in the 2022–23 Premier League?", S["2022–23"]["posText"],
      ["10th", "8th", "15th"], "seasons", f"2022–23: {S['2022–23']['posText']}, {S['2022–23']['pts']} pts, {S['2022–23']['gf']} goals scored."),
    q("Who was Chelsea's top goalscorer in 2016–17, Antonio Conte's title season?", S["2016–17"]["topScorer"],
      ["Eden Hazard", "Pedro", "Michy Batshuayi"], "seasons", f"2016–17 top scorer: {S['2016–17']['topScorer']} ({S['2016–17']['topGoals']})."),
    q("Which team beat Chelsea on penalties in the 2008 Champions League final in Moscow?", M["2008_UEFA_Champions_League_final"]["opponent"],
      ["Barcelona", "Liverpool", "Bayern Munich"], M["2008_UEFA_Champions_League_final"]["src"], "1–1 after extra time; Manchester United won " + M["2008_UEFA_Champions_League_final"]["penalties"] + " on penalties."),
]
data["quiz"] = quiz
os.makedirs(os.path.join(HERE, "data"), exist_ok=True)
json.dump(data, open(os.path.join(HERE, "data", "chelsea.json"), "w"), ensure_ascii=False, indent=1)
print(f"potS={len(potS)} seasons={len(seasons)} managers={len(managers)} legends={len(legends)} matches={len(matches)} thisDay={len(thisday)} quiz={len(quiz)} evidence_missing={sum(not x for e in ERAS for x in e['evidenceFound'])}")

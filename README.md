# Blue Since Boyhood: Chelsea FC, 1990s to now

An interactive Chelsea history for Boyd, a Chelsea fan since the 1990s. Runs on this box at **http://127.0.0.1:4247**. An offline single-file copy is at `dist/chelsea-time-machine-snapshot.html`.

## What's inside
- **Era timeline** (scrollable). It covers three eras:
  - *Survival to silverware* (1990–2003)
  - *The Abramovich era* (2003–2022)
  - *BlueCo and the rebuild* (2022–now)

  Each era shows verbatim quotes from Wikipedia's Chelsea F.C. article, every manager in the period (tenure, games, win %, honours), the trophies won, the iconic finals and the legends.
- **League finishes.** An SVG chart covers all 36 seasons from 1990–91 to 2025–26. 🏆 marks a league title and ★ marks other trophies. Hover for a tooltip, or click or tap a season for its full record. A full season table sits below.
- **This day: 7 October.** It lists every 7 October fixture found in the season pages from 1990–91 to 2026–27: 1992 (League Cup v Walsall), 2007 (at Bolton), 2018 (at Southampton) and 2023 (at Burnley). Chelsea won all four.
- **Finals & legends.** It shows 12 finals from 1997 to 2025, with score, scorers, venue and penalties all taken from each final's own page. It also shows the all-time top-10 appearance and goal leaders whose careers ran into the 1990s or later, the supporters' Player of the Season for every year from 1991 to 2026 (also shown in each era of the timeline), and the full honours table.
- **Quiz.** It has 15 multiple-choice questions, each generated from the data. Every answer shows the supporting fact and its source link.
- **Sources.** All 21 pages, with the date each was fetched.

## Honesty rules
- Every fact comes from free public Wikipedia pages. They were fetched on 2026-10-07 and saved under `data/raw/`, and the app runs from those copies.
- `build_data.py` parses the saved pages into `data/chelsea.json`. Nothing numeric is typed in by hand.
- The era summary lines are my framing. Every claim under them is a verbatim quote that the smoke test checks against the saved article.
- Every number and quote has a bracketed source link.
- Wikipedia is current to the fetch date. That includes events after mid-2025, such as Maresca leaving on 1 Jan 2026 and Xabi Alonso's appointment from 1 Jul 2026. Those come from the pages as fetched and were not checked against a second source.
- The "top goalscorer" column follows the seasons table, as listed there.

## Run
```
./run.sh                      # rebuild data from data/raw (no network) and start on :4247 (nohup, idempotent)
python3 export_static.py      # write dist/chelsea-time-machine-snapshot.html
./screenshot.sh               # screenshots/01-…08-*.png (desktop + phone; 09 is a phone quiz shot taken by the QA probe)
python3 tests/smoke_test.py   # 510 checks
```
The smoke test re-parses the saved seasons table with BeautifulSoup, separately from the build's pandas parser. It checks each chart point against the table: position, P/W/D/L, goals, points, FA Cup and League Cup. It also checks:
- that W+D+L equals games played and points equal 3W+D;
- that league-title markers appear only for 1st-place finishes;
- managers, legends and every Player of the Season against their pages;
- finals' scores, scorers and penalties against each final's page;
- the era quotes, verbatim;
- the 7 October fixtures;
- that every quiz answer appears in the data;
- the live server and the snapshot.

To refresh the sources, re-fetch the pages into `data/raw/` (the URLs are in `data/chelsea.json` under `sources`). Then run `python3 build_data.py && python3 export_static.py && python3 tests/smoke_test.py`.

## Files
`build_data.py` (parser) · `server.py` (stdlib server, `/api/health`, `/api/data`) · `web/` (index.html, style.css, app.js) · `data/raw/` (saved source pages) · `data/chelsea.json` · `dist/` · `screenshots/` · `tests/smoke_test.py` · `run.sh`


---
## Repo notes
- **Built:** 2026-10-07, by TokenMax (Boyd's Grok Bot) on the Grok Bot box.
- **Run:** `./run.sh` (then open the localhost URL it prints).
- Imported from `/workspace/tokenmax/chelsea-time-machine` on Oct 23, 2026. node_modules, virtualenvs, logs and files over 20 MB were left out.

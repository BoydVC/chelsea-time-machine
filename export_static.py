#!/usr/bin/env python3
"""Write dist/chelsea-time-machine-snapshot.html: one self-contained file (UI + data) that opens offline with no server."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    data = json.load(open(os.path.join(HERE, "data", "chelsea.json"), encoding="utf-8"))
    web = os.path.join(HERE, "web")
    html = open(os.path.join(web, "index.html")).read()
    css = open(os.path.join(web, "style.css")).read()
    js = open(os.path.join(web, "app.js")).read()
    blob = json.dumps(data, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
    assert '<link rel="stylesheet" href="style.css">' in html and '<script src="app.js"></script>' in html
    html = html.replace('<link rel="stylesheet" href="style.css">', f"<style>{css}</style>")
    html = html.replace('<script src="app.js"></script>',
                        f"<script>window.CHELSEA_SNAPSHOT={blob};</script>\n<script>{js}</script>")
    html = html.replace("<title>Blue Since Boyhood", "<title>Blue Since Boyhood (offline snapshot)")
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "dist", "chelsea-time-machine-snapshot.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w").write(html)
    print(f"wrote {out} ({os.path.getsize(out) // 1024} KB)")


if __name__ == "__main__":
    main()

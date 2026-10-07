#!/usr/bin/env python3
"""Blue Since Boyhood: tiny stdlib server (default port 4247). Serves web/ plus data/chelsea.json."""
import http.server
import json
import os
import socketserver
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get("CHELSEA_TM_PORT", "4247"))


def bundle():
    return json.load(open(os.path.join(HERE, "data", "chelsea.json"), encoding="utf-8"))


class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=os.path.join(HERE, "web"), **k)

    def log_message(self, fmt, *args):
        sys.stderr.write("%s %s\n" % (self.log_date_time_string(), fmt % args))

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/api/health"):
            return self._json({"ok": True, "app": "chelsea-time-machine", "port": PORT})
        if self.path.startswith("/api/data"):
            return self._json(bundle())
        return super().do_GET()


class S(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


if __name__ == "__main__":
    with S(("0.0.0.0", PORT), H) as srv:
        print(f"Blue Since Boyhood on http://127.0.0.1:{PORT}", flush=True)
        srv.serve_forever()

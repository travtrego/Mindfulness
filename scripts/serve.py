#!/usr/bin/env python3
"""Serve the prototype locally.

    python3 scripts/serve.py            # http://localhost:8000
    python3 scripts/serve.py --port 3000

The prototype is authored as a fragment (no <html>/<head>/<body>) so it can be published
as an artifact. This wraps it in a document and serves it, so the same file works both ways
without maintaining two copies.
"""
import argparse
import http.server
import inspect
import json
import socketserver
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
APP = ROOT / "docs/app.html"
DOC = ROOT / "docs/prototype.html"
SRC = APP

SHELL = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>*{{margin:0;padding:0}}body{{margin:0}}</style>
</head>
<body>
{body}
</body>
</html>"""


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path not in ("/", "/index.html"):
            return super().do_GET()
        page = SHELL.format(body=SRC.read_text()).encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(page)))
        self.send_header("Cache-Control", "no-store")   # always reflect the file on disk
        self.end_headers()
        self.wfile.write(page)

    def do_POST(self):
        """The chat and the questions. The key stays here and never reaches the browser."""
        from generator import api

        routes = {"/api/talk": api.talk, "/api/questions": api.questions}
        fn = routes.get(self.path)
        if not fn:
            return self.send_error(404)

        try:
            n = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(n) or "{}")
            # signature parameters only. co_varnames also lists locals, so a body key that
            # happened to match one - "llm", "usage", "template" - was forwarded as a kwarg
            allowed = set(inspect.signature(fn).parameters)
            out = fn(**{k: v for k, v in body.items() if k in allowed})
        except Exception as e:
            # The app falls back to its own canned copy on any failure, so a broken model
            # call degrades to the old behaviour instead of an empty screen.
            out = {"error": f"{type(e).__name__}: {e}", "live": False}
            print(f"  !! {self.path} {out['error']}")

        payload = json.dumps(out).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *a):
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--no-open", action="store_true")
    ap.add_argument("--doc", action="store_true",
                    help="serve the annotated design document instead of the app")
    a = ap.parse_args()

    global SRC
    SRC = DOC if a.doc else APP

    # threaded: a live /api call runs 10-30s, and on a single-threaded server that blocks
    # every other request including the page reload
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    socketserver.ThreadingTCPServer.daemon_threads = True
    with socketserver.ThreadingTCPServer(("127.0.0.1", a.port), Handler) as srv:
        url = f"http://localhost:{a.port}"
        print(f"{'document' if a.doc else 'app':<10} {url}")
        print(f"           edit {SRC.relative_to(ROOT)} and refresh — no rebuild")
        print("           ctrl-c to stop")
        if not a.no_open:
            try:
                webbrowser.open(url)
            except Exception:
                pass
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print("\nstopped")


if __name__ == "__main__":
    main()

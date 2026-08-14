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
from urllib.parse import urlsplit

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
APP = ROOT / "docs/app.html"
DOC = ROOT / "docs/prototype.html"
SRC = APP
MAX_BODY_BYTES = 48_000

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
    server_version = "Mindfulness"
    sys_version = ""

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Permissions-Policy", "microphone=(self), screen-wake-lock=(self)")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; style-src 'self' 'unsafe-inline'; "
            "script-src 'self' 'unsafe-inline'; connect-src 'self'; "
            "img-src 'self' data:; media-src 'self' blob:; "
            "frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
        )
        super().end_headers()

    def _json(self, out: dict, status: int = 200):
        payload = json.dumps(out).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/healthz":
            return self._json({"ok": True})
        if path not in ("/", "/index.html"):
            return self.send_error(404)
        page = SHELL.format(body=SRC.read_text()).encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(page)))
        self.send_header("Cache-Control", "no-store")   # always reflect the file on disk
        self.end_headers()
        self.wfile.write(page)

    def do_HEAD(self):
        """Mirror the tiny GET surface without exposing filesystem metadata."""
        path = urlsplit(self.path).path
        if path not in ("/", "/index.html", "/healthz"):
            return self.send_error(404)
        self.send_response(200)
        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8" if path == "/healthz" else "text/html; charset=utf-8",
        )
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def do_POST(self):
        """Intake and generation. The key stays here and never reaches the browser."""
        from generator import api

        path = urlsplit(self.path).path
        routes = {
            "/api/talk": api.talk,
            "/api/questions": api.questions,
            "/api/generate": api.generate_session,
        }
        fn = routes.get(path)
        if not fn:
            return self.send_error(404)

        try:
            content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if content_type != "application/json":
                return self._json({"error": "Content-Type must be application/json."}, 415)
            n = int(self.headers.get("Content-Length", 0))
            if n <= 0:
                return self._json({"error": "A JSON request body is required."}, 400)
            if n > MAX_BODY_BYTES:
                return self._json({"error": "Request body is too large."}, 413)
            body = json.loads(self.rfile.read(n) or "{}")
            if not isinstance(body, dict):
                return self._json({"error": "JSON body must be an object."}, 400)
            # signature parameters only. co_varnames also lists locals, so a body key that
            # happened to match one - "llm", "usage", "template" - was forwarded as a kwarg
            allowed = set(inspect.signature(fn).parameters)
            out = fn(**{k: v for k, v in body.items() if k in allowed})
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            print(f"  !! {path} invalid request: {type(exc).__name__}")
            return self._json({"error": "The request was not valid.", "live": False}, 400)
        except Exception as exc:
            # Do not send exception strings to the browser; provider errors can contain
            # request metadata that belongs only in the server log.
            print(f"  !! {path} failed: {type(exc).__name__}")
            return self._json({"error": "The request could not be completed.", "live": False}, 500)

        self._json(out)

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

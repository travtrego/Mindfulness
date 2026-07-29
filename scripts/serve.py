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
import socketserver
import webbrowser
from pathlib import Path

ROOT = Path(__file__).parent.parent
SRC = ROOT / "docs/prototype.html"

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

    def log_message(self, *a):
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--no-open", action="store_true")
    a = ap.parse_args()

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", a.port), Handler) as srv:
        url = f"http://localhost:{a.port}"
        print(f"prototype  {url}")
        print("           edit docs/prototype.html and refresh — no rebuild")
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

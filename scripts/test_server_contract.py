#!/usr/bin/env python3
"""Exercise the public HTTP surface without a model key or external network."""

import json
import sys
import threading
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.serve import Handler, MAX_BODY_BYTES
from socketserver import ThreadingTCPServer


def request(base: str, path: str, *, body=None, content_type="application/json"):
    data = None if body is None else (body if isinstance(body, bytes) else json.dumps(body).encode())
    headers = {"Content-Type": content_type} if data is not None else {}
    req = Request(base + path, data=data, headers=headers, method="POST" if data is not None else "GET")
    try:
        with urlopen(req, timeout=10) as response:
            return response.status, response.headers, response.read()
    except HTTPError as error:
        return error.code, error.headers, error.read()


def head(base: str, path: str):
    req = Request(base + path, method="HEAD")
    try:
        with urlopen(req, timeout=10) as response:
            return response.status
    except HTTPError as error:
        return error.code


def main() -> None:
    ThreadingTCPServer.allow_reuse_address = True
    with ThreadingTCPServer(("127.0.0.1", 0), Handler) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_address[1]}"
        try:
            status, headers, page = request(base, "/")
            assert status == 200 and b"Guided visualization" in page
            assert headers["X-Content-Type-Options"] == "nosniff"
            assert "default-src 'self'" in headers["Content-Security-Policy"]

            status, _, health = request(base, "/healthz")
            assert status == 200 and json.loads(health) == {"ok": True}

            status, _, _ = request(base, "/pyproject.toml")
            assert status == 404, "repository files must never be served"
            assert head(base, "/pyproject.toml") == 404

            status, _, payload = request(base, "/api/generate", body={"category": "Nature"})
            session = json.loads(payload)
            assert status == 200 and session["beats"] and session["template"] == "immersive"

            status, _, _ = request(base, "/api/generate", body=b"not-json")
            assert status == 400
            status, _, _ = request(base, "/api/generate", body={"category": "Nature"},
                                   content_type="text/plain")
            assert status == 415
            status, _, _ = request(base, "/api/generate", body=b" " * (MAX_BODY_BYTES + 1))
            assert status == 413
        finally:
            server.shutdown()
            thread.join(timeout=5)

    print("server contract ok: app/API work and repository files stay private")


if __name__ == "__main__":
    main()

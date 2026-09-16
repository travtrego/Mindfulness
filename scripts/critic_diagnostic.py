"""Enable a one-hour diagnostic window or probe it without printing its credential."""
import argparse
import hashlib
import json
import secrets
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

ROOT = Path(__file__).resolve().parent.parent
TOKEN_FILE = ROOT / ".local" / "critic-diagnostic-token"
VERIFIER = ROOT / "generator" / "diagnostic_access.py"


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None  # Never forward a credential to a different host.


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["enable", "disable", "status", "probe"])
    parser.add_argument("--url", default="https://mindfulness-theta.vercel.app")
    args = parser.parse_args()
    if args.action in ("enable", "disable"):
        token = secrets.token_hex(32) if args.action == "enable" else ""
        digest = hashlib.sha256(token.encode()).hexdigest() if token else ""
        expires = int(time.time()) + 3600 if token else 0
        if token:
            TOKEN_FILE.parent.mkdir(exist_ok=True)
            TOKEN_FILE.write_text(token, encoding="utf-8")
        else:
            TOKEN_FILE.unlink(missing_ok=True)
        VERIFIER.write_text(
            '"""Public verifier only; the random bearer token is never deployed or committed."""\n'
            f'TOKEN_SHA256 = "{digest}"\nEXPIRES_AT = {expires}\n', encoding="utf-8")
        print(f"Diagnostic {args.action} prepared. Commit and deploy the public verifier only.")
        return
    target = urlsplit(args.url)
    if (target.scheme != "https" or not target.hostname or target.username or target.password
            or target.query or target.fragment or target.path not in ("", "/")):
        parser.error("--url must be an HTTPS origin without credentials, path, or query")
    request = Request(args.url.rstrip("/") + "/api/diagnostics/critic",
                      method="POST" if args.action == "probe" else "GET",
                      headers={"Authorization": "Bearer " + TOKEN_FILE.read_text().strip()})
    try:
        response = build_opener(NoRedirect).open(request, timeout=45)
    except HTTPError as error:
        response = error
    with response:
        code = response.code
        payload = response.read()
        try:
            result = json.loads(payload)
        except ValueError:
            result = {"reason": "non_json_response"}
        # Only the diagnostic's fixed, safe fields may be printed.
        fields = ("ok", "reason", "configured", "critic_model", "model_configured",
                  "checked_at", "reachable", "critic_model_responded", "scope",
                  "latency_ms", "provider_http_status")
        print(json.dumps({"http_status": code, **{k: result[k] for k in fields if k in result}}, indent=2))
        raise SystemExit(0 if code == 200 else 1)


if __name__ == "__main__":
    main()

"""Isolated, authenticated production check of the existing OpenAI critic call."""
import hashlib
import hmac
import re
import threading
import time
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError

from . import critic, diagnostic_access

PATH = "/api/diagnostics/critic"
_lock = threading.Lock()
_next_probe_at = 0.0


def authorized(header: str) -> bool:
    # A 256-bit random capability with a public hash avoids distributing provider keys
    # or requiring a change to the production environment. It expires on every replica.
    if time.time() >= diagnostic_access.EXPIRES_AT:
        return False
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not re.fullmatch(r"[0-9a-f]{64}", token):
        return False
    return hmac.compare_digest(
        hashlib.sha256(token.encode()).hexdigest(), diagnostic_access.TOKEN_SHA256
    )


def status() -> dict:
    model = critic._critic_model()
    return {
        "configured": bool(critic._openai_key()),
        "critic_model": model if re.fullmatch(r"(?:gpt-|o[1-9])[\w.-]{1,100}", model) else "custom",
        "model_configured": bool(model),
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "reachable": None,
        "critic_model_responded": False,
        "scope": "synthetic_critic_probe",
    }


def probe() -> tuple[dict, int]:
    global _next_probe_at
    out = status()
    if not out["configured"] or not out["model_configured"]:
        return {**out, "ok": False, "reason": "not_configured"}, 503
    # Defense in depth for accidental repeated clicks, not a distributed rate limiter.
    # Authentication + a short expiration are the fleet-wide access boundary.
    with _lock:
        now = time.monotonic()
        if now < _next_probe_at:
            return {**out, "ok": False, "reason": "cooldown"}, 429
        _next_probe_at = now + 60

    started = time.monotonic()
    try:
        critique = critic._call_openai({
            "category": "Nature", "template": "immersive", "duration_s": 30,
            "beats": [{"role": "arrival", "source": "generated", "text":
                "Your shoes settle into the damp sand. A small wave spreads around "
                "your soles, then slips back, leaving the sand cool beneath you."}],
        }, timeout=30, require_completed=True)
        out["reachable"] = True
        # HTTP success alone is insufficient: require usable critic JSON.
        if (not isinstance(critique, dict)
                or critique.get("verdict") not in ("keep", "revise")
                or not isinstance(critique.get("summary"), str)
                or not isinstance(critique.get("revisions"), list)
                or len(critique["revisions"]) > critic.MAX_REVISIONS
                or any(not isinstance(r, dict) or r.get("role") != "arrival"
                       or not isinstance(r.get("instruction"), str)
                       or not r["instruction"].strip() for r in critique["revisions"])
                or (critique["verdict"] == "revise" and not critique["revisions"])):
            raise ValueError("invalid critique")
        out.update(ok=True, critic_model_responded=True, reason="critic_responded")
        code = 200
    except HTTPError as exc:
        out.update(ok=False, reachable=True, provider_http_status=exc.code,
                   reason={401: "authentication_failed", 403: "access_denied",
                           404: "model_unavailable", 429: "rate_limit_or_quota"}
                   .get(exc.code, "provider_error"))
        code = 502
    except (TimeoutError, URLError, OSError):
        out.update(ok=False, reason="connection_or_timeout")
        code = 504
    except (ValueError, TypeError, KeyError, AttributeError):
        out.update(ok=False, reachable=True, reason="invalid_critic_response")
        code = 502
    except Exception:
        out.update(ok=False, reason="diagnostic_failed")
        code = 500
    out["latency_ms"] = round((time.monotonic() - started) * 1000)
    # Never expose model output, exception text, provider bodies/headers, or credentials.
    return out, code

# Production critic diagnostic

`/api/diagnostics/critic` tests the existing OpenAI critic independently of session
generation. It does not run Opus, rewrite beats, synthesize audio, or change fail-open behavior.
Both methods require a separate diagnostic bearer token; the OpenAI key never leaves Vercel.

- `GET`: configuration only, no provider call. `reachable: null` means untested.
- `POST` with no body: send one fixed synthetic beat through `critic._call_openai`, using
  its configured model, Responses API, prompt, output budget, and JSON parser. The probe
  uses a 30-second network timeout; normal generation retains its 75-second timeout.
- Success requires a completed response and valid critic JSON. Response fields include
  `configured`, `critic_model`, `reachable`, `critic_model_responded`, `checked_at`, and
  `latency_ms`. No key fragments, model output, provider error bodies, or exception messages
  are returned or logged.
- `401`: unauthorized or expired access; `503`: missing configuration; `502`: provider
  rejection or invalid critique; `504`: network failure/timeout; `429`: local cooldown.
  HTTP errors prove the provider was reachable, but do not prove model success.

## Safe operation

From the repository root:

```sh
python scripts/critic_diagnostic.py enable
# Commit generator/diagnostic_access.py with the implementation, then deploy.
python scripts/critic_diagnostic.py status
python scripts/critic_diagnostic.py probe
```

The default target is `https://mindfulness-theta.vercel.app`. Use `--url https://...` to
check a particular deployment. The helper refuses redirects and never prints the token.

`enable` creates a random 256-bit token in `.local/critic-diagnostic-token`, excluded from
Git and CLI deployments. Only its SHA-256 verifier and one-hour expiry are committed.
The verifier is safe to publish: it cannot authenticate a request. Every server instance
rejects the token after expiry, even on old deployment URLs. This avoids changing provider
credentials or production environment variables merely to verify the integration.
Re-enable and deploy a new verifier for another maintenance window. For early revocation,
run `python scripts/critic_diagnostic.py disable` and deploy the verifier change; old
deployment URLs remain protected by their original expiry until it passes.

The one-minute cooldown is per process, not a distributed rate limiter. The secret token
and global expiry are the access controls. Authorized POST requests incur a small model
charge (at most the existing 1,800 output-token budget); there are no automatic retries.
GET and unauthenticated requests incur no model usage. All JSON responses use `no-store`.

A successful probe proves that production credentials can call the configured critic and
parse its response at the reported time. It does not prove that every real session invokes
the critic, that Opus revisions succeeded, or that audio pacing is correct. Real generation
still reports its own `quality_layer` metadata.

## Offline checks

```sh
python -X utf8 scripts/test_critic_diagnostic.py
python -X utf8 scripts/test_server_contract.py
python -X utf8 scripts/check_app_contract.py
python -X utf8 scripts/test_api_sessions.py
```

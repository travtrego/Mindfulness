"""Offline safety, shared-call, HTTP access, and fail-open regression checks."""
import hashlib
import io
import json
import os
import sys
import threading
import time
import unittest
from pathlib import Path
from socketserver import ThreadingTCPServer
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import app
from generator import api, critic, diagnostics, diagnostic_access

VALID = {"verdict": "keep", "summary": "Specific and grounded.", "revisions": []}
SECRET = "provider-secret-must-not-appear"


class DiagnosticTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {"OPENAI_API_KEY": SECRET,
                                         "OPENAI_CRITIC_MODEL": "gpt-test"}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)
        diagnostics._next_probe_at = 0

    def test_real_transport_uses_configured_model_and_parser(self):
        response = io.BytesIO(json.dumps({"status": "completed", "output": [{"type": "message", "content": [
            {"type": "output_text", "text": json.dumps(VALID)}]}]}).encode())
        with patch.object(critic, "urlopen", return_value=response) as call:
            out, code = diagnostics.probe()
        self.assertEqual(code, 200)
        self.assertTrue(out["critic_model_responded"])
        request = call.call_args.args[0]
        self.assertEqual(request.full_url, critic.OPENAI_RESPONSES_URL)
        self.assertEqual(json.loads(request.data)["model"], "gpt-test")
        self.assertEqual(call.call_args.kwargs["timeout"], 30)
        self.assertNotIn(SECRET, json.dumps(out))
        self.assertNotIn(VALID["summary"], json.dumps(out))

    def test_incomplete_response_is_not_success(self):
        response = io.BytesIO(json.dumps({"status": "incomplete", "output": [{"type": "message", "content": [
            {"type": "output_text", "text": json.dumps(VALID)}]}]}).encode())
        with patch.object(critic, "urlopen", return_value=response):
            out, code = diagnostics.probe()
        self.assertEqual(code, 502)
        self.assertFalse(out["critic_model_responded"])

    def test_missing_key_never_calls_provider(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": " "}), patch.object(critic, "_call_openai") as call:
            out, code = diagnostics.probe()
        self.assertEqual(code, 503)
        self.assertFalse(out["configured"])
        call.assert_not_called()

    def test_errors_are_sanitized_and_not_success(self):
        cases = [
            (HTTPError("https://example.com", 401, SECRET, {}, io.BytesIO(SECRET.encode())), 502, True),
            (HTTPError("https://example.com", 404, SECRET, {}, None), 502, True),
            (HTTPError("https://example.com", 429, SECRET, {}, None), 502, True),
            (TimeoutError(SECRET), 504, None), (URLError(SECRET), 504, None),
            (ValueError(SECRET), 502, True), (RuntimeError(SECRET), 500, None),
        ]
        for error, expected_code, reachable in cases:
            with self.subTest(error=type(error).__name__):
                diagnostics._next_probe_at = 0
                with patch.object(critic, "_call_openai", side_effect=error):
                    out, code = diagnostics.probe()
                self.assertEqual(code, expected_code)
                self.assertEqual(out["reachable"], reachable)
                self.assertFalse(out["critic_model_responded"])
                self.assertNotIn(SECRET, json.dumps(out))

    def test_bad_critique_and_cooldown(self):
        for payload in ({}, {**VALID, "verdict": "unknown"}, {**VALID, "revisions": [{}]},
                        {**VALID, "verdict": "revise"}):
            diagnostics._next_probe_at = 0
            with patch.object(critic, "_call_openai", return_value=payload):
                self.assertEqual(diagnostics.probe()[1], 502)
        with patch.object(critic, "_call_openai") as call:
            self.assertEqual(diagnostics.probe()[1], 429)
            call.assert_not_called()

    def test_generation_wiring_and_fail_open(self):
        self.assertIs(api.generate_session, critic.generate_session)
        original = {"live": True, "script": "original", "beats": []}
        with patch.object(critic, "_base_generate_session", return_value=original.copy()), \
             patch.object(critic, "_call_openai", side_effect=TimeoutError(SECRET)):
            result = api.generate_session(category="Nature")
        self.assertEqual(result["script"], "original")
        self.assertFalse(result["quality_layer"]["active"])
        with patch.object(critic, "_base_generate_session", return_value=original.copy()), \
             patch.dict(os.environ, {"OPENAI_API_KEY": ""}), \
             patch.object(critic, "_call_openai") as call:
            result = api.generate_session(category="Nature")
            self.assertEqual(result["quality_layer"]["reason"], "openai_not_configured")
            call.assert_not_called()
        with patch.object(critic, "_base_generate_session", return_value=original.copy()), \
             patch.object(critic, "_call_openai", return_value=VALID) as call:
            result = api.generate_session(category="Nature")
            self.assertTrue(result["quality_layer"]["active"])
            self.assertEqual(call.call_args.kwargs, {})  # generation retains 75s default

    def test_production_http_forwards_inputs_and_runs_critic(self):
        inputs = {"category": "Nature", "history": [], "answers": [],
                  "exclusions": [], "memory": {}}
        original = {"live": True, "fallback": False, "script": "original", "beats": []}
        with patch.object(critic, "_base_generate_session", return_value=original) as base, \
             patch.object(critic, "_call_openai", return_value=VALID) as judge, \
             ThreadingTCPServer(("127.0.0.1", 0), app.handler) as server:
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            try:
                req = Request(f"http://127.0.0.1:{server.server_address[1]}/api/generate",
                              data=json.dumps({**inputs, "untrusted_extra": "ignored"}).encode(),
                              headers={"Content-Type": "application/json"})
                with urlopen(req, timeout=5) as response:
                    result = json.loads(response.read())
                    self.assertEqual(response.status, 200)
                base.assert_called_once_with(**inputs)
                judge.assert_called_once()
                self.assertTrue(result["quality_layer"]["active"])
            finally:
                server.shutdown()
                worker.join()

    def test_http_access_and_read_only_get(self):
        token = "a" * 64  # test-only credential, never used by the deployment
        with patch.object(diagnostic_access, "TOKEN_SHA256", hashlib.sha256(token.encode()).hexdigest()), \
             patch.object(diagnostic_access, "EXPIRES_AT", time.time() + 60), \
             patch.object(critic, "_call_openai", return_value=VALID) as call, \
             ThreadingTCPServer(("127.0.0.1", 0), app.handler) as server:
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            def request(method="GET", auth=None, data=None):
                req = Request(f"http://127.0.0.1:{server.server_address[1]}{diagnostics.PATH}",
                              method=method, data=data,
                              headers={"Authorization": auth} if auth else {})
                try:
                    response = urlopen(req, timeout=5)
                except HTTPError as error:
                    response = error
                with response:
                    self.assertEqual(response.headers["Cache-Control"], "no-store")
                    return response.code, json.loads(response.read())
            try:
                self.assertEqual(request()[0], 401)
                self.assertEqual(request("POST", "Bearer wrong")[0], 401)
                auth = "Bearer " + token
                self.assertEqual(request(auth=auth)[0], 200)
                self.assertEqual(request("POST", auth, b'{}')[0], 400)
                call.assert_not_called()
                self.assertEqual(request("POST", auth)[0], 200)
                self.assertEqual(request("POST", auth)[0], 429)
                self.assertEqual(call.call_count, 1)
                with patch.object(diagnostic_access, "EXPIRES_AT", 0):
                    self.assertEqual(request("POST", auth)[0], 401)
                self.assertEqual(call.call_count, 1)
            finally:
                server.shutdown()
                worker.join()


if __name__ == "__main__":
    unittest.main()

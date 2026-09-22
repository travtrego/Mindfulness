"""Server-side ElevenLabs narration.

The browser requests short speech clips, then joins their PCM samples with exact silence
into one WAV. Pause markers never reach the speech model. Credentials stay server-side.
"""
from __future__ import annotations

import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

API_ROOT = "https://api.elevenlabs.io/v1"

# Product direction: intimate, low, velvety female narration with a sensual, whispery edge.
# Natasha is a public ElevenLabs Voice Library voice described by ElevenLabs as sensual,
# hypnotic, gentle, whispery, playful, and suitable for guided meditation / hypnosis.
PREFERRED_VOICE_ID = "PB6BdkFkZLbI39GHdnbQ"  # Natasha — Sensual, Hypnotic and Playful

# Female American fallback if the Voice Library voice is not available to this API account.
FALLBACK_FEMALE_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"

DEFAULT_MODEL_ID = "eleven_multilingual_v2"
SAMPLE_RATE = 24_000
OUTPUT_FORMAT = "pcm_24000"
MAX_TEXT_CHARS = 600
MAX_AUDIO_BYTES = SAMPLE_RATE * 2 * 75


def _key() -> str:
    return (os.environ.get("ELEVENLABS_API_KEY") or "").strip()


def _model_id() -> str:
    return (os.environ.get("ELEVENLABS_MODEL_ID") or DEFAULT_MODEL_ID).strip()


def _voice_id(preference: str | None = None) -> str:
    """Return the current product voice.

    Old ELEVENLABS_VOICE_ID / *_LOWER / *_DEEPER values are deliberately ignored here.
    The explicit warm-voice override remains available for controlled production tests.
    """
    return (os.environ.get("ELEVENLABS_VOICE_ID_WARM") or PREFERRED_VOICE_ID).strip()


def prepare_text(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("text is required")
    text = text.strip()
    if len(text) > MAX_TEXT_CHARS:
        raise ValueError("speech clip is too long")
    # Pauses belong to the sample timeline, never SSML (which can accelerate speech).
    if re.search(r"\*\[.*?\]\*|<[^>]+>", text):
        raise ValueError("speech clips cannot contain pause markers or markup")
    return text


def _request_audio(key: str, voice_id: str, prepared: str, model_id: str,
                   previous_text: str = "", next_text: str = "") -> bytes:
    body = json.dumps({
        "text": prepared,
        "model_id": model_id,
        "previous_text": previous_text,
        "next_text": next_text,
        "voice_settings": {
            "stability": 0.75,
            "similarity_boost": 0.80,
            "style": 0.0,
            "use_speaker_boost": True,
            "speed": 0.90,
        },
    }).encode("utf-8")
    request = Request(
        f"{API_ROOT}/text-to-speech/{quote(voice_id)}?output_format={OUTPUT_FORMAT}",
        data=body, method="POST",
        headers={"xi-api-key": key, "Content-Type": "application/json",
                 "Accept": "application/octet-stream"},
    )
    with urlopen(request, timeout=90) as response:
        audio = response.read(MAX_AUDIO_BYTES + 1)
    if not audio or len(audio) % 2 or len(audio) > MAX_AUDIO_BYTES:
        raise RuntimeError("ElevenLabs returned invalid or oversized PCM audio")
    return audio


def status() -> dict:
    """Verify the configured credential without exposing it."""
    key = _key()
    model_id = _model_id()
    if not key:
        return {
            "configured": False,
            "ok": False,
            "voice_id": PREFERRED_VOICE_ID,
            "model_id": model_id,
            "note": "ELEVENLABS_API_KEY is not configured.",
        }

    request = Request(f"{API_ROOT}/voices", headers={"xi-api-key": key, "Accept": "application/json"})
    try:
        with urlopen(request, timeout=12) as response:
            payload = json.loads(response.read().decode("utf-8"))
        voices = payload.get("voices", []) if isinstance(payload, dict) else []
        listed = any(v.get("voice_id") == PREFERRED_VOICE_ID for v in voices if isinstance(v, dict))
        return {
            "configured": True,
            "ok": True,
            "voice_id": PREFERRED_VOICE_ID,
            "preferred_voice_listed": listed,
            "fallback_voice_id": FALLBACK_FEMALE_VOICE_ID,
            "model_id": model_id,
        }
    except HTTPError as exc:
        return {
            "configured": True,
            "ok": False,
            "voice_id": PREFERRED_VOICE_ID,
            "model_id": model_id,
            "provider_status": exc.code,
        }
    except (URLError, TimeoutError, ValueError):
        return {
            "configured": True,
            "ok": False,
            "voice_id": PREFERRED_VOICE_ID,
            "model_id": model_id,
            "provider_status": "unreachable",
        }


def synthesize(text: str, voice: str | None = None, *, previous_text: str = "",
               next_text: str = "", pinned_voice: str | None = None) -> tuple[bytes, str]:
    prepared = prepare_text(text)
    previous_text = previous_text or ""
    next_text = next_text or ""
    if any(not isinstance(t, str) or len(t) > MAX_TEXT_CHARS
           for t in (previous_text, next_text)):
        raise ValueError("invalid speech context")
    preferred = _voice_id(voice)
    if pinned_voice is not None and pinned_voice not in {preferred, FALLBACK_FEMALE_VOICE_ID}:
        raise ValueError("invalid pinned voice")
    key = _key()
    if not key:
        raise RuntimeError("ElevenLabs is not configured")
    selected = pinned_voice or preferred
    try:
        return (_request_audio(key, selected, prepared, _model_id(), previous_text, next_text), selected)
    except HTTPError as exc:
        # Resolve fallback on the FIRST clip only. Never change voice mid-session.
        if pinned_voice or selected == FALLBACK_FEMALE_VOICE_ID or exc.code not in {400, 403, 404, 422}:
            raise
        return (_request_audio(key, FALLBACK_FEMALE_VOICE_ID, prepared, _model_id(),
                               previous_text, next_text), FALLBACK_FEMALE_VOICE_ID)

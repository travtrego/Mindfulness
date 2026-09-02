"""Server-side ElevenLabs narration.

The browser never receives the ElevenLabs credential. The app posts the finished session
script here; this module converts our pause markers into short SSML breaks and returns one
complete MP3 so playback uses a real media element rather than browser speech synthesis.
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
OUTPUT_FORMAT = "mp3_44100_128"
MAX_TEXT_CHARS = 20_000


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


def _pause_seconds(raw: str) -> float:
    """Turn legacy 4-12s silence markers into short, intentional spoken pauses."""
    seconds = max(0.0, float(raw))
    return max(0.7, min(2.8, seconds * 0.32))


def prepare_text(text: str) -> str:
    if not isinstance(text, str):
        raise ValueError("text is required")
    text = text.strip()
    if not text:
        raise ValueError("text is required")
    if len(text) > MAX_TEXT_CHARS:
        raise ValueError("text is too long")

    text = re.sub(
        r"\*\[\s*(\d+(?:\.\d+)?)\s*s\s*\]\*",
        lambda m: f'<break time="{_pause_seconds(m.group(1)):.1f}s" />',
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"^[>#]+\s*", "", text, flags=re.MULTILINE)
    text = text.replace("**", "").replace("__", "").replace("`", "")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _request_audio(key: str, voice_id: str, prepared: str, model_id: str) -> bytes:
    body = json.dumps({
        "text": prepared,
        "model_id": model_id,
        "voice_settings": {
            "stability": 0.38,
            "similarity_boost": 0.80,
            "style": 0.24,
            "use_speaker_boost": True,
            "speed": 0.90,
        },
    }).encode("utf-8")

    url = f"{API_ROOT}/text-to-speech/{quote(voice_id)}?output_format={OUTPUT_FORMAT}"
    request = Request(
        url,
        data=body,
        method="POST",
        headers={
            "xi-api-key": key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
    )
    with urlopen(request, timeout=90) as response:
        audio = response.read()
    if not audio:
        raise RuntimeError("ElevenLabs returned empty audio")
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


def synthesize(text: str, voice: str | None = None) -> bytes:
    key = _key()
    if not key:
        raise RuntimeError("ElevenLabs is not configured")

    prepared = prepare_text(text)
    model_id = _model_id()
    preferred = _voice_id(voice)

    try:
        return _request_audio(key, preferred, prepared, model_id)
    except HTTPError as exc:
        # Voice Library access can depend on plan/account availability. If the selected
        # library voice is unavailable, preserve the product's female voice direction rather
        # than falling back to browser speech or an old male voice.
        if preferred == FALLBACK_FEMALE_VOICE_ID or exc.code not in {400, 403, 404, 422}:
            raise
        return _request_audio(key, FALLBACK_FEMALE_VOICE_ID, prepared, model_id)

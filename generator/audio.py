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
DEFAULT_LOWER_VOICE_ID = "pNInz6obpgDQGcFmaJgB"  # Adam, ElevenLabs premade voice
DEFAULT_DEEPER_VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"  # George, ElevenLabs premade voice
DEFAULT_MODEL_ID = "eleven_multilingual_v2"
OUTPUT_FORMAT = "mp3_44100_128"
MAX_TEXT_CHARS = 20_000


def _key() -> str:
    return (os.environ.get("ELEVENLABS_API_KEY") or "").strip()


def _model_id() -> str:
    return (os.environ.get("ELEVENLABS_MODEL_ID") or DEFAULT_MODEL_ID).strip()


def _voice_id(preference: str | None = None) -> str:
    if preference == "lower":
        value = os.environ.get("ELEVENLABS_VOICE_ID_LOWER")
        if value:
            return value.strip()
    if preference == "deeper":
        value = os.environ.get("ELEVENLABS_VOICE_ID_DEEPER")
        if value:
            return value.strip()

    general = os.environ.get("ELEVENLABS_VOICE_ID")
    if general:
        return general.strip()
    if preference == "lower":
        return DEFAULT_LOWER_VOICE_ID
    return DEFAULT_DEEPER_VOICE_ID


def _pause_seconds(raw: str) -> float:
    """Turn legacy 4-12s silence markers into natural, bounded spoken pauses.

    ElevenLabs supports exact SSML breaks up to 3 seconds on Multilingual v2. The old
    browser player deliberately used much longer silence; owner listening showed that those
    waits feel dead rather than calm, so narration compresses them aggressively.
    """
    seconds = max(0.0, float(raw))
    return max(0.8, min(3.0, seconds * 0.38))


def prepare_text(text: str) -> str:
    if not isinstance(text, str):
        raise ValueError("text is required")
    text = text.strip()
    if not text:
        raise ValueError("text is required")
    if len(text) > MAX_TEXT_CHARS:
        raise ValueError("text is too long")

    # Our scripts mark silence as *[6s]*. Multilingual v2 understands exact SSML breaks.
    text = re.sub(
        r"\*\[\s*(\d+(?:\.\d+)?)\s*s\s*\]\*",
        lambda m: f'<break time="{_pause_seconds(m.group(1)):.1f}s" />',
        text,
        flags=re.IGNORECASE,
    )
    # Strip the markdown-ish craft notation that should never be spoken.
    text = re.sub(r"^[>#]+\s*", "", text, flags=re.MULTILINE)
    text = text.replace("**", "").replace("__", "").replace("`", "")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def status() -> dict:
    """Verify the configured credential and selected default voice without exposing the key."""
    key = _key()
    voice_id = _voice_id("deeper")
    model_id = _model_id()
    if not key:
        return {
            "configured": False,
            "ok": False,
            "voice_id": voice_id,
            "model_id": model_id,
            "note": "ELEVENLABS_API_KEY is not configured.",
        }

    request = Request(f"{API_ROOT}/voices", headers={"xi-api-key": key, "Accept": "application/json"})
    try:
        with urlopen(request, timeout=12) as response:
            payload = json.loads(response.read().decode("utf-8"))
        voices = payload.get("voices", []) if isinstance(payload, dict) else []
        found = any(v.get("voice_id") == voice_id for v in voices if isinstance(v, dict))
        return {
            "configured": True,
            "ok": True,
            "voice_id": voice_id,
            "voice_found": found,
            "model_id": model_id,
        }
    except HTTPError as exc:
        return {
            "configured": True,
            "ok": False,
            "voice_id": voice_id,
            "model_id": model_id,
            "provider_status": exc.code,
        }
    except (URLError, TimeoutError, ValueError):
        return {
            "configured": True,
            "ok": False,
            "voice_id": voice_id,
            "model_id": model_id,
            "provider_status": "unreachable",
        }


def synthesize(text: str, voice: str | None = None) -> bytes:
    key = _key()
    if not key:
        raise RuntimeError("ElevenLabs is not configured")

    voice_id = _voice_id(voice)
    model_id = _model_id()
    prepared = prepare_text(text)
    body = json.dumps({
        "text": prepared,
        "model_id": model_id,
        "voice_settings": {
            "stability": 0.46,
            "similarity_boost": 0.78,
            "style": 0.12,
            "use_speaker_boost": True,
            "speed": 1.04,
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

"""Optional second-model quality pass for finished guided visualizations.

Opus remains the author. GPT-5.6 Sol reads the finished session as an editor, identifies at
most two weak generated beats, and gives precise revision notes. Opus then rewrites only those
beats. If OpenAI is not configured or either provider fails, the original Opus session is
returned unchanged so this layer can improve quality without becoming a new availability risk.
"""
from __future__ import annotations

import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from . import prompts
from .api import generate_session as _base_generate_session
from .craft import check
from .pipeline import _live_llm, _rewrite_prompt

OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
DEFAULT_CRITIC_MODEL = "gpt-5.6-sol"
MAX_REVISIONS = 2


def _openai_key() -> str:
    return (os.environ.get("OPENAI_API_KEY") or "").strip()


def _critic_model() -> str:
    return (os.environ.get("OPENAI_CRITIC_MODEL") or DEFAULT_CRITIC_MODEL).strip()


def _json_from(text: str) -> dict:
    fenced = re.search(r"```(?:json)?\s*(.+?)```", text, re.S)
    raw = fenced.group(1) if fenced else text
    start = raw.find("{")
    if start < 0:
        raise ValueError("critic returned no JSON object")
    out = json.JSONDecoder().raw_decode(raw[start:])[0]
    if not isinstance(out, dict):
        raise ValueError("critic response is not an object")
    return out


def _response_text(payload: dict) -> str:
    """Extract text from the REST Responses API without depending on the OpenAI SDK."""
    parts: list[str] = []
    for item in payload.get("output", []) if isinstance(payload, dict) else []:
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if isinstance(content, dict) and content.get("type") == "output_text":
                text = content.get("text")
                if isinstance(text, str):
                    parts.append(text)
    return "".join(parts).strip()


def _critic_prompt(session: dict) -> str:
    beats = [
        {"role": b.get("role"), "source": b.get("source"), "text": b.get("text", "")}
        for b in session.get("beats", [])
        if isinstance(b, dict) and b.get("text")
    ]
    return f"""You are the final editorial judge for an audio-first guided visualization app.
The north-star standard is: the session should feel like a lived memory, not a story being
read to the listener.

Review the COMPLETE session below. Do not rewrite it. Decide whether any generated beat is
materially weakening the experience. Reference/cached beats are context only and may not be
selected for revision.

Judge for:
- immersion: concrete, embodied, present-tense experience rather than generic coaching
- specificity: it should feel shaped by this session, not interchangeable meditation copy
- continuity: one coherent place/event with no unexplained jumps
- emotional movement: something actually develops rather than a flat sequence of instructions
- restraint: no therapy voice, motivational speech, purple prose, or excessive explanation
- sensory craft: details arrive one at a time and leave room for the listener's own imagery
- repetition: avoid obvious recycled sentence shapes and repeated "you notice" scaffolding
- ending: earned by what happened before it, not pasted-on reassurance

Be conservative. A strong beat should be left alone. Select AT MOST TWO generated beats whose
revision would create the biggest improvement. Do not select a beat for tiny wording preferences.

Session metadata:
category={session.get('category')!r}
template={session.get('template')!r}
target_duration_s={session.get('duration_s')!r}

Beats:
{json.dumps(beats, ensure_ascii=False, indent=2)}

Return JSON only:
{{
  "verdict": "keep" | "revise",
  "summary": "one short sentence",
  "revisions": [
    {{"role": "exact beat role", "instruction": "specific editorial instruction"}}
  ]
}}
"""


def _call_openai(session: dict) -> dict:
    key = _openai_key()
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    body = json.dumps({
        "model": _critic_model(),
        "input": _critic_prompt(session),
        "max_output_tokens": 1800,
    }).encode("utf-8")
    request = Request(
        OPENAI_RESPONSES_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    with urlopen(request, timeout=75) as response:
        payload = json.loads(response.read().decode("utf-8"))
    text = _response_text(payload)
    if not text:
        raise ValueError("OpenAI critic returned no text")
    return _json_from(text)


def _revision_prompt(role: str, text: str, instruction: str, session: dict) -> str:
    pause_markers = re.findall(r"\*\[\s*\d+(?:\.\d+)?\s*s\s*\]\*", text, flags=re.I)
    return f"""You wrote this beat in a guided visualization. A separate senior editor found one
material weakness. Rewrite ONLY this beat to address that note.

Beat role: {role}
Category: {session.get('category')}
Template: {session.get('template')}
Editor's note: {instruction}

Hard constraints:
- Preserve the same event/place and factual content; do not introduce a new direction.
- Keep approximately the same word count (within 10%).
- Preserve the number and durations of these silence markers: {pause_markers}
- Keep second person, present tense.
- Improve lived, embodied immediacy; do not explain the technique or add reassurance.
- Follow the craft standard exactly.

Original beat:
\"\"\"{text}\"\"\"

Return the revised narration only. No headings or explanation.
"""


def _apply_revisions(session: dict, critique: dict) -> tuple[dict, int]:
    revisions = critique.get("revisions", []) if isinstance(critique, dict) else []
    if not isinstance(revisions, list) or not revisions:
        return session, 0

    llm = _live_llm()
    if llm is None:
        return session, 0

    allowed = {
        b.get("role"): b
        for b in session.get("beats", [])
        if isinstance(b, dict) and b.get("source") not in {"cached", "reference"} and b.get("text")
    }
    changed = 0
    seen: set[str] = set()

    for item in revisions[:MAX_REVISIONS]:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "").strip()
        instruction = str(item.get("instruction") or "").strip()
        if not role or not instruction or role in seen or role not in allowed:
            continue
        seen.add(role)
        beat = allowed[role]
        original = str(beat.get("text") or "")
        if not original:
            continue

        revised = llm(
            _revision_prompt(role, original, instruction, session),
            system=prompts.CRAFT_RULES,
        ).strip()
        report = check(revised)
        if not report.ok and revised:
            revised = llm(_rewrite_prompt(revised, report), system=prompts.CRAFT_RULES).strip()
            report = check(revised)

        # The quality layer never makes a craft-valid session worse just to obey a critic.
        if revised and report.ok:
            beat["text"] = revised
            changed += 1

    if changed:
        session["script"] = "\n\n".join(
            str(b.get("text") or "").strip()
            for b in session.get("beats", [])
            if isinstance(b, dict) and str(b.get("text") or "").strip()
        )
    return session, changed


def generate_session(*args, **kwargs) -> dict:
    """Generate with Opus, then optionally run the OpenAI editorial pass."""
    session = _base_generate_session(*args, **kwargs)
    if not isinstance(session, dict) or not session.get("live") or session.get("fallback"):
        return session

    if not _openai_key():
        session["quality_layer"] = {"active": False, "reason": "openai_not_configured"}
        return session

    try:
        critique = _call_openai(session)
        session, changed = _apply_revisions(session, critique)
        session["quality_layer"] = {
            "active": True,
            "critic_model": _critic_model(),
            "verdict": str(critique.get("verdict") or "keep")[:20],
            "revised_beats": changed,
            "summary": str(critique.get("summary") or "")[:240],
        }
    except (HTTPError, URLError, TimeoutError, ValueError, RuntimeError, OSError) as exc:
        print(f"  !! quality layer skipped: {type(exc).__name__}")
        session["quality_layer"] = {"active": False, "reason": type(exc).__name__}
    return session

"""What the app calls. All functions are safe to call without an API key.

The browser never sees the key and never talks to Anthropic directly - it talks to
scripts/serve.py, which calls this. That is not a nicety: a key shipped to a browser is a
key published.

Without a key both functions return the hand-written fallbacks that used to be hardcoded in
docs/app.html, so the interface still works offline. Every response carries `live` so the UI
can say which it is rather than pretending.
"""
from __future__ import annotations

import re
from pathlib import Path

from . import prompts
from .pipeline import Usage, _json_from, _live_llm, generate
from .templates import Template, for_category

MAX_TURNS = 3            # SPEC.md 2.2. Hard cap, not a target.
MAX_QUESTIONS = 3

# The category labels the app shows, mapped to the category ids the templates know about.
CATEGORY_IDS = {
    "Just breathing": "just_breathing", "Body scan": "body_scan",
    "Nature": "nature", "Adventure": "adventure", "Fantasy": "fantasy",
    "Into sleep": "into_sleep", "Interview": "interview",
    "Game or match": "competition", "Competition": "competition",
    "Hard conversation": "hard_conversation", "Confidence": "confidence",
    "Gratitude": "gratitude", "Creativity": "creativity",
    "Safe place": "safe_place", "First day back": "going_back",
    "Seeing people again": "going_back",
    "Something else": "nature",       # the open entry - intent parsing decides for real
}

# Used when there is no key. These are the strings that were hardcoded in the page.
FALLBACK_REPLIES = [
    "Is it the thing itself, or what comes after it?",
    "Then that's what we'll do. Same place, same people — you leave it another way.",
]
FALLBACK_QUESTIONS = {
    "competition": [
        {"question": "Same pitch, or somewhere neutral?",
         "options": ["same pitch", "neutral ground"]},
        {"question": "Do you want the crowd, or do you want it quiet?",
         "options": ["the crowd", "quiet"]},
    ],
    "going_back": [
        {"question": "Does anyone ask, or does it just not come up?",
         "options": ["they ask", "it doesn't come up"]},
        {"question": "What's the part of the day you can still do without thinking?",
         "options": ["the work itself", "the routine", "the people"]},
    ],
    "_default": [
        {"question": "Somewhere you've been, or somewhere new?",
         "options": ["been there", "somewhere new"]},
    ],
}
DURATION_QUESTION = {"question": "How long have we got?",
                     "options": ["10 min", "14 min", "20 min"], "fills": "duration"}

REFERENCE_DIR = Path(__file__).parent.parent / "docs" / "sessions"
REFERENCE_BY_TEMPLATE = {
    "rehearsal": "01-clean-and-jerk.md",
    "reentry": "02-first-day-back.md",
    "anchored_place": "03-safe-place-return.md",
    "breath_only": "04-just-breathing.md",
    "immersive": "05-frozen-lake.md",
    "reflective": "06-what-your-hands-did.md",
}
REFERENCE_DURATION_S = {
    "rehearsal": 850,
    "reentry": 1201,
    "anchored_place": 650,
    "breath_only": 386,
    "immersive": 942,
    "reflective": 652,
}

# The cached opening is normally a pre-recorded asset. Until those recordings exist, the
# browser narrator reads the same approved copy. Keeping it here also means a generated
# session never begins with a silent beat while the rest of the script is complete.
INTRO_TEXT = {
    "settling": """Settle into the shape your body has already chosen.

*[5s]*

Let your eyes close — or let your focus soften onto a single still point.

*[6s]*

The surface beneath you is taking all of your weight. It has been holding you all along.

*[7s]*

Let the breath lengthen. Not deeper — only slower.

*[12s]*

There is nothing to seek here, and nothing that needs to be seen clearly.

*[10s]*""",
    "neutral": """Take the position you are going to stay in.

*[5s]*

Let your eyes close — or let your focus rest on one unmoving thing.

*[6s]*

Notice the weight of your hands. They usually go unnoticed.

*[7s]*

Let the breath find its own pace, a little under the speed of speech.

*[11s]*

Nothing here needs to be seen clearly.

*[9s]*""",
    "activating": """Sit the way you would if something were about to begin.

*[4s]*

Let your eyes close — or let your focus hold on one fixed point.

*[5s]*

Notice where the floor meets you. That contact is the whole anchor.

*[6s]*

Let the breath even out. Not slower — even.

*[9s]*

Nothing here needs to be seen clearly.

*[7s]*""",
    "sensitive": """Settle only as far as you want to. There is no further to get to.

*[6s]*

Let your eyes close, or keep them open. Both work.

*[7s]*

The surface beneath you is holding your weight, and it will keep holding it.

*[8s]*

Let the breath lengthen if it will. It does not have to.

*[12s]*

Nothing here needs to be seen clearly.

*[9s]*

You can stop this at any point. Nothing is lost by stopping.

*[10s]*""",
}


def resolve(category: str) -> tuple[str, Template]:
    cid = CATEGORY_IDS.get(category, category)
    return cid, for_category(cid)


def talk(category: str, history: list[dict]) -> dict:
    """One turn of layer 2a. `history` alternates {role: user|app, text: ...}."""
    cid, template = resolve(category)
    # Count what the listener said, not what the app said - the thread is seeded with an
    # opening line the app did not have to ask for, and counting it burns a turn.
    said = sum(1 for m in history if m["role"] == "user")

    if said >= MAX_TURNS:
        return {"reply": "", "done": True, "slots": {}, "live": False,
                "note": f"turn cap ({MAX_TURNS}) reached"}

    usage = Usage()
    llm = _live_llm(usage)
    if llm is None:
        return {"reply": FALLBACK_REPLIES[min(said - 1, len(FALLBACK_REPLIES) - 1)],
                "slots": {}, "live": False, "done": said >= 2}

    out = _json_from(llm(prompts.talk_prompt(template, cid, history)))
    return {"reply": out.get("reply", ""), "done": bool(out.get("done")),
            "slots": out.get("slots", {}), "live": True, "cost": round(usage.cost, 4)}


def questions(category: str, history: list[dict] | None = None,
              slots: dict | None = None) -> dict:
    """Layer 2b. Up to three, generated FROM what was said in 2a."""
    cid, template = resolve(category)
    slots = dict(slots or {})
    transcript = "\n".join(m["text"] for m in (history or []) if m["role"] == "user")

    usage = Usage()
    llm = _live_llm(usage)
    if llm is None:
        qs = FALLBACK_QUESTIONS.get(cid, FALLBACK_QUESTIONS["_default"])
        return {"questions": qs + [DURATION_QUESTION], "live": False,
                "template": template.name}

    still_empty = [s for s in template.required_slots if s not in slots]
    out = _json_from(llm(prompts.question_prompt(template, slots, still_empty, transcript)))
    qs = [q for q in out if q.get("question")][:MAX_QUESTIONS - 1]
    return {"questions": qs + [DURATION_QUESTION], "live": True,
            "template": template.name, "cost": round(usage.cost, 4)}


def _intro_for(template_name: str, cached_ref: str | None = None) -> str:
    """Return the approved cached opening for a generated or reference session."""
    if cached_ref:
        match = re.search(r"intro/([a-z]+)_", cached_ref)
        if match and match.group(1) in INTRO_TEXT:
            return INTRO_TEXT[match.group(1)]
    if template_name == "rehearsal":
        return INTRO_TEXT["activating"]
    if template_name == "breath_only":
        return INTRO_TEXT["settling"]
    return INTRO_TEXT["neutral"]


def _reference_session(category_id: str, template: Template, reason: str | None = None) -> dict:
    """Load the hand-written session for this template as a no-key/error fallback.

    These are not generic filler. They are the six sessions the craft validator is calibrated
    against, so a failed live model call still leaves every category with a complete session
    that can be narrated, paused, resumed, and ended.
    """
    text = (REFERENCE_DIR / REFERENCE_BY_TEMPLATE[template.name]).read_text()
    pattern = re.compile(
        r"^## Beat \d+[^\n]*role:\s*([a-z_]+)\s*\n(.*?)(?=^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    beats = []
    for role, block in pattern.findall(text):
        if role == "grounding_intro":
            narration = _intro_for(template.name)
        else:
            quoted = []
            for line in block.splitlines():
                if not line.startswith(">"):
                    continue
                line = line[1:].lstrip()
                if line.startswith("*(cached:"):
                    continue
                quoted.append(line)
            narration = "\n".join(quoted).strip()
        if narration:
            beats.append({"role": role, "source": "reference", "text": narration})

    return {
        "category": category_id,
        "template": template.name,
        "duration_s": REFERENCE_DURATION_S[template.name],
        "beats": beats,
        "script": "\n\n".join(b["text"] for b in beats),
        "live": False,
        "personalized": False,
        "fallback": True,
        "note": reason or "Reference session used because live generation is unavailable.",
    }


def _listener_text(category: str, history: list[dict], answers: list[dict]) -> str:
    said = [m.get("text", "").strip() for m in history if m.get("role") == "user"]
    answered = [
        f"{a.get('question', '').strip()} — {a.get('answer', '').strip()}"
        for a in answers if a.get("answer")
    ]
    parts = [f"Category selected: {category}."]
    if said:
        parts.append("What the listener said:\n" + "\n".join(said))
    if answered:
        parts.append("Answers to follow-up questions:\n" + "\n".join(answered))
    if len(parts) == 1:
        parts.append("No further details. Make reasonable, conservative choices.")
    return "\n\n".join(parts)


def generate_session(category: str, history: list[dict] | None = None,
                     answers: list[dict] | None = None,
                     exclusions: list[str] | None = None) -> dict:
    """Generate and serialize one complete, playable meditation session."""
    category_id, template = resolve(category)
    history = list(history or [])
    answers = list(answers or [])
    user_text = _listener_text(category, history, answers)

    # The live pipeline already degrades to dry mode without a key, but a dry Session has an
    # outline and no narration. Detect that shape and serve the matching hand-written session.
    try:
        session = generate(
            user_text,
            category=category_id,
            standing_exclusions=list(exclusions or []),
            progress=True,
        )
        if not session.beats or not session.script.strip():
            return _reference_session(category_id, template)

        beats = []
        for beat in session.beats:
            narration = (beat.get("text") or "").strip()
            if beat.get("source") == "cached":
                narration = _intro_for(template.name, beat.get("cached_ref"))
            if narration:
                beats.append({
                    "role": beat["role"],
                    "source": beat.get("source", "generated"),
                    "text": narration,
                })

        if not beats:
            return _reference_session(category_id, template, "Live generation returned no narration.")

        duration_s = (session.outline or {}).get("target_duration_s")
        return {
            "category": session.category,
            "template": session.template.name,
            "duration_s": duration_s,
            "beats": beats,
            "script": "\n\n".join(b["text"] for b in beats),
            "live": True,
            "personalized": True,
            "fallback": False,
            "cost": round(session.usage.cost, 4),
        }
    except Exception as exc:
        print(f"  !! /api/generate {type(exc).__name__}: {exc}")
        return _reference_session(
            category_id,
            template,
            f"Live generation failed ({type(exc).__name__}); reference session used.",
        )

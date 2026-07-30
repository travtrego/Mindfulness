"""What the app calls. Two functions, both safe to call without an API key.

The browser never sees the key and never talks to Anthropic directly - it talks to
scripts/serve.py, which calls this. That is not a nicety: a key shipped to a browser is a
key published.

Without a key both functions return the hand-written fallbacks that used to be hardcoded in
docs/app.html, so the interface still works offline. Every response carries `live` so the UI
can say which it is rather than pretending.
"""
from __future__ import annotations

from . import prompts
from .pipeline import Usage, _json_from, _live_llm
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

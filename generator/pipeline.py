"""Session generation pipeline.

    intent -> questions -> outline -> draft (per beat) -> craft gate -> targeted rewrite

Three text calls plus one draft call per beat. All fast; TTS is what gets parallelised
afterwards (SPEC.md 5). The cached grounding intro covers the whole text window, which is
why no loading state exists anywhere in the product.

Runs without an API key in dry mode: builds and shows every prompt, allocates the beat
budget, and validates whatever it is given. That is enough to check the shape before paying
for a single token.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import Callable

from . import prompts
from .craft import Report, check
from .templates import Template, allocate, for_category

MODEL = "claude-opus-5"
MAX_REWRITES = 2          # then pass with a log entry rather than looping
INTRO_SECONDS = {"slow": 128, "standard": 103, "brisk": 84}


@dataclass
class Trace:
    """Everything the pipeline did, for inspection and for dry runs."""
    steps: list[dict] = field(default_factory=list)

    def add(self, stage: str, **kw):
        self.steps.append({"stage": stage, **kw})

    def prompts_only(self) -> str:
        out = []
        for s in self.steps:
            if "prompt" not in s:
                continue
            out.append(f"\n{'=' * 78}\n{s['stage'].upper()}\n{'=' * 78}\n{s['prompt']}")
        return "\n".join(out)


@dataclass
class Session:
    category: str
    template: Template
    slots: dict
    outline: dict | None = None
    beats: list[dict] = field(default_factory=list)
    trace: Trace = field(default_factory=Trace)

    @property
    def script(self) -> str:
        return "\n\n".join(b["text"] for b in self.beats if b.get("text"))


LLM = Callable[[str], str]


def _live_llm() -> LLM | None:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    try:
        import anthropic
    except ImportError:
        return None
    client = anthropic.Anthropic(api_key=key)

    def call(prompt: str) -> str:
        msg = client.messages.create(
            model=MODEL, max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text
    return call


def _json_from(text: str) -> dict | list:
    """Models wrap JSON in prose and fences more often than not."""
    fenced = re.search(r"```(?:json)?\s*(.+?)```", text, re.S)
    raw = fenced.group(1) if fenced else text
    start = min((raw.find(c) for c in "[{" if raw.find(c) != -1), default=0)
    return json.loads(raw[start:])


def generate(user_text: str, *, category: str | None = None, memory: dict | None = None,
             standing_exclusions: list[str] | None = None,
             llm: LLM | None = None, pacing: str = "standard") -> Session:
    """Run the pipeline. With llm=None it builds prompts and skips model calls."""
    llm = llm or _live_llm()
    dry = llm is None
    trace = Trace()

    # --- 1. intent -------------------------------------------------------------
    p = prompts.intent_prompt(user_text, category, memory)
    trace.add("intent", prompt=p)
    if dry:
        intent = {
            "category": category or "nature",
            "slots": {}, "still_empty": [],
            "target_duration_s": 840, "sensitivity_flag": False,
            "session_exclusions": [],
        }
        trace.add("intent", note="dry run - using stub", result=intent)
    else:
        intent = _json_from(llm(p))
        trace.add("intent", result=intent)

    template = for_category(intent["category"])
    slots = dict(intent.get("slots", {}))
    exclusions = {
        "standing": standing_exclusions or [],
        "session": intent.get("session_exclusions", []),
    }
    target_s = int(intent.get("target_duration_s") or template.duration_range[0])
    lo, hi = template.duration_range
    target_s = max(lo, min(hi, target_s))

    # sensitivity forces the slow, sensitive intro
    if intent.get("sensitivity_flag"):
        pacing = "slow"

    # --- 2. amplifying questions ----------------------------------------------
    still_empty = [s for s in template.required_slots if s not in slots]
    if still_empty and template.depth > 0:
        p = prompts.question_prompt(template, slots, still_empty, user_text)
        trace.add("questions", prompt=p)
        if not dry:
            trace.add("questions", result=_json_from(llm(p)))

    # --- 3. outline ------------------------------------------------------------
    intro_s = INTRO_SECONDS[pacing]
    budget = allocate(template, target_s, intro_s)
    p = prompts.outline_prompt(template, slots, budget, exclusions, target_s)
    trace.add("outline", prompt=p, budget=budget)

    session = Session(category=intent["category"], template=template,
                      slots=slots, trace=trace)

    if dry:
        session.outline = {
            "schema_version": "1.0", "template": template.name,
            "category": intent["category"], "target_duration_s": target_s,
            "sensitivity_flag": bool(intent.get("sensitivity_flag")),
            "exclusions": exclusions, "slots": slots,
            "beats": budget, "transitions": [],
        }
        return session

    session.outline = _json_from(llm(p))

    # --- 4. draft each beat, then gate ----------------------------------------
    prior = ""
    for beat in session.outline["beats"]:
        if beat.get("source") == "cached":
            session.beats.append({**beat, "text": None})
            continue

        exemplar = prompts.load_exemplar(beat["role"])
        p = prompts.draft_prompt(beat, template, slots, prior, exemplar)
        trace.add("draft", role=beat["role"], prompt=p)
        text = llm(p).strip()

        report = check(text)
        attempts = 0
        while not report.ok and attempts < MAX_REWRITES:
            attempts += 1
            fix = _rewrite_prompt(text, report)
            trace.add("rewrite", role=beat["role"], attempt=attempts,
                      findings=[f.rule for f in report.errors], prompt=fix)
            text = llm(fix).strip()
            report = check(text)

        if not report.ok:
            trace.add("craft-pass-with-warnings", role=beat["role"],
                      findings=[f"{f.rule}: {f.detail}" for f in report.errors])

        session.beats.append({**beat, "text": text, "craft": report})
        prior += "\n\n" + text

    return session


def _rewrite_prompt(text: str, report: Report) -> str:
    """Rewrite only the offending sentences. Never the whole beat."""
    issues = "\n".join(
        f"  - [{f.rule}] {f.detail}" + (f"\n      in: {f.sentence}" if f.sentence else "")
        for f in report.errors
    )
    return f"""\
This narration fails the craft standard. Fix ONLY the flagged problems.

{issues}

Change nothing else. Keep the word count, the silence markers, and every line that was not
flagged exactly as they are.

{prompts.CRAFT_RULES}

Narration:
\"\"\"{text}\"\"\"

Return the corrected narration only.
"""

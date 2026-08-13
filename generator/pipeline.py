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

from . import intros, prompts
from .craft import Report, check
from .templates import Template, allocate, for_category

MODEL = "claude-opus-5"
MAX_REWRITES = 2          # then pass with a log entry rather than looping

# claude-opus-5, USD per million tokens. Cache writes bill at 1.25x, reads at 0.1x.
PRICE_IN = 5.00
PRICE_OUT = 25.00
PRICE_CACHE_WRITE = PRICE_IN * 1.25
PRICE_CACHE_READ = PRICE_IN * 0.10


@dataclass
class Usage:
    """What the run actually cost, accumulated across every call."""
    calls: int = 0
    input: int = 0
    output: int = 0
    cache_write: int = 0
    cache_read: int = 0

    def add(self, u) -> None:
        self.calls += 1
        self.input += u.input_tokens
        self.output += u.output_tokens
        self.cache_write += getattr(u, "cache_creation_input_tokens", 0) or 0
        self.cache_read += getattr(u, "cache_read_input_tokens", 0) or 0

    @property
    def cost(self) -> float:
        return (self.input * PRICE_IN
                + self.output * PRICE_OUT
                + self.cache_write * PRICE_CACHE_WRITE
                + self.cache_read * PRICE_CACHE_READ) / 1_000_000

    def summary(self) -> str:
        cached = ""
        if self.cache_read or self.cache_write:
            cached = (f"  cache {self.cache_read} read / {self.cache_write} written")
        return (f"{self.calls} calls   {self.input} in / {self.output} out"
                f"{cached}\ncost  ${self.cost:.4f}")


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
    usage: Usage = field(default_factory=Usage)

    @property
    def script(self) -> str:
        return "\n\n".join(b["text"] for b in self.beats if b.get("text"))


LLM = Callable[..., str]


def _live_llm(usage: Usage | None = None) -> LLM | None:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    try:
        import anthropic
    except ImportError:
        print("ANTHROPIC_API_KEY is set but the SDK is missing - pip install anthropic")
        return None
    client = anthropic.Anthropic(api_key=key)

    def call(prompt: str, system: str | None = None) -> str:
        kw = {}
        if system:
            # byte-identical on every draft call, so it is the one cacheable prefix here.
            # It sits close to the 512-token minimum for Opus 5 - if caching does not
            # engage, the cache counters in the usage summary stay at zero and say so.
            kw["system"] = [{
                "type": "text", "text": system,
                "cache_control": {"type": "ephemeral"},
            }]

        # streaming so a long beat cannot trip the request timeout; adaptive thinking
        # because choosing what NOT to say is the hard part of every one of these calls.
        with client.messages.stream(
            model=MODEL, max_tokens=8000,
            thinking={"type": "adaptive"},
            messages=[{"role": "user", "content": prompt}],
            **kw,
        ) as stream:
            msg = stream.get_final_message()

        if usage is not None:
            usage.add(msg.usage)
        # with thinking on, content leads with thinking blocks
        return "".join(b.text for b in msg.content if b.type == "text")
    return call


def _json_from(text: str) -> dict | list:
    """Models wrap JSON in prose and fences more often than not.

    raw_decode rather than loads: a model that answers with the object and then adds
    "Let me know if you'd like changes" is the single most common shape after fencing, and
    loads rejects it outright as trailing data.
    """
    fenced = re.search(r"```(?:json)?\s*(.+?)```", text, re.S)
    raw = fenced.group(1) if fenced else text
    start = min((raw.find(c) for c in "[{" if raw.find(c) != -1), default=0)
    return json.JSONDecoder().raw_decode(raw[start:])[0]


def generate(user_text: str, *, category: str | None = None, memory: dict | None = None,
             standing_exclusions: list[str] | None = None,
             llm: LLM | None = None, pacing: str = "standard",
             dry: bool = False, progress: bool = False) -> Session:
    """Run the pipeline. Dry means: build every prompt, allocate the budget, call nothing.

    Dry is the default whenever no key is present, and `dry=True` forces it even when one
    is. Passing a stub llm is not a way to run dry - the stub gets called for real.
    """
    usage = Usage()
    llm = None if dry else (llm or _live_llm(usage))
    dry = llm is None
    trace = Trace()

    def say(msg: str) -> None:
        """A minute of silence makes a working command look like a hung one."""
        if progress and not dry:
            print(msg, flush=True)

    say("reading what you said...")

    # --- 1. intent -------------------------------------------------------------
    p = prompts.intent_prompt(user_text, category, memory)
    trace.add("intent", prompt=p)
    if dry:
        intent = {
            "category": category or "nature",
            "slots": {}, "still_empty": [],
            "sensitivity_flag": False,
            "session_exclusions": [],
        }
        trace.add("intent", note="dry run - using stub", result=intent)
    else:
        try:
            intent = _json_from(llm(p))
            if not isinstance(intent, dict):
                raise ValueError(f"intent is a {type(intent).__name__}, not an object")
        except (ValueError, TypeError) as e:
            # unparseable intent used to take the whole run down before a word was drafted.
            # The category the listener tapped is already known; that is enough to proceed.
            trace.add("intent-unparseable", error=str(e))
            intent = {"category": category or "nature"}
        trace.add("intent", result=intent)

    try:
        template = for_category(intent.get("category"))
    except ValueError as e:
        trace.add("category-unknown", error=str(e), fell_back_to=category or "nature")
        intent["category"] = category if category else "nature"
        template = for_category(intent["category"])
    slots = dict(intent.get("slots", {}))
    exclusions = {
        "standing": standing_exclusions or [],
        "session": intent.get("session_exclusions", []),
    }
    # midpoint, not the floor - a template's range is what it can do, and defaulting to the
    # short end made every estimate look like a 14-minute session even for into_sleep
    target_s = int(intent.get("target_duration_s") or sum(template.duration_range) // 2)
    lo, hi = template.duration_range
    target_s = max(lo, min(hi, target_s))

    # sensitivity forces the slow, sensitive intro. It is the only script carrying explicit
    # stop permission (SPEC.md 8), so it is not a preference the model gets to weigh.
    sensitive = bool(intent.get("sensitivity_flag"))
    register = intent.get("intro_register") or "neutral"
    if register not in intros.SCRIPTS:
        register = "neutral"
    if sensitive:
        register, pacing = "sensitive", "slow"

    say(f"  -> {template.name} template, {target_s // 60} min")

    # --- 2. amplifying questions ----------------------------------------------
    still_empty = [s for s in template.required_slots if s not in slots]
    if still_empty and template.depth > 0:
        p = prompts.question_prompt(template, slots, still_empty, user_text)
        trace.add("questions", prompt=p)
        if not dry:
            trace.add("questions", result=_json_from(llm(p)))

    # --- 3. outline ------------------------------------------------------------
    intro_s = intros.duration(register, pacing)
    budget = allocate(template, target_s, intro_s)
    p = prompts.outline_prompt(template, slots, budget, exclusions, target_s)
    trace.add("outline", prompt=p, budget=budget)
    say("planning the beats...")

    session = Session(category=intent["category"], template=template,
                      slots=slots, trace=trace, usage=usage)

    if dry:
        # same builder as the live path, so a dry outline is the exact shape a real one is
        session.outline = _reconcile({}, budget, template, intent, exclusions,
                                     slots, target_s, Trace(), pacing, register)
        return session

    try:
        raw = _json_from(llm(p))
    except (ValueError, TypeError) as e:
        trace.add("outline-unparseable", error=str(e))
        raw = {}
    session.outline = _reconcile(raw, budget, template, intent, exclusions,
                                 slots, target_s, trace, pacing, register)

    # --- 4. draft each beat, then gate ----------------------------------------
    to_write = [b for b in session.outline["beats"] if b.get("source") != "cached"]
    say(f"writing {len(to_write)} beats...")
    written = 0

    prior = ""
    for beat in session.outline["beats"]:
        if beat.get("source") == "cached":
            session.beats.append({**beat, "text": None})
            continue

        exemplar = prompts.load_exemplar(beat["role"], template.name)
        p = prompts.draft_prompt(beat, template, slots, prior, exemplar)
        trace.add("draft", role=beat["role"], prompt=p)
        text = llm(p, system=prompts.CRAFT_RULES).strip()

        report = check(text)
        attempts = 0
        while not report.ok and attempts < MAX_REWRITES:
            attempts += 1
            # nothing to rewrite when there is nothing there - ask for the beat again
            if not text:
                trace.add("redraft", role=beat["role"], attempt=attempts,
                          reason="empty draft")
                text = llm(p, system=prompts.CRAFT_RULES).strip()
            else:
                fix = _rewrite_prompt(text, report)
                trace.add("rewrite", role=beat["role"], attempt=attempts,
                          findings=[f.rule for f in report.errors], prompt=fix)
                text = llm(fix, system=prompts.CRAFT_RULES).strip()
            report = check(text)

        if not report.ok:
            trace.add("craft-pass-with-warnings", role=beat["role"],
                      findings=[f"{f.rule}: {f.detail}" for f in report.errors])
        if not text:
            # every downstream consumer assumes a beat has words. Say so loudly rather than
            # writing a session with a hole in it.
            print(f"  !! beat {beat['role']} is empty after {attempts} attempt(s)")

        written += 1
        flags = [f.rule for f in report.errors]
        say(f"  {written}/{len(to_write)}  {beat['role']:<24}{report.words:>4}w"
            + (f"   craft: {', '.join(flags)}" if flags else ""))

        session.beats.append({**beat, "text": text, "craft": report})
        prior += "\n\n" + text

    return session


#: fields the model owns - what the beat is about. Everything else comes from the budget.
_MODEL_FIELDS = ("id", "note", "beats_on", "do_not_mention", "silence_plan", "cached_ref")


def _reconcile(raw: dict, budget: list[dict], template: Template, intent: dict,
               exclusions: dict, slots: dict, target_s: int, trace: Trace,
               pacing: str = "standard", register: str = "neutral") -> dict:
    """Merge the model's outline onto the locally computed budget.

    The budget is authoritative for anything numeric: role order, word_target,
    silence_total_s, wpm, source. Those were computed from the template and cannot be
    wrong. The model owns what each beat is *about*.

    This exists because the draft loop reads beat fields directly, so one missing key used
    to raise KeyError after the outline call was already paid for. A model that returns
    prose, half a schema, or nothing at all now costs one call and still produces a session.
    """
    beats_by_role: dict[str, dict] = {}
    for b in raw.get("beats", []) if isinstance(raw, dict) else []:
        if isinstance(b, dict) and b.get("role"):
            beats_by_role.setdefault(b["role"], b)

    repaired, beats = [], []
    for i, spec in enumerate(budget, 1):
        got = beats_by_role.get(spec["role"], {})
        if not got:
            repaired.append(spec["role"])
        beat = dict(spec)
        beat.setdefault("id", f"b{i}_{spec['role']}")
        for k in _MODEL_FIELDS:
            if got.get(k) is not None:
                beat[k] = got[k]
        # a cached beat introduces no imagery, so it can carry no exclusions to honour
        if beat.get("source") == "cached":
            beat["do_not_mention"] = []
            ref = f"intro/{register}_{pacing}"
            if beat.get("cached_ref") and beat["cached_ref"] != ref:
                trace.add("intro-overridden", model_said=beat["cached_ref"], used=ref)
            beat["cached_ref"] = ref
        else:
            beat.setdefault("do_not_mention", [])
            beat.setdefault("beats_on", [])
            beat.setdefault("silence_plan", [])
        beats.append(beat)

    extra = [r for r in beats_by_role if r not in {b["role"] for b in budget}]
    # a dry run passes {} on purpose - that is not a repair, it is the whole point
    if raw and (repaired or extra):
        trace.add("outline-reconciled", missing=repaired, ignored=extra)
        print(f"  outline repaired: {len(repaired)} beat(s) rebuilt from the budget"
              + (f", {len(extra)} unknown role(s) dropped" if extra else ""))

    return {
        "schema_version": "1.0",
        "template": template.name,
        "category": intent.get("category", template.categories[0]),
        "target_duration_s": target_s,
        "sensitivity_flag": bool(intent.get("sensitivity_flag")),
        "exclusions": exclusions,
        "slots": slots,
        "beats": beats,
        "transitions": raw.get("transitions", []) if isinstance(raw, dict) else [],
    }


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

Narration:
\"\"\"{text}\"\"\"

Return the corrected narration only.
"""

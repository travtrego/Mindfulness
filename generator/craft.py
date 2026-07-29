"""Craft validation for generated narration.

The craft standard is the product's actual moat, and a ban list inside a prompt will not
hold across 2,000 words. This module is the gate that runs *after* the draft: it fails the
text, names the offending sentences, and the pipeline rewrites only those.

Calibrated against the hand-written reference sessions. If a change here fails
docs/sessions/01 or 02, the change is wrong - not the sessions.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# SPEC.md 4 - generic wellness register
BANNED = {
    "breathtaking", "serene", "peaceful", "tranquil", "majestic", "stunning",
    "blissful", "soothing", "calming", "radiant", "luminous", "sacred", "divine",
    "magical", "wondrous", "ethereal", "pristine", "idyllic", "heavenly",
}

# hedges that weaken an instruction. "just" and "only" are deliberately absent -
# both are load-bearing in the reference sessions ("just the true part you wanted to say")
HEDGES = {"gently", "simply", "slightly", "somewhat", "perhaps", "maybe", "quite", "very"}

# a demand disguised as guidance
PERFORMANCE = [
    (r"\btry to\b", "instructs effort"),
    (r"\bmake sure\b", "instructs effort"),
    (r"\bfocus on\b", "instructs effort"),
    (r"\byou should\b", "prescriptive"),
    (r"\byou must\b", "prescriptive"),
    (r"\bimagine that you\b", "demands visualization"),
    (r"\bpicture (?:the|a|your)\b", "demands visualization"),
    (r"\bvisuali[sz]e\b", "demands visualization"),
]

# SPEC.md 8.2 - claims about how the intervention works, distinct from claims about outcome
MECHANISM = [
    (r"\brewir", "mechanism claim"),
    (r"\byour brain\b", "mechanism claim"),
    (r"\bnervous system\b", "mechanism claim"),
    (r"\bneural\b", "mechanism claim"),
    (r"\bsubconscious\b", "mechanism claim"),
    (r"can'?t tell the difference", "mechanism claim"),
    (r"\bscientifically\b", "mechanism claim"),
    (r"\bproven to\b", "mechanism claim"),
]

NOTICING = re.compile(
    r"\b(notice|notices|noticing|noticed|catch|catches|aware|hear|hears|feel|feels|"
    r"know|knows|find|finds)\b", re.I
)

SENSES = {
    "touch": r"\b(weight|warm|warmer|cold|colder|cool|texture|press|contact|rough|"
             r"smooth|hold|holding|grip|surface|skin)\b",
    "sound": r"\b(sound|hear|heard|quiet|noise|echo|beep|hum|silence|loud|voice)\b",
    "sight": r"\b(light|dark|pale|shadow|colou?r|bright|dim|see|seen|look|looks)\b",
    "smell": r"\b(smell|smells|scent|air)\b",
    "body":  r"\b(breath|breathe|jaw|shoulders|hands|feet|chest|ribs|elbows|heart|legs|"
             r"hips|heels|back)\b",
}

SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


@dataclass
class Finding:
    severity: str          # "error" | "warning"
    rule: str
    detail: str
    sentence: str = ""


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)
    words: int = 0
    sentences: int = 0
    noticing_ratio: float = 0.0
    senses_used: set[str] = field(default_factory=set)

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "error"]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "warning"]

    @property
    def ok(self) -> bool:
        return not self.errors


def check(text: str, *, is_cached: bool = False, min_noticing: float = 0.12,
          whole_script: bool = False) -> Report:
    """Validate a beat or a whole script.

    is_cached: cached beats may name nothing concrete beyond the body and the breath,
    because the recording cannot know the listener's standing exclusions.
    """
    r = Report()
    sentences = [s.strip() for s in SENTENCE_SPLIT.split(text.strip()) if s.strip()]
    r.sentences = len(sentences)
    words = re.findall(r"[a-z']+", text.lower())
    r.words = len(words)
    if not words:
        return r

    wordset = set(words)

    def add(sev, rule, detail, sentence=""):
        r.findings.append(Finding(sev, rule, detail, sentence))

    for w in sorted(BANNED & wordset):
        add("error", "banned-adjective", f"{w!r} is generic wellness register")
    for w in sorted(HEDGES & wordset):
        add("error", "hedge", f"{w!r} weakens the line")

    for s in sentences:
        low = s.lower()
        for pat, why in PERFORMANCE:
            if re.search(pat, low):
                add("error", "performance-demand", why, s)
        for pat, why in MECHANISM:
            if re.search(pat, low):
                add("error", "mechanism-claim", why, s)
        # Enumerated ALTERNATIVES are the tell - "imagine, sense, remember, or simply
        # know" reads as a form. Rhetorical tricolon is not: "heavy in the front rack,
        # heavy in your elbows, heavy in a way that asks a question" is good writing.
        # The distinguishing mark is "or" - offering the listener a menu.
        if s.count(",") >= 2 and re.search(r",\s*(?:or|and)\s+\w+", low):
            items = [x for x in re.split(r",\s*(?:or\s+|and\s+)?", s) if x.strip()]
            if len(items) >= 3 and all(len(x.split()) <= 4 for x in items):
                add("warning", "enumeration", f"{len(items)} enumerated alternatives", s)
        # first person or past tense narration
        # "we" is the guide including the listener and is fine. "I" never is.
        if re.search(r"\b(i|my|mine|me)\b", low):
            add("error", "person", "first person singular", s)
        if re.search(r"\byou (?:were|had|walked|felt|saw|went)\b", low):
            add("error", "tense", "past-tense narration", s)
        # decorative comparison - a warning, not a failure: "like the noise had to travel
        # to get to you" is one of the best lines in session 01
        if re.search(r"\blike a\b|\bas though\b|\bas if\b", low):
            add("warning", "simile", "decorative comparison", s)
        if len(s.split()) > 34:
            add("warning", "long-sentence", f"{len(s.split())} words", s)

    if is_cached:
        CONCRETE = (r"\b(water|wave|ocean|sea|river|forest|tree|mountain|sky|sun|moon|"
                    r"wind|rain|fire|beach|path|door|garden|field|cloud|star|bird)\b")
        for m in sorted(set(re.findall(CONCRETE, text.lower()))):
            add("error", "cached-imagery",
                f"{m!r} - a cached beat cannot know the listener's standing exclusions")

    noticing = len(NOTICING.findall(text))
    r.noticing_ratio = noticing / max(r.sentences, 1)
    if whole_script and r.noticing_ratio < min_noticing:
        add("error", "noticing",
            f"{noticing} noticing verbs across {r.sentences} sentences "
            f"({r.noticing_ratio:.2f} < {min_noticing})")

    r.senses_used = {name for name, pat in SENSES.items() if re.search(pat, text.lower())}
    # Whole-script property only. A beat that is entirely sound - a question being asked,
    # a badge beep - is correct writing; forcing five channels into every beat is not.
    if whole_script and len(r.senses_used) < 3:
        add("error", "sensory-variety",
            f"only {len(r.senses_used) or 'no'} sensory channel(s): "
            f"{', '.join(sorted(r.senses_used)) or 'none'}")

    return r


def format_report(name: str, r: Report) -> str:
    head = (f"{name:<28} {r.words:>4}w {r.sentences:>3}s  "
            f"notice {r.noticing_ratio:.2f}  senses {len(r.senses_used)}  ")
    head += "OK" if r.ok else f"{len(r.errors)} ERROR"
    lines = [head]
    for f in r.errors + r.warnings:
        tag = "FAIL" if f.severity == "error" else "warn"
        lines.append(f"    {tag}  [{f.rule}] {f.detail}")
        if f.sentence:
            lines.append(f"          {f.sentence[:74]}")
    return "\n".join(lines)

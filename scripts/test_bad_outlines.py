#!/usr/bin/env python3
"""Feed the pipeline outlines a real model might plausibly return, and prove none crash it.

    python3 scripts/test_bad_outlines.py

The draft loop reads beat fields directly, so before _reconcile a single missing key raised
KeyError *after* the outline call was already paid for. Every case here used to be a crash
or a silent mis-sized session; all of them must now produce a complete, well-formed one.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from generator import templates as T  # noqa: E402
from generator.pipeline import generate  # noqa: E402

TPL = T.TEMPLATES["rehearsal"]
BUDGET = T.allocate(TPL, 840, 103)
REQUIRED = ("role", "wpm", "source", "id")
# a cached beat is a recording - it has no word budget to hit and no silence to plan
REQUIRED_GENERATED = REQUIRED + ("word_target", "silence_total_s", "do_not_mention")

PROSE = "You notice the weight of your hands. *[6s]*\nAnd then you stand."
INTENT = json.dumps({"category": "competition", "slots": {}, "still_empty": [],
                     "target_duration_s": 840, "sensitivity_flag": False,
                     "session_exclusions": []})


def good() -> str:
    return json.dumps({"schema_version": "1.0", "template": "rehearsal",
                       "category": "competition", "target_duration_s": 840,
                       "sensitivity_flag": False,
                       "exclusions": {"standing": [], "session": []},
                       "slots": {}, "beats": BUDGET, "transitions": []})


CASES = {
    "well-formed": good(),
    "empty object": "{}",
    "not JSON at all": "Here is the outline you asked for! It has eight beats.",
    "a list, not an object": json.dumps(BUDGET),
    "beats present, all numbers missing":
        json.dumps({"beats": [{"role": b["role"]} for b in BUDGET]}),
    "half the beats":
        json.dumps({"beats": BUDGET[:4]}),
    "invented roles":
        json.dumps({"beats": BUDGET + [{"role": "epilogue", "word_target": 90}]}),
    "wrong types":
        json.dumps({"beats": [{**b, "word_target": "lots", "wpm": None} for b in BUDGET]}),
    "cached beat carrying exclusions":
        json.dumps({"beats": [{**b, "do_not_mention": ["missed lifts"]} for b in BUDGET]}),
    "fenced with commentary":
        "Sure!\n```json\n" + good() + "\n```\nLet me know if you'd like changes.",
}


def run(outline_text: str) -> tuple[bool, str]:
    def fake(prompt, system=None):
        head = prompt.splitlines()[0]
        if head.startswith("You are the intent parser"):
            return INTENT
        if head.startswith("Write up to THREE questions"):
            return "[]"
        if head.startswith("Produce the outline"):
            return outline_text
        return PROSE

    try:
        s = generate("meet saturday", category="competition", llm=fake)
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"

    beats = s.outline["beats"]
    if len(beats) != len(BUDGET):
        return False, f"{len(beats)} beats, expected {len(BUDGET)}"
    for b in beats:
        cached = b.get("source") == "cached"
        for k in (REQUIRED if cached else REQUIRED_GENERATED):
            if k not in b:
                return False, f"beat {b.get('role')} missing {k!r}"
        if not isinstance(b["wpm"], int):
            return False, f"beat {b['role']} has non-numeric wpm"
        if not cached and not isinstance(b["word_target"], (int, float)):
            return False, f"beat {b['role']} has non-numeric word_target"
        if cached and b.get("do_not_mention"):
            return False, "cached beat carries exclusions it cannot honour"
    drafted = [b for b in s.beats if b.get("text")]
    if len(drafted) != len([b for b in BUDGET if b["source"] != "cached"]):
        return False, f"only {len(drafted)} beats drafted"
    return True, f"{len(beats)} beats, {len(drafted)} drafted"


def main() -> int:
    if os.environ.get("ANTHROPIC_API_KEY"):
        print("note: a key is set, but this test always uses the fake model\n")
    failed = 0
    for name, text in CASES.items():
        ok, detail = run(text)
        print(f"  {'ok  ' if ok else 'FAIL'}  {name:<38}{detail}")
        failed += not ok
    print()
    if failed:
        print(f"{failed} case(s) can still break a paid run")
        return 1
    print("every malformed outline still produces a complete session")
    return 0


if __name__ == "__main__":
    sys.exit(main())

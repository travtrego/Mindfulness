#!/usr/bin/env python3
"""Every stage, fed what a real model plausibly returns. None of it may crash a paid run.

    python3 scripts/test_bad_model_output.py

test_bad_outlines.py covers the outline stage. This covers the rest: JSON extraction, the
intent call, and a draft that comes back empty. The intent call had no recovery at all -
a model that answered with the object and then added "Hope that helps!" took the whole run
down before a single word was drafted.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from generator import templates as T  # noqa: E402
from generator.craft import check  # noqa: E402
from generator.pipeline import _json_from, generate  # noqa: E402

BUDGET = T.allocate(T.TEMPLATES["rehearsal"], 840, 87)
PROSE = "You notice the weight of your hands. *[6s]*\nAnd then you stand."

JSON_CASES = {
    "plain": ('{"a": 1}', {"a": 1}),
    "fenced": ('```json\n{"a": 1}\n```', {"a": 1}),
    "fenced, no language": ('```\n{"a": 1}\n```', {"a": 1}),
    "prose before": ('Sure, here you go:\n{"a": 1}', {"a": 1}),
    "prose after": ('{"a": 1}\nLet me know if you want changes.', {"a": 1}),
    "prose both sides": ('Here:\n{"a": 1}\nAnything else?', {"a": 1}),
    "array with trailer": ('[{"a": 1}]\nDone!', [{"a": 1}]),
    "nested and quoted braces": ('{"a": {"b": [1,2]}, "c": "}"}', {"a": {"b": [1, 2]}, "c": "}"}),
    "braces in the prose": ('The set {a, b}.\n```json\n{"a": 1}\n```', {"a": 1}),
}

INTENT_CASES = {
    "well-formed": '{"category":"competition","slots":{},"sensitivity_flag":false}',
    "prose, no JSON": "I'm not sure what you're asking for.",
    "trailing prose": '{"category":"competition"}\nHope that helps!',
    "unknown category": '{"category":"open"}',
    "null category": '{"category":null}',
    "a list, not an object": "[1,2,3]",
    "empty string": "",
    "empty object": "{}",
}


def model(intent_text: str, empty_beats: int = 0):
    state = {"left": empty_beats}

    def fake(prompt, system=None):
        head = prompt.splitlines()[0]
        if head.startswith("You are the intent parser"):
            return intent_text
        if head.startswith("Write up to THREE"):
            return "[]"
        if head.startswith("Produce the outline"):
            return json.dumps({"beats": BUDGET})
        if state["left"] > 0:
            state["left"] -= 1
            return "   "
        return PROSE
    return fake


def main() -> int:
    failed = 0

    print("json extraction")
    for name, (text, want) in JSON_CASES.items():
        try:
            got = _json_from(text)
            ok = got == want
        except Exception as e:
            got, ok = f"{type(e).__name__}: {e}", False
        print(f"  {'ok  ' if ok else 'FAIL'}  {name:<28}{got!r}"[:100])
        failed += not ok

    print("\nintent stage")
    for name, text in INTENT_CASES.items():
        try:
            s = generate("meet saturday", category="competition", llm=model(text))
            drafted = len([b for b in s.beats if b.get("text")])
            ok = drafted == 7 and s.category == "competition"
            detail = f"{s.category}, {drafted} beats"
        except Exception as e:
            ok, detail = False, f"{type(e).__name__}: {e}"
        print(f"  {'ok  ' if ok else 'FAIL'}  {name:<28}{detail}"[:100])
        failed += not ok

    print("\nempty drafts")
    for n in (1, 2):
        s = generate("meet saturday", category="competition",
                     llm=model(INTENT_CASES["well-formed"], empty_beats=n))
        holes = [b["role"] for b in s.beats
                 if b.get("source") != "cached" and not (b.get("text") or "").strip()]
        redrafts = [t for t in s.trace.steps if t["stage"] == "redraft"]
        ok = not holes
        print(f"  {'ok  ' if ok else 'FAIL'}  {n} empty response(s):"
              f" {len(redrafts)} redraft(s), holes: {holes or 'none'}")
        failed += not ok

    print("\ncraft gate on degenerate input")
    for name, text, want_ok in (("empty", "", False), ("whitespace", "  \n ", False),
                                ("markers only", "*[6s]* *[8s]*", False),
                                ("real prose", PROSE, True)):
        r = check(text)
        ok = r.ok == want_ok
        print(f"  {'ok  ' if ok else 'FAIL'}  {name:<28}"
              f"{'passes' if r.ok else 'fails'}, {r.words} words")
        failed += not ok

    print()
    if failed:
        print(f"{failed} case(s) can still break a paid run")
        return 1
    print("every stage survives what a model plausibly returns")
    return 0


if __name__ == "__main__":
    sys.exit(main())

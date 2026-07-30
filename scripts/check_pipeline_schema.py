#!/usr/bin/env python3
"""Validate what the pipeline actually produces against docs/schema/outline.schema.json.

    python3 scripts/check_pipeline_schema.py

validate_outline.py checks a hand-written example. This checks the real thing, for every
template, which is a different question - and one nothing was asking. When it was first
run every template failed with 10-22 errors: the schema required `ambience` for a feature
the spec had descoped, forbade the `note` field the allocator emits, and demanded a word
budget from cached beats that are recordings.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import jsonschema  # noqa: E402
from generator import templates as T  # noqa: E402
from generator.pipeline import generate  # noqa: E402

ROOT = Path(__file__).parent.parent
SCHEMA = json.loads((ROOT / "docs/schema/outline.schema.json").read_text())
PROSE = "You notice the weight of your hands. *[6s]*\nAnd then you stand."

# one category per template, plus the sensitivity path
CASES = [
    ("competition", False), ("nature", False), ("gratitude", False),
    ("safe_place", False), ("just_breathing", False),
    ("going_back", False), ("going_back", True),
]


def build(cat: str, sensitive: bool):
    tpl = T.for_category(cat)
    budget = T.allocate(tpl, sum(tpl.duration_range) // 2, 103)

    def fake(prompt, system=None):
        h = prompt.splitlines()[0]
        if h.startswith("You are the intent parser"):
            return json.dumps({"category": cat, "slots": {}, "still_empty": [],
                               "sensitivity_flag": sensitive, "session_exclusions": []})
        if h.startswith("Write up to THREE"):
            return "[]"
        if h.startswith("Produce the outline"):
            # the model echoes the budget back, which is what the prompt asks for
            return json.dumps({"beats": budget})
        return PROSE

    return generate("x", category=cat, llm=fake), tpl


def main() -> int:
    jsonschema.Draft202012Validator.check_schema(SCHEMA)
    validator = jsonschema.Draft202012Validator(SCHEMA)
    failed = 0

    for cat, sensitive in CASES:
        session, tpl = build(cat, sensitive)
        errs = sorted(validator.iter_errors(session.outline), key=lambda e: list(e.path))
        label = f"{cat}{' (sensitive)' if sensitive else ''}"
        print(f"  {'ok  ' if not errs else 'FAIL'}  {label:<26}{tpl.name:<16}"
              f"{len(session.outline['beats'])} beats")
        for e in errs[:8]:
            print(f"          {list(e.path)}: {e.message[:100]}")
        failed += bool(errs)

    # and the hand-written example, which is what validate_outline.py checks
    for example in sorted((ROOT / "docs/schema").glob("example-*.json")):
        errs = list(validator.iter_errors(json.loads(example.read_text())))
        print(f"  {'ok  ' if not errs else 'FAIL'}  {example.name}")
        for e in errs[:8]:
            print(f"          {list(e.path)}: {e.message[:100]}")
        failed += bool(errs)

    print()
    if failed:
        print(f"{failed} case(s) produce outlines our own schema rejects")
        return 1
    print("every template produces a schema-valid outline")
    return 0


if __name__ == "__main__":
    sys.exit(main())

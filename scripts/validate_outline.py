#!/usr/bin/env python3
"""Validate a session outline against the schema, plus the constraints JSON Schema can't express.

    python3 scripts/validate_outline.py docs/schema/example-01-clean-and-jerk.json

Exits non-zero on any failure. Intended for CI and for gating the outline stage
of the generation pipeline before a draft is written.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from generator import intros  # noqa: E402

SCHEMA = Path(__file__).parent.parent / "docs/schema/outline.schema.json"
DRIFT_TOLERANCE = 0.10  # SPEC.md 5.2


def check(path: Path) -> int:
    import jsonschema

    schema = json.loads(SCHEMA.read_text())
    inst = json.loads(path.read_text())
    problems: list[str] = []

    jsonschema.Draft202012Validator.check_schema(schema)
    for e in jsonschema.Draft202012Validator(schema).iter_errors(inst):
        problems.append(f"schema: {list(e.path)} {e.message}")

    if problems:                       # structural errors make the rest meaningless
        for p in problems:
            print(f"  FAIL  {p}")
        return 1

    beats = inst["beats"]
    ids = {b["id"] for b in beats}
    speech = silence = 0.0

    print(f"{'beat':<22}{'role':<26}{'words':>6}{'wpm':>5}{'total':>8}")
    print("-" * 67)

    for b in beats:
        # cached beats may introduce no imagery and carry no exclusions
        if b["source"] == "cached":
            if b.get("do_not_mention"):
                problems.append(f"{b['id']}: cached beat carries exclusions it cannot honour")
            ref = b.get("cached_ref")
            if not ref:
                problems.append(f"{b['id']}: cached beat has no cached_ref")
            # a recording has a known length; take it from the matrix rather than a word
            # budget it does not have. An outline that omits both cannot be timed at all.
            elif "word_target" not in b:
                reg, _, pac = ref.removeprefix("intro/").partition("_")
                if reg in intros.SCRIPTS and pac in intros.PACING:
                    d = intros.duration(reg, pac)
                    speech += d
                    print(f"{b['id']:<22}{b['role']:<26}{'cached':>6}{b['wpm']:>5}{d:>7.0f}s")
                    continue
                problems.append(f"{b['id']}: cached_ref {ref!r} is not in the intro matrix")

        plan = sum(s["seconds"] for s in b.get("silence_plan", []))
        if plan != b.get("silence_total_s", plan):
            problems.append(
                f"{b['id']}: silence_plan sums to {plan}s, silence_total_s says {b['silence_total_s']}s"
            )
        sp = b.get("word_target", 0) / b["wpm"] * 60
        speech += sp
        silence += plan
        print(f"{b['id']:<22}{b['role']:<26}{b.get('word_target', 0):>6}{b['wpm']:>5}{sp + plan:>7.0f}s")

        # scene-building beats must not be delivered at conversational pace
        if b["role"] in ("event", "difficulty_and_response", "completion") and b["wpm"] > 90:
            problems.append(f"{b['id']}: {b['wpm']} wpm too fast for a {b['role']} beat (max 90)")

    for t in inst.get("transitions", []):
        for k in ("from_beat", "to_beat"):
            if t[k] not in ids:
                problems.append(f"transition references unknown beat: {t[k]}")

    # every session-level exclusion must reach the beats that could breach it
    generated = [b for b in beats if b["source"] == "generated"]
    for exc in inst["exclusions"]["standing"] + inst["exclusions"]["session"]:
        if not any(exc in b.get("do_not_mention", []) for b in generated):
            problems.append(f"exclusion never reaches any beat context: {exc!r}")

    # a rehearsal must always contain the difficulty beat, whatever the outcome frame
    if inst["template"] == "rehearsal":
        if not any(b["role"] == "difficulty_and_response" for b in beats):
            problems.append("rehearsal template is missing difficulty_and_response")

    # Re-entry: the feared moment must not be the climax
    if inst["template"] == "reentry":
        by_role = {b["role"]: b for b in beats}
        moment, cont = by_role.get("the_moment"), by_role.get("continuation")
        if not moment or not cont:
            problems.append("reentry template is missing the_moment or continuation")
        elif cont["word_target"] < moment["word_target"]:
            problems.append(
                f"continuation ({cont['word_target']}w) is shorter than the_moment "
                f"({moment['word_target']}w) - a session that peaks and stops says the "
                f"feared exchange was the event"
            )

    # every template except into_sleep must end reoriented
    if inst["category"] != "into_sleep" and beats[-1]["role"] != "reorientation":
        problems.append(f"session ends on {beats[-1]['role']}, not reorientation")

    total = speech + silence
    target = inst["target_duration_s"]
    drift = abs(total - target) / target

    print("-" * 67)
    print(f"{'TOTAL':<48}{total:>13.0f}s")
    print(f"\nruntime   {total / 60:.2f} min   target {target / 60:.2f} min   "
          f"drift {drift * 100:.1f}%")
    print(f"silence   {silence / total * 100:.0f}%")

    if drift > DRIFT_TOLERANCE:
        problems.append(
            f"runtime drift {drift * 100:.1f}% exceeds {DRIFT_TOLERANCE * 100:.0f}% "
            f"({total:.0f}s vs {target}s) - trim word_target and re-run"
        )
    if not 0.30 <= silence / total <= 0.55:
        problems.append(f"silence at {silence / total * 100:.0f}% is outside the 30-55% band")

    print()
    if problems:
        for p in problems:
            print(f"  FAIL  {p}")
        return 1
    print("  all checks pass")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(check(Path(sys.argv[1])))

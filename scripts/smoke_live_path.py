#!/usr/bin/env python3
"""Exercise the live code path end to end with a fake model - no key, no spend.

    python3 scripts/smoke_live_path.py [out.md]

Every stage runs for real except the model call itself: intent parsing, question
generation, outline, per-beat drafting, the craft gate, the rewrite loop, and the session
writer. The only thing this cannot tell you is whether the prose is any good.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
from pathlib import Path
from generator.pipeline import generate
from generator.cli import write_session_doc
from generator import templates

t = templates.for_category("competition")
budget = templates.allocate(t, 900, 103)
PROSE = ("You notice the weight of your hands where they rest. *[6s]*\n"
         "The air is cooler on one side of your face than the other. *[8s]*\n"
         "And then you stand.")

def fake(prompt, system=None):
    head = prompt.splitlines()[0]
    if head.startswith("You are the intent parser"):
        return json.dumps({"category": "competition", "slots": {"event": "a meet"},
                           "still_empty": [], "target_duration_s": 900,
                           "sensitivity_flag": False, "session_exclusions": []})
    if head.startswith("Write up to THREE questions"):
        return json.dumps([{"slot": "event", "question": "Which lift?"}])
    if head.startswith("Produce the outline"):
        return json.dumps({"schema_version": "1.0", "template": t.name,
                           "category": "competition", "target_duration_s": 900,
                           "sensitivity_flag": False,
                           "exclusions": {"standing": [], "session": []},
                           "slots": {}, "beats": budget, "transitions": []})
    return PROSE   # draft and rewrite

s = generate(
    "meet on saturday",
    category="competition",
    memory={
        "style": {"sensory_density": "nonvisual", "preferred_duration_s": 720},
        "content": {"things_to_keep": ["the cold bar in both hands"]},
    },
    llm=fake,
)
assert s.usage.calls == 0, "fake model must not touch the usage counter"
assert s.slots["sensory_density"] == "nonvisual"
assert s.slots["prior_things_to_keep"] == ["the cold bar in both hands"]
drafted = [b for b in s.beats if b.get("text")]
print(f"beats drafted  {len(drafted)} of {len(s.beats)}")
print(f"script words   {len(s.script.split())}")

import tempfile
out = Path(sys.argv[1] if len(sys.argv) > 1 else
           Path(tempfile.gettempdir()) / "smoke-session.md")
write_session_doc(s, out, "meet on saturday")
print(f"\n{out}:\n")
print("\n".join(out.read_text().split("\n")[:24]))

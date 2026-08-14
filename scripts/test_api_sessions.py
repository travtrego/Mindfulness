#!/usr/bin/env python3
"""Offline API contract check for every listener-facing category."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from generator.api import _history, _memory, generate_session, resolve


CATEGORIES = (
    "Just breathing",
    "Body scan",
    "Safe place",
    "Nature",
    "Adventure",
    "Fantasy",
    "Into sleep",
    "Interview",
    "Game or match",
    "Hard conversation",
    "Confidence",
    "First day back",
    "Seeing people again",
    "Gratitude",
    "Creativity",
    "Something else",
)


def main() -> None:
    for category in CATEGORIES:
        result = generate_session(category, history=[], answers=[])
        assert result["beats"], f"{category}: no playable beats"
        assert result["script"].strip(), f"{category}: empty narration"
        assert result["duration_s"] > 0, f"{category}: invalid duration"
        assert result["template"], f"{category}: missing template"
        for beat in result["beats"]:
            assert beat["role"] and beat["text"].strip()
        print(
            f"ok: {category:<16} -> {result['template']:<14} "
            f"({len(result['beats'])} beats, {result['duration_s']}s)"
        )

    memory = _memory({
        "style": {"sensory_density": "nonvisual", "preferred_duration_s": 99999,
                  "voice": "deeper", "ignored": "nope"},
        "content": {"category": "Nature", "things_to_keep": ["cold air", "ridge"]},
        "unexpected": {"secret": "drop me"},
    }, "Nature")
    assert memory["style"]["preferred_duration_s"] == 2700
    assert memory["content"]["things_to_keep"] == ["cold air", "ridge"]
    assert "unexpected" not in memory and "ignored" not in memory["style"]
    assert _memory({"content": {"category": "Nature", "things_to_keep": ["ridge"]}},
                   "Game or match") == {}

    oversized = [{"role": "user", "text": "x" * 2000} for _ in range(20)]
    cleaned = _history(oversized)
    assert len(cleaned) <= 7 and sum(len(item["text"]) for item in cleaned) <= 6000
    try:
        resolve("definitely-not-a-category")
    except ValueError:
        pass
    else:
        raise AssertionError("unknown categories must be rejected")
    print("ok: input bounds and category-scoped memory")


if __name__ == "__main__":
    main()

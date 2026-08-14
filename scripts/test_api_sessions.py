#!/usr/bin/env python3
"""Offline API contract check for every listener-facing category."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from generator.api import generate_session


CATEGORIES = (
    "Just breathing",
    "Safe place",
    "Nature",
    "Game or match",
    "First day back",
    "Gratitude",
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


if __name__ == "__main__":
    main()

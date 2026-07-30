"""The cached intro matrix: how long each recording actually runs.

Four registers x three pacings = twelve durations (docs/sessions/00-intro-matrix.md). The
pipeline needs these because the intro is subtracted from the target before the generated
beats get their budget - so an intro length that is wrong by 30s makes every session in
that category 30s short.

It was wrong. `INTRO_SECONDS = {"slow": 128, "standard": 103, "brisk": 84}` was one number
per pacing, and those three numbers are the *sensitive* row - the longest of the four. Every
non-sensitive session was budgeted as if it opened with the longest intro in the matrix and
came in under its target as a result.

scripts/check_intros.py asserts this table against the scripts themselves, so editing a
recording without editing this fails the check rather than silently mis-sizing sessions.
"""
from __future__ import annotations

# words, silence seconds - measured from the scripts, not estimated
SCRIPTS = {
    "settling": (64, 40),
    "neutral": (54, 38),
    "activating": (53, 31),
    "sensitive": (70, 52),
}

# delivery rate, and how much the silences stretch at that pacing
PACING = {"slow": (72, 1.35), "standard": (82, 1.00), "brisk": (92, 0.75)}


def duration(register: str, pacing: str) -> int:
    """Seconds of finished audio for one cached intro."""
    words, silence = SCRIPTS[register]
    wpm, mult = PACING[pacing]
    return round(words / wpm * 60 + silence * mult)


def table() -> dict[tuple[str, str], int]:
    return {(r, p): duration(r, p) for r in SCRIPTS for p in PACING}

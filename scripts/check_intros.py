#!/usr/bin/env python3
"""Verify the cached intro scripts: word counts, durations, and craft rules.

    python3 scripts/check_intros.py

Every intro is heard by every user on every session, so these are the highest-leverage
words in the product and the only ones that can never be regenerated. Checked, not trusted.
"""
import re
import sys
from pathlib import Path

DOC = Path(__file__).parent.parent / "docs/sessions/00-intro-matrix.md"

PACING = {"slow": (72, 1.35), "standard": (82, 1.00), "brisk": (92, 0.75)}

WORD_MIN, WORD_MAX = 45, 75
HEDGES = {"gently", "simply", "just", "slightly", "somewhat", "perhaps", "maybe"}
# a cached recording cannot know the user's standing exclusions, so it may name
# nothing concrete beyond the body and the breath
IMAGERY = {
    "water", "wave", "ocean", "sea", "river", "forest", "tree", "mountain", "sky",
    "light", "sun", "moon", "wind", "rain", "fire", "beach", "path", "door", "room",
    "garden", "field", "cloud", "star", "bird",
}


def fmt(sec: float) -> str:
    return f"{int(sec // 60)}:{int(sec % 60):02d}"


def main() -> int:
    text = DOC.read_text()
    problems: list[str] = []

    blocks = re.findall(
        r"\n## \d · (\w+)\n(.*?)`(\d+) words · (\d+)s silence`", text, re.S
    )
    if len(blocks) != 4:
        print(f"expected 4 intro scripts, found {len(blocks)}")
        return 1

    print(f"{'script':<12}{'words':>6}{'sil':>5}{'slow':>9}{'standard':>10}{'brisk':>8}")
    print("-" * 50)

    for name, block, stated_w, stated_s in blocks:
        lines = [l for l in block.split("\n") if l.startswith(">")]
        spoken = re.sub(r"\*\[\d+s[^\]]*\]\*", "", "\n".join(lines)).replace(">", " ")
        words = spoken.split()
        silences = [int(x) for x in re.findall(r"\*\[(\d+)s[^\]]*\]\*", block)]

        w, s = len(words), sum(silences)
        if w != int(stated_w):
            problems.append(f"{name}: stated {stated_w} words, actual {w}")
        if s != int(stated_s):
            problems.append(f"{name}: stated {stated_s}s silence, actual {s}")
        if not WORD_MIN <= w <= WORD_MAX:
            problems.append(f"{name}: {w} words outside the {WORD_MIN}-{WORD_MAX} band")

        bare = [re.sub(r"[^a-z]", "", x.lower()) for x in words]

        for h in HEDGES & set(bare):
            problems.append(f"{name}: hedging word {h!r}")
        for img in IMAGERY & set(bare):
            problems.append(f"{name}: concrete imagery {img!r} - cached beats may name only the body and the breath")

        # a cached intro must reach the body by the third spoken line
        spoken_lines = [l for l in lines if l.strip(" >") and not re.match(r"^>\s*\*\[", l)]
        BODY = ("body", "weight", "hands", "floor", "surface", "breath", "eyes", "sit", "settle", "position")
        if not any(any(b in l.lower() for b in BODY) for l in spoken_lines[:3]):
            problems.append(f"{name}: not physical within three lines")

        # three-item enumeration is the tell that made the first draft read as machine-written
        for l in spoken_lines:
            if len(re.findall(r",", l)) >= 2 and " and " in l:
                problems.append(f"{name}: possible three-item enumeration - {l.strip(' >')[:60]}")

        row = f"{name:<12}{w:>6}{s:>5}"
        for p in ("slow", "standard", "brisk"):
            wpm, mult = PACING[p]
            d = w / wpm * 60 + s * mult
            row += fmt(d).rjust(9 if p == "slow" else 10 if p == "standard" else 8)
        print(row)

    print("-" * 50)
    if problems:
        print()
        for p in problems:
            print(f"  FAIL  {p}")
        return 1
    print("\n  all checks pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())

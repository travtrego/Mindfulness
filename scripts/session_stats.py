#!/usr/bin/env python3
"""Measure the reference sessions: words, silence, and true runtime per beat.

    python3 scripts/session_stats.py
    python3 scripts/session_stats.py docs/sessions/05-frozen-lake.md

Runtime is computed at each beat's own wpm, not a session average. Estimating these by
hand has been wrong every single time it has been tried, so nothing in a session doc's
header should be written without running this first.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from generator.templates import TEMPLATES  # noqa: E402

ROOT = Path(__file__).parent.parent / "docs/sessions"
INTRO_S = 103          # standard pacing; slow is 128, brisk 84


def stats(path: Path) -> None:
    text = path.read_text()
    tpl = re.search(r"^\*template:\s*([a-z_]+)\*", text, re.M)
    if not tpl:
        return
    wpm = {b.role: b.wpm for b in TEMPLATES[tpl.group(1)].beats}

    print(f"\n{path.name}   template: {tpl.group(1)}")
    print(f"{'beat':<24}{'words':>6}{'wpm':>5}{'speech':>8}{'silence':>9}{'total':>8}")
    print("-" * 60)

    speech = silence = 0.0
    for block in re.split(r"\n## Beat ", text)[1:]:
        header = block.split("\n")[0]
        role = re.search(r"role:\s*([a-z_]+)", header)
        if not role or "CACHED" in header:
            continue
        quoted = "\n".join(l for l in block.split("\n") if l.startswith(">"))
        sil = sum(int(x) for x in re.findall(r"\*\[(\d+)s[^\]]*\]\*", quoted))
        prose = re.sub(r"\*\[\d+s[^\]]*\]\*", "", quoted)
        prose = re.sub(r"^>\s?", "", prose, flags=re.M)
        w = len(prose.split())
        if role.group(1) not in wpm:
            print(f"  !! beat role {role.group(1)!r} is not in the {tpl.group(1)} template")
            continue
        rate = wpm[role.group(1)]
        sp = w / rate * 60
        speech += sp
        silence += sil
        print(f"{role.group(1):<24}{w:>6}{rate:>5}{sp:>7.0f}s{sil:>8}s{sp + sil:>7.0f}s")

    total = speech + silence + INTRO_S
    print("-" * 60)
    print(f"{'+ cached intro':<24}{'':>11}{'':>8}{INTRO_S:>8}s")
    print(f"runtime {total / 60:.2f} min   silence "
          f"{silence / (speech + silence) * 100:.0f}% of generated")


def check_shares() -> int:
    """A template whose shares do not sum to 1 silently mis-sizes every session it makes."""
    bad = 0
    for name, t in TEMPLATES.items():
        s = sum(b.share for b in t.beats)
        if abs(s - 1) > 0.005:
            print(f"  FAIL  {name} shares sum to {s:.2f}, not 1.00")
            bad += 1
    return bad


if __name__ == "__main__":
    paths = [Path(p) for p in sys.argv[1:]] or sorted(ROOT.glob("[0-9][0-9]-*.md"))
    for p in paths:
        stats(p)
    print()
    sys.exit(1 if check_shares() else 0)

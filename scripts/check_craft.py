#!/usr/bin/env python3
"""Run the craft validator against the hand-written reference sessions.

    python3 scripts/check_craft.py

These sessions ARE the standard. If the validator fails them, the validator is wrong -
recalibrate it, don't edit the sessions. Exits non-zero on any error-level finding.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from generator.craft import check, format_report  # noqa: E402

ROOT = Path(__file__).parent.parent / "docs/sessions"


def beats(path: Path):
    """Yield (label, prose, is_cached) for each beat in a reference session."""
    text = path.read_text()
    text = re.split(r"\n# (?:Craft notes|The Re-entry template|Revision)", text)[0]
    for block in re.split(r"\n## (?:Beat )?", text)[1:]:
        label = block.split("\n")[0].strip()
        quoted = [l for l in block.split("\n") if l.startswith(">")]
        prose = re.sub(r"\*\[\d+s\]\*", "", "\n".join(quoted))
        prose = re.sub(r"^>\s?", "", prose, flags=re.M).strip()
        if len(prose.split()) < 10:
            continue
        yield label, prose, "CACHED" in label


def main() -> int:
    failed = 0
    for path in sorted(ROOT.glob("*.md")):
        print(f"\n{'=' * 78}\n{path.name}\n{'=' * 78}")
        whole = []
        for label, prose, cached in beats(path):
            r = check(prose, is_cached=cached)  # per-beat: bans, demands, person, tense
            whole.append(prose)
            print(format_report(label[:26], r))
            failed += len(r.errors)

        # 00-intro-matrix holds four independent scripts. Aggregating them is meaningless,
        # and an intro is instruction rather than observation - the noticing ratio does not
        # apply. Per-script rules above still run on each.
        if whole and not path.name.startswith("00-"):
            full = "\n\n".join(whole)
            r = check(full, whole_script=True)  # noticing ratio and sensory variety
            print("-" * 78)
            print(format_report("WHOLE SCRIPT", r))
            failed += len(r.errors)

    print(f"\n{'=' * 78}")
    if failed:
        print(f"{failed} error-level findings — recalibrate the validator, not the sessions")
        return 1
    print("all reference sessions pass — validator is calibrated")
    return 0


if __name__ == "__main__":
    sys.exit(main())

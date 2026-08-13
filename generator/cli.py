#!/usr/bin/env python3
"""Generate a session, or inspect the prompts that would generate one.

    python3 -m generator.cli "playoff game saturday" --category competition --dry
    python3 -m generator.cli "take me somewhere cold" --category nature

Without ANTHROPIC_API_KEY set it runs dry: builds every prompt, allocates the beat budget,
and prints both. Enough to check the shape before spending a token.
"""
import argparse
import datetime as dt
import re
import sys
from pathlib import Path

from . import prompts
from .craft import check
from .pipeline import PRICE_IN, PRICE_OUT, Session, generate
from .templates import TEMPLATES


def estimate(s: Session) -> str:
    """Project the cost of running this for real, from a dry run.

    Rough - tokens are counted at 4 chars each and thinking tokens are guessed at half the
    visible output. Good enough to answer 'can I afford to iterate on this', which is the
    only question it needs to answer.
    """
    beats = [b for b in s.outline["beats"] if b.get("source") != "cached"]
    inp = sum(len(st["prompt"]) for st in s.trace.steps if "prompt" in st) // 4
    out = 0
    prior = ""
    for b in beats:
        p = prompts.draft_prompt(b, s.template, s.slots, prior,
                                 prompts.load_exemplar(b["role"], s.template.name))
        inp += len(p) // 4
        words = b.get("word_target", 0)
        out += words * 4 // 3
        prior += " x" * words              # prior grows as beats accumulate
    out += 1500                            # the outline JSON
    out = int(out * 1.5)                   # + thinking, which bills as output
    inp += len(prompts.CRAFT_RULES) // 4 * len(beats)

    cost = (inp * PRICE_IN + out * PRICE_OUT) / 1_000_000
    return (f"~{inp:,} in / ~{out:,} out over {len(beats) + 3} calls\n"
            f"~${cost:.3f} per run   (~${cost * 10:.2f} for ten)")


def write_session_doc(s: Session, path: Path, user_text: str) -> None:
    """Write the generated session in the same shape as docs/sessions/*.md.

    Same shape on purpose: the only test that matters is reading it out loud beside the two
    hand-written ones and seeing whether you can tell which is which.
    """
    spoken = "\n".join(b["text"] for b in s.beats if b.get("text"))
    words = len(re.sub(r"\*\[[^\]]*\]\*", "", spoken).split())

    out = [
        f"# Generated — {s.category}",
        "",
        f"*{dt.datetime.now():%Y-%m-%d %H:%M} · {s.template.name} template · "
        f"{words} words · ${s.usage.cost:.4f}*",
        "",
        "## Inputs",
        "",
        f"- **said:** {user_text}",
        f"- **category:** {s.category}",
        *(f"- **{k}:** {v}" for k, v in s.slots.items()),
        "",
    ]
    for i, b in enumerate(s.beats, 1):
        title = b["role"].replace("_", " ").capitalize()
        src = "CACHED" if b.get("source") == "cached" else "GENERATED"
        out += [f"## Beat {i} — {title} · {src} · role: {b['role']}", ""]
        if not b.get("text"):
            out += [f"> *(cached: `{b.get('cached_ref', '?')}`)*", ""]
            continue
        out += ["> " + l if l.strip() else ">" for l in b["text"].split("\n")]
        r = check(b["text"])
        flags = [f"`{f.rule}` {f.detail}" for f in r.findings]
        out += ["", f"*{r.words}w · notice {r.noticing_ratio:.2f} · "
                    f"senses {len(r.senses_used)}*"]
        if flags:
            out += ["", "Craft findings: " + "; ".join(flags)]
        out += [""]

    path.write_text("\n".join(out))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("text", nargs="?", help="what the listener said")
    ap.add_argument("--category", help="skip intent parsing and use this category")
    ap.add_argument("--pacing", default="standard", choices=["slow", "standard", "brisk"])
    ap.add_argument("--dry", action="store_true", help="force dry run even with a key")
    ap.add_argument("--show-prompts", action="store_true")
    ap.add_argument("--templates", action="store_true", help="list templates and exit")
    ap.add_argument("--out", metavar="PATH", help="write the session as markdown")
    ap.add_argument("--estimate", action="store_true",
                    help="project the cost of a live run without making one")
    a = ap.parse_args()
    if not a.text and not a.templates:
        ap.error("text is required unless --templates")

    if a.templates:
        for t in TEMPLATES.values():
            print(f"\n{t.name:<16} depth {t.depth}  "
                  f"{t.duration_range[0]//60}-{t.duration_range[1]//60} min")
            print(f"  aims at: {t.aims_at}")
            print(f"  serves:  {', '.join(t.categories)}")
            print(f"  beats:   {' -> '.join(b.role for b in t.beats)}")
        return 0

    s = generate(a.text, category=a.category, pacing=a.pacing,
                 dry=a.dry or a.estimate, progress=True)

    print(f"\ncategory   {s.category}")
    print(f"template   {s.template.name}  (depth {s.template.depth})")
    print(f"aims at    {s.template.aims_at}")

    if s.outline:
        beats = s.outline["beats"]
        total_w = sum(b.get("word_target", 0) for b in beats)
        total_s = sum(b.get("silence_total_s", 0) for b in beats)
        speech = sum(b.get("word_target", 0) / b["wpm"] * 60 for b in beats if b.get("word_target"))
        print(f"target     {s.outline['target_duration_s']}s\n")
        print(f"{'beat':<26}{'words':>6}{'wpm':>5}{'silence':>9}")
        print("-" * 46)
        for b in beats:
            if b.get("source") == "cached":
                print(f"{b['role']:<26}{'cached':>6}{b['wpm']:>5}{'-':>9}")
            else:
                print(f"{b['role']:<26}{b['word_target']:>6}{b['wpm']:>5}"
                      f"{b['silence_total_s']:>8}s")
        print("-" * 46)
        print(f"{'':<26}{total_w:>6}{'':>5}{total_s:>8}s")
        print(f"\nprojected  {(speech + total_s) / 60:.1f} min speech+silence "
              f"(+ cached intro)")
        print(f"silence    {total_s / (speech + total_s) * 100:.0f}%")

    if s.script:
        print(f"\n{'=' * 78}\n{s.script}\n{'=' * 78}")

    if a.estimate:
        print(f"\n{estimate(s)}")

    if s.usage.calls:
        print(f"\n{s.usage.summary()}")

    if a.out:
        if not s.beats:
            print("\nnothing to write - dry run produced no narration")
        else:
            write_session_doc(s, Path(a.out), a.text)
            print(f"wrote {a.out}")

    if a.show_prompts:
        print(s.trace.prompts_only())

    return 0


if __name__ == "__main__":
    sys.exit(main())

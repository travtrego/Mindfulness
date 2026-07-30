# Guided Visualization Engine

Working title. An audio-first app that generates original guided visualizations tailored
to what the user needs right now — grounded in the mechanics of anxiety and PTSD
treatment (paced breathing, safe-place imagery, imaginal rehearsal), without clinical
claims.

Not a meditation app. Meditation is one application of a broader visualization engine.

> **North star:** every session should feel like a memory, not a story.

## Contents

| File | What it is |
|---|---|
| [`SPEC.md`](./SPEC.md) | Consolidated product + technical spec. Resolves the conflicts across the three source drafts and records the decisions with rationale. |
| [`docs/app.html`](./docs/app.html) | **The app.** Full-screen interface, no annotations. Real navigation, working chat, breathing pacer. No audio yet. |
| [`docs/prototype.html`](./docs/prototype.html) | The same flow as a design document — every screen annotated with why it is that way. |

## Running it locally

```bash
pip install -r requirements.txt
python3 scripts/serve.py                 # the app at localhost:8000
python3 scripts/serve.py --doc           # the annotated design document
python3 -m generator.cli --templates     # the six templates
```

### Generating a session

Without `ANTHROPIC_API_KEY` the generator runs dry: it builds every prompt and allocates
the per-beat word and silence budget, then stops. With a key it runs for real — no code
change, no flag.

```bash
export ANTHROPIC_API_KEY=sk-ant-...

python3 -m generator.cli "clean and jerk on saturday" --category competition \
        --out docs/sessions/gen-01.md
```

`--out` writes the session in the same format as the hand-written ones in
`docs/sessions/`, with per-beat craft findings. That is deliberate: **the only test that
matters is reading a generated session out loud beside `01` and `02` and seeing whether
you can tell which is which.**

Every run prints what it cost. Expect roughly **$0.13** per session.

```bash
python3 -m generator.cli "..." --dry     # force dry even with a key
python3 -m generator.cli "..." --show-prompts
```

### Checks

```bash
python3 scripts/check_craft.py           # craft validator vs the hand-written sessions
python3 scripts/check_intros.py          # the four cached intros
python3 scripts/validate_outline.py docs/schema/example-01-clean-and-jerk.json
python3 scripts/smoke_live_path.py       # whole live path against a fake model, no spend
```

## Status

Text pipeline built, validated, and wired to the live API. **No audio yet** — that needs
an ElevenLabs key. Nothing is deployed; the app runs locally only.

Three of six templates have hand-written exemplars (`rehearsal`, `reentry`,
`anchored_place`), so 16 of 19 beat roles resolve to a few-shot example. Three roles still
draft blind: `paced_breathing`, `meaningful_experience`, `consolidation`.

**Next up, in order:**

1. **Read a generated session out loud.** Everything above is unverified until prose comes
   out the other end and holds up beside `docs/sessions/01` and `02`. Nothing else is
   worth doing first.
2. Hand-write exemplars for `immersive`, `reflective`, and `breath_only` — the three
   roles that currently draft blind.
3. Wire the app's chat to the generator; its replies are canned today.
4. TTS: script → parallel synthesis → soundscape markers resolved against character
   timings → mixed render.

## Input model

```
1  CATEGORY   broad set, one tap — routes to a template, nothing more
2a TALK       up to 3 turns — only for categories that need your situation
2b AMPLIFY    up to 3 questions, generated from 2a — fills the template
3  MEMORY     informs all of it, fed by end-of-session reflection
```

**Depth scales with what the template needs** (`SPEC.md` §2.1):

| Depth | Path | Interactions |
|---|---|---|
| 0 | tap → audio | **1** |
| 1 | tap → 3 questions → audio | **4** |
| 2 | tap → talk → 3 questions → audio | **~7** |

Floor is one tap and about two seconds — that's the 2am case, and nothing may be added to
it. Hard caps at 3 chat turns and 3 questions.

**Fourteen categories on five templates.** Breadth is cheap; template count is the real
build cost. See `SPEC.md` §1.5.

| Group | Categories |
|---|---|
| Settle | Just breathing · Body scan |
| Go somewhere | Nature · Adventure · Fantasy · Into sleep |
| Prepare | Interview · Competition · Hard conversation · Confidence |
| Reflect | Gratitude · Creativity |

Plus Safe Place as a persistent return, and "just talk to me" as the chat entry.

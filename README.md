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
| [`docs/app.html`](./docs/app.html) | **The app.** Full-screen interface, no annotations. Real navigation, live chat and questions, breathing pacer. No audio yet. |
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

Every run prints what it cost, and `--estimate` projects it without spending anything:

```bash
python3 -m generator.cli "..." --estimate      # ~$0.12 per run (~$1.20 for ten)
python3 -m generator.cli "..." --dry           # force dry even with a key
python3 -m generator.cli "..." --show-prompts
```

| Template | Per run |
|---|---|
| `breath_only` | ~$0.08 |
| `reflective` | ~$0.11 |
| `anchored_place` | ~$0.11 |
| `rehearsal` | ~$0.12 |
| `immersive` (long) | ~$0.15 |

### The app's two endpoints

The chat and the amplifying questions call the generator through the local server. **The
browser never holds the key** — a key shipped to a browser is a key published.

```
POST /api/talk        {category, history[]}  -> {reply, done, slots, live}
POST /api/questions   {category, history[]}  -> {questions[], live}
```

With no key both return the hand-written fallbacks that used to be hardcoded in the page,
so the interface still works offline. `live: false` says which you are looking at, and the
browser console logs it. A failed call falls back rather than blanking the screen.

### Checks

```bash
python3 scripts/check_craft.py           # craft validator vs the hand-written sessions
python3 scripts/check_intros.py          # the four cached intros
python3 scripts/validate_outline.py docs/schema/example-01-clean-and-jerk.json
python3 scripts/smoke_live_path.py       # whole live path against a fake model, no spend
python3 scripts/session_stats.py         # measured runtime per session + template shares
python3 scripts/test_bad_outlines.py     # ten malformed model outlines, none may crash a run
python3 scripts/check_pipeline_schema.py # every template's real output vs our own schema
python3 scripts/test_bad_model_output.py # bad JSON, bad intent, empty drafts - none may crash
```

## Status

Text pipeline built, validated, and wired to the live API. **No audio yet** — that needs
an ElevenLabs key. Nothing is deployed; the app runs locally only.

**All six templates have a hand-written exemplar, and all 19 beat roles resolve to one.**
Exemplars are matched on template *and* role, because two templates can share a role name
and mean different things by it.

| # | Session | Template | Measured |
|---|---|---|---|
| 01 | Clean and jerk | `rehearsal` | 16:02 |
| 02 | First day back | `reentry` | 20:01 |
| 03 | Safe place, fourth visit | `anchored_place` | 10:50 |
| 04 | Just breathing | `breath_only` | 6:26 |
| 05 | Frozen lake at dusk | `immersive` | 15:42 |
| 06 | What your hands did today | `reflective` | 10:52 |

Runtimes include each session's own cached intro, read from its `cached_ref` — the four
intro scripts differ by up to 71 seconds, so assuming one number for all of them was worth
about 25 seconds a session.

**Next up, in order:**

1. **Read a generated session out loud.** Everything above is unverified until prose comes
   out the other end and holds up beside `docs/sessions/01` and `02`. Nothing else is
   worth doing first.
2. TTS: script → parallel synthesis → soundscape markers resolved against character
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

**Fourteen categories on six templates.** Breadth is cheap; template count is the real
build cost. See `SPEC.md` §1.5.

| Group | Categories |
|---|---|
| Settle | Just breathing · Body scan |
| Go somewhere | Nature · Adventure · Fantasy · Into sleep |
| Prepare | Interview · Competition · Hard conversation · Confidence |
| Reflect | Gratitude · Creativity |
| Going back | First day back · Seeing people again |

Plus Safe Place as a persistent return, and "just talk to me" as the chat entry.

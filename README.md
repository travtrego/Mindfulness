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
python3 scripts/serve.py                 # the app at localhost:8000
python3 scripts/serve.py --doc           # the annotated design document
python3 -m generator.cli --templates     # the six templates
python3 -m generator.cli "playoff game saturday" --category competition
```

The generator runs without an API key: it builds every prompt and allocates the per-beat
word and silence budget, then stops. It goes live the moment `ANTHROPIC_API_KEY` exists,
with no code change.

```bash
python3 scripts/check_craft.py           # craft validator vs the hand-written sessions
python3 scripts/check_intros.py          # the four cached intros
python3 scripts/validate_outline.py docs/schema/example-01-clean-and-jerk.json
```

## Status

Text pipeline built and validated. **No audio yet** — that needs an ElevenLabs key.
Nothing is deployed; the mock runs locally only.

**Next up, in order:**

1. Hand-write 3–5 complete sessions (one per template) as few-shot exemplars and the
   craft eval set. This surfaces schema questions no amount of spec work will.
2. Write the slot definition for each of the five templates — which slots the template
   needs filled, plus worked examples of good and bad amplifying questions. These drive
   question generation at runtime.
3. Lock the outline JSON schema and the stem tag enum.
4. Prove the pipeline shape end to end: 3 LLM calls → script → parallel TTS → mixed render.

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

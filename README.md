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
| [`docs/prototype.html`](./docs/prototype.html) | Interactive UX prototype — tap through the full flow, with design rationale per screen. Open in a browser. |

## Status

Pre-build. Spec and UX only — no application code yet.

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

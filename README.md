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

1. Hand-write 3–5 complete sessions (one per V1 category) as few-shot exemplars and the
   craft eval set. This surfaces schema questions no amount of spec work will.
2. Lock the outline JSON schema and the stem tag enum.
3. Prove the pipeline shape end to end: 3 LLM calls → script → parallel TTS → mixed render.

## V1 categories

Just Breathing · Safe Place · Upcoming Event · Nature Escape

Fantasy/Story and Sleep Journeys are deferred — see `SPEC.md` §1.5.

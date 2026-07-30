# Just breathing — six minutes

*template: breath_only*

Reference session #4. **Breath only** template. No narrative, no place, no scene. The
shortest and most-used thing the product will ever make, and the one with the least room
to hide.

Depth 0. One tap. This is the 2am case.

Target 6:00 · **measured 6:26** · 132 generated words · 55% silence · cached intro on top.

## Inputs

None. That is the point — nothing is asked, nothing is stored, nothing is generated from
anyone's situation. The only parameter is the cycle: **4 in · 2 hold · 6 out.**

```json
{ "template": "breath_only", "pattern": [4, 2, 6], "target_duration_s": 360 }
```

## Beat 1 — Grounding intro · CACHED · role: grounding_intro

> *(cached: `intro/settling_slow`)*

## Beat 2 — Settling · GENERATED · role: settling

> Wherever you are is where this happens. No adjustment needed.
>
> *[8s]*
>
> You notice the breath that is already going, before anything changes about it.
>
> *[8s]*

## Beat 3 — Paced breathing · GENERATED · role: paced_breathing

> In, through the nose. Four.
>
> *[4s — hold]*
>
> Hold it there. Two.
>
> *[2s — hold]*
>
> And out. Six. Longer going than coming.
>
> *[6s — hold]*
>
> Again. In.
>
> *[4s — hold]*
>
> Hold.
>
> *[2s — hold]*
>
> Out, and let the out be the long part.
>
> *[6s — hold]*
>
> In.
>
> *[4s — hold]*
>
> *[2s — hold]*
>
> Out.
>
> *[6s — hold]*
>
> Once more, and after that the counting is yours.
>
> *[12s — hold]*
>
> Nothing to keep track of now. The rhythm has it.
>
> *[14s — open]*
>
> If it drifts, it drifts. You notice, and you come back in on the next one.
>
> *[14s — open]*
>
> There is nothing else this is for.
>
> *[16s — open]*
>
> The next one, and the one after it, with nothing said over them.
>
> *[18s — open]*
>
> *[16s — open]*

## Beat 4 — Reorientation · GENERATED · role: reorientation

> Let the breath go back to its own business.
>
> *[6s]*
>
> Sound in the room. Weight where you are sitting.
>
> *[5s]*
>
> Eyes open when you want them.

## What writing this changed in the allocator

The flat 58/42 speech-to-silence split gave `paced_breathing` **130 words**. Writing it
honestly produced 85. The gap is not a rounding error — 130 words is enough to narrate
every cycle to the end, which is precisely the failure mode.

`BeatSpec` now takes a `silence_share` override, and `paced_breathing` sets it to 0.65.
Nothing else in any template moved.

## The move this session exists to demonstrate

**The narration withdraws.** It counts three full cycles, then hands the count over —
*"after that the counting is yours"* — and never takes it back. Word density falls beat to
beat while the silence blocks lengthen from 4s to 16s. By the end the listener is doing
the whole thing and the voice is only confirming that nothing is required.

A generator left to its own devices will do the opposite. It will keep talking, because
talking is what it does, and it will narrate every cycle to the end. That is the failure
this exemplar is here to prevent.

**Missing a breath is pre-forgiven, once, without ceremony.** *"If it drifts, it drifts."*
Not *"be kind to yourself"* — which is a demand for a feeling, and costs the listener
something to comply with.

## Why the silence is typed

The markers in beat 3 are `hold`, not `sensory` or `open`, until the counting is handed
over. That distinction is not cosmetic:

| Type | What the renderer does |
|---|---|
| `hold` | exact duration, no drift — it *is* the breath |
| `open` | may stretch under a slow narration rate |

A `hold` silence in a paced-breathing beat has a right answer to the tenth of a second. Get
it wrong and the listener is breathing against the track instead of with it, which is worse
than no pacing at all.

## The rule this session establishes

> **In a breath-only session, silence is the content and narration is the overhead.** If a
> beat's word count and its silence budget ever conflict, the words lose.

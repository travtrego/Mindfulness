# Frozen lake at dusk — sixteen minutes

*template: immersive*

Reference session #5. **Immersive** template. A real place, entered and moved through.
This is the template that covers nature, adventure, fantasy and into-sleep, which makes it
the one most likely to drift into travel-brochure writing.

Depth 1 — one tap, three questions, no chat.

Target 16:00 · **measured 15:42** · 538 generated words · 47% silence · cached intro on
top.

## Inputs

```json
{
  "category": "nature",
  "environment": "a frozen lake, late afternoon, walking out from the shore",
  "realism": "real",
  "movement": "walking, unhurried",
  "session_exclusions": []
}
```

The three questions that produced it — generated, not fixed:

> *"Somewhere warm or somewhere cold?"*
> *"Moving through it, or staying in one spot?"*
> *"Is it light or is it going dark?"*

None of them asks how the listener wants to feel. That slot does not exist (`slots.md`).

## Beat 1 — Grounding intro · CACHED · role: grounding_intro

> *(cached: `intro/neutral_standard`)*

## Beat 2 — Settling · GENERATED · role: settling

> Let the weight go where it is already going.
>
> *[8s]*
>
> There is nowhere to be for the next while, and nothing here that needs doing well.
>
> *[10s]*
>
> The breath finds its own length. Not deeper — only slower.
>
> *[10s]*
>
> Somewhere ahead of you there is cold air, and you are about to be standing in it.
>
> *[8s]*

## Beat 3 — Entry threshold · GENERATED · role: entry_threshold

> The last of the land is behind you. You notice the moment underfoot stops being ground
> and starts being ice.
>
> *[12s]*
>
> It does not give. That is the first surprise — how much it does not give.
>
> *[12s]*
>
> Cold finds your face before it finds anything else. The inside of your nose knows the
> temperature before your hands do.
>
> *[14s]*
>
> You take a step out anyway.
>
> *[12s]*

## Beat 4 — Establish world · GENERATED · role: establish_world

> Out here the light is going. Not dark — going.
>
> *[14s]*
>
> The lake is wider than it looked from the shore. Everything on the far side has become a
> single flat colour, and you could not name it if asked.
>
> *[16s]*
>
> Underfoot, the ice is not one thing. There are milky parts and clear parts, and where it
> is clear you are standing over a depth you cannot see the bottom of.
>
> *[18s]*
>
> Sound carries strangely. Something far off arrives sounding close, and something close by
> arrives sounding small.
>
> *[16s]*
>
> Your breath is the only warm thing in any direction.
>
> *[22s]*

## Beat 5 — Meaningful experience · GENERATED · role: meaningful_experience

> You walk out further. There is no reason to hurry and nothing to reach.
>
> *[14s]*
>
> Every so often the ice speaks. A long note that starts under one foot and travels away
> from you, out under the whole lake, and keeps going after you have stopped hearing it.
>
> *[18s]*
>
> It is not breaking. This is what thick ice does. It is the sound of something enormous
> settling further into being solid.
>
> *[16s]*
>
> You notice you have stopped bracing for it.
>
> *[14s]*
>
> Further out, the shore is a line rather than a place. Whatever is on it — trees, a
> building, a road, whatever it is for you — has stopped being separate things.
>
> *[16s]*
>
> Nobody knows exactly where you are standing. Not one person could put a finger on the
> map. And nothing about that is a problem.
>
> *[16s]*

## Beat 6 — Consolidation · GENERATED · role: consolidation

> Stop walking.
>
> *[12s]*
>
> The cold is on one side of your face and not the other. There is a wind, or there was
> one.
>
> *[16s]*
>
> Under you: a hundred feet of black water, held up by four inches of winter, holding you
> up without effort or opinion.
>
> *[18s]*
>
> Above you the colour is draining out of the sky from one edge.
>
> *[16s]*
>
> You are the only thing out here that is warm, and you are not cold.
>
> *[20s]*

## Beat 7 — Anchor · GENERATED · role: anchor

> Take one breath of this air. The kind that is cold enough to have an edge on the way in.
>
> *[10s]*
>
> That is the one that travels.
>
> *[8s]*
>
> Tomorrow, in a room that has none of this in it, you can take one breath that is slower
> than the one before it and a little cooler on the way in — and this comes back. Not the
> lake. The standing-out-on-it part.
>
> *[14s]*
>
> One breath. That is the whole anchor.
>
> *[12s]*

## Beat 8 — Reorientation · GENERATED · role: reorientation

> The lake stays where it is.
>
> *[6s]*
>
> Come back to the temperature of the room you are actually in. It is warmer than where you
> have been.
>
> *[6s]*
>
> Sound in this room. The weight of you on this surface.
>
> *[5s]*
>
> Eyes open, and stay a minute before you get up.

## On the beat word targets

Every beat here came in **under** the allocator's `word_target` — by 24% on settling, 32%
on establish-world — and the session still lands at 16:07 against a 16:00 target, because
the silence ran correspondingly long.

That is the intended relationship, and it is worth stating plainly: `word_target` is a
guide, **total runtime is the gate** (`SPEC.md` §5.2). A beat that says what it needs in
fewer words and then holds is not under-delivering. Padding it to hit the number is the
failure — and padding is the specific thing the craft standard exists to prevent.

## What this template gets wrong without an exemplar

**Establish world wants to be a list.** Four beautiful things stacked in one paragraph is
the default failure, and it reads as a brochure. Beat 4 sequences instead: light, then
width, then underfoot, then sound, then breath — one channel at a time, each given its own
silence.

**Nothing here is named that the listener has to accept.** The far side is *"a single flat
colour you could not name"*. The shore is *"trees, a building, a road, whatever it is for
you."* The lake is specified; its contents are not.

**The ice sound is the whole session.** It is the one event, it arrives in the movement
beat, and it is *reframed rather than resolved* — the fear is left standing and explained,
not deleted. *"It is not breaking. This is what thick ice does."* Then the beat marks the
change in the listener rather than the world: *"you have stopped bracing for it."*

## Why `consolidation` is a separate beat from `establish_world`

They describe the same place. The difference is motion — beat 4 is arriving, beat 6 is
having stopped. `consolidation` opens on **"Stop walking."** and every sentence after it is
static. If a generated session's consolidation beat still contains verbs of travel, the
beat has not happened.

It is also where the session is allowed its one moment of scale — *"a hundred feet of black
water, held up by four inches of winter"* — because by then the listener has been standing
on it long enough to have earned it. In beat 3 the same sentence would be a threat.

## The rule this session establishes

> **One event per immersive session, placed in `meaningful_experience`.** Not three
> wonders. The rest of the beats exist to make the one event land, and a session with a
> second one has no first one.

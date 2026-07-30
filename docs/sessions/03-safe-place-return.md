# Safe place — fourth visit

*template: anchored_place*

Reference session #3. **Anchored place** template, the only depth-0 template with stored
state. This is a *return* visit, not the establishing one: the place already exists in
memory, and the session's whole job is to not damage it.

One tap. No questions. From tap to audio is about two seconds.

Target 11:00 · **measured 10:50** · 379 generated words · 40% silence · cached intro on
top.

## Inputs

The place was supplied by the listener three visits ago and has never been re-asked. The
model does not invent any of this — it reads it.

```json
{
  "place_id": "porch",
  "visit_number": 4,
  "established_details": [
    "screened porch, late summer, after dark",
    "the screen door and the sound of its spring",
    "a wooden chair, arms worn smooth"
  ],
  "anchor": "thumb pressed into the worn spot on the chair arm",
  "new_detail": "(model supplies exactly one)"
}
```

## Beat 1 — Grounding intro · CACHED · role: grounding_intro

> *(cached: `intro/neutral_standard`)*

## Beat 2 — Settling · GENERATED · role: settling

> You notice the weight of your hands, wherever they have ended up.
>
> *[8s]*
>
> Nothing needs to move from here. Nothing needs to be decided from here.
>
> *[6s]*
>
> The breath finds its own length. Not deeper — only slower.
>
> *[8s]*
>
> And behind that, the porch is already there. It does not need you in it to go on being a
> porch.
>
> *[6s]*

## Beat 3 — Entry threshold · GENERATED · role: entry_threshold

> You do not have to go looking for it. That was the first visit's work, and it is done.
>
> *[7s]*
>
> By now the door is the part your hands know first. The give of the spring, and the sound
> it makes on the way back.
>
> *[10s]*
>
> You are through it before you have decided to be.
>
> *[9s]*
>
> The boards under you. Late summer, after dark.
>
> *[9s]*

## Beat 4 — Establish world · GENERATED · role: establish_world

> Everything is where you left it.
>
> *[8s]*
>
> The chair with the arms worn smooth — you notice the smoothness before you notice the
> chair.
>
> *[10s]*
>
> Beyond the screen, the dark is full of sound, and none of it is close. Insects, mostly,
> and the kind of far-off noise that stays far off.
>
> *[12s]*
>
> The air on this side of the mesh is warmer than the air on the other side. You can find
> the line where they meet, somewhere across your face.
>
> *[12s]*
>
> Nothing here asks anything of you. Nothing here has changed since you left it.
>
> *[16s]*

## Beat 5 — Deepening · GENERATED · role: deepening

> There is one thing here you did not notice before. Only one, and it was always here.
>
> *[9s]*
>
> The light from inside the house falls across the boards in a long rectangle.
>
> *[10s]*
>
> It stops short of the railing. Past that edge the dark starts, and it is not a dark that
> wants anything from you.
>
> *[12s]*
>
> You notice which side of you is lit and which side is not.
>
> *[10s]*
>
> That is all this visit needs to add. One thing, noticed once, and the rest of the porch
> exactly as you left it.
>
> *[10s]*

## Beat 6 — Anchor · GENERATED · role: anchor

> Your thumb finds the worn spot on the arm of the chair.
>
> *[7s]*
>
> The place the wood gave up its grain, from being pressed exactly there, this many times.
>
> *[8s]*
>
> Press it now.
>
> *[6s]*
>
> This is the part that travels. Tomorrow, in a room with none of this in it, your thumb
> can find an edge — a desk, a seam, the side of a phone — and press.
>
> *[11s]*
>
> The porch does not have to come with it. Only the pressing.
>
> *[10s]*

## Beat 7 — Reorientation · GENERATED · role: reorientation

> The porch keeps.
>
> *[5s]*
>
> Sound in the room you are actually in. The weight of you in the chair you are actually
> in.
>
> *[5s]*
>
> Eyes open when you want them.
>
> *[4s]*

## What this session is doing that the other two are not

**Nothing is described as new except one thing.** Beats 3 and 4 use only what was already
stored, and they use it in the same words each visit — the screen door, the worn arms, the
warm-side/cool-side of the mesh. Familiarity is the entire mechanism of this template. A
model that "improves" the porch each visit destroys the thing being built.

**Beat 5 adds exactly one detail, and announces that it is one.** *"That is all this visit
needs to add."* On visit twelve the porch should still be a porch, not a cathedral.

**Arrival is faster than it was on visit one.** *"You are through it before you have decided
to be."* The `entry_threshold` share shrinks as `visit_number` rises — by visit ten it is
almost nothing, because you do not need to be walked to a place you already live in.

**The anchor is portable, and the beat says so out loud.** The porch is not the deliverable.
The thumb is. That is the only part that works at a desk on a Tuesday.

## Where the craft rules did work

- *"you notice the smoothness before you notice the chair"* — names the sense, not the
  furniture, and does it in the order the sense actually arrives
- *"warmer on this side of the mesh than the other"* — contrast and asymmetry, and the
  screen is doing double duty as the boundary of the safe place
- *"a desk, a seam, the side of a phone"* — guided incompleteness at the one moment it
  matters most, since the listener's tomorrow is not knowable from here
- *"it is not a dark that wants anything from you"* — the dark is allowed to stay dark.
  Nothing in a safe place has to be made pleasant to be safe

## The rule this session establishes

> **Additive only.** A returning place may gain one detail per visit and may never lose or
> contradict one. If the model cannot fit a new detail without disturbing a stored one, it
> adds nothing and the beat gets shorter.

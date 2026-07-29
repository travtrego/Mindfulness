# The cached grounding intros

The first thing every user ever hears, and the only beat that is never generated.

It is also the **latency mask** (`SPEC.md` §1.1): it starts within ~200ms while the rest of
the session is still being written and synthesized. Nothing else in the product is allowed
to depend on the pipeline being fast.

---

## It's four scripts, not eighteen

The spec described a matrix of *3 pacings × 3 registers × 2 voices = 18 recordings*, and
I had been treating that as eighteen writing jobs. It isn't.

**Pacing does not change the words.** The sentences that settle someone who is wound up are
the same sentences whether read at 72 or 92 words per minute. Pacing is a *delivery*
parameter — words per minute plus a silence multiplier — applied at recording time.

**Register does change the words.** What you say to someone activated is genuinely
different from what you say to someone flat.

So:

| | Count |
|---|---|
| Scripts to write | **4** |
| Pacings per script | 3 |
| Voices per pacing | 2 |
| **Recordings to produce** | **24** |

Four registers, not three — `sensitive` is added below, because the spec already required
sensitivity-flagged sessions to carry explicit stop permission and that cannot be a
delivery parameter.

---

## Rules every intro obeys

1. **Physical by the third line.** This beat has no session material, so it drifts into
   explaining itself if not anchored in the body. That failure is documented in
   `01-clean-and-jerk.md`, Revision 1.
2. **No imagery whatsoever.** A cached recording cannot know the user's standing
   exclusions. A water simile here would breach a water exclusion the recording has no way
   to see. **Only the body and the breath.** Enforced by the schema (`maxItems: 0` on
   `do_not_mention` for cached beats).
3. **Composed, declarative, unhurried.** Never chatty, never reassuring, never mystical.
4. **No three-item enumeration.** Two is a pair; three is a list, and lists are the tell.
5. **No hedging adverbs.** No *gently, simply, just, a little.*
6. **~50–65 words.** The first draft ran 96 and every extra word was about the session
   rather than in it.

---

## 1 · Settling

**For:** activated, wound up, anxious. The 2am case, and the default before Breath-only.

> Settle into the shape your body has already chosen.
>
> *[5s]*
>
> Let your eyes close — or let your focus soften onto a single still point.
>
> *[6s]*
>
> The surface beneath you is taking all of your weight. It has been holding you all along.
>
> *[7s]*
>
> Let the breath lengthen. Not deeper — only slower.
>
> *[12s]*
>
> There is nothing to seek here, and nothing that needs to be seen clearly.
>
> *[10s]*

`64 words · 40s silence`

---

## 2 · Neutral

**For:** no strong state either way. The most-used variant, and the baseline the other
three are written against.

> Take the position you are going to stay in.
>
> *[5s]*
>
> Let your eyes close — or let your focus rest on one unmoving thing.
>
> *[6s]*
>
> Notice the weight of your hands. They usually go unnoticed.
>
> *[7s]*
>
> Let the breath find its own pace, a little under the speed of speech.
>
> *[11s]*
>
> Nothing here needs to be seen clearly.
>
> *[9s]*

`54 words · 38s silence`

**Note on line four.** *"A little under the speed of speech"* gives the listener a
referent they already have, rather than an abstraction like "slow and steady." They are
listening to speech at that exact moment.

---

## 3 · Activating

**For:** flat, tired, or heading into a rehearsal. This one must not sedate — a listener
about to mentally rehearse a competition needs to arrive alert, not softened.

> Sit the way you would if something were about to begin.
>
> *[4s]*
>
> Let your eyes close — or let your focus hold on one fixed point.
>
> *[5s]*
>
> Notice where the floor meets you. That contact is the whole anchor.
>
> *[6s]*
>
> Let the breath even out. Not slower — even.
>
> *[9s]*
>
> Nothing here needs to be seen clearly.
>
> *[7s]*

`53 words · 31s silence`

**Note.** *"Not slower — even"* deliberately breaks the parallel with the other three
scripts, which all say *slower*. Slowing the breath before rehearsal is the wrong
instruction; the target is steadiness, not sedation. Silences are also shorter throughout —
this register's job is to gather, not to release.

---

## 4 · Sensitive

**For:** sensitivity-flagged sessions (`SPEC.md` §8). Carries explicit stop permission and
removes every implicit demand.

> Settle only as far as you want to. There is no further to get to.
>
> *[6s]*
>
> Let your eyes close, or keep them open. Both work.
>
> *[7s]*
>
> The surface beneath you is holding your weight, and it will keep holding it.
>
> *[8s]*
>
> Let the breath lengthen if it will. It does not have to.
>
> *[12s]*
>
> Nothing here needs to be seen clearly.
>
> *[9s]*
>
> You can stop this at any point. Nothing is lost by stopping.
>
> *[10s]*

`70 words · 52s silence`

**Why this one exists.** Every other script contains a soft instruction — *settle, let,
notice.* For a listener who is dissociating or close to panic, an instruction is a demand,
and a demand they cannot meet confirms that something is wrong with them.

This script removes the floor from every line. *"It does not have to."* *"There is no
further to get to."* Nothing here can be failed.

**And it is the one place the stop permission is spoken aloud.** Everywhere else the
always-available exit control carries it, because saying it out loud makes an ordinary
session sound like a liability waiver (§1.1). Here it is worth the cost.

---

## Pacing

Applied at recording time. Same words, three deliveries.

| Pacing | wpm | Silence × | Used when |
|---|---|---|---|
| **slow** | 72 | 1.35 | sleep · sensitive · late night · long sessions |
| **standard** | 82 | 1.00 | default |
| **brisk** | 92 | 0.75 | short sessions · Breath-only · high activation |

### Resulting durations

| Script | Words | slow | standard | brisk |
|---|---|---|---|---|
| Settling | 64 | 1:47 | 1:26 | 1:11 |
| Neutral | 54 | 1:36 | 1:17 | 1:03 |
| Activating | 53 | 1:26 | 1:09 | 0:57 |
| Sensitive | 70 | 2:08 | 1:43 | 1:24 |

Measured by `scripts/check_intros.py`, not estimated.

**The band is 0:57 – 2:08, and every value in it is useful.** The intro is the latency
mask, so a longer intro is a larger generation buffer — the slow variants give the
pipeline nearly two extra minutes. Sleep and sensitive sessions, which get the slow
pacing, are also the ones whose scripts are longest and slowest to generate.

That alignment is convenient rather than designed, but it should be preserved: **never
pair a brisk intro with a long generated session.**

---

## Production

- **Voices:** 2, per `SPEC.md` §6.4 — the low/husky register and the deep/measured one.
  Both read all four scripts at all three pacings.
- **24 recordings.** At ~1:22 average that is about 33 minutes of finished audio.
- **Open question, `SPEC.md` §12.2:** voice actor or high-quality TTS. Leaning actor —
  24 short recordings is a single session's work, and this is the ritual anchor of the
  whole product. It is also the only audio a user hears identically every time, which
  makes it the one place TTS artifacts would compound.
- **Silences are recorded, not edited in.** A narrator holding a pause breathes; a
  digitally inserted gap does not. On a beat this repetitive, the difference is audible by
  the fourth session.

# Template slot definitions

What each template needs filled before it can generate, where each value comes from, and
what a good amplifying question looks like for it.

**This replaces the ~35 hand-written per-category questions.** Because talk runs before the
questions (`SPEC.md` §2.2), amplifiers are generated at runtime. These definitions are what
they're generated *against*: the model is told which slots are still empty and asked to
write questions that fill them.

Five files' worth of content, not thirty-five.

---

## How slots are filled

| Source | Meaning |
|---|---|
| `profile` | style memory — silent, never asked |
| `memory` | prior sessions — may pre-fill a chip, always overridable |
| `talk` | extracted from the layer-2a conversation |
| `amplify` | asked directly as a layer-2b question |
| `model` | invented by the model; **no question may be spent on these** |
| `default` | template constant |

**The rule that keeps sessions short:** a slot is only eligible for a question if it is
`required`, still empty after `talk` and `memory`, and cannot be filled by `model` without
loss. Everything else the model invents.

That is why Immersive asks three questions and Rehearsal asks three *after* a
conversation — Immersive can invent an excellent forest; no model can invent the thirty
seconds you are actually dreading.

### Depth is a floor, not a ceiling

The depth assigned to a category (`SPEC.md` §2.1) sets the **minimum** the system will ask.
It never caps what the user may say.

**"Or just say it" is present on every amplify screen, in every category, including depth 0.**
A user who types *"forest at the base of mountains with a black beach"* has given better
input than any chip set could collect — and the system takes it and **skips the chips
entirely**.

| User says | System asks |
|---|---|
| nothing | the 3 chips |
| one sentence | whatever the sentence left empty — often 1 |
| a rich description | **nothing** |

**The more the user says, the less the system asks.** Free text and speech fill slots
directly; every slot filled is a question retired. Rich input can only ever *shorten* the
path to audio.

The system controls the floor. The user controls the ceiling. It is never the other way
around.

---

## What makes an amplifying question good

| | Good | Bad |
|---|---|---|
| **Answerable** | one tap | requires a typed sentence *(that belongs in talk)* |
| **Necessary** | fills a slot the model can't invent | asks for something the model could have chosen |
| **Specific** | narrows to one concrete thing | gathers atmosphere |
| **In frame** | uses the user's own words back | uses product taxonomy |
| **Non-routing** | assumes the category | re-asks what the category settled |

**Worked pair, Rehearsal:**

> ✅ *"Do you want the crowd, or do you want it quiet?"*
> ❌ *"How would you like the ending to feel?"*

The first fills `audience`, is answerable in one tap, and shapes every ambience decision
downstream. The second asks the user to do the writing, and the model could have chosen an
ending itself.

**A generated question can be right in one conversation and wrong in the next.** An earlier
draft used *"on the walk off — do they see your face?"* as the worked example. That question
was correct for a soccer scenario where being seen after a miss was the whole subject. Carried
into a weightlifting meet it is simply strange — nobody at a platform is thinking about their
face.

The lesson is that generated questions need a **quality gate, not just a count limit**. Before
a question is shown it must pass:

1. Does it fill a slot that is actually empty?
2. Would a reasonable person in *this* situation find it relevant?
3. Is it answerable in one tap?

Fail any of the three and the model drops the question and fills the slot itself. **Asking
three questions is a maximum, never a quota.**

**Worked pair, Immersive:**

> ✅ *"Somewhere you've been, or somewhere new?"*
> ❌ *"What kind of nature scene appeals to you?"*

The first is a binary that changes generation strategy — retrieval vs. construction. The
second is a menu wearing a question mark.

---

## A · Breath only

*Just breathing* — **depth 0, no questions ever asked.**

| Slot | Req | Source | Notes |
|---|---|---|---|
| `pattern` | ✓ | `profile` | coherent ≈5.5/min · extended exhale · physiological sigh. **Never 4-7-8** (§12.3) |
| `duration_s` | ✓ | `profile` | 180–600 |
| `register` | ✓ | `default` | always `settling` |

Nothing is asked because nothing needs asking. This template exists to be reachable in one
tap at 2am, and any question added to it defeats its purpose.

---

## B · Anchored place

*Safe place* — **depth 0 after the establishing session.**

| Slot | Req | Source | Notes |
|---|---|---|---|
| `place_id` | ✓ | `memory` | |
| `established_details[]` | ✓ | `memory` | **Additive only. Never contradicted, never re-described as new.** |
| `new_detail` | ✓ | `model` | exactly one per visit, must not conflict with the above |
| `anchor` | ✓ | `memory` | the gesture or phrase already tied to this place |
| `visit_number` | ✓ | `memory` | pacing shortens as it rises — arrival gets faster each visit |

### The establishing session is different

First visit only, and the **only** time the system asks about the place:

> *"Somewhere you've actually been, or somewhere that doesn't exist?"*
> *"Indoors or outdoors?"*
> *"Is anyone there?"*

**Never generated from scratch** (`SPEC.md` §8). The user supplies the place; the system
only elaborates within what it was given. This is the one hard prohibition in the slot
system.

---

## C · Rehearsal

*Interview · Competition · Hard conversation · Confidence* — **depth 2.**

| Slot | Req | Source | Notes |
|---|---|---|---|
| `event` | ✓ | `talk` | what is actually happening |
| `dreaded_moment` | ✓ | `talk` | **the highest-value slot in the product** |
| `setting` | ✓ | `talk` / `amplify` | sensation only — never furnished (§4) |
| `audience` | — | `amplify` | who is present, and whether the listener wants them there |
| `difficulty` | ✓ | `model` | derived from `dreaded_moment`; feeds `difficulty_and_response` |
| `desired_response` | ✓ | `model` | the adaptive action taken when it gets hard |
| `outcome_frame` | ✓ | `amplify` | `succeed` · `recover_from_setback` |
| `anchor_action` | ✓ | `model` | must be **performable in the real situation** |
| `duration_s` | ✓ | `memory` | |

### Why this one gets a conversation

`dreaded_moment` cannot be asked cold. *"What are you dreading?"* asked from a blank screen
gets "the whole thing." Asked after two turns of conversation it gets *"the walk off, not
the miss"* — which is the entire session.

### `outcome_frame` is a session preference, never standing

Both values are legitimate and the same user will want each at different times.
Rehearsing a setback and recovering is real mental training; so is rehearsing a clean
execution before a PR attempt. **Never promoted to profile** (`SPEC.md` §2.3.1).

When `outcome_frame = succeed`, `difficulty_and_response` relocates *inside* the success —
the lift is slow out of the bottom and is stood up anyway. The beat is never skipped.

### Question examples

> ✅ *"What's the moment you're actually dreading?"* → `dreaded_moment`
> ✅ *"Do you want to walk through it going well, or handle it going sideways?"* → `outcome_frame`
> ✅ *"Do you want the crowd, or do you want it quiet?"* → `audience`
> ❌ *"Tell me about the event."* → belongs in talk
> ❌ *"How confident are you feeling?"* → fills nothing
> ❌ *"On the walk off — do they see your face?"* → **situationally wrong.** Correct for a
> soccer scenario about being seen after a miss; meaningless at a weightlifting platform.
> Caught by gate 2 above.

---

## D · Immersive

*Nature · Adventure · Fantasy · Into sleep* — **depth 1, three questions, no conversation.**

| Slot | Req | Source | Notes |
|---|---|---|---|
| `environment` | ✓ | `model` / `memory` | model invents unless memory has a strong prior |
| `retrieval_or_construction` | ✓ | `amplify` | somewhere you've been vs. somewhere new — **changes generation strategy** |
| `realism` | ✓ | `default` by category | Nature `real` · Adventure `real` · Fantasy `invented` · Sleep `real` |
| `time_of_day` | — | `amplify` / `model` | |
| `temperature` | — | `amplify` | warm/cold is a single tap and shapes every sensory cue |
| `solitude` | — | `memory` / `model` | |
| `movement` | ✓ | `model` | what the body does — walking, climbing, sitting, drifting |
| `stillness_moment` | ✓ | `model` | the wonder beat |
| `duration_s` | ✓ | `memory` | Sleep 1800–2700, others 720–1200 |

**Environment must stay internally consistent** (`SPEC.md` §3.4). Start on a ridge, stay in
that landscape.

**Sleep overrides:** no return beat, no reorientation, sparse narration, long silences,
`ambience` may run past the final line.

### Question examples

> ✅ *"Somewhere you've been, or somewhere new?"* → `retrieval_or_construction`
> ✅ *"Warm or cold?"* → `temperature`
> ✅ *"How far from real do you want to go?"* → `realism`, Fantasy only
> ❌ *"What kind of landscape do you like?"* → the model can choose this
> ❌ *"Describe your ideal place."* → asks the user to write the session

---

## E · Reflective

*Body scan · Gratitude · Creativity* — **depth 1.**

| Slot | Req | Source | Notes |
|---|---|---|---|
| `focus` | ✓ | `default` by category | body · gratitude · creative |
| `object` | ✓ | `amplify` | body region · someone/something · the work in question |
| `direction` | — | `amplify` | Body scan: feet-up or head-down |
| `duration_s` | ✓ | `memory` | |

**No environment slot.** This template has no place in it, which is why the noticing
language of §4 carries the entire session — there is no scenery to lean on.

### Question examples

> ✅ *"Someone, or something?"* → `object`, Gratitude
> ✅ *"Start at your feet or your head?"* → `direction`, Body scan
> ❌ *"What are you grateful for?"* → that is the session, not a setup question

---

## Slots no template may have

Recorded so they don't get added later:

- **`mood_rating`** — no numeric self-assessment at entry. §10 bans engagement metrics, and
  asking someone anxious to score their anxiety is its own small harm.
- **`goal`** — outcome framing belongs in `outcome_frame`, bounded to a rehearsal. A
  general goal slot invites outcome claims (§8).
- **`music_preference`** — soundscape is atmosphere-level and not user-selected (§6.2.1).
- **`voice_per_session`** — voice is locked within an arc (§6.4).

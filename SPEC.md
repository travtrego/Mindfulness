# AI Guided Visualization Engine

**Working title — naming is open.**

An audio-first app that generates original guided visualizations tailored to what the
user needs right now. Not a meditation app: meditation is one application of a broader
visualization engine. Grounded in the mechanics of anxiety and PTSD treatment —
paced breathing, safe-place imagery, and imaginal rehearsal — without making clinical
claims.

**Evidence basis:** decisions here are grounded in `docs/research-basis.md`, which
records what the literature supports, what it contradicts, and where we are guessing.
Claims marked **design judgment** are not findings.

**North star:** every session should feel like a memory, not a story. If a user finishes
feeling as though they actually stood on a windswept ridge, or actually walked through
the interview and out the other side, the product worked.

---

## 1. Resolved decisions

These were in conflict across the three source drafts. Each is settled here, with the
reasoning, so they don't get re-litigated.

### 1.1 The breathing/grounding intro is cached — as a small matrix, not one recording

**Decision:** a matrix of pre-recorded grounding intros, selected by category, pacing,
and emotional register. Not one universal recording; not generated per session.

**Why:** the intro is the latency mask. It begins playing in ~200ms while the rest of the
session is still being written and synthesized. If it were generated, playback couldn't
start until the whole pipeline finished, and the user would stare at a dark screen
wondering if the app was broken.

The intro is also the one part of the session where the *words* matter least and the
*ritual* matters most. Familiarity is the mechanism, not a compromise.

**Matrix dimensions:** 3 pacings (slow / standard / brisk) × 3 registers (settling /
neutral / activating) × N voices. Start with 2 voices → 18 recordings.

**Every intro carries autonomy framing.** This is a safety requirement, not copy polish.
User control is central to guided-imagery practice, and imagery can evoke unplanned
emotion, memory, hyperarousal, or dissociation. Each recording establishes:

- the listener remains in control
- any detail may be altered or ignored
- **no clear visual picture is required**
- stopping or returning attention to the room is always available

> *"Nothing needs to appear perfectly. You can imagine, sense, remember, or simply know
> that the scene is there. You remain in control of the experience."*

**Eyes closed is the instruction; open is permitted, not offered as an equal.** The
literature lists eyes-open among standard autonomy provisions, but this product is built
around closed-eye immersion and the intros should say so. Permission is granted in
passing and never repeated:

> *"Let your eyes close. If you'd rather keep them open, that's fine — just find
> somewhere soft to rest them."*

One clause, once, in the intro. No mode, no setting, no toggle.

That phrasing also accommodates listeners whose imagery is emotional, spatial, auditory,
or bodily rather than visual — see §7.1.

### 1.2 Session structure is per-category, not global

**Decision:** there is no single fixed stage count. Each category has its own template
with its own beat structure. The outline stage emits fine-grained beats; the playback
state machine tracks coarse stages.

**Why:** the 4-stage and 6-stage drafts weren't really in conflict — the 6 is the 4 with
the body and close each split in two. But neither survives contact with "Just Breathing,"
which has no visualization body at all. Structure belongs to the template.

Script structure ≠ playback state machine. The outline needs finer granularity because
it drives soundscape transitions and pacing; the player doesn't need to know.

### 1.3 Input is three layers: category → amplify → memory

**Decision:** a broad category grid routes the session. Then, for categories that need it,
a short conversation followed by up to three *amplifying* questions written from what was
said. Memory from past sessions informs all of it, silently.

```
1  CATEGORY   broad set, one tap — routes to a template, nothing more
2a TALK       up to 3 turns — only for categories that need your situation
2b AMPLIFY    up to 3 questions, generated from 2a — fills the template
3  MEMORY     informs all of it, fed by end-of-session reflection
```

Depth varies by category — see §2.1. Most categories skip 2a entirely; two skip layer 2
altogether and go straight to audio.

**Why:** the source drafts all said "no menus, chatbot-style." That's right for a general
wellness audience and wrong for this one. For anxiety and PTSD, a blank text box is a
demand for articulation at exactly the moment articulation is hardest. Tapping a tile is
achievable mid-spiral; composing a sentence often isn't.

Separating the layers matters because it changes what questions are *for*. Once the
category has settled routing, follow-up questions stop being disambiguation ("which of
these did you mean?") and become amplification ("what would make this specific?").

*"What's the moment you're actually dreading?"* is the highest-value question in the
product. It turns a generic competition rehearsal into the specific thirty seconds
keeping the user awake. That question is only askable because the category already
removed the routing burden.

**Chat is layer 2a, not a replacement for layer 1.** It runs *before* the questions rather
than instead of them — which is what allows those questions to be generated rather than
pre-authored (see §2.2). Conversation surfaces detail no fixed question set would think
to ask for.

Every step in layer 2 is skippable. "Skip — surprise me" is always present.

### 1.4 Templates constrain the outline; prose stays open

**Decision:** predefined therapeutic templates govern beat count, beat durations, and arc
shape. The prose inside each beat is freely generated.

**Why:** reconciles "predefined therapeutic templates" with "the words are alive."
Reliability lives in the structure, variety lives in the language.

### 1.5 Fourteen categories on five templates

**Decision:** ship a broad category surface. Fourteen tiles in four groups, mapping onto
five beat templates.

**Why:** an earlier draft of this spec scoped V1 to four categories to limit build cost.
That was wrong reasoning. **Category count is not the cost — template count is.** A
category is a label plus a prompt constraint; a template is beat structure, pacing,
stem behavior, and validation rules.

Adding "Adventure" beside "Nature" costs one constraint (*the environment may be
invented*). Adding a sixth template costs real work.

So the surface can be broad while the engine stays small. Users shouldn't have to
translate "playoff game Saturday" into a taxonomy.

| Group | Categories |
|---|---|
| **Settle** | Just breathing · Body scan |
| **Go somewhere** | Nature · Adventure · Fantasy · Into sleep |
| **Prepare** | Interview · Competition · Hard conversation · Confidence |
| **Reflect** | Gratitude · Creativity |

Plus **Safe place**, surfaced separately as a persistent return (see 3.2), and
**"just talk to me"** as the chat entry.

Sleep still carries the worst unit economics (see 6.3) — mitigated by making sparseness
explicit in its template rather than by cutting the category.

---

## 2. Entry model

```
Home — category grid (14 tiles, 4 groups) + persistent Safe Place + "just talk to me"
  │
  ├─ DEPTH 0  →  straight to audio
  │
  ├─ DEPTH 1  →  3 generated questions  →  audio
  │
  └─ DEPTH 2  →  talk (≤3 turns)  →  3 questions written from what was said  →  audio
                    └─ "or just say it" available at every step

  → Screen goes dark → cached intro begins → rest renders underneath
  → Playback
  → Close: anchor line, then one open reflection question (skippable)
```

**There is never a loading screen.** The cached intro is the loading state.

### 2.1 The depth ladder — how many questions before audio

Depth scales with what the template actually needs. Three questions before "just
breathing" would be absurd; zero questions before a rehearsal produces a generic
run-through. **Each category declares its own depth.**

| Depth | Path | Interactions | Categories |
|---|---|---|---|
| **0** | tap → audio | **1** | Just breathing · Safe place |
| **1** | tap → 3 questions → audio | **4** | Nature · Adventure · Fantasy · Into sleep · Body scan · Gratitude · Creativity |
| **2** | tap → talk → 3 questions → audio | **~7** | Interview · Competition · Hard conversation · Confidence |

**Floor: one tap, ~2 seconds to audio.** This is the 2am case. Nothing may be added to
it — no confirmation, no "how are you feeling," no length picker.

**Ceiling: seven interactions, ~45 seconds.** A fair trade for a 14-minute rehearsal that
cannot work without knowing the user's situation. Not a fair trade for breathing.

**Hard caps: 3 chat turns, 3 amplifying questions.** If the model wants a fourth question
it does not get one — it guesses and proceeds. Interrogation is a failure state.

Only the **Rehearsal** template needs depth 2. Immersive doesn't: the system can build an
excellent rainforest knowing nothing about the user.

### 2.3 Safety boundaries are a fourth input

Alongside category, conversation, and memory, the system stores **excluded content**:
settings, topics, bodily sensations, and emotional intensity the user does not want.

This was absent from earlier drafts. It matters because **nature is not automatically
calming** — oceans, deep forests, darkness, isolation, heights, insects, and storms are
threatening to some listeners.

**Nothing is excluded by default.** Exclusions are a user-held instrument, not a content
policy applied pre-emptively. The evocative environments stay in the seed set exactly as
written — a rocky coastline in a storm and a desert under the Milky Way are among the
best things the Immersive template can build, and demoting them to opt-in would sand off
the range the product exists to cover. A listener who doesn't want storms says so once,
and never sees one again.

Exclusion axes, set at onboarding and adjustable any time:

| Axis | Options |
|---|---|
| Enclosure | enclosed · open |
| Light | daytime · nighttime |
| Company | alone · accompanied |
| Water | water · no water |
| Elevation | heights · ground level |
| Cultivation | wild · cultivated |
| Realism | realistic · fantastical |

Exclusions are **hard constraints on generation**, checked in the post-generation scan
(§8), not suggestions in a prompt.

### 2.2 Talk comes before the questions — which makes them generated

This ordering is the important part. Because the conversation happens *first*, the
amplifying questions do not have to be pre-authored per category. **The model writes them
from what the user just said.**

> — *playoff game saturday and i keep replaying last year*
> — *the walk off, not the miss*
>
> → *"Same pitch, or somewhere neutral?"* · *"On the walk off — do they see your face?"* ·
> *"How long have we got?"*

*"Do they see your face?"* only exists because the user mentioned the walk off. No fixed
per-category question set produces it.

This supersedes an earlier draft of this spec, which specified ~35 hand-written questions
(2–3 × 14 categories). That set is no longer needed. What replaces it is much smaller:
**one prompt per template** describing which slots the template needs filled, plus a few
worked examples of good and bad amplifying questions.

Depth-1 categories have no chat step, so their questions are generated from the category
plus memory alone — still not hand-authored, just working from less.

**Rules:**
- Every question is skippable; **Skip — surprise me** is always present
- Never more than 3, never a fourth
- Memory pre-fills answers where a confident prior exists, marked visually, always
  overridable
- **"Or just say it"** is always available — chips must never be the only route
- Sensitivity-flagged sessions get a check-in question here (see §8)
- Questions must be answerable in one tap. A question requiring a typed sentence belongs
  in the chat step, not here.

---

## 3. Categories and templates

Each category defines beats, durations, and which beats are cached vs. generated.

### 3.1 Just Breathing — 3–10 min

| Beat | Source | Notes |
|---|---|---|
| Settle | cached | ~30s |
| Paced breathing | parametric | 2–8 min, minimal narration |
| Return | cached | ~20s |

No visualization body. Almost entirely assembled from cached audio plus a pacing
parameter — the cheapest thing in the product and likely the highest-frequency use.
Not present in any source draft; added because it's what someone actually reaches for
at 2am.

### 3.2 Safe Place — 8–15 min

| Beat | Source | Notes |
|---|---|---|
| Grounding intro | cached | matrix selection |
| Transition | generated | bridge out of the room |
| Arrival | generated | **uses stored details, never invents them** |
| Deepening | generated | adds exactly one new sensory detail this session |
| Anchor | generated | a gesture or word tied to the place |
| Return | generated | |

**The safe place persists across sessions.** In trauma work the safe place isn't new each
time — it's the same place, accumulating detail over repeated visits, and the familiarity
*is* the therapeutic mechanism. Stored details are additive and never contradicted.

This is the "multi-session journey" concept from the source drafts, with actual grounding
behind it.

### 3.3 Rehearsal — 10–15 min

*Serves: Interview · Competition · Hard conversation · Confidence*

| Beat | Source | Notes |
|---|---|---|
| Grounding intro | cached | |
| Progressive relaxation | generated | |
| Approach | generated | the moments before, with realistic activation |
| The event | generated | begin the desired behaviour — sensory, not affirmational |
| **Obstacle & recovery** | generated | **one realistic thing goes wrong; an adaptive response follows** |
| Completion | generated | continue successfully *enough* — not flawlessly |
| Aftermath + anchor | generated | how it sits in the body; one concrete next step |

Builds confidence through rehearsal, not affirmations. No "you are confident." Instead:
the weight of the door handle, the sound of your own voice steadier than expected.

**The obstacle beat is required, and it corrects an earlier draft** which had the event
"lived through successfully." Imagining effortless perfection is less credible and less
behaviourally useful than rehearsing recovery from a small imperfection. Forced positivity
is alienating when the outcome feels unbelievable — imagery must be plausible enough to
inhabit, not an affirmation the user is required to believe.
(`docs/research-basis.md` §2.4)

The **dreaded moment** captured in layer 2 anchors the *event* beat. Without it the
session defaults to a generic run-through, which is the failure mode this template exists
to avoid.

### 3.4 Immersive — 12–20 min (Into sleep: 30–45)

*Serves: Nature · Adventure · Fantasy · Into sleep*

| Beat | Source | Notes |
|---|---|---|
| Grounding intro | cached | |
| Transition | generated | |
| Arrival | generated | |
| Movement through landscape | generated | internally consistent progression |
| Stillness | generated | the wonder beat |
| Anchor + return | generated | |

**Environments stay internally consistent.** If the listener starts hiking a ridge, the
session progresses through that landscape — it does not cut to a beach.

**Category differences are prompt constraints, not structural ones:**

| Category | Constraint |
|---|---|
| Nature | Environment must be a real, plausible place |
| Adventure | Real place, but with movement and mild stakes |
| Fantasy | Environment may be invented; physics may bend |
| Into sleep | Same beats, sparse narration, long silences, no return beat |

Seed environments: Appalachian sunrise, Pacific Northwest rainforest, Icelandic waterfall,
rocky coastline in a storm, alpine meadow after rain, desert under the Milky Way, quiet
summit, campfire beside a lake.

### 3.5 Reflective — 8–15 min

*Serves: Body scan · Gratitude · Creativity*

| Beat | Source | Notes |
|---|---|---|
| Grounding intro | cached | |
| Settling attention | generated | |
| Noticing sequence | generated | non-narrative, no environment |
| Widening | generated | |
| Anchor + return | generated | |

No place, no journey. Present-moment attention only. This template is where the
"noticing" language of the craft standard does the most work, because there is no
scenery to lean on.

---

## 3.6 Three session formats

| Format | Length | Use |
|---|---|---|
| **Reset** | 3–5 min | immediate state regulation |
| **Standard** | 10–15 min | default for regular use |
| **Deep journey** | 18–25 min | narrative, nature escape, goal rehearsal |

**10–15 minutes is the default.** Strongest practical compromise between immersion,
repeatability, and adherence. **Design judgment, not a proven optimum** — no universally
established dose exists for guided visualization. (`docs/research-basis.md` §4.2)

Every template ends with a **reorientation beat**: breath, contact with the surface,
sounds of the real room, moving hands and feet, eyes open when ready. Sessions end
**alert**, not vaguely floating — except Sleep, which has no return beat by design.

The **anchor** is a retrieval cue for later recall — a gesture, a phrase, a remembered
sound, one slower exhale. Copy must never imply the gesture has special neurological
power.

---

## 4. Craft standard

The narration standard is the actual moat. It is enforced programmatically, not hoped for.

**Rules:**
- **Name the sense, not the furniture.** Specify a sensory *channel and quality*; leave
  the *objects* to the listener. "Cooler on one side of your face" is right. "Seven grey
  stones beside a blue stream" furnishes their scene for them.
- **Guided incompleteness.** *"You may notice a path, an opening, or some other way into
  this place"* — not *"you walk down a narrow pine trail."* The listener's own scene is
  more personally relevant, easier to retrieve later, and far less likely to contain
  something unwanted. This corrects an earlier draft that pushed toward maximum concrete
  detail. (`docs/research-basis.md` §2.1)
- No generic adjectives. Banned: *breathtaking, serene, peaceful, tranquil, majestic,
  stunning, blissful.*
- One sensory detail per beat, sequenced — not stacked.
- **Vividness is never a performance demand.** Use *"notice whatever detail comes most
  easily"*, *"it may be clear, faint, or simply felt"*, *"there is no correct way for this
  to appear."* Vividness predicts relaxation, but implying failure to visualize is a
  failure of the script, not the listener.
- Sensory cues are embedded and separated by silence — never run as a checklist.
- Contrast and asymmetry over generic scene-setting: warm on one side of the face, cool
  on the other.
- "Noticing" language — *you notice, you catch, you become aware of* — rather than
  *you are in...*. Active perception, not passive narration.
- Second person, present tense, throughout.

**Enforcement — a validator, not a prompt instruction.** A ban list in a prompt will not
hold across 2,000 words. After the draft:

1. Regex the ban list
2. Check adjective density per sentence
3. Check "noticing"-verb ratio
4. Check sensory-channel variety across beats

On failure, rewrite **only the offending sentences**. Cap at 2 retries, then pass with a
log entry. Run the validator nightly against fresh generations — that's the regression
suite for craft.

### 4.1 Building the reference corpus

Before pipeline code: **hand-write 3–5 complete sessions**, one per category. Not prompts —
full scripts. These become the few-shot exemplars, and few-shot on 5 excellent examples
outperforms nearly anything else available at this stage.

Also collect a **bad-examples set** — the generic-wellness-voice failures. Contrastive
pairs ("this, not this") are unusually effective for style transfer.

Daily loop: generate 3 variants, pick the best, log the pick. That preference data
accumulates quietly and is what a fine-tune would need later, if ever.

**Skip fine-tuning for now.** It needs hundreds of examples and would lock in a style
before we know what works.

---

## 5. Generation pipeline

Three LLM calls produce the full script. TTS is then chunked and parallelized.

```
1. Intent parse    → { category, sub_intent, emotional_tone,
                       target_duration_min, sensitivity_flag }
2. Outline         → structured JSON: beats, target durations,
                     semantic transition markers, stem tags
3. Draft → sensory pass → validator → final script
```

**The critical split: LLM calls stay whole-session, TTS is chunked.**

Chunking the LLM calls destroys prose coherence across beats. Chunking TTS costs nothing.
So: three sequential LLM calls produce the complete script in ~15–25s, then the script is
segmented by beat and **all beats are synthesized in parallel**, playing in order as they
land.

The cached intro covers the LLM window. The math closes.

### 5.1 Beat durations are computed, not guessed

The outline emits **word counts and silence durations**, not timestamps. Duration falls
out of delivery rate:

| Context | Rate / duration |
|---|---|
| Ordinary guidance | 85–110 wpm |
| Scene-building passages | 65–90 wpm |
| Brief sensory pauses | 3–6 s |
| Scene transitions | 6–12 s |
| Open exploration | 15–30 s, minimal sound |

This solves the timestamp problem from the opposite direction to §6.1: the model never
estimates elapsed time, it specifies content volume, and the pipeline derives timing.

**Silence is content.** Continuous narration competes with the task the narration exists
to facilitate — listeners need processing time to construct images. Silence durations are
first-class fields in the outline schema, not gaps left over.

No peer-reviewed evidence establishes ideal wpm or pause length; these are production
standards. (`docs/research-basis.md` §5)

**Buffer floor:** never begin playback without N seconds of runway plus a live estimate
of generation rate. If the estimate degrades mid-session, extend the current beat's
trailing ambience rather than gapping.

---

## 6. Audio

### 6.1 Soundscape — semantic markers, not timestamps

**The outline must not emit timestamps.** LLM-guessed timings will not match synthesized
audio durations.

Instead, the outline emits *semantic* transitions:

```json
{ "from_beat": 3, "to_beat": 4,
  "description": "leaving the treeline, wind rises",
  "stems_out": ["forest_birds_dawn"],
  "stems_in": ["wind_ridge_moderate", "grass_movement"] }
```

After TTS returns character-level timings, markers resolve to real timestamps. Then mix.

**Stem tags are a fixed enum.** The model selects from the library; it never invents a
stem name that doesn't exist. This is the difference between a reliable system and a
constant source of missing-asset bugs.

### 6.2 Rendering

**Server-side render to a single stereo file for V1.** Simpler than client-side mixing,
one artifact per session, and it makes offline download fall out for free — which matters
for a dark-screen app used in bed and on planes.

Client-side dynamic mixing is a V2 optimization, justified only if sessions become
interactive.

### 6.2.1 Soundscape sophistication is descoped

**Decision:** atmosphere-level soundscape. Layered stems with slow crossfades between
major sections — not tightly scene-synchronised cinematic sound design.

**Why this reverses all three source drafts,** which named dynamic scene-synced sound as
the signature differentiator: there is no strong evidence that cinematic sound design,
binaural beats, frequency claims, or elaborate music independently improve guided-imagery
outcomes. It was also the most expensive item in the build.

The decisive argument is structural, not budgetary: **the soundscape must keep working
when the listener's imagined scene differs from the script** — which it always will, by
design (§4, guided incompleteness). Sound tightly synchronised to scene furniture the
listener never imagined is worse than sound that simply holds a place and a mood.

**Requirements:**
- reinforce location and emotional tone
- stay quieter than the voice
- no unexpected peaks
- limited melodic movement
- leave acoustic space
- fade, never stop abruptly

(`docs/research-basis.md` §2.2)

### 6.3 Stem library

Start at **30–40 stems** covering the Immersive and Reflective templates — those are the
only two that need environmental audio. License from a commercial library (Boom, A Sound
Effect); this is not a field-recording project.

Note the leverage: stems are needed per *template*, not per category. Nature, Adventure,
Fantasy and Into sleep all draw from the same library.

Layered and crossfaded on scene transitions. Never looping ambience.

### 6.4 Voice

TTS via ElevenLabs. Two reference registers, selected from the library by descriptor —
**not by cloning any real person** (right-of-publicity and licensing):

- **Female:** low, husky, unhurried, slight grain and audible breath, grounding
- **Male:** deep, warm, articulate, measured, quiet wry warmth

Voice is picked once at onboarding. **Voice is locked within a Safe Place or journey** —
switching narrators mid-arc is jarring and undoes the familiarity the format depends on.
Changeable between arcs.

---

## 7. Personalization

Layer 3. Memory informs both the category surface and the amplifying questions, silently.

**Stored, separately:**
- **Style memory** — pacing tolerance, sensory density, narrative style, preferred
  environments, voice. Applied silently, no prompting.
- **Content memory** — emotional topics, safe-place details, event context. **Opt-in per
  session.**

**Style travels across categories. Content does not.** The system learns you prefer
longer exhales and less visual language, and that applies on a ridge or in a tunnel. It
does not carry Tuesday's fantasy into Wednesday's match.

### 7.0 End-of-session reflection is the primary signal

**Decision:** after the anchor line, ask one open question — *"Anything you want to keep
from that?"* — answerable by voice or text, always skippable. No stars, no score.

**Why this reverses an earlier decision.** An earlier draft of this spec said: don't
build the learning loop for V1, there's no signal with zero users, and ratings break the
mood. The second half is true *during* a session. But the session is over — there is no
mood left to break, and reflection is a legitimate part of the practice rather than an
engagement mechanic bolted on.

It produces something skip-and-replay data never could: **language about what actually
landed.** Available from session one, which means personalization can ship in V1 after
all.

**Rules:**
- Never quoted back explicitly (*"last time you said…"* reads as surveillance). Folded in
  structurally — the detail that worked recurs, the register that didn't gets dropped.
- Skipping is free and unremarked. No nagging, no completion percentage.
- Reflections are content memory, and inherit its opt-in status.

**Secondary signals:** replays and repeat-similar-intent are the least confounded
behavioral signals and should be weighted highest after reflections. Completion is
confounded and its meaning is per-category — a session ended manually at minute 3 means
something very different in Just Breathing than in an Immersive session.

### 7.0.1 Sessions stand alone

Breathing one night, fantasy the next, a match the third is **normal use, not a failure
to engage.** Nothing in the product should make Wednesday depend on Tuesday.

This demotes the "multi-session journeys" concept from the source drafts. Journeys are
opt-in and scoped to **Safe Place only**, where returning to the same accumulating place
is the therapeutic mechanism. Everywhere else, every session is complete in itself.

Anything that makes sessions depend on each other is a retention mechanic wearing a
therapeutic hat, and §10 rules those out.

### 7.1 Onboarding asks three questions, once

1. **Sensory density** — accounts for aphantasia (~4% of people). This one *must* be
   explicit: it can't be learned implicitly before session one, and guessing wrong makes
   the first session actively alienating for someone who can't visualize.
2. **Voice** — the two registers.
3. **Typical session length** — a prior the system adjusts from, not a per-session picker.

Asked once, warmly, then never again.

---

## 8. Safety

Three gates, not one. The classifier is not sufficient on its own — classifiers fail.

1. **Intent classifier** sensitivity flag
2. **Deterministic keyword/pattern backstop** — string matching doesn't have a confidence
   score
3. **Post-generation script scan** — the check that catches a benign intent that generated
   something that went somewhere bad

**Routing:**

| Tier | Response |
|---|---|
| Crisis | **Do not generate.** Surface resources, offer an extended grounding-only session built from cached audio. |
| Grief / loss / trauma-adjacent | Human-reviewed templates. Tight constraints, narrow generative room. |
| Ordinary | Open generation within template. |

### 8.1 Required in every session

Meditation and imagery are commonly described as harmless. They are not universally so —
adverse experiences include anxiety, cognitive disturbance, perceptual change,
hyperarousal, and dissociation, at rates comparable to other psychological interventions.
(`docs/research-basis.md` §8)

- Warning against use while driving or performing hazardous tasks
- Immediate stop control, reachable without looking
- Permission to keep eyes open, stated once in the intro (§1.1)
- Ability to reduce voice or environmental intensity
- Content exclusions honoured (§2.3)
- Grounding option always available
- After-session distress check
- Instruction to discontinue and seek qualified support if sessions repeatedly increase
  panic, dissociation, intrusive memories, insomnia, or perceptual disturbance

**Prohibited claims:** treating, curing, reprogramming, healing trauma, altering immune
function, or replacing mental-health care.

**On the distress check vs. §10's ban on ratings.** These are different instruments. A
distress check is a safety signal with a defined escalation path; a rating is an
engagement metric. The check is single-item, appears only when a sensitivity flag was
raised or a session was abandoned early, and never becomes a score the user accumulates.

**Trauma-specific constraints:**
- **Never generate a safe place from scratch.** The user describes it; the system only
  elaborates within what they gave.
- **Always-available exit to breathing** — one tap, mid-session, drops to cached grounding
  audio. No confirmation dialog.
- Position as wellness. No clinical or treatment claims, no outcome promises.

The murky middle is real and should be treated as such: *"interview tomorrow, I lose my
house if I don't get it"* is Performance **and** distress.

---

## 9. Stack

| Layer | Choice | Rationale |
|---|---|---|
| Client | React Native + Expo | `react-native-track-player` solves background audio, lock-screen controls, and downloads |
| API | Vercel | generation routes, job orchestration |
| Data / auth / storage | Supabase | Postgres, auth, rendered audio in storage |
| LLM | Claude | 3-call pipeline |
| TTS | ElevenLabs | character-level timings needed for the mix |

### 9.1 Data model sketch

```
users
style_memory      -- auto-applied, silent
content_memory    -- opt-in per session
safe_places       -- persistent details, additive only
sessions          -- script, audio ref, template, outcome signals
journeys          -- multi-session arcs
stems             -- tag enum, license, file ref
intent_log        -- includes out-of-scope categories → V2 roadmap
```

---

## 10. Product principles

- Audio-first. The screen goes dark and stays dark during playback.
- **Eyes closed is the design centre.** Permission to keep them open is granted once in
  the intro (§1.1) and never built into the interface. There is no eyes-open mode, no
  toggle, and no alternate visual state — adding one would trade the product's core
  premise for an affordance almost nobody would use.
- **The app is dark-only.** Not a theme option — a product about reducing screen time and
  used mostly at night has no business being bright.
- Minimal UI. Interface exists for *selection*, not during playback.
- **No streaks, badges, gamification, or engagement mechanics.** Missing three days is not
  a failure state and the app will never say it is.
- Reduce screen time rather than compete for it.
- Sessions should feel handcrafted even though they're generated.

---

## 11. V1 scope

**In:**
- Fourteen categories on five templates
- Three-layer input: category → amplify → memory
- Amplifying questions per category, all skippable
- Chat as an alternate layer-2 route
- End-of-session reflection capture
- Style/content memory split, applied silently
- 3-call generation pipeline with parallel TTS
- Cached intro matrix
- Server-rendered soundscape mixing
- Safe Place persistence
- Onboarding (3 questions)
- Three-gate safety routing
- Offline download
- Full signal logging

**Out (deliberately):**
- Client-side dynamic mixing
- Fine-tuning
- Multi-session journeys outside Safe Place
- Any social, streak, or engagement layer

---

## 11.1 The premise: adaptation, not a library

**Decision:** sessions are generated and adapted to the user. There is no fixed library,
and building one is not a fallback we are holding in reserve.

**On the VR evidence.** A 2026 RCT found AI-generated VR renderings of a safe place did
not outperform ordinary eyes-closed imagery. That finding is about **replacing internal
imagery with external scenery** — the opposite of what this product does. We are not
building VR, not rendering environments, and not asking anyone to look at anything. The
result doesn't transfer, and it is recorded in `docs/research-basis.md` §3 as context
rather than as a challenge to the architecture.

**What actually supports adaptation:**

- **Vividness predicts relaxation** across every arm of that same trial. Anything that
  raises vividness is working on the mechanism the evidence identifies — and imagery
  built from a listener's own words, place, and dreaded moment is more vivid than imagery
  built for a generic listener.
- **Personally meaningful imagery** is more relevant, more emotionally engaging, and
  easier to retrieve later. Personalization carries moderate support in its own right.
- **Repetition beats single exposure** — which a fixed library actively undermines, since
  the fourth hearing of the same script is a recording, not an experience.
- **Imagery ability varies** (§7.1). A fixed library must pick one sensory register and
  alienate everyone outside it. Adaptation is the only way to serve an aphantasic
  listener and a vivid visualizer from the same product.

**What is honestly unknown:** clinical efficacy evidence for AI-generated scripts is
sparse — it is an early field, not a refuted one. `docs/research-basis.md` keeps that in
the "still uncertain" tier, alongside session length, narration rate, and music.

**How we resolve it: by measuring, not by hedging the architecture.** The question worth
instrumenting is not *generated vs. fixed* but **does adaptation compound** — do
reflections, style memory, and accumulated safe-place detail produce better sessions at
month three than at week one. If the answer is yes, the premise is doing real work. That
is measurable from the reflection data we already collect (§7.0), and it needs no
alternate product built alongside it.

---

## 12. Open questions

1. **Name.** Unresolved.
2. **Cached intro matrix — recorded by whom?** Voice actor vs. high-quality TTS render.
   TTS is cheaper and consistent with generated beats; a real actor is better and makes
   the ritual anchor genuinely distinct. Leaning actor, since it's ~18 short recordings.
3. **Just Breathing pacing patterns** — **4-7-8 is out for anxiety contexts.** Breath
   holding is contraindicated, and forced deep breathing can make anxious users
   light-headed or more body-conscious. Remaining candidates: coherent breathing
   (~5.5/min), extended exhale, physiological sigh. Framing throughout is *"allow the
   breath to become slightly slower and easier, without forcing it"* — never an
   instruction to breathe deeply. (`docs/research-basis.md` §2.6)
4. **Sensitivity review capacity** — who reviews the trauma-tier templates, and what does
   the coverage matrix look like before launch.
5. **Session length vs. cost ceiling** — need a real cost-per-session number for a 15-minute
   Immersive session before committing to durations.
6. **Slot definitions per template** — replaced the ~35 hand-written questions. Each
   template needs a description of which slots it requires filled, plus worked examples of
   good and bad amplifying questions. Five of these, not thirty-five.
7. **Reflection → memory extraction** — what actually gets pulled from a free-text
   reflection, and how it's weighted against behavioral signal. Needs a schema before the
   loop is wired.

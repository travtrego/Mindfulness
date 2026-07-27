# AI Guided Visualization Engine

**Working title — naming is open.**

An audio-first app that generates original guided visualizations tailored to what the
user needs right now. Not a meditation app: meditation is one application of a broader
visualization engine. Grounded in the mechanics of anxiety and PTSD treatment —
paced breathing, safe-place imagery, and imaginal rehearsal — without making clinical
claims.

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

**Decision:** a broad category grid routes the session. Category-specific *amplifying*
questions (or a free-form chat, user's choice) then fill in the specifics. Memory from
past sessions informs both, silently.

```
1  CATEGORY   broad set, one tap — routes to a template, nothing more
2  AMPLIFY    questions off that category, or just talk — fills the template
3  MEMORY     past sessions inform both, fed by end-of-session reflection
```

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

**Chat is layer 2, not a replacement for layer 1.** Some users would rather talk than
tap, and conversation surfaces detail no fixed question set would think to ask for. It
fills the same template slots by another route.

All amplifying questions are skippable. "Skip — surprise me" is always present.

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
| Approach | generated | the moments before |
| The event | generated | lived through successfully — sensory, not affirmational |
| Aftermath | generated | walking out, how it sits in the body |
| Anchor + return | generated | |

Builds confidence through rehearsal, not affirmations. No "you are confident." Instead:
the weight of the door handle, the sound of your own voice steadier than expected.

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

## 4. Craft standard

The narration standard is the actual moat. It is enforced programmatically, not hoped for.

**Rules:**
- Sensory specificity over adjective-stacking. Banned: *breathtaking, serene, peaceful,
  tranquil, majestic, stunning, blissful.*
- One sensory detail per beat, sequenced — not stacked.
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

## 12. Open questions

1. **Name.** Unresolved.
2. **Cached intro matrix — recorded by whom?** Voice actor vs. high-quality TTS render.
   TTS is cheaper and consistent with generated beats; a real actor is better and makes
   the ritual anchor genuinely distinct. Leaning actor, since it's ~18 short recordings.
3. **Just Breathing pacing patterns** — which protocols to ship (4-7-8, box, physiological
   sigh, coherent 5.5). Probably 3, with the default set at onboarding.
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

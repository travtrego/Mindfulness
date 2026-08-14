# Handoff

For an agent picking this up cold. Read `README.md` for how to run things and `SPEC.md` for
why the product is shaped this way. This file is the state of play: what exists, what is
decided, what is blocked, and what not to re-litigate.

---

## What this is

An audio-first app that **generates original guided visualizations** tailored to what the
user needs right now. Grounded in the mechanics of the owner's own anxiety/PTSD treatment —
paced breathing, safe-place imagery, imaginal rehearsal — without clinical claims.

**Not a meditation app.** Meditation is one application of a broader visualization engine.
The owner is explicit about this and it shapes scope: rehearsal for a competition and a
fantasy landscape are the same machine.

> **North star: every session should feel like a memory, not a story.**

Working title only. Naming is still open (`SPEC.md` §12.1).

---

## Where things stand

**End-to-end browser MVP: built and deployed.** Intake reaches the generator, every category
returns a complete playable session, narration uses the browser's installed speech voice,
and pause/resume, ±15-second seek, early exit, breathing-only escape, and reflection work in
the player. Onboarding preferences and category-scoped reflections persist on the device and
inform later generation. The real-model prose still needs an owner listening test.

| Area | State |
|---|---|
| Spec | Settled. Conflicts resolved with rationale recorded |
| Six templates | Built as data, all shares sum to 1 |
| Six reference sessions | Hand-written, all 19 beat roles covered |
| Craft validator | Calibrated against the references |
| Outline schema | Validated against real pipeline output, all templates |
| Generator | Live-wired: streaming, adaptive thinking, cached system prompt, cost tracking |
| App | Intake, generation, narrated player, controls, emergency exit, reflection |
| Audio | Browser Web Speech API; production voice is a later quality upgrade |
| Deployment | Vercel on the repository's active branch |
| Persistence | Device-local preferences/reflections; accounts and database still pending |

Branch: `claude/hello-j0yf74`. 32 commits. Everything pushed.

---

## The remaining generation blocker

**There is no `ANTHROPIC_API_KEY` anywhere.** The owner has one but is working from a phone,
and the cloud environment's env-var field warns in plain text that values are visible to
anyone using the environment — which disqualifies it for a live billing credential. The key
needs a laptop.

Until then the live generator runs dry. The app now falls back to the validated hand-written
session for the selected template, so the experience remains complete and narrated; it is
just not newly personalized prose.

**Do not work around this by putting a key in the environment variables.** That was
considered and rejected for the reason above.

---

## The one test that matters

```bash
python3 -m generator.cli "final clean and jerk at a meet saturday" \
        --category competition --out docs/sessions/gen-01.md
```

Then read `gen-01.md` out loud beside `docs/sessions/01-clean-and-jerk.md` and see whether
you can tell which is which. `--out` writes generated sessions in the *exact* format of the
hand-written ones for precisely this comparison.

The owner is the judge. They wrote the reference material, they read it aloud, and they
caught the one thing automated checks could not: an early intro draft that "sounds very like
ai wrote it." Their ear is the acceptance test, not the validators.

Everything downstream — TTS, deployment, more templates — waits on that answer.

---

## Architecture in one page

### Input model (`SPEC.md` §1.3)

```
1  CATEGORY   broad grid, one tap - routes to a template, nothing more
2a TALK       up to 3 turns - only for categories that need your situation
2b AMPLIFY    up to 3 questions, generated FROM 2a - fills the template
3  MEMORY     informs all of it, fed by end-of-session reflection
```

**Depth is a floor, not a ceiling.** The template sets the minimum; the user can always say
more, and saying more means *fewer* questions.

| Depth | Path | Interactions |
|---|---|---|
| 0 | tap → audio | 1 |
| 1 | tap → 3 questions → audio | 4 |
| 2 | tap → talk → 3 questions → audio | ~7 |

The floor is one tap and about two seconds. That is **the 2am case** and nothing may be
added to it.

### Fourteen categories, six templates

Category count is not the build cost; template count is. Adding a category is one line.

| Template | Depth | Serves | Aims at |
|---|---|---|---|
| `breath_only` | 0 | just_breathing | regulation, no narrative |
| `anchored_place` | 0 | safe_place | familiarity, accumulating detail |
| `rehearsal` | 2 | interview, competition, hard_conversation, confidence | competence |
| `immersive` | 1 | nature, adventure, fantasy, into_sleep | wonder, being somewhere |
| `reflective` | 1 | body_scan, gratitude, creativity | presence |
| `reentry` | 2 | going_back | the unremarkable |

### Pipeline

```
intent -> questions -> outline -> draft per beat -> craft gate -> targeted rewrite
```

Three calls plus one per beat, ~10-12 total. **LLM-whole, TTS-chunked**: chunking LLM calls
destroys coherence, chunking TTS is free.

The **cached intro is a latency mask** — it starts in ~200ms while the rest generates, which
is why there is no loading state anywhere in the product.

### Files

| Path | What |
|---|---|
| `generator/templates.py` | Six templates as data, beat budget allocator, silence planner |
| `generator/prompts.py` | Four prompts + craft rules + exemplar loader |
| `generator/pipeline.py` | Orchestration, live client, outline reconciler, usage/cost |
| `generator/craft.py` | Post-draft validator — the programmatic craft gate |
| `generator/intros.py` | The 12 cached-intro durations |
| `generator/api.py` | What the app calls: `talk()`, `questions()`, and `generate_session()` |
| `generator/cli.py` | CLI, `--estimate`, session-doc writer |
| `docs/sessions/00-06` | Intro matrix + six hand-written reference sessions |
| `docs/schema/outline.schema.json` | The outline contract |
| `docs/templates/slots.md` | What each template needs filled, and question quality gates |
| `docs/app.html` | The app |
| `docs/prototype.html` | Same flow, annotated as a design document |

---

## Decisions already made — do not re-open without the owner

These were argued through. Several reverse an obvious-seeming default.

- **Result claims are allowed and encouraged.** Rehearsing a successful outcome *is* the
  intervention. Mechanism claims ("this rewires your brain") are banned. The owner corrected
  an earlier draft that conflated the two.
- **Eyes closed is the design centre.** An eyes-open mode was proposed from the literature
  and cut. Offer "you may," do not build the mode.
- **No fixed library.** Sessions are generated. The owner rejected a
  generated-vs-fixed-library split outright.
- **Dark during playback, interface during selection.**
- **No `mood_rating`, `goal`, `music_preference`, or `voice_per_session` slot.** Never ask
  how someone wants to feel.
- **Soundscape is descoped** (`SPEC.md` §6.2.1). Unevidenced, expensive, and it must keep
  working when the listener's imagined scene differs from the script — which it always does.
- **Three exclusion tiers by lifetime**: global prohibition / standing / session-only. A
  session preference is *never* promoted to the profile.
- **The craft standard is a programmatic gate**, not a prompt instruction. A ban list inside
  a prompt does not hold across 2,000 words.
- **`word_target` is a guide; total runtime is the gate** (§5.2). On drift, trim words —
  **never raise wpm**.
- **The app is dark-only** by product decision, not by oversight.

### The craft standard, compressed

Full version in `SPEC.md` §4 and enforced in `generator/craft.py`.

- **Name the sense, not the furniture.** "The bar is colder than the room," not "a narrow
  pine trail with seven grey stones."
- **Guided incompleteness.** "A path, an opening, or some other way in" — the listener's own
  scene is more relevant, easier to recall, and far less likely to contain something they
  did not want.
- **One sensory detail per beat, sequenced. Never stacked.**
- **Contrast and asymmetry.** Warm on one side of the face, cool on the other.
- **Noticing language.** Drop to plain declarative only at a climax, deliberately.
- **Second person, present tense, always.**

---

## Findings that cost real work to discover

Written down so nobody re-derives them.

1. **Four intro scripts, not eighteen.** Pacing is a delivery parameter — words per minute
   plus a silence multiplier — so only *register* changes the words. 24 recordings, not 54.
2. **The re-entry template exists** because writing session 02 proved the feared moment is
   *not* the climax. `continuation` must outlast `the_moment`, and that is enforced
   structurally (its share is larger) and in `validate_outline.py`.
3. **`paced_breathing` must withdraw.** A flat silence split gave it 130 words; written
   honestly it is 85. 130 is enough to narrate every cycle to the end, which is the one
   thing a breath beat must not do.
4. **`reflective` and `immersive` share role names and mean different things by them.**
   `meaningful_experience` is movement through a landscape in one and a noticing sequence in
   the other. Exemplars are matched on template *and* role for this reason.
5. **Semantic soundscape markers, not timestamps.** The model cannot estimate elapsed time;
   markers resolve against real TTS character timings.
6. **Every bug found in the audit lived in a path nothing had executed.** The happy path was
   tested; the ways a model actually misbehaves were not.

---

## Checks — run all of these before claiming anything works

```bash
python3 scripts/check_craft.py            # validator vs the six hand-written sessions
python3 scripts/check_intros.py           # intro scripts + the duration table agree
python3 scripts/session_stats.py          # measured runtimes + template shares sum to 1
python3 scripts/smoke_live_path.py        # whole live path, fake model, no spend
python3 scripts/test_bad_outlines.py      # 10 malformed outlines, none may crash a run
python3 scripts/test_bad_model_output.py  # bad JSON, bad intent, empty drafts
python3 scripts/check_pipeline_schema.py  # every template's real output vs the schema
python3 scripts/validate_outline.py docs/schema/example-01-clean-and-jerk.json
```

All eight pass as of the last commit. **If a change makes `check_craft.py` fail the
reference sessions, the change is wrong — not the sessions.**

Two rules that have repeatedly saved work:

- **Never estimate a word count or a runtime.** Every hand-estimate so far has been wrong.
  Run `session_stats.py`.
- **When two places hold the same number, add the check that compares them.** Every drift
  bug found so far was two copies of a number that nothing was comparing.

---

## Costs

Measured from real prompt sizes, `claude-opus-5` at $5/$25 per 1M.

| Template | Per run |
|---|---|
| `breath_only` | ~$0.08 |
| `reflective` / `anchored_place` | ~$0.11 |
| `rehearsal` | ~$0.12 |
| `immersive`, long | ~$0.15 |

`--estimate` projects a run without making one. Every live run prints what it actually cost.
At 1,000 sessions/day that is ~$3,900/mo in Claude alone, so a $10/mo subscriber doing a
session a day costs about $4/mo — real margin, but not infinite, and it collapses if
sessions get longer.

Levers, in order of size: **prompt caching** (~20%, the craft rules are already in a cached
system block), **model split** for the intent/question calls (drafting stays on Opus —
that is where the product lives), **Batch API at 50%** if journey pre-generation ever
happens.

A 15-minute session is **~4,100 characters** of speech, not the ~12,000 a normal 15 minutes
would imply — sessions run 39-55% silence at slow narration rates. TTS is cheaper than it
looks. Price it against live ElevenLabs rates when buying; do not quote from memory.

---

## Short term, in order

1. **Get a key onto a laptop and generate one session.** Nothing else is worth doing first.
2. **Read it out loud beside session 01.** Better, worse, or close.
3. If close: TTS. Script → parallel synthesis → soundscape markers resolved against
   character timings → mixed render.
4. If not close: the fix is prompts and exemplars, not architecture. The pipeline shape is
   proven; the writing is not.

## Longer term

- **Memory.** End-of-session reflection feeds the profile, which informs every later
  session. The `anchored_place` template is the visible case: the same place, one new detail
  per visit, arrival getting shorter as the visit count rises. Nothing is built yet.
- **Voice.** 24 short cached recordings. Leaning voice actor over TTS — it is a single
  session's work and it is the ritual anchor of the product (`SPEC.md` §12.2). Open.
- **Naming.** Unresolved (§12.1).
- **Stack when it leaves local**: React Native + Expo, Vercel, Supabase, Claude, ElevenLabs.
- **The adaptation premise** (§11.1) is the thing that has to be true for any of this to
  matter: that a session shaped to *this* person, *this* week, beats a good recording of a
  generic one. It is unproven. The reference sessions are the argument; a real listener is
  the evidence.

---

## How to work with the owner

- They asked for **bite-size, step by step** when instructions got long. Honour that.
- They gave standing permission to act without asking: *"you dont need to ask permission to
  allow action just do it. I trust you."* Use it — but surface real problems plainly.
- They are the guinea pig and the source of session material. Session 01 is their actual
  weightlifting meet; 02 is their actual return to work after treatment. Treat that material
  with care.
- When they push back, they are usually right about the product and worth arguing with about
  the code.

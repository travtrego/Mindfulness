# Research basis

Evidence synthesis underlying the decisions in `SPEC.md`. Literature through July 2026,
concentrated on 2021–2026.

**How to read this:** each section states what the evidence supports, what it contradicts
in earlier drafts of our spec, and what remains unknown. Where the spec makes a call the
evidence doesn't settle, that is labelled as a **design judgment**, not a finding.

---

## 1. Confidence tiers

### Relatively strong support

- Guided imagery reduces short-term anxiety and distress
- Recorded audio is a viable delivery format, including self-administered via headphones
- A short relaxation induction before the scene is useful
- Sensory (not merely visual) imagery is central
- Nature scenes can be beneficial; nature imagery reduced state anxiety more than urban
- Repetition is more useful than single exposure
- User control and safety framing matter

### Moderate / emerging

- Personalization
- Process-based future imagery
- Dynamic (moving) imagery over static scenes
- Imagery anchors used outside the session
- Combining imagery with brief breathing or muscle release
- Tailoring to imagery ability

### Still uncertain — we are guessing

- Ideal session length
- Ideal narration speed
- Ideal pause duration
- Whether music improves outcomes
- **Whether cinematic sound design improves outcomes**
- **Whether AI personalization improves outcomes**
- Whether VR is superior
- Whether biometric adaptation improves outcomes
- Best frequency for ordinary users
- Whether one standardized scene works across cultures

---

## 2. Corrections to earlier spec drafts

These contradict decisions made before this synthesis. Each has been applied.

### 2.1 Guided incompleteness beats sensory specificity

**Earlier position:** maximize concrete sensory detail — *"the water's the colour of slate,
and the light coming off it catches the underside of your jaw."*

**Evidence:** over-specification is identified as a common scriptwriting mistake. The
listener's own scene is more personally relevant, easier to retrieve later, and less
likely to contain an unwanted detail.

> Better: *"You may notice a path, an opening, or some other way into this place."*
> Worse: *"You walk down a narrow pine trail with seven gray stones beside a blue stream."*

**Applied as:** *name the sense, not the furniture.* Specifying a sensory **channel and
quality** is good; specifying **scene objects** is not. "Cooler on one side of your face"
leaves the source to the listener. The ban on generic adjectives is unaffected.

### 2.2 Soundscape sophistication is unevidenced

**Earlier position:** layered cinematic soundscapes with scene-synced stem crossfades were
described as the signature differentiator across all three source drafts.

**Evidence:** no strong evidence that cinematic sound design, binaural beats, frequency
claims, or elaborate music independently improve guided-imagery outcomes. Further, the
soundscape *should continue to work when the user's imagined scene differs from the
script* — which argues against tight scene-synchronisation.

**Applied as:** soundscape descoped to atmosphere-level support. See `SPEC.md` §6.

### 2.3 Autonomy framing was absent

**Earlier position:** grounding intros contained no permission language.

**Evidence:** user control is central to guided-imagery practice. Imagery can evoke
unplanned emotion, memory, hyperarousal, or dissociation. Clinical guidance recommends
particular caution for unresolved trauma, psychosis, hallucinations, or delusions.

**Applied as:** every intro carries autonomy framing. See `SPEC.md` §1.1 and §8.

### 2.4 Rehearsal should not visualize flawless success

**Earlier position:** the event beat was "lived through successfully."

**Evidence:** effective goal visualization includes approaching the situation, noticing
realistic discomfort, choosing an adaptive response, **recovering from a small
imperfection**, and completing or progressing. Forced positivity can be alienating,
particularly when the outcome feels unbelievable. Imagery should be plausible enough to
inhabit, not an affirmation the user must believe.

**Applied as:** an obstacle-and-recovery beat added to the Rehearsal template.

### 2.5 Nature is not automatically safe

**Evidence:** oceans, deep forests, darkness, isolation, heights, insects, and storms can
be threatening rather than restorative.

**Applied as:** content exclusions promoted to a first-class input — **user-held, empty by
default.** No environment is pre-emptively demoted. The evocative seed environments
(*rocky coastline in a storm*, *desert under the Milky Way*) stay in the default set:
they are among the best things the Immersive template can build, and excluding them
pre-emptively would sand off the range the product exists to cover. A listener who
doesn't want storms says so once.

### 2.6 Breath holding is contraindicated for anxiety

**Evidence:** forced deep breathing can make anxious users light-headed or more
body-conscious. For anxiety regulation specifically: avoid breath holding.

> *"Allow the breath to become slightly slower and easier, without forcing it."*

**Applied as:** 4-7-8 removed from the candidate protocol set for anxiety contexts.
Coherent breathing (~5.5/min) and extended-exhale patterns retained.

### 2.7 Eyes-open permission, not an eyes-open mode

**Evidence:** eyes-open is listed as a standard autonomy provision.

**Applied as:** one clause in the intro — *"let your eyes close; if you'd rather keep them
open, that's fine"* — and nothing else. **No mode, setting, or toggle.**

This deliberately takes less than the literature offers. Eyes-closed immersion is the
product's design centre, and building a parallel visual state would trade that premise
for an affordance almost nobody would use. The autonomy requirement is satisfied by the
permission; the emphasis stays on closed. (Product decision, `SPEC.md` §1.1, §10.)

---

## 3. On the VR findings

The 2026 JMIR AI randomized controlled trial compared three minutes of traditional
eyes-closed safe-place imagery against three minutes inside an **AI-generated VR version
of the same safe place**, after a 12-minute personalized safe-place construction exercise.

**Both conditions improved relaxation substantially. VR was not superior. Match and
satisfaction with the AI-generated environment did not predict greater relaxation.
Imagery vividness predicted relaxation across both groups.**

**This does not transfer to our architecture.** The trial tested *replacing internal
imagery with external scenery*. We generate **narration**, not environments — nothing is
rendered and nobody looks at anything. Recorded here as context, not as a challenge to
the premise.

**The transferable finding is the vividness result**, and it argues *for* adaptation:
vividness predicted relaxation in both arms, and imagery built from a listener's own
words, place, and dreaded moment is more vivid than imagery built for a generic listener.
See `SPEC.md` §11.1.

**What remains genuinely uncertain** is clinical efficacy evidence for AI-generated
scripts, which is sparse — early field, not refuted one. Held in §1's "still uncertain"
tier alongside session length, narration rate, and music.

## 4. Session architecture

The sequence supported by converging evidence:

```
orientation and permission
  → physiological settling
    → construction of a personally meaningful scene
      → multisensory exploration
        → emotionally meaningful action or experience
          → consolidation
            → gradual return and grounding
```

No universally accepted script structure, session length, narration rate, or practice
schedule exists. Recent systematic reviews repeatedly identify substantial heterogeneity.
What follows is **conservative design inference**.

### 4.1 Reference 15-minute architecture

| Time | Beat | Content |
|---|---|---|
| 0:00–0:45 | Orientation & autonomy | safe location, eyes open or closed, every detail optional, may stop |
| 0:45–2:30 | Physiological transition | points of contact, jaw/shoulders/hands, 2–3 slower breaths, stay partly connected to the room |
| 2:30–4:00 | Entry threshold | path, doorway, shoreline, clearing; user determines much of the appearance |
| 4:00–7:00 | Establish the world | space, light, sound, temperature, body position, scent only where natural |
| 7:00–10:30 | Meaningful experience | restoration *or* goal rehearsal with obstacle and recovery |
| 10:30–12:30 | Emotional consolidation | what changed internally; name the felt quality |
| 12:30–13:30 | Retrieval cue | gesture, phrase, remembered sound, or one slower exhale |
| 13:30–15:00 | Reorientation | breath, contact, real room sounds, move hands and feet, end **alert** |

The retrieval cue is an **anchor for later recall**, not a claim that the gesture has
special neurological power. Copy must not imply otherwise.

### 4.2 Three formats

| Format | Length | Use |
|---|---|---|
| **Reset** | 3–5 min | immediate state regulation |
| **Standard** | 10–15 min | default for regular use |
| **Deep journey** | 18–25 min | narrative, nature escape, goal rehearsal |

10–15 minutes is the strongest practical compromise between immersion, repeatability, and
adherence. **This is an implementation judgment, not a proven physiological optimum.**

Evidence points sampled: a 3-minute imagery period following 12-minute safe-place
construction; ~20-minute nature-based guided imagery; multi-session programs combining
imagery with muscle relaxation; repeated audio sessions across weeks in medical
populations.

A 2025 Bayesian meta-analysis of 24 RCTs (1,294 athletes) estimated ~45 minutes weekly
over ~100 days for favourable mental-health outcomes — **preliminary, heterogeneous,
publication-bias affected, and specific to athletes.** Not a consumer dose.

---

## 5. Narration rate and silence

Continuous narration competes with the task the narration exists to facilitate. Listeners
need processing time to construct images.

**No peer-reviewed evidence establishes ideal words-per-minute or pause duration. This is
a genuine research gap.** The following are production standards derived from cognitive
load and common intervention structures:

| Context | Rate / duration |
|---|---|
| Ordinary guidance | 85–110 wpm |
| Scene-building passages | 65–90 wpm |
| Brief sensory pauses | 3–6 s |
| Important scene transitions | 6–12 s |
| Open exploration | 15–30 s, minimal sound |

**Engineering value:** these make beat durations *computable* from word count rather than
guessed by the model. See `SPEC.md` §5.

---

## 6. Per-type structural guidance

| Type | Goal | Do | Avoid |
|---|---|---|---|
| **Nature escape** | restoration, awe, refuge | environmental sound, discovery, unstructured time | turning every scene into a lesson |
| **Anxiety regulation** | reduce activation, preserve orientation | shorter sessions, steady cues, predictable transitions, less silence, easy exit | breath holding, darkness, entrapment, loss-of-control language |
| **Sleep** | reduce effort, diffuse attention | slower pace, fewer instructions, gentle repetition, minimal plot | energetic return; requiring the user to reach the end |
| **Performance / conversation** | rehearsal and confidence | first-person process imagery, specific actions, coping with disruption, completion, concrete next step | flawless success |
| **Fantasy** | exploration, wonder, play | symbolism, transformation, user agency | presenting generated symbolism as psychological diagnosis or hidden truth |
| **Trauma stabilization** | present-moment safety, **not processing** | choice, external orientation, neutral detail, short duration, frequent control reminders | reliving events, confronting perpetrators, retrieving memories, interpreting imagery as fact |

---

## 7. Vividness

Imagery vividness is repeatedly associated with stronger emotional and relaxation effects.
A 2024 insomnia study found most participants benefited regardless of imagery ability,
though weaker visualizers improved more slowly.

**But vividness must never become a performance demand.** Preferred phrasing:

- *"Notice whatever detail comes most easily."*
- *"Allow the scene to become a little more tangible."*
- *"It may be clear, faint, or simply felt."*
- *"There is no correct way for this to appear."*

### 7.1 Aphantasia

A 2024 systematic review describes aphantasia as a meaningful spectrum of reduced or
absent voluntary visual imagery. Affected people retain conceptual, spatial, semantic,
emotional, and other sensory imagination — but heavily visual exercises feel ineffective
or frustrating.

> *"You do not need to see it. You might sense its space, remember what it would feel
> like, hear it, or simply understand where you are."*

This confirms and sharpens the onboarding sensory-density question.

---

## 8. Safety

Meditation and imagery are frequently described as harmless. They are not universally so.

A systematic review found adverse meditation experiences including anxiety, depression,
cognitive disturbance, and perceptual changes, with prevalence estimates varying
substantially by study design. A detailed study of mindfulness-program participants found
transient distress and negative functional effects at rates comparable to other
psychological interventions, with **hyperarousal and dissociative experiences** among the
concerns.

**Required in every session:**

- Warning against use while driving or performing hazardous tasks
- Immediate stop control
- Eyes-open mode
- Ability to reduce voice or environmental intensity
- Content exclusions
- Grounding option
- After-session distress check
- Instruction to discontinue and seek qualified support if sessions repeatedly increase
  panic, dissociation, intrusive memories, insomnia, or perceptual disturbance

**Prohibited claims:** treating, curing, reprogramming, healing trauma, altering immune
function, or replacing mental-health care.

---

## 9. Technology assessment

| Technology | Verdict |
|---|---|
| **Personalization** | Promising. Improves relevance and ownership. Supported by functional imagery and safe-place work. |
| **Virtual reality** | Potentially useful for people who struggle with internal imagery. **Not consistently better** than ordinary guided imagery. |
| **AI-generated scenery** | **Unproven as an enhancer.** Did not outperform traditional imagery in the 2026 RCT. |
| **AI-generated scripts** | Potentially valuable for relevance, accessibility, variety. **Safety and efficacy evidence sparse.** Use constrained templates, exclusion rules, conservative claims, predefined grounding. |
| **Biofeedback** | Theoretically useful. Session must work without sensors. Evidence does not support making biometrics the arbiter of correct practice. |

The guidance on AI scripts — *constrained templates, excluded-content rules, conservative
claims, and predefined grounding sequences rather than unrestricted generation* — is a
direct endorsement of `SPEC.md` §1.4.

---

## 10. Recommended input model

The synthesis proposes generating from five inputs:

1. **Intent** — escape, regulate, rehearse, motivate, sleep, recover, explore
2. **Desired state** — calm, confidence, courage, connection, awe, focus
3. **World preferences** — nature type, realism, weather, light, solitude, movement
4. **Guidance preferences** — voice density, sensory intensity, duration, directness
5. **Safety boundaries** — excluded settings, topics, bodily sensations, memories,
   emotional intensity

Our three-layer model covers 1–4. **Input 5 was missing** and is now added — see
`SPEC.md` §2.3.

The principle to preserve: *the same validated backbone with a changing narrative world.*
Personalization must not extend to letting the model improvise clinical structure or
safety rules.

---

## 11. Key papers

| Paper | Year | Relevance |
|---|---|---|
| AI-Generated Personalized Visualization of the Safe Place in VR vs Traditional Safe Place Imagery (RCT), *JMIR AI* | 2026 | Traditional imagery ≈ AI-generated VR; vividness predicted relaxation |
| Self-guided functional imagery training to reduce anxiety, *Behaviour Research and Therapy* | 2026 | Early-phase personalized digital imagery for anxiety-related avoidance |
| Audio-recorded guided imagery on psychological distress (SR + MA) | 2025 | Supports recorded delivery; does not settle dose |
| Guided imagery on psychological outcomes in cancer patients (SR + MA) | 2025 | Positive; protocol heterogeneity persists |
| Nature-Based Guided Imagery and Meditation (RCT) | 2025 | ~20-min nature interventions; n=40, preliminary |
| Optimal dosage of imagery practice on athletes' mental health (Bayesian MA) | 2025 | ~45 min/week over ~100 days; athlete-specific |
| Early phase testing of functional imagery training for anxiety | 2025 | Promising, preliminary |
| Personalized VR vs Guided Imagery for PMR (pilot RCT), *JMIR Mental Health* | 2024 | Both reduced state anxiety; VR not superior overall |
| Guided Imagery for Symptom Management in Life-Limiting Illnesses (SR of RCTs) | 2024 | 10 of 14 trials beneficial; methodological variation |
| Guided Imagery on Perioperative Anxiety in Hospitalized Adults (SR) | 2024 | Reduces anxiety; calls for standardized trials |
| Interventions Targeting Negative Mental Imagery in Social Anxiety (SR + MA) | 2024 | Imagery can modify distress-maintaining self-images |
| A Systematic Review of Aphantasia | 2024 | Supports nonvisual pathways into imagery |
| Vividness of visual imagery and relaxation-response meditation | 2024 | Imagery ability affects speed/magnitude, not eligibility |
| Impact of Guided Imagery on Stress, Brain Functions, and Attention | 2023 | Reduced stress, EEG alpha changes; needs replication |
| Effectiveness of PMR, Deep Breathing, and Guided Imagery | 2021 | Supports brief physiological transition before imagery |

---

## 12. Open research questions we are absorbing as risk

1. Optimal session length for consumer use
2. Optimal narration rate and pause duration
3. Whether our soundscape investment returns anything
4. Whether generated sessions beat a fixed library
5. Whether personalization improves outcomes or only engagement
6. Frequency and adherence patterns for non-clinical users
7. Cross-cultural validity of any single scene vocabulary

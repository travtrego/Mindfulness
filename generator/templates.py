"""The six templates, as data.

Category count is not the build cost - template count is. Fifteen categories map onto six
beat structures here, and adding a category is one line while adding a template is real work.

See docs/templates/slots.md for what each template needs filled and where it comes from.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class BeatSpec:
    role: str
    share: float                 # fraction of generated runtime
    wpm: int                     # delivery rate - belongs to the beat, not the session
    note: str = ""
    source: str = "generated"
    optional: bool = False


@dataclass(frozen=True)
class Template:
    name: str
    categories: tuple[str, ...]
    depth: int                   # 0 = no questions, 1 = questions, 2 = talk then questions
    duration_range: tuple[int, int]
    beats: tuple[BeatSpec, ...]
    aims_at: str
    required_slots: tuple[str, ...] = ()
    rules: tuple[str, ...] = ()

    @property
    def generated_beats(self) -> list[BeatSpec]:
        return [b for b in self.beats if b.source == "generated"]


INTRO = BeatSpec("grounding_intro", 0.0, 82, "cached matrix, never generated", source="cached")
REORIENT = BeatSpec("reorientation", 0.06, 88, "end alert, not floating")

TEMPLATES: dict[str, Template] = {

    "breath_only": Template(
        name="breath_only",
        categories=("just_breathing",),
        depth=0,
        duration_range=(180, 600),
        aims_at="regulation, with no narrative at all",
        beats=(
            INTRO,
            BeatSpec("settling", 0.15, 80),
            BeatSpec("paced_breathing", 0.75, 70, "parametric, minimal narration",
                     source="parametric"),
            BeatSpec("reorientation", 0.10, 85),
        ),
        rules=(
            "No imagery, no place, no narrative.",
            "Never 4-7-8 - breath holding is contraindicated for anxiety.",
            "Reachable in one tap. Any question added here defeats the template.",
        ),
    ),

    "anchored_place": Template(
        name="anchored_place",
        categories=("safe_place",),
        depth=0,
        duration_range=(480, 900),
        aims_at="familiarity - the same place, accumulating detail",
        required_slots=("place_id", "established_details", "anchor", "visit_number"),
        beats=(
            INTRO,
            BeatSpec("settling", 0.12, 82),
            BeatSpec("entry_threshold", 0.15, 75, "shortens as visit_number rises"),
            BeatSpec("establish_world", 0.25, 72, "uses stored details ONLY"),
            BeatSpec("deepening", 0.22, 72, "exactly one new detail this visit"),
            BeatSpec("anchor", 0.18, 85),
            REORIENT,
        ),
        rules=(
            "NEVER generate the place. The listener supplied it; only elaborate within it.",
            "Established details are additive and never contradicted.",
            "Exactly one new sensory detail per visit. Not two.",
        ),
    ),

    "rehearsal": Template(
        name="rehearsal",
        categories=("interview", "competition", "hard_conversation", "confidence"),
        depth=2,
        duration_range=(600, 960),
        aims_at="competence - having already done the thing once",
        required_slots=("event", "dreaded_moment", "outcome_frame", "anchor_action"),
        beats=(
            INTRO,
            BeatSpec("settling", 0.10, 85),
            BeatSpec("approach", 0.20, 90, "the moments before, with realistic activation"),
            BeatSpec("event", 0.16, 72, "begin the behaviour - sensory, not affirmational"),
            BeatSpec("difficulty_and_response", 0.20, 68, "NEVER skipped"),
            BeatSpec("completion", 0.14, 70, "successfully enough, not flawlessly"),
            BeatSpec("anchor", 0.14, 85, "must be performable in the real situation"),
            REORIENT,
        ),
        rules=(
            "difficulty_and_response is never skipped. With outcome_frame=succeed it "
            "relocates INSIDE the success - the lift is slow out of the bottom and is "
            "stood up anyway.",
            "The difficulty beat is what earns the ending. A session that skips to success "
            "has the same words and none of the weight.",
            "Result claims are allowed and encouraged. Mechanism claims are not.",
        ),
    ),

    "immersive": Template(
        name="immersive",
        categories=("nature", "adventure", "fantasy", "into_sleep"),
        depth=1,
        duration_range=(720, 2700),
        aims_at="wonder, and being somewhere",
        required_slots=("environment", "realism", "movement"),
        beats=(
            INTRO,
            BeatSpec("settling", 0.10, 82),
            BeatSpec("entry_threshold", 0.14, 75),
            BeatSpec("establish_world", 0.24, 70),
            BeatSpec("meaningful_experience", 0.26, 70, "movement through the landscape"),
            BeatSpec("consolidation", 0.14, 72, "the stillness beat"),
            BeatSpec("anchor", 0.12, 85),
            REORIENT,
        ),
        rules=(
            "The environment stays internally consistent. Start on a ridge, stay in that "
            "landscape - never cut to a beach.",
            "Category is a constraint, not a structure: nature=real, adventure=real with "
            "stakes, fantasy=invented, into_sleep=real and sparse.",
            "into_sleep drops the reorientation beat entirely and runs far more silence.",
        ),
    ),

    "reflective": Template(
        name="reflective",
        categories=("body_scan", "gratitude", "creativity"),
        depth=1,
        duration_range=(480, 900),
        aims_at="presence - attention to what is already here",
        required_slots=("focus", "object"),
        beats=(
            INTRO,
            BeatSpec("settling", 0.18, 80),
            BeatSpec("meaningful_experience", 0.42, 72, "the noticing sequence"),
            BeatSpec("consolidation", 0.20, 75, "widening"),
            BeatSpec("anchor", 0.13, 85),
            REORIENT,
        ),
        rules=(
            "No place and no journey. There is no scenery to lean on, which is why the "
            "noticing language carries the entire session.",
        ),
    ),

    "reentry": Template(
        name="reentry",
        categories=("going_back",),
        depth=2,
        duration_range=(840, 1260),
        aims_at="the unremarkable - being allowed to have an ordinary day",
        required_slots=("setting", "the_feared_exchange", "competence_domain"),
        beats=(
            INTRO,
            BeatSpec("settling", 0.09, 82, "must state that nothing is a test"),
            BeatSpec("threshold", 0.14, 78, "the crossing-in. usually the anchor's source"),
            BeatSpec("competence", 0.17, 78, "what the listener can still do. NEVER absent"),
            BeatSpec("the_moment", 0.13, 72, "embedded, NOT climactic"),
            BeatSpec("what_returns", 0.12, 74, "small. not a speech"),
            BeatSpec("continuation", 0.19, 80, "LOAD-BEARING. must outlast the_moment"),
            BeatSpec("anchor", 0.10, 85, "a daily-recurring physical event"),
            REORIENT,
        ),
        rules=(
            "continuation must be at least as long as the_moment in words. A session that "
            "peaks and stops says the feared exchange was the event - when the point is "
            "that it happened and the day went on.",
            "competence always precedes the_moment. The listener stands on something they "
            "can still do before the feared thing arrives.",
            "Never argue with the belief. Do not say 'they don't think that about you' - "
            "arguing treats it as a proposition worth debating. Put the listener somewhere "
            "the belief has nothing to attach to.",
            "The target is mundane, so vividness must come from precision about ordinary "
            "things. The ordinariness is the payload, not the backdrop.",
        ),
    ),
}

CATEGORY_TO_TEMPLATE = {
    cat: t.name for t in TEMPLATES.values() for cat in t.categories
}


def for_category(category: str) -> Template:
    try:
        return TEMPLATES[CATEGORY_TO_TEMPLATE[category]]
    except KeyError:
        raise ValueError(
            f"unknown category {category!r}. known: {sorted(CATEGORY_TO_TEMPLATE)}"
        ) from None


def allocate(template: Template, target_s: int, intro_s: int) -> list[dict]:
    """Turn a template plus a duration into concrete per-beat word and silence budgets.

    Silence runs ~42% of runtime in the reference sessions, so speech gets ~58%.
    """
    generated_s = max(target_s - intro_s, 60)
    speech_s = generated_s * 0.58
    out = []
    for b in template.beats:
        if b.source == "cached":
            out.append({"role": b.role, "source": "cached", "wpm": b.wpm})
            continue
        beat_speech = speech_s * b.share
        out.append({
            "role": b.role,
            "source": b.source,
            "wpm": b.wpm,
            "word_target": max(round(beat_speech / 60 * b.wpm), 20),
            "silence_total_s": round(generated_s * b.share * 0.42),
            "note": b.note,
        })
    return out

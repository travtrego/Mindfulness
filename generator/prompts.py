"""The three prompts.

Call 1 parses intent, call 2 produces an outline, call 3 drafts prose. All three are text
calls and run in ~15-25s total; TTS is what gets parallelised afterwards (SPEC.md 5).

The craft rules appear in the draft prompt AND are enforced afterwards by generator.craft.
Both are needed: the prompt gets most of the way there, the validator catches the drift
that a prompt cannot hold across 2,000 words.
"""
from __future__ import annotations

import json
from pathlib import Path

from .templates import Template

REFERENCE_DIR = Path(__file__).parent.parent / "docs/sessions"

CRAFT_RULES = """\
CRAFT STANDARD — these are hard requirements, and the draft is validated against them.

Name the sense, not the furniture.
  Specify a sensory channel and quality. Leave the objects to the listener.
  YES: "The bar is colder than the room."   "Cooler on one side of your face."
  NO:  "A narrow pine trail with seven grey stones beside a blue stream."

Guided incompleteness.
  "You may notice a path, an opening, or some other way in" — not "you walk down the
  gravel path." The listener's own scene is more relevant to them, easier to recall
  later, and far less likely to contain something they did not want.

One sensory detail per beat, sequenced. Never stacked.

Contrast and asymmetry over scene-setting. Warm on one side of the face, cool on the other.

Noticing language. "You notice", "you catch", "you become aware of" — not "you are in".
  Drop to plain declarative only at a climax, deliberately: "And then you stand."

Second person, present tense, throughout. Never "I". "We" is acceptable.

Vividness is never a performance demand.
  "Notice whatever detail comes most easily." "It may be clear, faint, or simply felt."
  Never imply the listener has failed to visualise.

Silence is content. It carries ~42% of runtime. Place it deliberately — the longest holds
go after a climax or after an anchor lands, not spread evenly.

BANNED: breathtaking, serene, peaceful, tranquil, majestic, stunning, blissful, soothing,
calming, radiant, luminous, sacred, divine, magical, wondrous, ethereal, pristine.

BANNED hedges: gently, simply, slightly, somewhat, perhaps, maybe, quite, very.

BANNED demands: try to, make sure, focus on, you should, picture the, visualise.

BANNED mechanism claims: rewires, your brain, nervous system, neural, subconscious,
"can't tell the difference", scientifically, proven to.
  Claims about OUTCOME are fine and encouraged — "you will stand it up again" is good.
  Claims about MECHANISM are not. Say what happens; never explain what it is doing to them.
"""


def intent_prompt(user_text: str, category: str | None, memory: dict | None = None) -> str:
    mem = json.dumps(memory or {}, indent=2)
    given = f"The listener already chose the category: {category}." if category else \
        "No category was chosen — infer one."
    return f"""\
You are the intent parser for a guided visualization engine.

{given}

What the listener said:
\"\"\"{user_text}\"\"\"

Known about this listener from previous sessions:
{mem}

Return JSON only:
{{
  "category": "<one of: just_breathing, body_scan, safe_place, nature, adventure, fantasy,
                into_sleep, interview, competition, hard_conversation, confidence,
                gratitude, creativity, going_back>",
  "slots": {{ }},                    // everything you can extract or reasonably infer
  "still_empty": [ ],                // required slots you could NOT fill
  "target_duration_s": <int>,
  "sensitivity_flag": <bool>,        // grief, trauma, crisis-adjacent, or self-harm
  "session_exclusions": [ ]          // things the listener asked you not to raise
}}

sensitivity_flag is conservative: when unsure, set it true.

session_exclusions are THIS SESSION ONLY and must never be written back to the listener's
profile. "Don't bring up bombing out" before a PR attempt does not mean that listener never
wants to rehearse recovering from a miss.
"""


def question_prompt(template: Template, slots: dict, still_empty: list[str],
                    transcript: str) -> str:
    return f"""\
Write up to THREE questions to ask before generating this session.

Template: {template.name} — aims at {template.aims_at}
Already known: {json.dumps(slots, indent=2)}
Still empty: {still_empty}

What the listener said:
\"\"\"{transcript}\"\"\"

Each question must pass all three gates, or you drop it and fill the slot yourself:
  1. Does it fill a slot that is actually empty?
  2. Would a reasonable person in THIS situation find it relevant?
  3. Is it answerable in one tap?

Three is a maximum, never a quota. Asking two good questions beats asking three.

Write them FROM what the listener said, not from a generic list. "Do they see your face?"
is an excellent question after someone mentions walking off a pitch, and a strange one at a
weightlifting platform.

Never ask something the model could reasonably invent itself. You can imagine an excellent
forest; you cannot imagine the thirty seconds they are actually dreading.

Return JSON: [{{"question": "...", "options": ["...", "..."], "fills": "slot_name"}}]
"""


def outline_prompt(template: Template, slots: dict, budget: list[dict],
                   exclusions: dict, target_s: int) -> str:
    rules = "\n".join(f"  - {r}" for r in template.rules)
    all_exc = exclusions.get("standing", []) + exclusions.get("session", [])
    return f"""\
Produce the outline for a {template.name} session. JSON only, matching the beat budget exactly.

Aims at: {template.aims_at}
Target: {target_s}s

Template rules — these are not suggestions:
{rules}

Slots:
{json.dumps(slots, indent=2)}

Exclusions — {all_exc}
  Every one of these must appear in the do_not_mention of EVERY beat where the model might
  otherwise reach for it. A session-level note is not enough; by beat 6 it has drifted.

Beat budget — use these word_target and silence_total_s values as given:
{json.dumps(budget, indent=2)}

For each beat return:
  id, role, source, word_target, wpm, silence_total_s,
  silence_plan: [{{"type": "sensory|transition|open|hold", "seconds": int}}]
      sensory 3-6s, transition 6-12s, open 15-30s, hold after a climax or an anchor.
      MUST sum exactly to silence_total_s.
  beats_on: [slot keys this beat uses]
  do_not_mention: [exclusions relevant to THIS beat]
  ambience: "none" | {{"stems": [...], "level": "bed|present"}}
      Climax beats should be "none". A stem system that always has something playing
      ruins them.

Then transitions: [{{from_beat, to_beat, description, stems_out, stems_in, crossfade_s}}]
  description is SEMANTIC — "leaving the treeline, wind rises". Never a timestamp. You
  cannot know the real timings; they are resolved after speech synthesis.

Stems come from this fixed list and nothing else:
  room_tone_small room_tone_large room_tone_outdoor wind_low wind_ridge wind_trees
  rain_light rain_heavy water_stream water_lake water_surf fire_close birds_dawn
  birds_distant insects_night forest_canopy grass_movement gravel_underfoot
  snow_underfoot crowd_distant crowd_hush bell_distant creak_wood hum_low
"""


def draft_prompt(beat: dict, template: Template, slots: dict, prior: str,
                 exemplar: str) -> str:
    return f"""\
Write the narration for ONE beat.

{CRAFT_RULES}

Beat: {beat['role']} — {beat.get('note', '')}
Word target: {beat['word_target']} (±10%)
Silence plan: {json.dumps(beat.get('silence_plan', []))}
  Mark each silence inline as *[Ns]* in the position you intend it.

Slots this beat uses: {beat.get('beats_on', [])}
{json.dumps({k: v for k, v in slots.items() if k in beat.get('beats_on', [])}, indent=2)}

DO NOT MENTION — {beat.get('do_not_mention', [])}
  Not once, not obliquely, not as something being avoided.

What has already been narrated (do not repeat or contradict it):
\"\"\"{prior[-1200:] if prior else '(this is the first generated beat)'}\"\"\"

A hand-written beat at this standard, for register only — do not copy its content:
\"\"\"{exemplar}\"\"\"

Return the narration only. No preamble, no headings, no explanation.
"""


def load_exemplar(role: str) -> str:
    """Pull a hand-written beat of the same role from the reference sessions.

    Few-shot on five excellent examples beats almost anything else available at this stage,
    and these are the only text in the repo known to meet the standard.
    """
    import re
    best = ""
    for path in sorted(REFERENCE_DIR.glob("0[12]*.md")):
        text = path.read_text().split("\n# ")[0]
        for block in re.split(r"\n## Beat ", text)[1:]:
            header = block.split("\n")[0].lower()
            if role.split("_")[0] not in header.replace(" ", "_"):
                continue
            quoted = [l for l in block.split("\n") if l.startswith(">")]
            prose = re.sub(r"^>\s?", "", "\n".join(quoted), flags=re.M).strip()
            if len(prose) > len(best):
                best = prose
    return best or "(no exemplar for this role yet)"

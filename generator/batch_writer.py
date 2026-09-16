"""Draft coherent sessions in one call, then repair flagged beats together."""
import json

from . import prompts
from .craft import check


def _texts(raw, allowed):
    """Only accept known roles with nonempty narration; never trust model metadata."""
    if not isinstance(raw, dict) or not isinstance(raw.get("beats"), list):
        raise ValueError("invalid batch narration")
    result = {}
    for item in raw["beats"]:
        if not isinstance(item, dict):
            raise ValueError("invalid beat")
        role, text = item.get("role"), item.get("text")
        if not isinstance(role, str) or role not in allowed or role in result:
            raise ValueError("unknown or duplicate beat role")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("empty narration")
        result[role] = text.strip()
    if set(result) != set(allowed):
        raise ValueError("incomplete narration")
    return result


def draft_session(session, llm, parse):
    outline = session.outline
    generated = [b for b in outline["beats"] if b.get("source") != "cached"]
    roles = [b["role"] for b in generated]
    rules = list(session.template.rules)
    examples = {b["role"]: prompts.load_exemplar(b["role"], session.template.name)
                for b in generated}
    request = f"""Write the COMPLETE guided visualization in one coherent pass.
Follow the beat order exactly. Each beat continues naturally from the preceding one.
Preserve the environment, narrative facts, exclusions and second-person present tense.
Meet each beat's word_target within 10 percent. Place every planned silence inline as
*[Ns]*. Do not narrate beat labels. Cached intro beats are supplied separately: omit them.
Use the full listener slots to make reasonable choices where details are missing.

Template: {session.template.name}
Aims at: {session.template.aims_at}
Rules: {json.dumps(rules)}
Slots: {json.dumps(session.slots)}
Exclusions: {json.dumps(outline['exclusions'])}
Beat budgets and content plan: {json.dumps(generated)}
Examples for register only (do not copy their content): {json.dumps(examples)}

Return JSON only: {{"beats": [{{"role": "exact role", "text": "narration"}}]}}
Include every requested generated beat exactly once, with nonempty narration.
"""
    # A malformed response gets one bounded retry, never a long per-beat restart.
    for attempt in range(2):
        try:
            texts = _texts(parse(llm(request, system=prompts.CRAFT_RULES)), roles)
            break
        except (ValueError, TypeError):
            if attempt:
                raise
            session.trace.add("batch-format-retry")

    for attempt in range(2):
        reports = {role: check(text) for role, text in texts.items()}
        failed = [role for role in roles if not reports[role].ok]
        if not failed:
            break
        repairs = [{"role": role, "text": texts[role], "issues": [
            {"rule": f.rule, "detail": f.detail, "sentence": f.sentence}
            for f in reports[role].errors]} for role in failed]
        repair_prompt = f"""Repair ONLY the flagged narration beats below.
Keep the setting, meaning, word count, silence markers and all unflagged sentences.
The full session is context for continuity only; return only the requested repaired roles.
Return JSON: {{"beats": [{{"role": "exact role", "text": "corrected narration"}}]}}
Full session: {json.dumps(texts)}
Repairs: {json.dumps(repairs)}
"""
        try:
            updates = _texts(parse(llm(repair_prompt, system=prompts.CRAFT_RULES)), failed)
        except (ValueError, TypeError):
            session.trace.add("batch-repair-invalid", attempt=attempt + 1)
            continue
        for role, text in updates.items():
            if len(check(text).errors) <= len(reports[role].errors):
                texts[role] = text
        session.trace.add("batch-craft-repair", roles=failed, attempt=attempt + 1)

    return [{**beat, "text": None} if beat.get("source") == "cached" else
            {**beat, "text": texts[beat["role"]], "craft": check(texts[beat["role"]])}
            for beat in outline["beats"]]

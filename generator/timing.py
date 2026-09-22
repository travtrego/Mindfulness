"""Duration checks shared by drafting and editorial revision; never adjust speaking speed."""
import re

PAUSE = re.compile(r"\*\[\s*(\d+(?:\.\d+)?)\s*s\b[^\]]*\]\*", re.I)


def metrics(text):
    pauses = [float(value) for value in PAUSE.findall(text)]
    words = len(re.findall(r"[\w]+(?:['’][\w]+)*", PAUSE.sub(' ', text)))
    return words, pauses


def timing_issues(text, beat):
    words, pauses = metrics(text)
    target_words = beat['word_target']
    target_silence = beat['silence_total_s']
    issues = []
    # Match the authored budgets, not metadata claiming the script lasts N minutes.
    if abs(words - target_words) > max(4, target_words * .15):
        issues.append(f"{words} spoken words; need about {target_words}")
    if abs(sum(pauses) - target_silence) > max(1, target_silence * .05):
        issues.append(f"{sum(pauses):g}s of pauses; need {target_silence}s distributed through the beat")
    if any(p > 30 for p in pauses):
        issues.append("split long pauses naturally; no individual pause over 30 seconds")
    return issues


def preserves_timing(original, revised):
    old_words, old_pauses = metrics(original)
    words, pauses = metrics(revised)
    return pauses == old_pauses and abs(words - old_words) <= max(3, old_words * .1)

#!/usr/bin/env python3
"""Static browser contract checks for the zero-build single-file application."""

from pathlib import Path


APP = Path(__file__).resolve().parent.parent / "docs" / "app.html"


def main() -> None:
    html = APP.read_text()
    assert html.count("<script>") == 1, "disabled/duplicate application scripts returned"
    assert "retained temporarily" not in html
    assert "var LINES" not in html, "fake playback copy returned"

    required_ids = (
        "s-home", "s-talk", "s-ask", "s-generate", "s-play", "s-close",
        "start-session", "pp", "rewind", "forward", "end-session",
        "breathing-only", "reflection", "reflection-mic",
    )
    for element_id in required_ids:
        assert html.count(f'id="{element_id}"') == 1, f"missing/duplicate #{element_id}"

    required_wiring = (
        'post("/api/generate"',
        "memory: generationMemory()",
        "window.speechSynthesis.speak(utterance)",
        "window.speechSynthesis.pause()",
        "window.speechSynthesis.resume()",
        "pauseBtn.onclick",
        "rewindBtn.onclick",
        "forwardBtn.onclick",
        "endBtn.onclick",
        "reflectionMic.onclick",
        "rememberReflection(reflection.value)",
    )
    for marker in required_wiring:
        assert marker in html, f"missing app wiring: {marker}"

    print("app contract ok: generation, narration, controls, and memory are wired")


if __name__ == "__main__":
    main()

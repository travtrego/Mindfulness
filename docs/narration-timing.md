# Narration timing repair

The previous audio adapter sent a complete session in one ElevenLabs request. It multiplied
plain pause markers by 0.32 and capped them at 2.8 seconds. Annotated markers such as
`*[14s — open]*` were not recognized at all. The script budgets still counted the full
silence. ElevenLabs also documents speed instability with excessive SSML break tags.

## Audio path

1. Split narration at its authored pause markers. Bound speech clips to 600 characters,
   preferring sentence boundaries. Supply adjacent speech as previous/next text context.
2. Generate signed 16-bit little-endian mono PCM at 24 kHz. The first successful request
   resolves the preferred/fallback voice; every subsequent request pins that same voice.
   Keep speed at 0.90, raise stability to 0.75 and remove style exaggeration.
3. Request at most two clips concurrently after the first clip. Each request has a timeout;
   successfully fetched clips are reused if preparation is retried. No provider key reaches
   the browser. Each response is capped at 3.6 MB; no server-side whole-session audio response.
4. Assemble the exact PCM speech samples and zero-valued silence samples into one WAV Blob
   on the device. A 12-second marker adds exactly 288,000 silence samples, including markers
   with annotations. Do not time-stretch speech or add filler silence to reach a target.
5. Use the existing HTML audio player at playbackRate 1. The recording's actual duration is
   shown before playback. A deviation above 10% (minimum 30 seconds) is explicitly disclosed.
   Beat navigation follows measured sample boundaries, not equal fractions of the session.

This trades one long provider request for multiple bounded requests. Voice preparation may
therefore take longer, and long WAVs use more device memory than MP3s (48 KB per second).
Progress is visible while preparing. Background playback and seeking use the media timeline,
so JS timer throttling cannot remove pauses.

## Script duration

The explicit duration answer wins over model interpretation and template default ranges.
Batch drafts are checked for word budget (15% tolerance) and silence budget (5% tolerance).
One grouped repair is allowed; drafts still outside their budgets use the existing disclosed
reference fallback. Editorial revisions must preserve pause durations/order and word counts.
The final recording duration remains the source of truth: model speaking rate is variable,
and word-budget checks are not a promise of an exact requested runtime.

## Verification

- `python scripts/test_audio.py`
- `python scripts/test_batch_writer.py`
- `node scripts/test_audio_timeline.mjs`
- `node scripts/test_voice_loading.mjs`
- Existing craft, intro, reference, malformed-model, schema, API, app and HTTP checks.

Provider contract tests use mocked PCM. A real ElevenLabs listening test on a phone remains
required to judge cadence, continuity across clips, preparation latency and long-session
memory use. No voice-quality claim should be based solely on these automated checks.

References:
- https://elevenlabs.io/docs/overview/capabilities/text-to-speech/best-practices
- https://elevenlabs.io/docs/api-reference/text-to-speech/convert

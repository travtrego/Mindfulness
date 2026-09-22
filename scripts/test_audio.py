"""Speech clips keep pauses out of TTS and pin one voice for the complete recording."""
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from urllib.error import HTTPError
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from generator import audio
from generator.timing import timing_issues, preserves_timing

class AudioTests(unittest.TestCase):
    def test_provider_contract(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b'\x01\x00' * 24000
        with patch.dict(os.environ, {'ELEVENLABS_API_KEY': 'test-only'}), patch.object(audio, 'urlopen', return_value=response) as request:
            pcm, voice = audio.synthesize('You notice the warmth.', previous_text='Your hands settle.', next_text='You stay here.')
        call = request.call_args.args[0]
        self.assertIn('output_format=pcm_24000', call.full_url)
        payload = json.loads(call.data)
        self.assertEqual(payload['text'], 'You notice the warmth.')
        self.assertEqual(payload['previous_text'], 'Your hands settle.')
        self.assertEqual(payload['next_text'], 'You stay here.')
        self.assertEqual(payload['voice_settings']['speed'], .90)
        self.assertGreaterEqual(payload['voice_settings']['stability'], .7)
        self.assertEqual(payload['voice_settings']['style'], 0)
        self.assertEqual(len(pcm), 48000)

    def test_pause_markup_and_oversized_requests_never_reach_provider(self):
        with patch.object(audio, '_request_audio') as request:
            for text in ('Rest. *[12s]* Stay.', '<break time="3s" />', 'a'*601, '', None):
                with self.subTest(text=str(text)[:20]), self.assertRaises(ValueError):
                    audio.synthesize(text)
            request.assert_not_called()

    def test_fallback_is_resolved_once(self):
        unavailable = HTTPError('https://example.test', 404, '', {}, None)
        with patch.dict(os.environ, {'ELEVENLABS_API_KEY': 'test-only'}), patch.object(audio, '_request_audio', side_effect=[unavailable, b'\0\0']) as request:
            _, voice = audio.synthesize('Rest.')
            self.assertEqual(voice, audio.FALLBACK_FEMALE_VOICE_ID)
            self.assertEqual(request.call_count, 2)
        with patch.dict(os.environ, {'ELEVENLABS_API_KEY': 'test-only'}), patch.object(audio, '_request_audio', side_effect=unavailable) as request:
            with self.assertRaises(HTTPError):
                audio.synthesize('Rest.', pinned_voice=audio.PREFERRED_VOICE_ID)
            self.assertEqual(request.call_count, 1)

    def test_bad_pcm_rejected(self):
        for pcm in (b'', b'123', b'\0' * (audio.MAX_AUDIO_BYTES + 2)):
            response = MagicMock()
            response.__enter__.return_value.read.return_value = pcm
            with patch.object(audio, 'urlopen', return_value=response), self.assertRaises(RuntimeError):
                audio._request_audio('test', 'voice', 'Rest.', 'model')

    def test_short_draft_missing_silence_rejected(self):
        budget = {'word_target': 100, 'silence_total_s': 60}
        self.assertTrue(timing_issues('You rest. *[3s]*', budget))
        valid = ('Your hands rest here. ' * 25) + '*[20s]* *[20s]* *[20s]*'
        self.assertFalse(timing_issues(valid, budget))
        self.assertFalse(preserves_timing(valid, valid.replace('*[20s]*', '*[2s]*')))
        self.assertTrue(preserves_timing(valid, valid.replace('hands', 'feet')))

if __name__ == '__main__':
    unittest.main()

"""Exercise production batch drafting across all category templates without network."""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from generator import api
from generator.batch_writer import _texts
from generator.pipeline import generate

PROSE = "Your hands rest on your thighs. *[6s]* The fabric is warm beneath your palms."


class BatchTests(unittest.TestCase):
    def test_every_category_is_complete_in_three_calls(self):
        for label, category in api.CATEGORY_IDS.items():
            calls = []
            def model(prompt, system=None):
                calls.append(prompt.splitlines()[0])
                if prompt.startswith("You are the intent parser"):
                    return json.dumps({"category": category, "slots": {}, "target_duration_s": 600})
                if prompt.startswith("Produce the outline"):
                    return '{}'
                if prompt.startswith("Write the COMPLETE"):
                    beats = json.loads(prompt.split("Beat budgets and content plan: ")[1].splitlines()[0])
                    return json.dumps({"beats": [{"role": b['role'], "text": PROSE} for b in beats]})
                raise AssertionError("unexpected stage: " + prompt[:30])
            with self.subTest(category=label):
                session = generate('Ten minutes', category=category, llm=model, batch_drafts=True)
                self.assertEqual(len(calls), 3)
                for beat in session.beats:
                    if beat['source'] != 'cached':
                        self.assertTrue(beat['text'])
                self.assertEqual([b['role'] for b in session.beats],
                                 [b['role'] for b in session.outline['beats']])

    def test_invalid_batch_cannot_become_incomplete_session(self):
        for result in ({}, {'beats': []}, {'beats': [{'role': 'arrival', 'text': ''}]},
                       {'beats': [{'role': 'unknown', 'text': PROSE}]},
                       {'beats': [{'role': 'arrival', 'text': PROSE}] * 2}):
            with self.subTest(result=result), self.assertRaises(ValueError):
                _texts(result, ['arrival'])

    def test_api_uses_batch_mode_and_still_falls_back(self):
        with patch.object(api, 'generate', side_effect=ValueError('bad batch')) as call:
            result = api.generate_session('Nature')
            self.assertTrue(result['fallback'])
            self.assertTrue(result['beats'])
            self.assertTrue(call.call_args.kwargs['batch_drafts'])


if __name__ == '__main__':
    unittest.main()

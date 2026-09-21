"""Offline permission-check regression tests; no network/dependencies required."""
import ast
import json
from pathlib import Path
import re
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

source = Path(__file__).with_name('update_news.py').read_text()
function = next(n for n in ast.parse(source).body
                if isinstance(n, ast.FunctionDef) and n.name == 'youtube_video_embeddable')
scope = dict(re=re, sys=sys, subprocess=subprocess, json=json)
exec(compile(ast.Module(body=[function], type_ignores=[]), '<embed-check>', 'exec'), scope)
check = scope['youtube_video_embeddable']


class EmbedPermissionTests(unittest.TestCase):
    def test_metadata(self):
        for info, expected in [
            ({'playable_in_embed': True, 'availability': 'public'}, True),
            ({'playable_in_embed': True, 'availability': 'unlisted'}, True),
            ({'playable_in_embed': False, 'availability': 'public'}, False),
            ({'availability': 'public'}, False),
            ({'playable_in_embed': True, 'availability': 'private'}, False),
            ({'playable_in_embed': True, 'availability': 'subscriber_only'}, False),
        ]:
            with self.subTest(info=info), patch.object(subprocess, 'run', return_value=SimpleNamespace(returncode=0, stdout=json.dumps(info))):
                self.assertEqual(check('abcdefghijk'), expected)

    def test_failures_never_grant_permission(self):
        for result in [SimpleNamespace(returncode=1, stdout=''),
                       SimpleNamespace(returncode=0, stdout=''),
                       SimpleNamespace(returncode=0, stdout='not json')]:
            with patch.object(subprocess, 'run', return_value=result):
                self.assertFalse(check('abcdefghijk'))
        with patch.object(subprocess, 'run', side_effect=subprocess.TimeoutExpired('test', 30)):
            self.assertFalse(check('abcdefghijk'))


if __name__ == '__main__':
    unittest.main()

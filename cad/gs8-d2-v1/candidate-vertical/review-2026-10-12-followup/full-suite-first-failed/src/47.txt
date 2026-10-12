# SPDX-License-Identifier: MIT
"""Locale-independence smoke test of the REPRODUCE.md inspect commands (review VN-02/VN-03, fix FP-02).

Run:  run_locked.py -- cad/gs8-d2-v1/candidate-vertical/tests/test_windows_smoke.py

Each inspect command runs twice in a child interpreter: with UTF-8 mode forced off (-X utf8=0, so on Windows
the locale code page, e.g. cp1252, is the default text encoding) and forced on (-X utf8=1). PYTHONUTF8 and
PYTHONIOENCODING are removed from the child environment. The results must be identical and free of
Unicode errors; the docs audit (written to a scratch --out, never over the committed report) must contain no
backslash and no CR. The structural check must pass. The BOM check must give the same verdict in both modes;
whether that verdict is "current" depends on evidence binding (it embeds verifier hashes), not on this fix.
No CAD is imported.
"""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest

CV = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_cross_platform_io import json_backslashes  # noqa: E402

BOM = CV / 'make_bom_vertical.py'
STRUCTURAL = CV / 'structural-review' / 'update_concealed_vent_structure.py'
AUDIT = CV / 'review_docs_audit.py'
COMMITTED_AUDIT = CV / 'out' / 'review-docs-audit.json'


def run(utf8, *args, cwd):
    env = {k: v for k, v in os.environ.items() if k not in ('PYTHONUTF8', 'PYTHONIOENCODING')}
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    r = subprocess.run([sys.executable, '-X', 'utf8=%d' % utf8, *map(str, args)], cwd=str(cwd), env=env,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=1800)
    return r.returncode, r.stdout.replace(b'\r\n', b'\n'), r.stderr.replace(b'\r\n', b'\n')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


class TestLocaleIndependence(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def assertNoUnicodeError(self, err):
        self.assertNotIn(b'UnicodeDecodeError', err, err[-800:])
        self.assertNotIn(b'UnicodeEncodeError', err, err[-800:])

    def test_structural_check_passes_in_both_modes(self):
        before = sha(STRUCTURAL.parent / 'concealed-vent-structural.json')
        off, on = run(0, STRUCTURAL, '--check', cwd=self.d), run(1, STRUCTURAL, '--check', cwd=self.d)
        self.assertNoUnicodeError(off[2])
        self.assertEqual(off[0], 0, off[2][-1500:].decode('utf-8', 'replace'))
        self.assertEqual(off, on)
        self.assertEqual(sha(STRUCTURAL.parent / 'concealed-vent-structural.json'), before)

    def test_bom_check_same_verdict_in_both_modes(self):
        off, on = run(0, BOM, '--check', cwd=self.d), run(1, BOM, '--check', cwd=self.d)
        self.assertNoUnicodeError(off[2])
        self.assertEqual(off, on, 'BOM --check depends on the locale encoding')
        print('\n[bom --check] exit %d: %s' % (off[0], (off[1] + off[2]).decode('utf-8', 'replace').strip()[-300:]))

    def test_docs_audit_is_locale_independent_posix_and_read_only(self):
        committed = sha(COMMITTED_AUDIT)
        a, b = self.d / 'audit-utf8-off.json', self.d / 'audit-utf8-on.json'
        off, on = run(0, AUDIT, '--out', a, cwd=self.d), run(1, AUDIT, '--out', b, cwd=self.d)
        self.assertNoUnicodeError(off[2])
        # FP-04 (VN-05): the audit exits 1 on any failed binding and 3 when only rebuildable caches are missing; the
        # locale must not change the verdict, and the run must not crash.
        self.assertIn(off[0], (0, 1, 3), off[2][-1500:].decode('utf-8', 'replace'))
        self.assertEqual(off[0], on[0])
        self.assertNotIn(b'Traceback', off[2] + on[2], off[2][-1500:].decode('utf-8', 'replace'))
        raw_a, raw_b = a.read_bytes(), b.read_bytes()
        self.assertNotIn(b'\r', raw_a)
        self.assertTrue(raw_a.endswith(b'}\n'))
        ja, jb = json.loads(raw_a), json.loads(raw_b)
        ja.pop('generated_utc')
        jb.pop('generated_utc')
        self.assertEqual(ja, jb)
        self.assertEqual(json_backslashes(self.d), [])
        self.assertEqual(sha(COMMITTED_AUDIT), committed, 'inspection rewrote the committed audit')


if __name__ == '__main__':
    unittest.main(verbosity=2)

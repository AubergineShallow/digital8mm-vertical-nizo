# SPDX-License-Identifier: MIT
"""Extended bonded-stub catch record (review 2026-10-12 corrective, GEO-1 / GEO-2 / CHE-2).

Run:  run_locked.py -- cad/gs8-d2-v1/candidate-vertical/tests/test_catch_extended.py

Pure standard library (no CAD). review-2026-10-12-corrective/catch-extended/catch-extended-<variant>.json is made by
catch_extended_cases.py from the committed STEPs. This test keeps that record honest and visible:
- it is bound to the committed manifest, every committed STEP, the committed verification.json and the current
  sources (j7_collar_checks.py, model.py, steps.py, r7 checks.py, the script itself);
- its validation case reproduces the committed 'stub_tilt_on_joint_edge' rows exactly (machinery check);
- it reports the catch as FAILING (decision 16 open) with the yaw (Y2) and full-clearance tilt (T02) cases failing,
  and every failing row is below the unchanged r7 window rule. Nobody can drop or soften the finding quietly: a pass
  needs new geometry, a re-export and these cases folded into j7_collar_checks.STUB_CASES (README).
"""
import hashlib
import json
import sys
import unittest
from pathlib import Path

CV = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CV))
from cv_io import read_text   # noqa: E402

DIR = CV / 'review-2026-10-12-corrective' / 'catch-extended'
VARIANTS = ('compact-kowa_lm6hc', 'compact-fujinon_hf6xa', 'original-kowa_lm6hc')
REQUIRED = ('compact-kowa_lm6hc',)
MUST_FAIL = ('T02_tilt_on_joint_edge', 'Y2_yaw_pivot_xplus')
WORST_GAP_RULE = 0.10            # r7 check_roll_catch window rule: worst offset >= 0.10 mm (unchanged)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def records():
    return {v: DIR / ('catch-extended-%s.json' % v) for v in VARIANTS if (DIR / ('catch-extended-%s.json' % v)).exists()}


class CatchExtended(unittest.TestCase):
    def test_required_records_exist(self):
        for v in REQUIRED:
            self.assertTrue((DIR / ('catch-extended-%s.json' % v)).exists(), v)
        self.assertTrue((DIR / 'catch_extended_cases.py').exists())
        self.assertTrue((DIR / 'README.md').exists())

    def test_bound_to_committed_export(self):
        for v, p in records().items():
            rec = json.loads(read_text(p))
            out = CV / 'out' / v
            meta = json.loads(read_text(out / 'manifest.json'))
            self.assertEqual(rec['variant'], v)
            self.assertEqual(rec['manifest'], 'out/%s/manifest.json' % v)
            self.assertEqual(rec['manifest_sha256'], sha(out / 'manifest.json'), v)
            self.assertEqual(rec['verification_sha256'], sha(out / 'verification.json'), v)
            self.assertEqual(set(rec['step_sha256']), {r['id'] for r in meta['rows']}, v)
            for k, h in rec['step_sha256'].items():
                self.assertEqual(h, meta['files']['step/%s.step' % k], (v, k))
                self.assertEqual(h, sha(out / 'step' / ('%s.step' % k)), (v, k))
            self.assertTrue(rec['sources_stable_during_run'], v)
            self.assertEqual(set(rec['sources']), {'j7_collar_checks.py', 'model.py', 'steps.py', '../checks.py',
                                                   'review-2026-10-12-corrective/catch-extended/catch_extended_cases.py'})
            for rel, h in rec['sources'].items():
                self.assertEqual(h, sha(CV / rel), (v, rel))

    def test_validation_reproduces_committed_rows(self):
        for v, p in records().items():
            rec = json.loads(read_text(p))
            val = rec['cases'][0]
            self.assertEqual(val['case'], 'tilt_on_joint_edge')
            self.assertTrue(rec['validation']['matches_committed'], v)
            self.assertEqual(val['validation_mismatch'], [], v)
            self.assertGreater(val['validation_rows_compared'], 0)
            self.assertEqual(val['validation_rows_compared'], val['validation_committed_rows'], v)

    def test_catch_reported_failing(self):
        for v, p in records().items():
            rec = json.loads(read_text(p))
            self.assertEqual(rec['status'], 'fail', v)
            self.assertTrue(rec['catch'].startswith('OPEN'), v)
            for c in MUST_FAIL:
                self.assertIn(c, rec['failing_cases'], (v, c))
            cases = {c['case']: c for c in rec['cases']}
            for c in MUST_FAIL:
                self.assertTrue(cases[c]['feasible'], (v, c))
                self.assertLessEqual(cases[c]['stub_stock_overlap_mm3'], rec['feasible_overlap_mm3'], (v, c))
            bad = [r for r in rec['checks'] if r['status'] == 'fail']
            self.assertTrue(bad, v)
            self.assertEqual({r['stub_case'] for r in bad}, set(rec['failing_cases']), v)
            for r in bad:
                if r.get('item') == 'window':
                    self.assertTrue(r['worst_gap'] < WORST_GAP_RULE or r['centred_gap'] < 0.30, r['id'])
            for c in rec['cases']:                  # every graded pose carries its rows; blocked poses say why
                if c['case'].startswith('info_'):
                    self.assertNotIn('rows', c)
                elif c['feasible']:
                    self.assertGreater(c['rows'], 0, (v, c['case']))
                else:
                    self.assertGreater(c['stub_stock_overlap_mm3'], rec['feasible_overlap_mm3'], (v, c['case']))

    def test_no_local_paths(self):
        for v, p in records().items():
            raw = read_text(p)
            for bad in ('C:', 'Users', 'AppData', chr(92)):
                self.assertNotIn(bad, raw, (v, bad))


if __name__ == '__main__':
    unittest.main(verbosity=2)

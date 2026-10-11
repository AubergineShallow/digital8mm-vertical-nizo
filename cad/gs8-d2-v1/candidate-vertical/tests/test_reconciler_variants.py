# SPDX-License-Identifier: MIT
"""FP-13 (review 2026-10-10 VN-27): the reconciler requires a full audit for every variant.

Run:  run_locked.py -- cad/gs8-d2-v1/candidate-vertical/tests/test_reconciler_variants.py

reconcile_review_evidence.py gates out/<variant>/verification.json and print-checks.json for compact-fujinon_hf6xa
and original-kowa_lm6hc: each must exist, bind its own variant manifest and the current verifier, the main audit may
fail only on the shared pi5/cooler witness, and the print failures must equal the accepted (empty) set. The test
writes a valid synthetic pair into a light copy of the tree (tests/_evidence_fixture.py), confirms no variant finding
for that variant, then removes, rebinds or adds a failure and confirms each produces its finding. The reconciler must
never write while any gate fails. CAD-free; the live tree is never touched.
"""
from pathlib import Path
import json
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import _evidence_fixture as FX  # noqa: E402
import reconcile_review_evidence as R  # noqa: E402

FIXTURE = None
COOLER = dict(category='interference', id='pi5/cooler', status='fail')


def setUpModule():
    global FIXTURE
    FIXTURE = FX.Fixture()


def tearDownModule():
    FIXTURE.cleanup()


def put(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2), encoding='utf-8', newline='\n')


def valid_pair(cv, v, checks=None, failing=None):
    d = cv / 'out' / v
    mh = FX.sha(d / 'manifest.json')
    put(d / 'verification.json', dict(manifest_sha256=mh, verification_source_sha256=FX.sha(cv / 'verify_candidate.py'),
                                      checks=[dict(COOLER)] if checks is None else checks, summary={}))
    put(d / 'print-checks.json', dict(manifest_sha256=mh, verification_source_sha256=FX.sha(cv / 'verify_print_checks.py'),
                                      failing={} if failing is None else failing, summary={}))


def reconcile(cv):
    target = cv / 'out/compact-kowa_lm6hc/current-review-evidence.json'
    h = FX.sha(target)
    rc, so, se = FX.run(cv / 'reconcile_review_evidence.py', '--write')
    assert 'Traceback' not in se, se[-2000:]
    assert FX.sha(target) == h, 'the reconciler wrote while a gate failed'
    return rc, FX.first_json(so)['failures']


def variant_findings(failures, v):
    return [f for f in failures if f[0] == 'variant_audit:' + v or (len(f) > 1 and f[1] == v)]


class TestVariantAuditGate(unittest.TestCase):
    V = 'compact-fujinon_hf6xa'

    def test_declared_for_every_other_variant(self):
        self.assertEqual(sorted(R.VARIANT_AUDITS), sorted(set(FX.VARIANTS) - {'compact-kowa_lm6hc'}))
        self.assertEqual(dict(R.VARIANT_REPORTS), {'verification.json': 'verify_candidate.py',
                                                  'print-checks.json': 'verify_print_checks.py'})

    def test_valid_pair_passes_the_variant_gate(self):
        cv = FIXTURE.clone()
        for v in R.VARIANT_AUDITS:
            valid_pair(cv, v)
        rc, failures = reconcile(cv)
        for v in R.VARIANT_AUDITS:
            self.assertEqual(variant_findings(failures, v), [], v)

    def test_missing_report_fails(self):
        for name, _ in R.VARIANT_REPORTS:
            cv = FIXTURE.clone()
            valid_pair(cv, self.V)
            (cv / 'out' / self.V / name).unlink()
            rc, failures = reconcile(cv)
            self.assertEqual(rc, 1)
            got = variant_findings(failures, self.V)
            self.assertTrue(got and got[0][0] == 'variant_audit:' + self.V, (name, got))

    def test_foreign_manifest_and_stale_verifier_fail(self):
        for key, value, word in (('manifest_sha256', 'f' * 64, 'Different mechanical snapshot'),
                                 ('verification_source_sha256', '0' * 64, 'Different verifier')):
            for name, _ in R.VARIANT_REPORTS:
                cv = FIXTURE.clone()
                valid_pair(cv, self.V)
                p = cv / 'out' / self.V / name
                j = json.loads(p.read_text(encoding='utf-8'))
                j[key] = value
                put(p, j)
                rc, failures = reconcile(cv)
                self.assertEqual(rc, 1)
                got = variant_findings(failures, self.V)
                self.assertTrue(got and got[0][1] == word, (key, name, got))

    def test_new_rigid_fault_or_missing_witness_fails(self):
        for checks in ([dict(COOLER), dict(category='driver', id='p_x', status='fail')], []):
            cv = FIXTURE.clone()
            valid_pair(cv, self.V, checks=checks)
            rc, failures = reconcile(cv)
            self.assertEqual(rc, 1)
            got = variant_findings(failures, self.V)
            self.assertTrue(got and got[0][1] == 'New active rigid fault', (checks, got))

    def test_print_failure_is_a_finding(self):
        cv = FIXTURE.clone()
        valid_pair(cv, self.V, failing={'bed_chamfer': ['panel']})
        rc, failures = reconcile(cv)
        self.assertEqual(rc, 1)
        got = variant_findings(failures, self.V)
        self.assertEqual([f[0] for f in got], ['print_failures_differ'], got)


if __name__ == '__main__':
    unittest.main(verbosity=2)

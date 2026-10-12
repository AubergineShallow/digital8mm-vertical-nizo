"""The guide must not hide failing catch evidence or accept a stale rerun."""
from pathlib import Path
import copy
import hashlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'guide'))
from followup_guide_support import (CATCH_DIR, LEGACY_HELPER_SHA256, LEGACY_RECOMPUTE_PURPOSE,
                                    bind, validate_catch)


def fixture():
    case = dict(id='stub_case:feasibility', category='roll_catch', item='stub_feasibility',
                status='pass', case='case', stub_case='case', feasible=True,
                stub_stock_overlap_mm3=0.0, joint_face_gap_range_mm=[0., .2399520144])
    rows = [case,
            dict(id='stub_case:window', category='roll_catch', item='window',
                 status='fail', stub_case='case', stub_feasible=True, worst_gap=.084, centred_gap=.355),
            dict(id='stub_pose_coverage', category='roll_catch', item='stub_pose_coverage',
                 status='pass', cases=['case'], pose_count=1, feasible_count=1, errors=[])]
    report = dict(status='fail', variant='compact-kowa_lm6hc', purpose=LEGACY_RECOMPUTE_PURPOSE,
                  sources={CATCH_DIR + '/catch_extended_cases.py': LEGACY_HELPER_SHA256},
                  sources_stable_during_run=True, inputs_stable_during_run=True,
                  freshness_errors=[], checks=copy.deepcopy(rows),
                  cases=[copy.deepcopy(case)], failing_rows=['stub_case:window'],
                  validation=dict(matches_committed=True, mismatch=[], missing=[],
                                  rows_compared=3, committed_rows=3))
    return report, {'checks': rows}


class FollowupGuideBindings(unittest.TestCase):
    def test_current_failure_is_preserved_in_the_caption(self):
        report, main = fixture()
        summary = validate_catch(report, main)
        self.assertEqual(summary['status'], 'fail')
        self.assertEqual(summary['minimum_worst_window_gap_mm'], .084)
        self.assertEqual(summary['failing_rows'], 1)
        self.assertEqual(summary['feasible_functional_rows'], 1)
        self.assertEqual(summary['feasible_window_rows'], 1)
        self.assertEqual(summary['feasible_first_contact_rows'], 0)
        self.assertEqual(summary['blocked_legacy_diagnostic_rows'], 0)
        self.assertEqual(summary['maximum_feasible_joint_face_opening_mm'], .2399520144)
        self.assertEqual(summary['evidence_mode'], 'same_implementation_rerun')
        self.assertTrue(summary['geometry_recomputed'])
        self.assertFalse(summary['physical_qualified'])

    def test_blocked_legacy_diagnostics_do_not_inflate_feasible_counts(self):
        report, main = fixture()
        blocked = dict(id='stub_blocked:feasibility', category='roll_catch', item='stub_feasibility',
                       status='pass', case='blocked', stub_case='blocked', feasible=False,
                       legacy=True, legacy_blocked_diagnostic=True, stub_stock_overlap_mm3=2.0,
                       joint_face_gap_range_mm=[0., 2.0])
        diagnostic = dict(id='stub_blocked:window', category='roll_catch', item='window',
                          status='fail', stub_case='blocked', stub_feasible=False,
                          legacy_blocked_diagnostic=True, worst_gap=.001, centred_gap=.355)
        main['checks'].extend([blocked, diagnostic])
        main['checks'][2].update(cases=['case', 'blocked'], pose_count=2)
        report['checks'] = copy.deepcopy(main['checks'])
        report['cases'].append(copy.deepcopy(blocked))
        report['failing_rows'].append('stub_blocked:window')
        report['validation'].update(rows_compared=5, committed_rows=5)
        summary = validate_catch(report, main)
        self.assertEqual(summary['functional_rows'], 2)
        self.assertEqual(summary['feasible_functional_rows'], 1)
        self.assertEqual(summary['blocked_legacy_diagnostic_rows'], 1)
        self.assertEqual(summary['minimum_worst_window_gap_mm'], .001)
        self.assertEqual(summary['minimum_feasible_worst_window_gap_mm'], .084)
        self.assertEqual(summary['maximum_feasible_joint_face_opening_mm'], .2399520144)

    def test_functional_row_must_belong_to_a_classified_pose(self):
        report, main = fixture()
        main['checks'][1]['stub_case'] = 'unknown'
        report['checks'] = copy.deepcopy(main['checks'])
        with self.assertRaisesRegex(RuntimeError, 'lacks a feasible or blocked legacy pose'):
            validate_catch(report, main)

    def test_saved_full_audit_is_distinguished_from_recomputation(self):
        report, main = fixture()
        report.update(variant='compact-fujinon_hf6xa', evidence_mode='saved_full_audit',
                      geometry_recomputed=False)
        summary = validate_catch(report, main)
        self.assertEqual(summary['evidence_mode'], 'saved_full_audit')
        self.assertFalse(summary['geometry_recomputed'])
        self.assertEqual(summary['status'], 'fail')

    def test_authentic_alternate_variant_rerun_is_supported(self):
        report, main = fixture()
        for variant in ('compact-fujinon_hf6xa', 'original-kowa_lm6hc'):
            summary = validate_catch(dict(report, variant=variant), main)
            self.assertEqual(summary['evidence_mode'], 'same_implementation_rerun')
            self.assertTrue(summary['geometry_recomputed'])

    def test_saved_mode_cannot_claim_recomputation(self):
        report, main = fixture()
        report.update(evidence_mode='saved_full_audit', geometry_recomputed=True)
        with self.assertRaisesRegex(RuntimeError, 'must not claim'):
            validate_catch(report, main)

    def test_unknown_mode_and_unrecognized_legacy_format_are_rejected(self):
        report, main = fixture()
        for change in ({'evidence_mode': 'independent'}, {'variant': 'unrecognized-variant'},
                       {'purpose': 'similar purpose'}, {'sources': {}}):
            with self.assertRaisesRegex(RuntimeError, 'Absent or unknown'):
                validate_catch(dict(report, **change), main)

    def test_relabelled_failure_is_rejected(self):
        report, main = fixture()
        report['status'] = 'pass'
        report['failing_rows'] = []
        with self.assertRaisesRegex(RuntimeError, 'preserve'):
            validate_catch(report, main)

    def test_claimed_match_does_not_hide_changed_geometry_result(self):
        report, main = fixture()
        report['checks'][1]['worst_gap'] = .15
        with self.assertRaisesRegex(RuntimeError, 'differs'):
            validate_catch(report, main)

    def test_removed_case_is_rejected(self):
        report, main = fixture()
        report['cases'] = []
        with self.assertRaisesRegex(RuntimeError, 'accounting'):
            validate_catch(report, main)

    def test_changed_sources_during_rerun_are_rejected(self):
        report, main = fixture()
        report['sources_stable_during_run'] = False
        with self.assertRaisesRegex(RuntimeError, 'changed during'):
            validate_catch(report, main)

    def test_stale_or_changed_inputs_are_rejected(self):
        report, main = fixture()
        for change in ({'inputs_stable_during_run': False}, {'freshness_errors': None},
                       {'freshness_errors': ['stale main audit']}):
            changed = dict(report, **change)
            with self.assertRaisesRegex(RuntimeError, 'unstable inputs or stale'):
                validate_catch(changed, main)

    def test_missing_and_stale_files_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'alternate-report.json'
            path.write_text('{}', encoding='utf-8', newline='\n')
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            files = set()
            bind(path, digest, files)
            self.assertEqual(files, {path})
            path.write_text('{"status":"pass"}', encoding='utf-8', newline='\n')
            with self.assertRaisesRegex(RuntimeError, 'changed or is absent'):
                bind(path, digest, files)
            path.unlink()
            with self.assertRaisesRegex(RuntimeError, 'changed or is absent'):
                bind(path, digest, files)


if __name__ == '__main__':
    unittest.main(verbosity=2)

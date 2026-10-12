# SPDX-License-Identifier: MIT
"""CAD-free saved-receipt controls; mutations never alter committed audit evidence."""
from collections import Counter
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

CV = Path(__file__).resolve().parents[1]
SOURCE = CV / 'review-2026-10-12-corrective/catch-extended/catch_saved_receipt.py'
spec = importlib.util.spec_from_file_location('saved_catch_receipt_test', SOURCE)
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)
VARIANT = 'compact-kowa_lm6hc'


def summarize(main):
    counts = Counter(row['status'] for row in main['checks'])
    main['summary'] = {k: counts[k] for k in ('pass', 'fail', 'info')}
    main['geometry_computed_pass'] = counts['fail'] == 0


class _SavedMainFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # A real completed full audit supplies the control, never a claimed rerun.
        out = CV / 'out' / VARIANT
        cls.meta = json.loads((out / 'manifest.json').read_text(encoding='utf-8'))
        cls.main = json.loads((out / 'verification.json').read_text(encoding='utf-8'))

    def mutated(self, change):
        value = copy.deepcopy(self.main)
        change(value)
        summarize(value)
        return value

    def row(self, value, ident):
        return next(r for r in value['checks'] if r['category'] == 'roll_catch' and r['id'] == ident)


class SavedCatchRows(_SavedMainFixture):
    def test_exact_main_rows_and_all_cases_preserved_without_cad(self):
        cad_before = {name for name in sys.modules if name == 'cadquery' or name.startswith('OCP')}
        result = S.validate_saved_rows(self.meta, self.main)
        expected = [r for r in self.main['checks'] if r['category'] == 'roll_catch' and
                    r['id'].startswith('stub_') and r['id'] != 'stub_production_context']
        self.assertEqual(result['checks'], expected)
        self.assertEqual(len(result['cases']), 69)
        self.assertEqual(result['coverage']['s_values'], [i / 4 for i in range(13)])
        self.assertEqual(result['coverage']['feasible_count'], 49)
        self.assertEqual({name for name in sys.modules if name == 'cadquery' or name.startswith('OCP')}, cad_before)

    def test_failure_is_preserved_verbatim(self):
        ident = 'stub_Y2_yaw_pivot_xplus:window@s0.00'
        value = self.mutated(lambda m: self.row(m, ident).update(status='fail', error='planted obstruction'))
        result = S.validate_saved_rows(self.meta, value)
        self.assertEqual(next(r for r in result['checks'] if r['id'] == ident), self.row(value, ident))
        case = next(r for r in result['cases'] if r['case'] == 'Y2_yaw_pivot_xplus')
        self.assertIn(ident, case['fail_rows'])

    def test_missing_yaw_coupled_translation_legacy_and_bfar_rows_fail(self):
        for ident in ('stub_Y2_yaw_pivot_xplus:feasibility', 'stub_YP_yaw_m_xminus_near:feasibility',
                      'stub_C_xyz_mmm_near:feasibility', 'stub_CI_xyz_ppp_far:feasibility',
                      'stub_P_full_y_clearance:feasibility', 'stub_tilt_on_tenon_top_edge:feasibility',
                      'stub_T02_tilt_on_joint_edge:window@s3.00',
                      'stub_T02_tilt_on_joint_edge:first_contact@s3.00'):
            value = self.mutated(lambda m: m['checks'].remove(self.row(m, ident)))
            with self.subTest(ident=ident), self.assertRaises(ValueError):
                S.validate_saved_rows(self.meta, value)

    def test_duplicate_row_or_removed_offset_sample_fails(self):
        ident = 'stub_T02_tilt_on_joint_edge:first_contact@s0.00'
        for change in (lambda m: m['checks'].append(copy.deepcopy(self.row(m, ident))),
                       lambda m: self.row(m, ident)['cases'].pop(),
                       lambda m: self.row(m, 'stub_T02_tilt_on_joint_edge:window@s0.00')['gaps'].pop('+0.00/+0.55/+1')):
            with self.subTest(change=change), self.assertRaises(ValueError):
                S.validate_saved_rows(self.meta, self.mutated(change))

    def test_threshold_pose_and_feasibility_weakening_fail(self):
        for ident, values in (
                ('stub_T02_tilt_on_joint_edge:first_contact@s0.00', {'rule_margin_deg': .5}),
                ('stub_T02_tilt_on_joint_edge:window@s0.00', {'window_deg': 1.}),
                ('stub_T02_tilt_on_joint_edge:window@s0.00', {'rule': 'centred >= 0.20, worst offset >= 0.05'}),
                ('stub_T02_tilt_on_joint_edge:feasibility', {'feasible_overlap_mm3': .01}),
                ('stub_T02_tilt_on_joint_edge:feasibility', {'stub_stock_overlap_mm3': .1}),
                ('stub_T02_tilt_on_joint_edge:feasibility', {'minimum_axial_engagement_mm': 0.}),
                ('stub_T02_tilt_on_joint_edge:feasibility', {'shift_mm': [0, .1, 0]}),
                ('stub_pose_coverage', {'s_values': [0., 3.]}),
                ('stub_pose_coverage', {'production_insert_supplied': False})):
            value = self.mutated(lambda m: self.row(m, ident).update(values))
            with self.subTest(ident=ident, values=values), self.assertRaises(ValueError):
                S.validate_saved_rows(self.meta, value)

    def test_subthreshold_sample_cannot_be_relabelled_pass(self):
        def window(m):
            row = self.row(m, 'stub_T02_tilt_on_joint_edge:window@s0.00')
            row['gaps']['-0.55/+0.00/+1'] = .078
            row['worst_gap'] = .078
        def contact(m):
            row = self.row(m, 'stub_T02_tilt_on_joint_edge:first_contact@s0.00')
            case = row['cases'][0]
            case.update(pcb_cover_deg=case['metal_deg'] + .5, margin_deg=.5, pcb_cover_to=['panel'])
        for change in (window, contact):
            with self.subTest(change=change), self.assertRaises(ValueError):
                S.validate_saved_rows(self.meta, self.mutated(change))

    def test_partial_scope_summary_or_physical_claim_fails(self):
        for field, value in (('scope', 'j7'), ('physical_qualified', True),
                             ('summary', {'pass': 0, 'fail': 0, 'info': 0}),
                             ('geometry_computed_pass', True)):
            with self.subTest(field=field), self.assertRaises(ValueError):
                S.validate_saved_rows(self.meta, dict(self.main, **{field: value}))


class SavedCatchBindings(_SavedMainFixture):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.cv = Path(self.temp.name) / 'candidate-vertical'
        self.out = self.cv / 'out' / VARIANT
        self.out.mkdir(parents=True)
        for name in S.SOURCES:
            path = self.cv / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('# synthetic binding fixture: ' + name, encoding='utf-8', newline='\n')
        self.fm, self.fv = copy.deepcopy(self.meta), copy.deepcopy(self.main)
        self.fm['files'] = {name: '' for name in self.fm['files'] if name.endswith('.step')}
        for name in self.fm['files']:
            path = self.out / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(('synthetic STEP fixture: ' + name).encode('utf-8'))
            self.fm['files'][name] = S.sha(path)
        self.fm['sources'] = {'candidate-vertical/model.py': S.sha(self.cv / 'model.py')}
        self.fv['checks'] = [r for r in self.fv['checks'] if r['category'] != 'source_binding']
        self.fv['checks'].append(dict(category='source_binding', id='candidate-vertical/model.py', status='pass'))
        for row in self.fv['checks']:
            if row['category'] == 'integrity':
                row['step_sha256'] = self.fm['files']['step/' + row['id'] + '.step']
        self.row(self.fv, 'stub_production_context')['step_sha256'] = self.fm['files']['step/tab_catch_insert.step']
        context = S.one(self.fv['checks'], 'j7_float', 'camera_model_match')
        context.update(j7_collar_checks_sha256=S.sha(self.cv / 'j7_collar_checks.py'),
                       steps_sha256=S.sha(self.cv / 'steps.py'), r7_checks_sha256=S.sha(self.cv.parent / 'checks.py'))
        self.fv.update(verification_source_sha256=S.sha(self.cv / 'verify_candidate.py'),
                       state_model_sha256=S.sha(self.cv / 'steps.py'))
        self.write_inputs()

    def write_inputs(self):
        (self.out / 'manifest.json').write_text(json.dumps(self.fm), encoding='utf-8', newline='\n')
        self.fv['manifest_sha256'] = S.sha(self.out / 'manifest.json')
        summarize(self.fv)
        (self.out / 'verification.json').write_text(json.dumps(self.fv), encoding='utf-8', newline='\n')

    def test_receipt_explicitly_derives_and_preserves_main_failure(self):
        receipt = S.build_receipt(self.cv, VARIANT)
        self.assertEqual(receipt['evidence_mode'], 'saved_full_audit')
        self.assertFalse(receipt['geometry_recomputed'])
        self.assertFalse(receipt['physical_qualified'])
        self.assertEqual(receipt['main_summary'], self.fv['summary'])
        self.assertFalse(receipt['main_geometry_computed_pass'])
        self.assertIn('assembly.step', receipt['input_file_sha256'])
        self.assertEqual(receipt['verification_sha256'], S.sha(self.out / 'verification.json'))
        self.assertEqual(receipt['validation']['method'], 'exact_saved_rows_and_policy')

    def test_derived_receipt_preserves_catch_failure(self):
        ident = 'stub_Y2_yaw_pivot_xplus:window@s0.00'
        self.row(self.fv, ident).update(status='fail', error='planted obstruction')
        self.write_inputs()
        receipt = S.build_receipt(self.cv, VARIANT)
        self.assertEqual(receipt['status'], 'fail')
        self.assertEqual(receipt['failing_rows'], [ident])
        self.assertEqual(next(r for r in receipt['checks'] if r['id'] == ident), self.row(self.fv, ident))

    def test_stale_manifest_main_and_context_sources_fail(self):
        for name in ('model.py', 'steps.py', 'j7_collar_checks.py', '../checks.py', 'verify_candidate.py'):
            path = self.cv / name
            original = path.read_bytes()
            path.write_bytes(original + b'\nchanged')
            try:
                with self.subTest(source=name), self.assertRaises(ValueError):
                    S.build_receipt(self.cv, VARIANT)
            finally:
                path.write_bytes(original)

    def test_changed_production_insert_part_or_assembly_step_fails(self):
        for name in ('step/tab_catch_insert.step', 'step/tub.step', 'assembly.step'):
            path = self.out / name
            original = path.read_bytes()
            path.write_bytes(original + b'changed')
            try:
                with self.subTest(step=name), self.assertRaises(ValueError):
                    S.build_receipt(self.cv, VARIANT)
            finally:
                path.write_bytes(original)

    def test_changed_inputs_or_sources_during_derivation_fail(self):
        original = S.validate_saved_rows
        for path in (self.out / 'verification.json', self.out / 'manifest.json',
                     self.out / 'step/tab_catch_insert.step', self.cv / S.SELF):
            before = path.read_bytes()
            def change(meta, main):
                result = original(meta, main)
                path.write_bytes(before + b' ')
                return result
            try:
                with self.subTest(path=path.name), patch.object(S, 'validate_saved_rows', side_effect=change), self.assertRaises(ValueError):
                    S.build_receipt(self.cv, VARIANT)
            finally:
                path.write_bytes(before)


if __name__ == '__main__':
    unittest.main(verbosity=2)

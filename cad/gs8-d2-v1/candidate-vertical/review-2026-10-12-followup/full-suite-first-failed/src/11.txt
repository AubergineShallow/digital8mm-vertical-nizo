# SPDX-License-Identifier: MIT
"""Historical failure witnesses and fail-closed main bonded-catch acceptance.

Pure standard library. Run through run_locked.py. PosePolicyUnits and
HistoricalCatchFailure can run before re-export. ProductionAcceptance requires
all three final main verification records; stale geometry cannot pass.
"""
import copy
from contextlib import nullcontext
import hashlib
import importlib.util
import itertools
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

CV = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CV))
import j7_collar_checks as J

DIR = CV / 'review-2026-10-12-corrective' / 'catch-extended'
VARIANTS = ('compact-kowa_lm6hc', 'compact-fujinon_hf6xa', 'original-kowa_lm6hc')
BASELINE = DIR / 'catch-extended-compact-kowa_lm6hc.json'
BASELINE_SHA256 = 'd6c53a0a255120692c1db158d1869a2d34772178191bd3a96edc8d3216fded44'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def fixture():
    model = SimpleNamespace(TAB_CATCH_TENON=dict(x=(-12.9, -9.8), t=1.6, h=10.), TAB_CATCH_SPLIT_Z=83.5)
    web = dict(x=(-14.5, -8.2), y=(10., 13.), z=(79., 98.))
    bounds = (-13., -9.7, 10., 11.8, 83.4, 93.6)
    poses = J.stub_pose_table(model, web, bounds)
    L = SimpleNamespace(ROLL_CATCH=dict(J.STUB_CONTACT_RULES))
    CK = SimpleNamespace(J7_RUNNING=.1, J7_TOL=.001)
    rows = [dict(item='window', s=0., status='pass', centred_gap=.45, worst_gap=.15),
            dict(item='first_contact', s=0., status='pass', rule_margin_deg=1.)]
    records = {p['case']: dict(p, feasible=True, geometry_valid=True,
                              stub_stock_overlap_mm3=0., feasible_overlap_mm3=.001,
                              rows=copy.deepcopy(rows)) for p in poses}
    return model, web, bounds, poses, records, L, CK


class HistoricalCatchFailure(unittest.TestCase):
    def test_immutable_reviewed_failure(self):
        # Deliberately binds historical bytes, NOT today's model/STEP: no hybrid
        # baseline can turn the witnessed failing geometry into a passing record.
        self.assertEqual(sha(BASELINE), BASELINE_SHA256)
        rec = json.loads(BASELINE.read_text(encoding='utf-8'))
        self.assertEqual(rec['status'], 'fail')
        self.assertTrue(rec['sources_stable_during_run'])
        self.assertTrue(rec['validation']['matches_committed'])
        cases = {c['case']: c for c in rec['cases']}
        for name, gap, count in (('T02_tilt_on_joint_edge', .084, 13), ('Y2_yaw_pivot_xplus', .078, 7)):
            c = cases[name]
            self.assertTrue(c['feasible'])
            self.assertLessEqual(c['stub_stock_overlap_mm3'], .001)
            self.assertEqual(c['min_worst_window_gap'], gap)
            self.assertEqual(len(c['fail_rows']), count)
            self.assertIn(name, rec['failing_cases'])
        for r in rec['checks']:
            if r['item'] == 'window':
                self.assertEqual(r['rule'], 'centred >= 0.30, worst offset >= 0.10')
            elif r['item'] == 'first_contact':
                self.assertEqual(r['rule_margin_deg'], 1.)


class PosePolicyUnits(unittest.TestCase):
    def setUp(self):
        self.model, self.web, self.bounds, self.poses, self.records, self.L, self.CK = fixture()

    def errors(self):
        return J.stub_acceptance_errors(self.poses, self.records, (0.,), self.L, self.CK)

    def test_complete_policy(self):
        self.assertEqual(len(self.poses), 69)
        self.assertEqual(self.errors(), [])
        self.assertEqual([p['case'] for p in self.poses[:5]], [r[0] for r in J.STUB_CASES])
        self.assertEqual(J.STUB_CASES, (('x+0.1', (.1, 0., 0.), 0., 0.),
            ('x-0.1', (-.1, 0., 0.), 0., 0.), ('film+y0.05', (0., .05, 0.), 0., 0.),
            ('tilt_on_joint_edge', (0., 0., 0.), -1., 0.),
            ('tilt_on_tenon_top_edge', (0., 0., 0.), 1., 1.)))

    def test_actual_pocket_drives_full_tilt(self):
        a = next(p for p in self.poses if p['case'] == 'T02_tilt_on_joint_edge')
        self.assertAlmostEqual(a['rotations'][0]['deg'], -math.degrees(math.atan(.2 / 10.)))
        tighter = list(self.bounds); tighter[3] -= .05
        b = next(p for p in J.stub_pose_table(self.model, self.web, tighter)
                 if p['case'] == 'T02_tilt_on_joint_edge')
        self.assertAlmostEqual(b['rotations'][0]['deg'], -math.degrees(math.atan(.15 / 10.)))

    def test_coupled_core_obeys_pocket_xy_and_explicit_z_screen(self):
        tn, zs, yin = self.model.TAB_CATCH_TENON, self.model.TAB_CATCH_SPLIT_Z, self.web['y'][0]
        corners = list(itertools.product(tn['x'], (yin, yin + tn['t']), (zs, zs + tn['h'])))
        for pose in (p for p in self.poses if p['family'] == 'coupled_xyz'):
            if not pose['fits_pocket_bounds']:
                self.assertTrue(any(lo > hi for lo, hi in pose['translation_intervals_mm']))
                continue
            for point in corners:
                for r in pose['rotations']:
                    point = J._rotate_point(point, r['axis'], r['pivot'], r['deg'])
                point = [v + d for v, d in zip(point, pose['shift_mm'])]
                for i, v in enumerate(point):
                    lower = self.bounds[2 * i] if i < 2 else zs - J.STUB_UNDERSEAT_SCREEN_MM
                    self.assertGreaterEqual(v, lower - 1e-9)
                    self.assertLessEqual(v, self.bounds[2 * i + 1] + 1e-9)

    def test_missing_yaw_rejected(self):
        self.poses = [p for p in self.poses if p['family'] != 'yaw_z']
        self.records = {p['case']: self.records[p['case']] for p in self.poses}
        self.assertTrue(any('yaw' in e or 'Y2' in e for e in self.errors()))

    def test_missing_full_pocket_yaw_rejected(self):
        self.poses = [p for p in self.poses if p['family'] != 'pocket_yaw_z']
        self.records = {p['case']: self.records[p['case']] for p in self.poses}
        self.assertTrue(any('full-pocket yaw' in e for e in self.errors()))

    def test_full_pocket_yaw_exceeds_film_yaw(self):
        angles = {p['case']: abs(p['rotations'][0]['deg']) for p in self.poses if p['rotations']}
        self.assertAlmostEqual(angles['YP_yaw_p_xminus_near'], math.degrees(math.atan(.2 / 3.1)))
        self.assertGreater(angles['YP_yaw_p_xminus_near'], angles['Y1_yaw_pivot_xminus'])

    def test_missing_coupled_rejected(self):
        self.poses = [p for p in self.poses if p['family'] != 'coupled_xyz']
        self.records = {p['case']: self.records[p['case']] for p in self.poses}
        self.assertTrue(any('coupled' in e for e in self.errors()))

    def test_missing_translation_endpoint_rejected(self):
        self.poses = [p for p in self.poses if p['case'] != 'P_full_y_clearance']
        self.records.pop('P_full_y_clearance')
        self.assertTrue(any('translation' in e for e in self.errors()))

    def test_translation_endpoints_cover_pocket_corners(self):
        poses = {p['case']: p for p in self.poses}
        self.assertAlmostEqual(poses['P_full_y_clearance']['shift_mm'][1], .2)
        self.assertAlmostEqual(poses['P_underseat_zminus']['shift_mm'][2], -.1)
        got = {tuple(round(x, 6) for x in p['shift_mm']) for p in self.poses
               if p['case'].startswith('P_corner_') or p['case'] in ('x+0.1', 'x-0.1')}
        self.assertEqual(got, set(itertools.product((-.1, .1), (0., .2), (-.1, 0.))))

    def test_missing_one_coupled_sign_rejected(self):
        self.poses = [p for p in self.poses if p['case'] != 'C_xyz_ppp_near']
        self.records.pop('C_xyz_ppp_near')
        self.assertTrue(any('coupled' in e for e in self.errors()))

    def test_missing_quarter_coupled_family_rejected(self):
        self.poses = [p for p in self.poses if p.get('rotation_fraction') != .25]
        self.records = {p['case']: self.records[p['case']] for p in self.poses}
        self.assertTrue(any('0.25' in e for e in self.errors()))

    def test_cutter_overlap_does_not_set_underseat_screen(self):
        changed = list(self.bounds); changed[4] -= .5
        other = J.stub_pose_table(self.model, self.web, changed)
        for old, new in zip(self.poses, other):
            self.assertEqual(old['shift_mm'], new['shift_mm'])
        under = next(p for p in self.poses if p['case'] == 'P_underseat_zminus')
        self.assertAlmostEqual(under['minimum_axial_engagement_mm'], 9.9)

    def test_lost_engagement_rejected(self):
        self.records['P_underseat_zminus']['minimum_axial_engagement_mm'] = 0
        self.assertTrue(any('feasibility' in e for e in self.errors()))

    def test_missing_feasible_failure_cannot_be_hidden(self):
        self.records['Y2_yaw_pivot_xplus']['rows'].pop()
        self.assertTrue(any('full-BFAR' in e for e in self.errors()))
        self.records['Y2_yaw_pivot_xplus']['rows'][0].update(worst_gap=.078, status='pass')
        self.assertTrue(any('relabelled' in e for e in self.errors()))

    def test_feasible_case_cannot_be_silently_excluded(self):
        self.records['Y1_yaw_pivot_xminus'].update(feasible=False, rows=[])
        self.assertTrue(any('feasibility' in e for e in self.errors()))

    def test_collision_cannot_be_labelled_feasible(self):
        self.records['T02_tilt_on_joint_edge']['stub_stock_overlap_mm3'] = .002
        self.assertTrue(any('feasibility' in e for e in self.errors()))

    def test_actual_overlap_feasibility_and_nan_fail_closed(self):
        class Solid:
            def isValid(self): return True
            def Solids(self): return [self]
        for volume, feasible, valid in ((0., True, True), (.0011, False, True), (float('nan'), False, False)):
            stock = SimpleNamespace(intersect=lambda _: SimpleNamespace(Volume=lambda: volume))
            result = J.stub_pose_feasibility(stock, Solid(), self.poses[0])
            self.assertEqual((result['feasible'], result['geometry_valid']), (feasible, valid))
        clear = SimpleNamespace(intersect=lambda _: SimpleNamespace(Volume=lambda: 0.))
        pose = dict(self.poses[0], fits_pocket_bounds=False)
        self.assertTrue(J.stub_pose_feasibility(clear, Solid(), pose)['feasible'],
                        'rectangular proxy must not veto an actually clear, engaged production pose')

    def test_threshold_weakening_rejected(self):
        for key, value in (('window_gap', .29), ('margin_deg', .9), ('window_deg', 1.3), ('scan_deg', 15.)):
            with self.subTest(key=key):
                old = self.L.ROLL_CATCH[key]; self.L.ROLL_CATCH[key] = value
                self.assertTrue(self.errors()); self.L.ROLL_CATCH[key] = old
        for key, value in (('J7_RUNNING', .09), ('J7_TOL', .002)):
            old = getattr(self.CK, key); setattr(self.CK, key, value)
            self.assertTrue(self.errors()); setattr(self.CK, key, old)
        with patch.object(J, 'STUB_FEASIBLE_OVERLAP_MM3', .01):
            self.assertTrue(self.errors())

    def test_camera_cache_retains_every_s_and_head(self):
        calls = []
        def build(L, s, head_side='both'):
            calls.append((s, head_side))
            return object()
        get = J.cached_camera_parts(build)
        for s in (0., .25, 3.):
            for side in ('both', '+Y', '-Y'):
                self.assertIs(get(self.L, s, side), get(self.L, s, side))
                self.assertIs(get(self.L, s, side), get(J.LayoutView(self.L), s, side))
        self.assertEqual(calls, list(itertools.product((0., .25, 3.), ('both', '+Y', '-Y'))))

    def test_main_pipeline_preserves_feasible_window_failures(self):
        # Exercise row retention through the actual main integration. CAD is
        # replaced by deterministic geometry doubles, not by a copied checker.
        class Shape:
            def isValid(self): return True
            def Solids(self): return [self]
            def intersect(self, other): return SimpleNamespace(Volume=lambda: 0.)
            def fuse(self, other): return self
            def clean(self): return self
            def Vertices(self): return [SimpleNamespace(Z=83.5, toTuple=lambda: (-12.9, 10., 83.5))]
        stock, stub = Shape(), Shape()
        bbox = SimpleNamespace(**{a + e: self.bounds[2 * i + j] for i, a in enumerate('xyz')
                                  for j, e in enumerate(('min', 'max'))})
        model = copy.copy(self.model)
        model.L = SimpleNamespace(tab_catch_boxes=lambda: [dict(self.web, side=1, kind='web')])
        model.tub_print_parts = lambda _: (stock, stub)
        model.tab_catch_split = lambda: dict(pocket=SimpleNamespace(BoundingBox=lambda: bbox))
        fake_rows = [('roll_catch', 'window@s0.00', dict(item='window', s=0., centred_gap=.4,
                       worst_gap=.078, status='fail')),
                     ('roll_catch', 'first_contact@s0.00', dict(item='first_contact', s=0.,
                       rule_margin_deg=1., status='pass'))]
        with patch.dict(sys.modules, {'cadquery': SimpleNamespace(), 'model': model,
                'j4_trial_geometry': SimpleNamespace(trial_layout=lambda *a, **k: nullcontext())}), \
                patch.object(J, 'transform_stub', return_value=stub), \
                patch.object(J, 'roll_catch_rows', return_value=fake_rows):
            out = J.roll_catch_stub_rows(self.L, {'tub': {'shape': Shape()}}, {}, self.CK, None,
                                        s_values=(0.,), parts_of=lambda *a, **k: {})
        index = {i: r for _, i, r in out}
        self.assertEqual(index['stub_Y2_yaw_pivot_xplus:window@s0.00']['status'], 'fail')
        self.assertEqual(index['stub_Y2_yaw_pivot_xplus:window@s0.00']['worst_gap'], .078)
        self.assertTrue(index['stub_Y2_yaw_pivot_xplus:feasibility']['feasible'])
        self.assertEqual(index['stub_pose_coverage']['errors'], [])


class ReceiptFreshness(unittest.TestCase):
    def test_stale_export_or_main_sources_cannot_pass_on_equal_numbers(self):
        spec = importlib.util.spec_from_file_location('catch_extended_cases', DIR / 'catch_extended_cases.py')
        helper = importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)
        with tempfile.TemporaryDirectory() as td:
            cad = Path(td); cv = cad / 'candidate-vertical'; cv.mkdir()
            for p in (cv / 'model.py', cv / 'j7_collar_checks.py', cv / 'steps.py', cad / 'checks.py'):
                p.write_text(p.name, encoding='utf-8', newline='\n')
            meta = dict(sources={'candidate-vertical/model.py': sha(cv / 'model.py')})
            context = dict(category='j7_float', id='camera_model_match', status='pass',
                j7_collar_checks_sha256=sha(cv / 'j7_collar_checks.py'), steps_sha256=sha(cv / 'steps.py'),
                r7_checks_sha256=sha(cad / 'checks.py'))
            ver = dict(manifest_sha256='selected-manifest', checks=[context,
                dict(category='roll_catch', id='stub_Y2:window', status='pass', worst_gap=.129)])
            self.assertEqual(helper.freshness_errors(meta, ver, 'selected-manifest', cv), [])
            self.assertTrue(helper.freshness_errors(meta, ver, 'new-manifest', cv))
            for path in (cv / 'model.py', cv / 'steps.py', cv / 'j7_collar_checks.py', cad / 'checks.py'):
                original = path.read_text(encoding='utf-8'); path.write_text(original + '\n# changed', encoding='utf-8', newline='\n')
                self.assertTrue(helper.freshness_errors(meta, ver, 'selected-manifest', cv), path.name)
                path.write_text(original, encoding='utf-8', newline='\n')
            ver['checks'].pop(0)
            self.assertTrue(helper.freshness_errors(meta, ver, 'selected-manifest', cv))


class ProductionAcceptance(unittest.TestCase):
    def test_all_variants_gate_production_poses(self):
        for variant in VARIANTS:
            with self.subTest(variant=variant):
                out = CV / 'out' / variant
                meta = json.loads((out / 'manifest.json').read_text(encoding='utf-8'))
                verification = json.loads((out / 'verification.json').read_text(encoding='utf-8'))
                rows = [r for r in verification['checks'] if r['category'] == 'roll_catch']
                index = {r['id']: r for r in rows}
                self.assertIn('stub_production_context', index)
                context = index['stub_production_context']
                self.assertTrue(context['manifest_file_binding'])
                self.assertEqual(context['step_sha256'], meta['files']['step/tab_catch_insert.step'])
                self.assertEqual(context['step_sha256'], sha(out / 'step/tab_catch_insert.step'))
                coverage = index['stub_pose_coverage']
                self.assertEqual(coverage['status'], 'pass', coverage.get('errors'))
                self.assertEqual(coverage['pose_count'], 69)
                self.assertTrue(coverage['production_insert_supplied'])
                self.assertEqual(coverage['errors'], [])
                for name in coverage['cases']:
                    feasibility = index['stub_' + name + ':feasibility']
                    functional = [r for r in rows if r.get('stub_case') == name and
                                  r['item'] in ('window', 'first_contact')]
                    self.assertEqual(feasibility['feasible_overlap_mm3'], .001)
                    if feasibility['feasible']:
                        self.assertLessEqual(feasibility['stub_stock_overlap_mm3'], .001)
                        self.assertEqual(len(functional), 2 * len(coverage['s_values']))
                        self.assertTrue(all(r['status'] == 'pass' for r in functional), name)
                    else:
                        self.assertTrue(feasibility['stub_stock_overlap_mm3'] > .001 or
                                        feasibility['minimum_axial_engagement_mm'] <= 0)
                        self.assertTrue(feasibility['exclusion_reason'])
                        if not feasibility.get('legacy'):
                            self.assertEqual(functional, [])
                    for r in functional:
                        if r['item'] == 'window':
                            self.assertEqual(r['rule'], 'centred >= 0.30, worst offset >= 0.10')
                            self.assertGreaterEqual(r['centred_gap'], .299)
                            self.assertGreaterEqual(r['worst_gap'], .099)
                        else:
                            self.assertEqual(r['rule_margin_deg'], 1.)


if __name__ == '__main__':
    unittest.main(verbosity=2)

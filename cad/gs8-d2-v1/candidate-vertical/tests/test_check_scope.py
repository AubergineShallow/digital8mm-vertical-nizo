# SPDX-License-Identifier: MIT
"""Check-scope fixes of the candidate (review VN-29, VN-30, VN-33..VN-38; fix FP-12).

Run:  run_locked.py -- cad/gs8-d2-v1/candidate-vertical/tests/test_check_scope.py

CAD-free fixtures for every rule in check_scope.py, the r7 reproduction of the ported stack-retention rules and the
EVF axis extraction, the steps.py microSD dog-leg, the obstacle-set rules of verify_wire_solids.py / verify_hdmi.py,
and, when the FP-12 run reports exist, their binding and key results (review-2026-10-10/fp12/ or out/<variant>/).
"""
import copy
import json
import math
import sys
import unittest
from pathlib import Path

CV = Path(__file__).resolve().parents[1]
R7 = CV.parent
for _p in (str(R7), str(CV)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
from cv_io import read_text    # noqa: E402
import check_scope as CS        # noqa: E402
import evidence_rules as ER     # noqa: E402
import steps as ST              # noqa: E402

FP12 = CV / 'review-2026-10-10/fp12'
VAR = 'compact-kowa_lm6hc'


def rd(p):
    return json.loads(read_text(p))


def sha(p):
    import hashlib
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


VERIFIER = {'microsd-service-dependency.json': 'verify_microsd_service.py', 'hdmi-solid-checks.json': 'verify_hdmi.py',
            'wire-solid-checks.json': 'verify_wire_solids.py', 'check-scope-checks.json': 'verify_check_scope.py'}


def report(name):
    """FP-12 run report bound to the current manifest AND written by the current verifier (selected folder first,
    then review-2026-10-10/fp12); None when no such run exists (the dependent test is skipped, never passed)."""
    mh = sha(CV / 'out' / VAR / 'manifest.json')
    vh = sha(CV / VERIFIER[name])
    for p in (CV / 'out' / VAR / name, FP12 / name):
        if p.exists():
            r = rd(p)
            if mh in (r.get('manifest_sha256'), r.get('mechanical_manifest_sha256')) and r.get('verification_source_sha256') == vh:
                stale = ER.dependency_mismatches(r, CV)   # fixup-1: a changed helper or input fails, never skips
                if stale:
                    raise AssertionError('%s binds the current manifest and verifier but stale helpers/inputs: %s'
                                         % (p.relative_to(CV).as_posix(), stale))
                return r
    return None


REF = rd(CV / 'structural-review/reference-export18-structural-binding.json')
OLD = rd(CV / 'history/reviewed-export18/manifest.json')
MANS = {p.parent.name: rd(p) for p in sorted((CV / 'out').glob('*/manifest.json')) if 'storage' in rd(p)}


class J4Screen(unittest.TestCase):          # VN-33
    def test_lower_set_is_the_reference_free_body(self):
        ids, res = CS.j4_lower_set(REF, OLD)
        self.assertEqual(set(ids), set(ST.GRIP + ['strap', 'p_grip'] + list(ST.POWER_IDS)))
        self.assertLess(abs(res), 1e-6)

    def test_per_variant_and_envelope(self):
        per = {v: CS.j4_screen(REF, OLD, m, ER.changed_rows) for v, m in MANS.items()}
        self.assertTrue(all(r['valid'] for r in per.values()))
        sup = rd(CV / 'structural-review/concealed-vent-structural.json')['coupon_load']
        self.assertAlmostEqual(per[VAR]['equal_share_plus_wiring_Nm'], sup['equal_share_plus_wiring_Nm'], places=12)
        o = per['original-kowa_lm6hc']
        self.assertAlmostEqual(o['equal_share_plus_wiring_Nm'], 0.9763, places=4)       # register: 0.976
        self.assertAlmostEqual(o['seventy_percent_share_plus_wiring_Nm'], 1.3669, places=4)  # register: 1.367
        env = CS.j4_envelope(per)
        self.assertFalse(env['compact_screen_covers']['original-kowa_lm6hc'])
        self.assertTrue(env['compact_screen_covers'][VAR])
        self.assertEqual(env['all_variants_screen_Nm'], 1.0)
        self.assertEqual(env['governing_variant'], 'original-kowa_lm6hc')
        # the generated supplement states the covering screen (regression: a stale supplement fails here)
        self.assertEqual(sup['all_variants_screen_Nm'], env['all_variants_screen_Nm'])
        self.assertEqual(sup['compact_screen_covers'], env['compact_screen_covers'])

    def test_lower_change_refused(self):
        bad = copy.deepcopy(MANS[VAR])
        for r in bad['rows']:
            if r['id'] == 'base_grip':
                r['mass_est_g'] += 5
        res = CS.j4_screen(REF, OLD, bad, ER.changed_rows)
        self.assertFalse(res['valid'])
        self.assertIn('base_grip', res['lower_rows_touched'])
        self.assertEqual(CS.j4_envelope({'x': res})['invalid_variants'], ['x'])


class AreaParityAndFlow(unittest.TestCase):  # VN-37, VN-36
    def test_series_section_governs_hot_bay(self):
        r = CS.branch_parity([dict(name='hot_bottom', mouth_mm2=324., series_mm2=[357., 299.4, 312.04]),
                              dict(name='hot_front', mouth_mm2=210., series_mm2=[540.])], 510.)
        self.assertFalse(r['passed'])
        self.assertAlmostEqual(r['effective_sum_mm2'], 509.4, places=9)
        self.assertEqual(r['branches'][0]['governed_by'], 'series section')
        self.assertEqual(r['branches'][1]['governed_by'], 'mouth')
        old = CS.branch_parity([dict(name='a', mouth_mm2=324., series_mm2=[]), dict(name='b', mouth_mm2=210., series_mm2=[])], 510.)
        self.assertTrue(old['passed'])     # the 9ced753 parallel-mouth comparison passed the same bay

    def test_cold_bay_passes(self):
        r = CS.branch_parity([dict(name='cold_rear', mouth_mm2=420., series_mm2=[500.]),
                              dict(name='cold_bottom', mouth_mm2=426., series_mm2=[437.4])], 420.)
        self.assertTrue(r['passed'])

    def el(self, k=1.0):
        return dict(cold_rear=dict(mouth_mm2=420 * k, series_mm2=1e9, series_min_mm2=1e9),
                    cold_bottom=dict(mouth_mm2=426 * k, series_min_mm2=1e9),
                    hot_bottom=dict(mouth_mm2=324 * k, series_min_mm2=299.4 * k),
                    hot_front=dict(mouth_mm2=210 * k, series_min_mm2=1e9),
                    cold_ports_mm2=420 * k, hot_ports_mm2=510 * k, csi_mm2=323.14 * k)

    def test_network(self):
        self.assertAlmostEqual(CS.series(846., 420.), 376.2, places=1)    # review orifice estimate
        rows = {r['case']: r for r in CS.flow_network(self.el())}
        n = rows['nominal']
        self.assertAlmostEqual(n['csi_share_of_intake'] + n['cold_path_share_of_intake'], 1.0, places=12)
        self.assertGreater(n['csi_eff_mm2'], 0.8 * n['cold_path_eff_mm2'])   # review: CSI >= 0.86x concealed path
        self.assertAlmostEqual(rows['csi_plugged']['intake_area_change_percent'], -100 * n['csi_share_of_intake'], places=9)
        self.assertLess(rows['set_down_on_table']['system_eff_mm2'], rows['hot_bottom_blocked']['system_eff_mm2'] + 1e-9)
        self.assertLess(rows['cold_bottom_strap_20_of_71']['intake_eff_mm2'], n['intake_eff_mm2'])
        scaled = {r['case']: r for r in CS.flow_network(self.el(3.0))}
        for c in rows:   # flow fractions do not depend on scale (or Cd): the fan curve is not needed for the split
            self.assertAlmostEqual(rows[c]['system_flow_ratio_vs_nominal'], scaled[c]['system_flow_ratio_vs_nominal'], places=12)


class HdmiFace(unittest.TestCase):           # VN-35
    def test_formula_sign_jump_is_carried(self):
        frames = []
        for i in range(61):                              # U turn in the XZ plane, width along Y
            th = math.pi * i / 60
            t = [math.cos(th + math.pi / 2), 0, math.sin(th + math.pi / 2)]
            n = [-math.cos(th), 0, -math.sin(th)]
            if i > 30:
                n = [-x for x in n]                      # formula flips its sign half way
            frames.append(dict(point=[5 * math.cos(th), 0, 5 * math.sin(th)], tangent=t, normal=n))
        tr = CS.track_face(frames)
        self.assertTrue(tr['ok'])
        self.assertEqual(tr['formula_sign_changes_at'], [31])
        self.assertAlmostEqual(tr['end_normal'][0], 1.0, places=9)    # the physical face turned over by the U

    def test_selected_route(self):
        snap = rd(CV / 'routing-snapshots/hdmi-export17-selected-20261009-0704/input.json')
        for key in ('hdmi_installed', 'hdmi_premate'):
            tr = CS.track_face(snap[key]['frames'])
            self.assertTrue(tr['ok'], key)
            self.assertIsNotNone(CS.axis_name(tr['start_normal']))
            self.assertIsNotNone(CS.axis_name(tr['end_normal']))

    def test_face_match(self):
        fm = CS.face_match([0, 0, -1], [1, 0, 0])
        self.assertIsNone(fm['status'])
        self.assertEqual(fm['required_if_ribbon']['same'], dict(pi_head_3557='-Z', evf_head_3556='+X'))
        self.assertEqual(fm['required_if_ribbon']['opposite']['evf_head_3556'], '-X')
        ok = CS.face_match([0, 0, -1], [1, 0, 0], dict(pi_head_3557='-Z', evf_head_3556='+X', ribbon_3562='same'))
        self.assertTrue(ok['status'])
        bad = CS.face_match([0, 0, -1], [1, 0, 0], dict(pi_head_3557='-Z', evf_head_3556='-X', ribbon_3562='same'))
        self.assertFalse(bad['status'])
        flip = CS.face_match([0, 0, -1], [1, 0, 0], dict(pi_head_3557='+Z', evf_head_3556='-X', ribbon_3562='same'))
        self.assertTrue(flip['status'])
        self.assertEqual(flip['contacts_on'], 'B')
        self.assertTrue(all(v is None for v in CS.HDMI_CONTACT_SIDES.values()), 'contact sides are unmeasured')


class StackAndPosts(unittest.TestCase):      # VN-38
    @classmethod
    def setUpClass(cls):
        import checks as CK
        cls.CK = CK

    def test_r7_reproduced(self):
        r7 = rd(R7 / 'out/checks.json')['results']['stack_retention'][0]
        ret = [((p[0], p[1]), p[2]) for p in r7['retention_points']]
        holes = [tuple(float(v) for v in k.strip('()').split(',')) for k in r7['max_lift_at_bosses_mm']]
        # r7 contacts are its 4 boss pockets, so call the r7 rule directly with them
        m = self.CK._inside_margin(self.CK._hull2([p for p, _ in ret]), tuple(r7['stack_com_xy']))
        self.assertAlmostEqual(m, r7['com_inside_hull_margin_mm'], delta=0.06)
        for h in holes:
            v = self.CK._max_lift(ret, [q for q in holes if q != h], h)
            self.assertAlmostEqual(v, r7['max_lift_at_bosses_mm']['(%.1f, %.1f)' % h], places=3)

    def test_two_screw_carrier_fails(self):
        r = CS.stack_retention([((-127., 69.), 0.), ((-25., 9.), 0.)], (-78., 36.), [(-96., 60.), (-30., 10.)], self.CK, 4.8)
        self.assertFalse(r['passed'])
        self.assertIsNone(r['com_inside_hull_margin_mm'])
        self.assertFalse(r['lift_bounded'])
        third = CS.stack_retention([((-127., 69.), 0.), ((-25., 9.), 0.), ((-96., 6.), 0.2)], (-78., 36.),
                                   [(-96., 60.), (-30., 10.)], self.CK, 4.8)
        self.assertTrue(third['passed'])       # a third locating feature closes it (CAD phase, register VN-38)

    def test_post_bending(self):
        pb = CS.post_root_bending(100.0, 2, 10.0, 40.0, 10.0, shares=(0.5,), screen_mpa=5.0)
        F = 0.1 * CS.G * 5
        self.assertAlmostEqual(pb['cases'][0]['root_stress_MPa'], 0.5 * F * 50 * 32 / (math.pi * 1000), places=9)
        self.assertTrue(pb['passed'])
        self.assertFalse(CS.post_root_bending(2000.0, 2, 10.0, 40.0, 10.0, screen_mpa=5.0)['passed'])


class EvfFace(unittest.TestCase):            # VN-34
    def test_axis_extraction(self):
        r7 = {p['id']: p['bbox'] for p in rd(R7 / 'out/parts-manifest.json')['parts'] if p.get('bbox')}
        g7 = CS.evf_geometry(r7, ('tub', 'panel', 'hood'))
        self.assertAlmostEqual(g7['axis_y'], 16.0, delta=CS.BBOX_RESOLUTION_MM)   # r7 layout EVF axis Y16 Z78, F -154
        self.assertAlmostEqual(g7['axis_z'], 78.0, delta=CS.BBOX_RESOLUTION_MM)
        self.assertAlmostEqual(g7['flange_x'], -154.0, delta=CS.BBOX_RESOLUTION_MM)
        gc = CS.evf_geometry({r['id']: r['bbox_mm'] for r in MANS[VAR]['rows']}, ('tub', 'panel'))
        self.assertAlmostEqual(gc['axis_y'], 11.0, delta=CS.BBOX_RESOLUTION_MM)
        self.assertAlmostEqual(gc['flange_x'], -MANS[VAR]['core_dimensions_mm'][0], delta=CS.BBOX_RESOLUTION_MM)
        rows = {r['id']: r for r in CS.evf_face_screen(gc, g7)}
        self.assertEqual(set(rows), {'eyecup_protrusion_mm', 'left_extent_mm', 'right_extent_mm', 'top_extent_mm'})
        better = dict(gc, eyecup_protrusion_mm=g7['eyecup_protrusion_mm'] + 1, left_extent_mm=g7['left_extent_mm'] - 1)
        rb = {r['id']: r for r in CS.evf_face_screen(better, g7)}
        self.assertTrue(rb['eyecup_protrusion_mm']['passed'] and rb['left_extent_mm']['passed'])
        worse = dict(gc, top_extent_mm=g7['top_extent_mm'] + 0.2)
        self.assertFalse({r['id']: r for r in CS.evf_face_screen(worse, g7)}['top_extent_mm']['passed'])


class MicroSD(unittest.TestCase):            # VN-29
    def test_dogleg_declared(self):
        p = ST.MOTIONS['microsd_out']['path']
        self.assertEqual(p[0], (0.0, 0.0, 0.0))
        self.assertTrue(12 <= p[1][0] <= 24 and p[1][1:] == (0.0, 0.0))
        self.assertEqual((p[2][0], p[2][2]), (p[1][0], 0.0))
        rows = {r['id']: r for r in MANS[VAR]['rows']}
        self.assertGreater(rows['microsd']['bbox_mm'][2] + p[2][1], max(rows['tub']['bbox_mm'][3], rows['panel']['bbox_mm'][3]))
        doc = [o for o in ST.SERVICE['microsd']['ops'] if o['id'] == 'svc_microsd_out'][0]['doc']
        self.assertIn(ST.MICROSD_TOOL, doc)
        self.assertIn('HOLD', doc)
        src = read_text(CV / 'verify_microsd_service.py')
        for probe in ("'dogleg_window_x10'", "'dogleg_window_x26'", "'panel_off_straight_x45'"):
            self.assertIn(probe, src)

    def test_run_report(self):
        r = report('microsd-service-dependency.json')
        if r is None or 'panel_off' not in r:
            self.skipTest('no FP-12 microSD run bound to the current manifest')
        c = {x['id']: x for x in r['panel_off']['checks']}
        self.assertEqual(r['panel_off']['summary']['fail'], 0)
        self.assertEqual(c['dogleg_selected']['total_hits'], 0)
        self.assertIn('lens_collar', c['panel_off_straight_x45']['hit_parts'])
        self.assertEqual(r['closed_panel_case'], 'REJECTED')
        self.assertEqual(sorted(r['panel_off']['obstacles']), sorted({m['id']: m for m in ST.motion_table(
            {x['id'] for x in MANS[VAR]['rows']})}['microsd_out']['obstacles']))


class ObstacleSets(unittest.TestCase):       # VN-30
    def test_sources(self):
        w = read_text(CV / 'verify_wire_solids.py')
        self.assertNotIn("if r['kind']!='printed':continue", w)
        self.assertIn('TERMINALS', w)
        h = read_text(CV / 'verify_hdmi.py')
        self.assertIn("possible=[n for n in STATE_FIXED[state] if potential(n,b)]", h)
        self.assertIn('hard_head_vs_material', h)

    def test_hdmi_state_sets_cover_present_hardware(self):
        rows = {r['id'] for r in MANS[VAR]['rows']}
        for state, ids in (('installed', ST.final_state()), ('premate', ST.state_before('evf_mate'))):
            hw = {n for n in ids if n in rows and n.startswith(('p_', 's_'))}
            self.assertTrue(hw, state)
        r = report('hdmi-solid-checks.json')
        if r is None or 'obstacle_sets' not in r:
            self.skipTest('no FP-12 HDMI run bound to the current manifest')
        for state, ids in (('installed', ST.final_state()), ('premate', ST.state_before('evf_mate'))):
            hw = {n for n in ids if n in rows and n.startswith(('p_', 's_'))}
            self.assertTrue(hw <= set(r['obstacle_sets'][state]['obstacles']), state)
        fx = [c for c in r['checks'] if c['category'] == 'obstacle_fixture']
        self.assertTrue(fx and all(c['status'] == 'pass' for c in fx))

    def test_wire_report(self):
        r = report('wire-solid-checks.json')
        if r is None or 'obstacles' not in r:
            self.skipTest('no FP-12 wire run bound to the current manifest')
        kinds = {x['id']: x['kind'] for x in MANS[VAR]['rows']}
        self.assertTrue({k for k, v in kinds.items() if v in ('cots', 'hardware', 'printed')} <= set(r['obstacles']))
        self.assertEqual({x['id'] for x in r['exclusions']}, {k for k, v in kinds.items() if v == 'keepout'})
        fx = {x['id']: x for x in r['rows'] if x['id'].startswith('fixture_')}
        self.assertEqual(set(fx), {'fixture_hardware', 'fixture_cots', 'fixture_buried_xt30_wire'})
        self.assertTrue(all(x['status'] == 'pass' for x in fx.values()))
        for run in r['terminal_runs']:      # fixup-1 (VN-30): every terminal run is bounded and within its bound
            self.assertLessEqual(run['run_length_mm'], run['max_entry_mm'] + 1e-9, run)
            self.assertTrue(run['gate'] and run['max_entry_source'], run)


class FlowDrift(unittest.TestCase):      # VN-36 (fixup-1): at least one flow_network row can fail
    BASE = rd(CV / 'review-2026-10-10/fp12/flow-network-baseline.json')

    def elements(self):
        r = rd(CV / self.BASE['source_report'])     # the current report (its first values are the baseline's provenance)
        return copy.deepcopy(next(c for c in r['checks'] if c['category'] == 'flow_network' and c['id'] == 'model')['elements'])

    def test_recorded_network_matches_its_baseline(self):
        ok, det = CS.flow_drift(CS.flow_network(self.elements()), self.BASE)
        self.assertTrue(ok, det)
        self.assertEqual(det['compared_cases'], len(CS.FLOW_CASES))

    def test_cut_cold_path_or_larger_csi_fails(self):
        for key, factor in (('cold_ports_mm2', 0.5), ('csi_mm2', 1.2)):
            el = self.elements()
            el[key] *= factor
            ok, det = CS.flow_drift(CS.flow_network(el), self.BASE)
            self.assertFalse(ok, key)
            self.assertTrue(any(d['case'] == 'nominal' for d in det['drifts']), key)


class CheckScopeReport(unittest.TestCase):
    def test_report(self):
        r = report('check-scope-checks.json')
        if r is None:
            self.skipTest('no FP-12 check-scope run bound to the current manifest')
        cats = {c['category'] for c in r['checks']}
        self.assertEqual(cats, {'j4_screen', 'area_parity', 'flow_network', 'hdmi_face', 'evf_restraint', 'evf_face',
                                'stack_retention', 'post_root_bending'})
        ev = [c for c in r['checks'] if c['category'] == 'evf_restraint']
        self.assertEqual(len([c for c in ev if c['id'] != 'control_without_panel']), 8)
        self.assertEqual({c['id']: c for c in ev}['control_without_panel']['status'], 'pass')
        st = {c['id']: c for c in r['checks'] if c['category'] == 'stack_retention'}['vertical_carrier']
        self.assertEqual(st['status'], 'fail')          # expected until the CAD phase adds a locating feature
        hot = {c['id']: c for c in r['checks'] if c['category'] == 'area_parity'}['hot_branch_series']
        self.assertLess(hot['effective_sum_mm2'], hot['wall_ports_mm2'])
        drift = {c['id']: c for c in r['checks'] if c['category'] == 'flow_network'}['baseline_drift']
        self.assertIn(drift['status'], ('pass', 'fail'))     # a computed gate, not info (VN-36)


if __name__ == '__main__':
    unittest.main(verbosity=2)

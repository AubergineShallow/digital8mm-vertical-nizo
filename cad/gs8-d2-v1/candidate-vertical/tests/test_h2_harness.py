# SPDX-License-Identifier: MIT
"""H2 (review 2026-10-10: VN-28, VN-43, VN-47 / VN-62 / VN-72 check parts): QT fan-in, free-lead routes, the
obstacle-checked pigtail service corridor, the G-W5 decision table and the EVF HDMI carried margin / unplug corridor.

Run:  run_locked.py -- cad/gs8-d2-v1/candidate-vertical/tests/test_h2_harness.py

CAD-free except the bound-report checks (which read the reports written by verify_harness_checks.py and
verify_hdmi.py). Every rule is shown failing on a mutated input (negative control) as well as passing on the route of
record; nothing here relaxes an r7 number.
"""
import copy
import json
import math
import sys
import unittest
from pathlib import Path

CV = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CV))
sys.path.insert(0, str(CV.parent))
from cv_io import read_text   # noqa: E402
import harness_rules as HR    # noqa: E402
import routes as R            # noqa: E402
import steps as ST            # noqa: E402

OUT = CV / 'out' / 'compact-kowa_lm6hc'
NO_HITS = lambda spec, targets: []   # noqa: E731
_C = {}


def data(context=True):
    key = 'H%d' % context
    if key not in _C:
        meta = json.loads(read_text(OUT / 'manifest.json'))
        out = _C.setdefault('out', R.build())
        H = HR.collect(out, {r['id']: r for r in meta['rows']}, R.L, ST)
        if context:
            HR.neighbour_context(H, out, json.loads(read_text(CV / 'out/fps-service-study/mated-carry-input.json')))
        _C[key] = H
    return copy.deepcopy(_C[key])


def row(rows, rid, cat=None):
    return next(r for r in rows if r['id'] == rid and (cat is None or r['category'] == cat))


def planted(name):
    return lambda spec, targets: [h for h in HR.box_hits(spec, targets) if h['obstacle'] == name]


def plant(H, name, p, moving=False):
    H['boxes'][name] = [p[0] - 1, p[0] + 1, p[1] - 1, p[1] + 1, p[2] - 1, p[2] + 1]
    H['kinds'][name] = 'printed'


class QTFanIn(unittest.TestCase):
    def test_every_branch_ends_on_the_main_start_tangent(self):
        sig = data()['cables']['qt']
        start = sig['points'][0]
        out = _C['out']['signal_geometry']
        for b in [b for b in out['branches'] if b['cable'] == 'qt']:
            c = b['curve']
            self.assertFalse(c['errors'], b['id'])
            self.assertLess(math.dist(c['sampled_centerline'][-1], start), 1e-9, b['id'])
            k = c['knots']
            d = [k[-1][i] - k[-2][i] for i in range(3)]
            self.assertAlmostEqual(d[0], 0.0, places=9)
            self.assertAlmostEqual(d[1], 0.0, places=9)
            self.assertGreater(d[2], 0.0)                        # last leg +Z, along the main's first leg
        self.assertEqual(out['qt']['fan_in_point'], list(start))

    def test_fan_in_gap_rule_still_bites(self):
        H = data()
        r = row(HR.cable_routes_rows(H, R.rounded_path), 'qt')
        # Review CHE-1: the QT row now fails on the restored r7 length rule, so the control asserts the fan-in
        # problem itself (absent at the committed geometry, present when the branches stop short).
        self.assertEqual(r['fan_in_gap_mm'], 0.0)
        self.assertFalse([p for p in r['problems'] if 'fan-in gap' in p])
        for br in H['cables']['qt']['branches']:            # the 9ced753 branches stopped at Z25 on their own X
            br['points'] = [p for p in br['points'] if p[2] <= 25.0 + 1e-9]
        r = row(HR.cable_routes_rows(H, R.rounded_path), 'qt')
        self.assertGreater(r['fan_in_gap_mm'], HR.ROUTE_END_TOL)
        self.assertTrue([p for p in r['problems'] if 'fan-in gap' in p])
        self.assertEqual(r['status'], 'fail')

    def test_family_minimum_and_stow(self):
        H = data()
        r = row(HR.cable_routes_rows(H, R.rounded_path), 'qt')
        # Review CHE-1 / GEO-5: the r7 rule judges the installed storage family's shortest member (195.92 + 43.07);
        # it fails the 25 mm allowance against the 240 mm minimum stock. The released pose (203.54, slack 11.46) is a
        # proposed rule change reported as info, never the gate.
        self.assertAlmostEqual(r['min_route_mm'], 238.99, delta=0.05)
        self.assertAlmostEqual(r['slack_mm'], -23.99, delta=0.05)
        self.assertEqual(r['status'], 'fail')
        self.assertTrue(any('allowance' in p for p in r['problems']))
        rel = r['basis']['released_minimum']
        self.assertEqual((rel['status'], rel['gating'], rel['would_pass_length_gate']), ('info', False, True))
        self.assertAlmostEqual(rel['min_route_mm'], 203.54, delta=0.05)
        self.assertAlmostEqual(rel['slack_mm'], 11.46, delta=0.05)
        self.assertEqual(r['proposed_rule_change']['status'], 'info')
        H['cables']['qt']['length_range'] = (215.0, 260.0)    # a lead 25 mm shorter than the BOM minimum fails
        r2 = row(HR.cable_routes_rows(H, R.rounded_path), 'qt')
        self.assertEqual(r2['status'], 'fail')
        self.assertTrue([p for p in r2['problems'] if 'shortest route' in p and 'minimum stock 215.0' in p])
        st = row(HR.cable_stow_rows(data(), R.rounded_path), 'qt')
        self.assertEqual(st['status'], 'pass')
        self.assertGreaterEqual(st['family_max_mm'], 260.0)

    def test_bound_members_clear_the_fps_harness(self):
        """QT_LOW 38: the under-tool run keeps its envelope off the FPS mated-carry 200 main (Z33.5, same lane);
        the superseded Z34 bound member overlapped it (negative control)."""
        H = data()
        c = H['cables']['qt']
        fps = [q for n, q, d in HR.neighbour_cables(H, 'qt') if n == 'header_branch:fps_fps_200_main'][0]
        need = (3.2 + 2.6) / 2
        for v in c['family']['bound']:
            mem = HR.family_eval(R.rounded_path, c['curve'], c['family'], v)['points']
            self.assertGreaterEqual(HR.polyline_distance(mem, fps, HR.SEPARATION_TOL), need, v)
        old = copy.deepcopy(c['curve'])
        for i in (3, 4):
            old['knots'][i][2] = 34.0
        old_pts = R.rounded_path(old['knots'], 6.4, 3, 4, 0.5)['sampled_centerline']
        self.assertLess(HR.polyline_distance(old_pts, fps, HR.SEPARATION_TOL), need)

    def test_csi_tool_clearance_kept(self):
        """The QT legs beside the angled CSI tool are unchanged: >= 0.6 mm (signal_routes literal) for the installed
        route and both bound members, computed here from the tool capsules (15 mm r2 + 75 mm r4)."""
        H = data()
        c = H['cables']['qt']
        tool = _C['out']['signal_geometry']['csi_tool_access']
        d = tool['backward_unit_direction']
        caps = []
        for tip in tool['tips_mm']:
            for sg in tool['segments']:
                a = [tip[i] + d[i] * sg['start_mm'] for i in range(3)]
                b = [tip[i] + d[i] * (sg['start_mm'] + sg['length_mm']) for i in range(3)]
                caps.append((a, b, sg['radius_mm']))
        members = [c['points']] + [HR.family_eval(R.rounded_path, c['curve'], c['family'], v)['points']
                                   for v in c['family']['bound']]
        worst = min(HR.polyline_distance(m, [a, b], 0.0) - r - 1.6 for m in members for a, b, r in caps)
        self.assertGreaterEqual(worst, 0.6 - 0.05)

    def test_installed_sweep_covers_the_branches(self):
        H = data()
        ic = HR.installed_clearance(H, 'qt', set(ST.final_state()), NO_HITS)
        self.assertEqual((ic['hits'], ic['cable_overlaps']), ({}, []))
        br = H['cables']['qt']['branches'][3]['points']
        plant(H, 'zz_on_branch', br[len(br) // 2])
        saved = ST.final_state
        try:
            ST.final_state = lambda steps=None: frozenset(saved(steps)) | {'zz_on_branch'}
            ic = HR.installed_clearance(H, 'qt', set(ST.final_state()), planted('zz_on_branch'))
        finally:
            ST.final_state = saved
        self.assertIn('zz_on_branch', ic['hits'])


class FreeLeads(unittest.TestCase):
    def _rows(self, H, hits=NO_HITS, lengths=None):
        return HR.mate_reach_rows(H, R.rounded_path, ST, hits, lengths)[0]

    def test_qt_documented_order_passes_on_its_free_route(self):
        r = row(self._rows(data()), 'qt_enc')
        self.assertEqual(r['status'], 'pass', r['problems'])
        fl = r['free_lead']
        self.assertAlmostEqual(fl['route_mm'], 147.47, delta=0.05)
        self.assertAlmostEqual(fl['fixed_mm'], 43.07, delta=0.05)
        self.assertAlmostEqual(fl['slack_mm'], 25.45, delta=0.05)
        self.assertEqual((fl['start_gap_mm'], fl['end_gap_mm']), (0.0, 0.0))
        self.assertTrue(r['secured_lane_case']['problems'])     # kept, labelled, not gating
        self.assertTrue(r['lead_state'].startswith('free at panel_prop'))

    def test_without_a_free_route_the_hold_returns(self):
        H = data()
        H['free_leads'] = {}
        for rid in ('qt_enc', 'j2_btn'):
            r = row(self._rows(H), rid)
            self.assertEqual(r['status'], 'fail')
            self.assertIn('no obstacle-checked free-lead route', r['problems'][0])

    def test_lead_shortened_10mm_fails(self):
        # Corrective route: fixed 43.07 + route 147.47 = 190.54; the unchanged margin requires L >= 211.8.
        ok = row(self._rows(data(), lengths={'qt': 220.0}), 'qt_enc')
        bad = row(self._rows(data(), lengths={'qt': 210.0}), 'qt_enc')
        self.assertEqual(ok['status'], 'pass', ok['problems'])
        self.assertEqual(bad['status'], 'fail')
        self.assertTrue(any('lead short' in p for p in bad['problems']), bad['problems'])

    def test_end_and_tangent_rules(self):
        H = data()
        H['free_leads']['qt_enc']['knots'][-1] = [-72.0, 76.8, 77.0]     # 2 mm off the posed plug
        r = row(self._rows(H), 'qt_enc')
        self.assertTrue(any('ends 2.00 mm from the posed end' in p for p in r['problems']), r['problems'])
        H = data()
        H['free_leads']['qt_enc']['knots'][-2] = [-86.7, 70.0, 77.0]     # last leg no longer along +X
        r = row(self._rows(H), 'qt_enc')
        self.assertTrue(any('arrives at the posed end' in p for p in r['problems']), r['problems'])

    def test_planted_part_on_the_free_route_fails(self):
        H = data()
        pts = HR.free_lead_curve(H['free_leads']['qt_enc'], R.rounded_path)['sampled_centerline']
        plant(H, 'zz_free', pts[len(pts) // 2])
        saved = ST.build_sequence
        try:   # the planted part is in the body at panel_prop
            def seq(steps=None):
                for o, b, a, g in saved(steps):
                    yield o, (set(b) | {'zz_free'}) if o['id'] == 'panel_prop' else b, a, g
            ST.build_sequence = lambda steps=None: list(seq(steps))
            r = row(self._rows(H, planted('zz_free')), 'qt_enc')
        finally:
            ST.build_sequence = saved
        self.assertEqual(r['status'], 'fail')
        self.assertIn('zz_free', r['free_lead']['hits'])

    def test_moving_set_is_displaced(self):
        """A planted part riding with the panel is hit where the propped panel puts it, not where it sits closed."""
        H = data()
        fl = H['free_leads']['qt_enc']
        pts = HR.free_lead_curve(fl, R.rounded_path)['sampled_centerline']
        p = pts[-12]                                              # near the posed plug, in the prop gap
        plant(H, 'zz_panel_rider', [p[0], p[1] - 60.0, p[2]])    # closed position: 60 mm toward -Y
        saved = ST.build_sequence
        try:
            def seq(steps=None):
                for o, b, a, g in saved(steps):
                    if o['id'] == 'panel_prop':
                        g = dict(g); g[o['group']] = list(g.get(o['group'], ())) + ['zz_panel_rider']
                    yield o, b, a, g
            ST.build_sequence = lambda steps=None: list(seq(steps))
            r = row(self._rows(H, planted('zz_panel_rider')), 'qt_enc')
        finally:
            ST.build_sequence = saved
        self.assertIn('zz_panel_rider', r['free_lead']['hits'])

    def test_j2_fails_only_on_the_fpc_envelope_at_the_hypothetical_pads(self):
        r = row(self._rows(data()), 'j2_btn')
        self.assertEqual(r['status'], 'fail')
        fl = r['free_lead']
        self.assertEqual(len(fl['problems']), 1, fl['problems'])
        self.assertIn('overlaps cable(s): fpc', fl['problems'][0])
        self.assertTrue(all(a['feasible'] for a in fl['assignments']))
        self.assertGreaterEqual(fl['junction_at'][1], data()['opening_y'] + HR.JUNCTION_OUT)
        self.assertGreaterEqual(fl['hand_out_of_mm'], 0.0)
        self.assertIn('free_lead:qt_enc', fl['tightest_separation'])   # the other free lead is a neighbour


class PigtailCorridor(unittest.TestCase):
    def test_corridor_is_obstacle_checked(self):
        H = data()
        rows = HR.pigtail_reach_rows(H, R.rounded_path, hits=NO_HITS, ST=ST)
        rtv = row(rows, 'pigtail_xt30_mouth_rtv_only')
        cc = rtv['corridor_clearance']
        self.assertEqual(set(cc), set(HR.POWER_CORES))
        self.assertTrue(cc['positive']['cable_overlaps'])        # run leads and the FPC envelope (current routes)
        self.assertTrue(any('service corridor overlaps' in p for p in rtv['would_fail']))
        c = HR.corridor(H, 'negative', HR.FACE_OUT_MIN, R.rounded_path)['sampled_centerline']
        plant(H, 'zz_corridor', c[len(c) // 2])
        saved = ST.build_sequence
        try:
            def seq(steps=None):
                for o, b, a, g in saved(steps):
                    yield o, (set(b) | {'zz_corridor'}) if o['id'] == HR.CORRIDOR_OP else b, a, g
            ST.build_sequence = lambda steps=None: list(seq(steps))
            rows = HR.pigtail_reach_rows(H, R.rounded_path, hits=planted('zz_corridor'), ST=ST)
        finally:
            ST.build_sequence = saved
        self.assertIn('zz_corridor', row(rows, 'pigtail_xt30_mouth')['corridor_clearance']['negative']['hits'])
        self.assertTrue(any('intersects zz_corridor' in p for p in row(rows, 'pigtail_xt30_mouth')['problems']))

    def test_without_hits_nothing_is_claimed(self):
        r = row(HR.pigtail_reach_rows(data(), R.rounded_path), 'pigtail_xt30_mouth')
        self.assertEqual(r['corridor_clearance'], 'not swept (no hit function)')


class DropDecisionTable(unittest.TestCase):
    def test_table_follows_the_model_and_never_relaxes(self):
        r = HR.pigtail_drop_row()
        self.assertEqual(r['limit_v'], 0.15)
        t = r['decision_data']['by_finished_length_mm']
        self.assertAlmostEqual(t['270.0']['hi_v'], r['drop_hi_v'], places=6)
        hi = [t[k]['hi_v'] for k in sorted(t, key=float)]
        self.assertEqual(hi, sorted(hi))
        # ELE-1: the gate charges the 2.4 mohm XT30 loop; shorter_path_max is 182.6 mm, so every tabulated length fails
        self.assertGreater(t['220.0']['hi_v'], 0.150)
        self.assertEqual(r['decision_data']['shorter_path_max_mm_hot_fuse'], 182.6)
        self.assertEqual(r['xt30_loop_cases']['1.0']['shorter_path_max_mm_hot_fuse'], 225.4)   # r7 1.0 (info)
        self.assertEqual(r['status'], 'fail')


class HDMICarried(unittest.TestCase):
    def test_generator_reproduces_the_snapshot(self):
        import hdmi_routes as HD
        snap = json.loads(read_text(CV / 'routing-snapshots/hdmi-corrected-ports-20261009-0623/input.json'))
        for key, kw in (('hdmi_installed', dict(lift=0, drop=0)), ('hdmi_premate', dict(lift=0, drop=6))):
            live = HD.compact_300_service(**kw)
            a = [v for s in live['segments'] for c in s['vertices'] for v in c]
            b = [v for s in snap[key]['segments'] for c in s['vertices'] for v in c]
            self.assertEqual(len(a), len(b))
            self.assertLess(max(abs(x - y) for x, y in zip(a, b)), 1e-9)

    def test_carried_drop_is_stroke_plus_three(self):
        import hdmi_routes as HD
        src = read_text(CV / 'verify_hdmi.py')
        self.assertIn('CARRIED_MARGIN_MM=3.0', src)
        self.assertIn('CARRIED_DROP_MM=EVF_STROKE_MM+CARRIED_MARGIN_MM', src)
        self.assertIn("translate(cq.Vector(0,0,-CARRIED_DROP_MM))", src)
        snap = json.loads(read_text(CV / 'routing-snapshots/hdmi-corrected-ports-20261009-0623/input.json'))
        stroke = next(q for q in snap['connectors'] if q['id'] == 'p_hdmi_evf')['stroke']
        self.assertEqual(stroke, 6.0)
        r = HD.ribbon300(158, pose='service', lift=0, drop=stroke + 3.0, initial_u=5.5, tail=2.0)
        self.assertAlmostEqual(r['routed_length_mm'], 300.0, places=6)
        self.assertEqual(r['evf_head_displacement'], [0, 0, -9.0])

    def test_unplug_corridor_uses_r7_tool_numbers(self):
        src = read_text(CV / 'verify_hdmi.py')
        self.assertIn('JAW_T,JAW_GRIP,JAW_H,UNPLUG_OUT=2.2,8.0,9.4,10.0', src)
        r7 = read_text(CV.parent / 'layout.py')
        self.assertIn("B(-147.0, -144.8, 4.0, 12.0, 52.0, 61.4)", r7)   # jaw 2.2 x 8.0 x 9.4 (tips <= 2.0 thick)
        self.assertIn('tips <= 2.0 thick', r7)
        self.assertIn("op_states('svc_evf_unplug')", src)


class BoundReports(unittest.TestCase):
    def test_hdmi_report(self):
        p = OUT / 'hdmi-solid-checks.json'
        rep = json.loads(read_text(p))
        if 'carried_drop_mm' not in rep:
            self.skipTest('hdmi-solid-checks.json predates H2 (regenerate with verify_hdmi.py)')
        car = row(rep['checks'], 'carrier_headers_hdmi_premate', 'carried_sweep')
        self.assertEqual((car['evf_head_drop_mm'], car['margin_below_mouth_mm'], car['status']), (9.0, 3.0, 'pass'))
        ids = {r['id'] for r in rep['checks'] if r['category'] == 'service_access'}
        self.assertEqual(ids, {'evf_head_unplug_jaw_minus_x', 'evf_head_unplug_jaw_plus_x', 'evf_head_unplug_shank'})

    def test_harness_report_rows(self):
        rep = json.loads(read_text(OUT / 'harness-checks.json'))
        if 'free_lead' not in row(rep['checks'], 'qt_enc'):
            self.skipTest('harness-checks.json predates H2')
        cr = row(rep['checks'], 'qt', 'cable_routes')
        self.assertEqual(cr['fan_in_gap_mm'], 0.0)
        self.assertEqual(cr['member_clearance']['use'], 'shortest member (the minimum route)')   # CHE-1: gating member
        self.assertEqual(cr['installed_clearance']['hits'], {})  # corrected stored route, unchanged HDMI
        self.assertEqual(cr['installed_clearance']['cable_overlaps'], [])
        self.assertEqual(cr['status'], 'fail')                   # r7 allowance at the installed family (CHE-1 / GEO-5)
        self.assertTrue(any('allowance' in p for p in cr['problems']))
        rel = cr['basis']['released_minimum']
        self.assertEqual((rel['status'], rel['gating']), ('info', False))
        self.assertEqual(rel['member_clearance']['hits'], {})   # the proposed released pose is still swept strictly
        # Corrective 2026-10-12: own end parts remain exempt only near their terminal. The free route
        # rises above the Pi before traversing it; the old crossing remains an exact negative-control study.
        q = row(rep['checks'], 'qt_enc')
        self.assertEqual(q['status'], 'pass')
        self.assertEqual(q['free_lead']['hits'], {})
        self.assertEqual(q['problems'], [])
        j2 = row(rep['checks'], 'j2_btn')['free_lead']
        self.assertEqual(set(j2['hits']), {'cooler'})
        self.assertTrue(j2['cable_overlaps'][0].startswith('fpc '))


if __name__ == '__main__':
    unittest.main(verbosity=2)

# SPDX-License-Identifier: MIT
"""FX-H (review 2026-10-10, phase-2 verifier findings on the harness / wiring checks):

1 cable_stow loop rows sweep the members that store L_min / mid / L_max of the purchased lead against the installed
  target set (HDMI ribbon cells, FPS pair box, strict tolerance, cable separation); the previous 260 mm QT geometry fails and the corrected stored family passes.
2 every cable_routes row with a route gets the installed sweep (power_button with the VN-73 / G-V-POWER hold, fan, and
  the ribbons with an explicit round-envelope caveat).
3 own end parts are exempt only within END_ZONE_MM of the terminal at them; a planted end part mid-route is a hit.
4 no superseded J2 SKU in the harness data; every SKU quoted in a WIRING lead section is on the BOM line it cites.
5 the J2 stow space is charged at the larger V-28 legacy estimate, with its source conflict retained; the j2_btn hand is not the PicoBlade pinch envelope.
6 the usb_5v route row reports its binding feed segment.
7 a free lead that decides a mate_reach row also supplies its row-level numbers.

Run:  run_locked.py -- cad/gs8-d2-v1/candidate-vertical/tests/test_fxh_harness.py
CAD-free except TestBoundReport (reads out/compact-kowa_lm6hc/harness-checks.json). The CAD-free KEEPOUTS hit function
tests the HDMI cells and the FPS pair box against each whole capsule segment's bounding box (coarser than the exact
verifier, which splits segments into 5 mm pieces); its volumes are not the exact ones, only the pass / fail direction of
the stow fixtures is relied on, and the exact verdicts are asserted on the bound report.
"""
import copy
import csv
import json
import math
import re
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
REPORT = OUT / 'harness-checks.json'
NO_HITS = lambda spec, targets: []   # noqa: E731
KEEPOUTS = lambda spec, targets: HR.box_hits(spec, [t for t in targets if t['kind'] == 'keepout'])   # noqa: E731
_C = {}


def data():
    if 'H' not in _C:
        meta = json.loads(read_text(OUT / 'manifest.json'))
        _C['out'] = R.build()
        H = HR.collect(_C['out'], {r['id']: r for r in meta['rows']}, R.L, ST)
        HR.neighbour_context(H, _C['out'], json.loads(read_text(CV / 'out/fps-service-study/mated-carry-input.json')))
        _C['H'] = H
    return copy.deepcopy(_C['H'])


def run(H, hits):
    return HR.run_all(H, R.rounded_path, ST, hits=hits, printed_dist=lambda i, b: 9.9, cots_dist=lambda i, b: 9.9)


def base(kind):
    """run_all on the route of record, cached: 'no' (NO_HITS) or 'ko' (KEEPOUTS)."""
    if kind not in _C:
        _C[kind] = run(data(), NO_HITS if kind == 'no' else KEEPOUTS)
    return copy.deepcopy(_C[kind])


def stow(H, hits):
    rows = HR.cable_stow_rows(H, R.rounded_path)
    HR.apply_member_clearance(rows, H, R.rounded_path, set(ST.final_state()), hits)
    return rows


def route_row(H, cid, hits, final=None):
    """The installed sweep applied to a passing cable_routes row (as run_all does), without the rest of run_all."""
    r = dict(category='cable_routes', id=cid, status='pass', problems=[])
    HR.apply_installed_clearance([r], H, final or set(ST.final_state()), hits)
    return r


def row(rows, rid, cat=None):
    return next(r for r in rows if r['id'] == rid and (cat is None or r['category'] == cat))


def only(name):
    return lambda spec, targets: [h for h in HR.box_hits(spec, targets) if h['obstacle'] == name]


def cube(p, h=1.0):
    return [p[0] - h, p[0] + h, p[1] - h, p[1] + h, p[2] - h, p[2] + h]


def at_s(pts, s):
    return HR._cut_at(pts, HR.cumulative(pts), s)[1]


def previous_qt_family(H):
    """Retain the colliding pre-correction storage geometry as a negative control."""
    H = copy.deepcopy(H)
    c = H['cables']['qt']
    c['curve'] = copy.deepcopy(c['released_minimum_curve'])
    c['family'] = dict(var='top', knots=(1, 2), axis=2, bound=(56., 87.5), src='previous QT storage negative control')
    value = HR._value_for_length(H, R.rounded_path, 'qt', 250.)
    ev = HR.family_eval(R.rounded_path, c['curve'], c['family'], value)
    c['curve'] = R.rounded_path(ev['knots'], 6.4, 3, 4, .2)
    c['points'] = c['curve']['sampled_centerline']
    return H


class TestStowMembers(unittest.TestCase):
    def test_qt_260_lead_fails_on_the_hdmi_band(self):
        r = row(stow(previous_qt_family(data()), KEEPOUTS), 'qt')
        self.assertEqual(r['status'], 'fail')
        sw = {s['stores_lead_mm']: s for s in r['stow_members']['sweeps']}
        self.assertEqual(sorted(sw), [240.0, 250.0, 260.0])
        self.assertIn('hdmi_ribbon', sw[260.0]['hits'])
        self.assertTrue(sw[260.0]['installed_targets'])
        self.assertTrue(any(p.startswith('member storing 260.0 mm') for p in r['problems']))
        self.assertGreater(sw[260.0]['value'], 78.4)                       # above the U-turn bottom band (H2)

    def test_lead_stored_below_the_band_passes(self):
        """Negative control: a lead whose longest length stays below the band (H2: <= 248.34 mm) is not failed."""
        H = previous_qt_family(data())
        H['cables']['qt']['length_range'] = (240.0, 248.0)
        r = row(stow(H, KEEPOUTS), 'qt')
        self.assertEqual(r['status'], 'pass', r.get('problems'))
        self.assertTrue(all(not s['hits'] for s in r['stow_members']['sweeps']))

    def test_corrected_full_stock_members_clear_hdmi(self):
        r = row(base('ko'), 'qt', 'cable_stow')
        self.assertEqual(r['status'], 'pass', r.get('problems'))
        sw = r['stow_members']['sweeps']
        self.assertEqual([s['stores_lead_mm'] for s in sw], [240., 250., 260.])
        self.assertTrue(all(not s['hits'] and not s['cable_overlaps'] for s in sw))

    def test_fixup1_bound_member_still_swept(self):
        r = row(base('no'), 'qt', 'cable_stow')
        self.assertEqual((r['member_clearance']['value'], r['member_clearance']['use']),
                         (44.0, 'longest member (the spare home)'))

    def test_member_storing_a_length(self):
        H = data()
        c = H['cables']['qt']
        br = max(b['length'] for b in c['branches'])
        for L in (240.0, 260.0):
            v = HR._value_for_length(H, R.rounded_path, 'qt', L)
            got = HR.family_eval(R.rounded_path, c['curve'], c['family'], v)['length'] + br
            self.assertAlmostEqual(got, L, delta=0.01)
        self.assertIsNone(HR._value_for_length(H, R.rounded_path, 'qt', 400.0))


class TestReleasedQTMinimum(unittest.TestCase):
    def test_the_stored_family_cannot_replace_the_released_reach_pose(self):
        H = data()
        H['cables']['qt']['released_minimum_curve'] = None
        q = row(HR.cable_routes_rows(H, R.rounded_path), 'qt')
        self.assertEqual(q['status'], 'fail')
        self.assertTrue(any('allowance' in p for p in q['problems']))

    def test_released_minimum_must_keep_root_and_radius(self):
        for kind in ('root', 'radius'):
            H = data()
            c = H['cables']['qt']['released_minimum_curve']
            if kind == 'root': c['knots'][0][0] += 2.0
            else: c['centerline_radius_mm'] -= 1.0
            self.assertEqual(row(HR.cable_routes_rows(H, R.rounded_path), 'qt')['status'], 'fail')

    def test_released_minimum_receives_strict_part_sweep(self):
        H = data()
        c = H['cables']['qt']['released_minimum_curve']
        p = c['sampled_centerline'][len(c['sampled_centerline']) // 2]
        H['boxes']['zz_released'] = cube(p)
        H['kinds']['zz_released'] = 'printed'
        rows = HR.cable_routes_rows(H, R.rounded_path)
        def planted(spec, targets):
            return [h for h in HR.box_hits(spec, targets) if h['obstacle'] == 'zz_released']
        HR.apply_member_clearance(rows, H, R.rounded_path, set(ST.final_state()) | {'zz_released'}, hits=planted)
        q = row(rows, 'qt')
        self.assertEqual(q['status'], 'fail')
        self.assertIn('zz_released', q['member_clearance']['hits'])


class TestInstalledSweepEveryRoute(unittest.TestCase):
    def test_every_routed_cable_is_swept(self):
        for cid, c in HR.CABLES.items():
            if 'delegated' not in c:
                self.assertIn(cid, HR.INSTALLED_CLEARANCE, cid)
        rows = base('no')
        for cid in ('power_button', 'fan', 'fpc', 'oled_flex'):
            self.assertIn('installed_clearance', row(rows, cid, 'cable_routes'), cid)

    def _planted_mid(self, cid, name='zz_planted'):
        H = data()
        pts = H['cables'][cid]['points']
        H['boxes'][name] = cube(at_s(pts, HR.arc_length(pts) / 2))
        H['kinds'][name] = 'printed'
        return route_row(H, cid, only(name), set(ST.final_state()) | {name})

    def test_power_button_planted_fails_with_hold(self):
        r = self._planted_mid('power_button')
        self.assertEqual(r['status'], 'fail')
        self.assertIn('zz_planted', r['installed_clearance']['hits'])
        self.assertTrue(any('[VN-73 / G-V-POWER]' in p for p in r['problems']))

    def test_fan_planted_fails(self):
        r = self._planted_mid('fan')
        self.assertEqual(r['status'], 'fail')
        self.assertIn('zz_planted', r['installed_clearance']['hits'])

    def test_ribbon_result_carries_its_caveat(self):
        for cid in ('fpc', 'oled_flex'):
            r = self._planted_mid(cid)
            self.assertEqual(r['status'], 'fail', cid)
            self.assertTrue(r['installed_clearance']['ribbon_round_envelope'])
            self.assertTrue(any('NOT proof of a conflict' in p for p in r['problems']), cid)

    def test_clear_routes_keep_their_status(self):
        rows = base('no')
        for cid in ('fan', 'run_pin37', 'usb_5v'):
            r = row(rows, cid, 'cable_routes')
            self.assertEqual(r['installed_clearance']['hits'], {}, cid)


class TestEndZones(unittest.TestCase):
    LINE = [[float(x), 0.0, 0.0] for x in range(0, 101)]

    def test_split(self):
        def spans(pieces):
            return [(round(p[0][0], 6), round(p[-1][0], 6), sorted(ex)) for p, ex in pieces]
        self.assertEqual(spans(HR.end_zone_pieces(None, self.LINE, ('A', 'B'))),
                         [(0, 10, ['A']), (10, 90, []), (90, 100, ['B'])])
        self.assertEqual(spans(HR.end_zone_pieces(None, self.LINE, ('A', 'B'), no_start=True)),
                         [(0, 90, []), (90, 100, ['B'])])
        self.assertEqual(spans(HR.end_zone_pieces(None, self.LINE, ('A', 'B'), start_only=True)),
                         [(0, 10, ['A']), (10, 100, [])])
        self.assertEqual(spans(HR.end_zone_pieces(None, self.LINE[:16], ('A', 'B'))), [(0, 15, ['A', 'B'])])
        strict = [sp for sp, ex in HR.zone_specs(self.LINE, 2.0, ('A', 'B'), HR.INSTALLED_TOL) if not ex][0]
        self.assertEqual(sum(s['type'] == 'box' for s in strict), 2)        # joint cubes at both cut ends

    def _with_pi5_at(self, cid, s):
        H = data()
        pts = H['cables'][cid]['points']
        H['boxes']['pi5'] = cube(at_s(pts, s))
        return HR.installed_clearance(H, cid, set(ST.final_state()), only('pi5'))

    def test_end_part_planted_mid_route_is_a_hit(self):
        L = HR.arc_length(data()['cables']['run_pin37']['points'])
        self.assertIn('pi5', self._with_pi5_at('run_pin37', L / 2)['hits'])
        self.assertEqual(self._with_pi5_at('run_pin37', 3.0)['hits'], {})    # inside the terminal zone: exempt

    def test_branched_main_start_is_not_a_terminal(self):
        """QT: the main run starts at the fan-in point; the terminals are the branch headers. pi5 planted at the main
        start is a hit; planted at a branch root it is exempt."""
        self.assertIn('pi5', self._with_pi5_at('qt', 2.0)['hits'])
        H = data()
        br = H['cables']['qt']['branches'][0]['points']
        H['boxes']['pi5'] = cube(at_s(br, 3.0))
        self.assertEqual(HR.installed_clearance(H, 'qt', set(ST.final_state()), only('pi5'))['hits'], {})

    def test_free_route_end_part_mid_route_is_a_hit(self):
        H = data()
        fl = H['free_leads']['qt_enc']
        pts = HR.free_lead_curve(fl, R.rounded_path)['sampled_centerline']
        H['boxes']['pi5'] = cube(at_s(pts, HR.arc_length(pts) / 2))
        mp = next(m for m in HR.MATE_POSES if m['id'] == 'qt_enc')
        res = HR.free_lead_eval(H, mp, fl, R.rounded_path, ST, only('pi5'))
        self.assertIn('pi5', res['hits'])

    def test_fan_terminals_follow_the_declared_order(self):
        """The fan route starts and ends inside both the cooler and the pi5 boxes; the declared order decides."""
        pieces = HR.end_zone_pieces(None, data()['cables']['fan']['points'], HR.CABLES['fan']['ends'])
        self.assertEqual([sorted(ex) for _, ex in pieces], [['cooler'], [], ['pi5']])


class TestJ2(unittest.TestCase):
    def test_power_stow_charges_the_larger_legacy_estimate(self):
        data()
        res = next(q for q in _C['out']['slack_reservations'] if q['id'] == 'power_stow')
        self.assertEqual(res['rigid_splice_demand_mm3'], 7.5 * 11.0 * 20.0)
        self.assertNotIn('PH pair', res['method'].replace('was a 576 mm3 PH pair', ''))
        r = HR.j2_stow_row(_C['out'])
        lo, hi = r['demand_range_mm3']
        self.assertEqual(r['status'], 'fail' if hi > r['capacity_mm3'] else 'pass')
        if r['status'] == 'fail':
            self.assertTrue(any('user decision 13' in p and 'G-V-POWER' in p for p in r['problems']))

    def test_two_cores_and_selected_stock_are_not_credited_as_one(self):
        data()
        r = HR.j2_stow_row(_C['out'])
        self.assertEqual(r['wire_core_count'], 2)
        self.assertEqual(r['wire_core_od_mm'], 1.6)
        cases = r['wire_stock_cases']
        for c in cases.values():
            self.assertAlmostEqual(c['two_core_loop_mm3'], c['spare_per_circuit_mm'] * 2 * math.pi * .8**2)
        import wiring_data
        self.assertEqual(cases['selected_minimum']['wire_length_per_circuit_mm'], 2 * wiring_data.J2_DEFAULT['lead_min_mm'])
        self.assertAlmostEqual(cases['inherited_upper']['two_core_loop_mm3'], 1247.5774, places=3)
        self.assertAlmostEqual(cases['legacy_finished_allocation']['two_core_loop_mm3'], 294.5439, places=3)
        self.assertIsNone(r['selected_stock_maximum_mm'])
        self.assertIsNone(r['finished_cut_length_mm'])

    def test_gate_moves_with_the_class_envelope(self):
        """Negative control: a hypothetical tiny pair is gated on its own size (the loop alone still counts)."""
        data()
        saved = R.J2_PAIR_CLASS
        try:
            R.J2_PAIR_CLASS = dict(saved, volume_mm3=(1.0, 1.0))
            r = HR.j2_stow_row(_C['out'])
        finally:
            R.J2_PAIR_CLASS = saved
        self.assertEqual(r['status'], 'fail' if r['loop_demand_mm3'] + 1.0 > r['capacity_mm3'] else 'pass')

    def test_hand_and_names(self):
        mp = next(m for m in HR.MATE_POSES if m['id'] == 'j2_btn')
        self.assertNotEqual(mp['hand'], 'pinch_ph')
        txt = HR.CABLES['power_button']['range_src'] + repr(mp['halves'])
        for sku in ('2181120201', '2181110202'):
            self.assertNotIn(sku, txt)
        self.assertIn('V-28 keyed set', HR.CABLES['power_button']['range_src'])
        self.assertEqual(HR.CABLES['power_button']['length_range'], (363.0, 387.0))   # lengths unchanged
        self.assertEqual([h[1:] for h in mp['halves']], [(150.0, 6.0), (225.0, 6.0)])

    def test_generous_capacity_cannot_clear_known_connector_source_conflict(self):
        """A large empty reservation cannot qualify an undersized connector proxy."""
        data()
        out = copy.deepcopy(_C['out'])
        reservation = next(q for q in out['slack_reservations'] if q['id'] == 'power_stow')
        reservation.update(capacity_mm3=1e9, obstacle_overlaps=[], finished_cut_length_mm=150.0)
        row = HR.j2_stow_row(out)
        self.assertEqual(row['status'], 'fail')
        self.assertEqual(row['problems'], [R.J2_PAIR_CLASS['source_conflict']])


SKU_RE = re.compile(r'(?:Molex|Pololu|Adafruit|Amass|DigiKey|PRC)\s+([A-Z]*-?\d[\dA-Z-]{2,})|(?<![\w/.-])(\d{6,})(?![\w/.-])')
LINE_RE = re.compile(r'\b((?:D2|V)-\d+[A-Z]*)\b')


def sku_mismatches(md, bom):
    """[(lead, sku, cited lines)] for every SKU quoted in a table row of a section-4 lead section that is not on the
    BOM line(s) that row cites (item / sku_or_class columns only: a note may name a superseded SKU it replaces); a row
    that cites no line must quote a SKU that some BOM line carries."""
    sec = md.split('## 4.', 1)[1].split('\n## 5.', 1)[0]
    alltext = ' '.join(r['item'] + ' ' + r['sku_or_class'] for r in bom.values())
    bad = []
    for part in sec.split('\n### ')[1:]:
        lead = part.split('\n', 1)[0].strip('` ')
        for ln in part.splitlines()[1:]:
            cited = sorted(set(LINE_RE.findall(ln)) & set(bom))
            text = ' '.join(bom[l]['item'] + ' ' + bom[l]['sku_or_class'] for l in cited) if cited else alltext
            for m in SKU_RE.finditer(ln):
                sku = m.group(1) or m.group(2)
                if sku not in text:
                    bad.append((lead, sku, cited))
    return bad


class TestWiringSkus(unittest.TestCase):
    def setUp(self):
        with open(CV / 'BOM-VERTICAL.csv', newline='', encoding='utf-8') as f:
            self.bom = {r['line']: r for r in csv.DictReader(f)}
        self.md = read_text(CV / 'WIRING-VERTICAL.md')

    def test_every_lead_sku_is_on_its_cited_bom_line(self):
        self.assertEqual(sku_mismatches(self.md, self.bom), [])

    def test_planted_superseded_sku_is_caught(self):
        md = self.md.replace('| Stock `power_button` | ', '| Stock `power_button` | BOM V-28: Molex 2181120201 female; ', 1)
        self.assertIn(('power_button', '2181120201', ), [b[:2] for b in sku_mismatches(md, self.bom)])

    def test_j2_stow_criterion_in_the_text(self):
        self.assertIn('Criterion for user decision 13 / G-V-POWER: the chosen J2 family must fit the J2 stow space',
                      self.md)


class TestRowFigures(unittest.TestCase):
    def test_usb_route_row_reports_its_binding_segment(self):
        rows = base('no')
        seg = [r for r in rows if r['category'] == 'feed_volumes' and r.get('slack_mm') is not None]
        b = row(rows, 'usb_5v', 'cable_routes')['binding_segment']
        self.assertEqual(b['slack_mm'], min(r['slack_mm'] for r in seg))
        self.assertLess(b['slack_mm'], row(rows, 'usb_5v', 'cable_routes')['slack_mm'])

    def test_free_lead_supplies_the_row_numbers(self):
        r = row(base('no'), 'qt_enc', 'mate_reach')
        self.assertEqual(r['slack_mm'], r['free_lead']['slack_mm'])
        self.assertEqual(r['fixed_mm'], r['free_lead']['fixed_mm'])
        self.assertGreaterEqual(r['slack_mm'], 0.0)
        self.assertLess(r['secured_lane_case']['slack_mm'], 0.0)            # the secured-lane figure, moved
        for k in ('tail_mm', 'anchor_pt', 'W_pose'):
            self.assertNotIn(k, r)
            self.assertIn(k, r['secured_lane_case'])


class TestBoundReport(unittest.TestCase):
    def setUp(self):
        if not REPORT.exists():
            self.skipTest('harness-checks.json not generated yet')
        self.rep = json.loads(read_text(REPORT))
        if 'stow_members' not in row(self.rep['checks'], 'qt', 'cable_stow'):
            self.skipTest('harness-checks.json predates FX-H')

    def test_corrected_qt_stow_passes_exact_sweeps(self):
        r = row(self.rep['checks'], 'qt', 'cable_stow')
        self.assertEqual(r['status'], 'pass', r.get('problems'))
        self.assertTrue(all(not s['hits'] and not s['cable_overlaps'] for s in r['stow_members']['sweeps']))
        self.assertEqual([s['stores_lead_mm'] for s in r['stow_members']['sweeps']], [240., 250., 260.])

    def test_power_button_fails_with_hold(self):
        r = row(self.rep['checks'], 'power_button', 'cable_routes')
        self.assertEqual(r['status'], 'fail')
        self.assertIn('cooler', r['installed_clearance']['hits'])
        self.assertTrue(any('[VN-73 / G-V-POWER]' in p for p in r['problems']))

    def test_every_route_row_carries_the_exact_sweep(self):
        for cid in HR.INSTALLED_CLEARANCE:
            r = row(self.rep['checks'], cid, 'cable_routes')
            if r['status'] == 'pass' or 'installed_clearance' in r:
                self.assertIn('installed_clearance', r, cid)
                self.assertIn('within 10 mm', r['installed_clearance']['exempt_rule'])


if __name__ == '__main__':
    unittest.main(verbosity=2)

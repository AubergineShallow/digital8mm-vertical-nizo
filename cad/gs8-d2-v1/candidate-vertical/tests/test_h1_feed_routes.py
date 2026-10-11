# SPDX-License-Identifier: MIT
"""H1 (review 2026-10-10: VN-26 routes, VN-60 / FP-11f): run-lead re-route, installed usb_5v and pack-lead routes,
EVF feed volumes and the stale ko_5v_up / PH text.

Run:  run_locked.py -- cad/gs8-d2-v1/candidate-vertical/tests/test_h1_feed_routes.py

- Run lead (CAD-free): the recorded route and both solver-bound members keep the 1.8 mm capsule clear of the two
  full-width lower bosses (model.py CARRIER_SCREWS (-25, 9) r 4.8 and PANEL_SCREWS (-10.8, 8.3) r 4.5, both spanning
  the cavity in Y) and of the floor face z 2.5. Negative control: the 9ced753 knots (floor lay at z 4.9 under both
  bosses to a riser at x -12 / -14) fail the same test.
- usb_5v / pack_lead (CAD-free): an installed route exists, ends at its end parts and fits its stock with the r7
  allowance; the feed volumes sit on straight legs of the route in donor -> splice -> 2180 tail -> RCY -> 2181 tail
  order, each Pololu tail spans its segment with the allowance, and a feed volume pushed off its leg raises.
- Installed clearance fixture: a part planted on the installed usb_5v route, or a cable laid onto it, turns the
  cable_routes pass into a fail; a planted part on the RCY volume fails its feed_volumes row.
- Bound report: harness-checks.json carries the four cable_routes passes with exact installed-clearance sweeps (no hits,
  no cable overlaps) and every feed_volumes row passing with the exact method.
- Grep: no ko_5v_up and no EVF-feed PH pair / PH junction text in the live candidate sources and documents.
"""
import copy
import hashlib
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

VARIANT = 'compact-kowa_lm6hc'
OUT = CV / 'out' / VARIANT
REPORT = OUT / 'harness-checks.json'
NO_HITS = lambda spec, targets: []   # noqa: E731
_CACHE = {}
BOSSES = [((-25.0, 9.0), 4.8, (-25.55, 17.2)), ((-10.8, 8.3), 4.5, (-25.55, 23.5))]   # model.py lower bosses (x, z)
OLD_RUN = {'run_pin37': (-12.0, -30.0), 'run_pin39': (-14.0, -32.0)}                  # 9ced753 front / down X
FLOOR_HOLE = (-41.5 + 0.9, -28.0 - 0.9, 1.5 + 0.9, 9.0 - 0.9)                         # layout FLOOR_HOLES run_lead xy


def data():
    if 'H' not in _CACHE:
        meta = json.loads(read_text(OUT / 'manifest.json'))
        _CACHE['out'] = R.build()
        H = HR.collect(_CACHE['out'], {r['id']: r for r in meta['rows']}, R.L, ST)
        fps = json.loads(read_text(CV / 'out/fps-service-study/mated-carry-input.json'))
        _CACHE['H'] = HR.neighbour_context(H, _CACHE['out'], fps)
    return copy.deepcopy(_CACHE['H'])


def row(rows, rid, cat=None):
    return next(r for r in rows if r['id'] == rid and (cat is None or r['category'] == cat))


def boss_floor_clearance(points, r=0.9):
    """Worst (gap mm) of a 1.8 mm capsule to the two lower bosses (where they span the point's Y) and the floor."""
    worst = float('inf')
    for p in points:
        for (bx, bz), br, (y0, y1) in BOSSES:
            if y0 - r <= p[1] <= y1 + r:
                worst = min(worst, math.hypot(p[0] - bx, p[2] - bz) - br - r)
        in_hole = FLOOR_HOLE[0] <= p[0] <= FLOOR_HOLE[1] and FLOOR_HOLE[2] <= p[1] <= FLOOR_HOLE[3]
        if p[2] > 0.0 and not in_hole:                   # cavity floor (the lead leaves through the run floor hole)
            worst = min(worst, p[2] - 2.5 - r)
    return worst


class TestRunLeadReroute(unittest.TestCase):
    def test_recorded_and_bound_members_clear_bosses_and_floor(self):
        H = data()
        for cid in ('run_pin37', 'run_pin39'):
            c = H['cables'][cid]
            for val in [None] + list(c['family']['bound']):
                pts = c['points'] if val is None else HR.family_eval(R.rounded_path, c['curve'], c['family'], val)['points']
                self.assertGreater(boss_floor_clearance(pts), 0.0, (cid, val))

    def test_old_knots_fail_the_same_rule(self):
        H = data()
        for cid, (front, down) in OLD_RUN.items():
            kn = copy.deepcopy(H['cables'][cid]['curve']['knots'])
            lane = kn[1][1]
            old = kn[:5] if cid == 'run_pin37' else kn[:3]
            old = old + [[front, lane, 4.9], [front, lane, 52.0], [down, lane, 52.0], [down, lane, 12.0],
                         [down, 5.25, 12.0], [down, 5.25, -14.2]]
            pts = R.rounded_path(old, 3.2, 3, 3, 0.2)['sampled_centerline']
            self.assertLess(boss_floor_clearance(pts), 0.0, cid)

    def test_route_rows_pass_cad_free(self):
        rows = HR.run_all(data(), R.rounded_path, ST, hits=NO_HITS, printed_dist=lambda i, b: 9.9,
                          cots_dist=lambda i, b: 9.9)
        for cid in ('run_pin37', 'run_pin39', 'usb_5v', 'pack_lead'):
            r = row(rows, cid, 'cable_routes')
            self.assertEqual(r['status'], 'pass', (cid, r.get('problems')))
            self.assertEqual(r['installed_clearance']['cable_overlaps'], [], cid)
        for cid in ('run_pin37', 'run_pin39'):
            self.assertEqual(row(rows, cid, 'cable_stow')['status'], 'pass')


class TestFeedRoute(unittest.TestCase):
    def test_installed_routes_exist_and_fit(self):
        H = data()
        for cid, stock in (('usb_5v', 500.0), ('pack_lead', 60.0)):
            c = H['cables'][cid]
            self.assertFalse(c['errors'], cid)
            self.assertTrue(c['points'], cid)
            self.assertLessEqual(c['curve']['rounded_length_mm'] + HR.route_allowance(stock), stock, cid)
        self.assertEqual(len(H['cables']['pack_lead']['stubs']), 2)

    def test_usb_stock_is_the_segmented_bom_assembly(self):
        # H1 data correction (FIX-LOG): the feed is cut to length from the D2-22 donor (catalog 300, supplier 325 +/- 10)
        # and the two D2-23 100 mm tails; the superseded 200 mm allocation is no longer the stock of record, and each
        # segment is held to its own stock in feed_volumes.
        c = HR.CABLES['usb_5v']
        self.assertEqual((c['length'], c['length_range']), (300.0 + 2 * 100.0, (300.0 + 2 * 100.0, 335.0 + 2 * 100.0)))
        self.assertTrue(c['cut_to_length'])
        prov = json.loads(read_text(CV / 'routing-snapshots/hdmi-export17-selected-20261009-0704/usb-donor-provenance.json'))
        self.assertEqual(prov['superseded_allocation_mm'], 200)
        self.assertFalse(prov['installed_wire_length_is_fixed'])
        self.assertEqual([t['stock_length_mm'] for t in prov['D2-22']['tails']], [HR.POLOLU_TAIL_MM] * 2)
        self.assertEqual(prov['D2-22']['catalogue_length_mm'], HR.DONOR_MIN_MM)

    def test_long_tail_fails_its_segment_row(self):
        H = data()
        st = H['cables']['usb_5v']['feed']['stations_mm']
        st['board'] = st['rcy_end'] + 95.0                     # a 2181 tail span the 100 mm stock cannot cover with allowance
        rows = {r['id']: r for r in HR.feed_volume_rows(H, set(ST.final_state()), NO_HITS)}
        self.assertEqual(rows['usb_5v_tail_2181']['status'], 'fail')
        self.assertEqual(rows['usb_5v_tail_2180']['status'], 'pass')

    def test_feed_order_and_tails(self):
        H = data()
        feed = H['cables']['usb_5v']['feed']
        st = feed['stations_mm']
        order = [st[k] for k in ('head_exit', 'splice_start', 'splice_end', 'rcy_start', 'rcy_end', 'board')]
        self.assertEqual(order, sorted(order))
        self.assertLessEqual(st['rcy_start'] - st['splice_end'] + HR.route_allowance(100.0), 100.0)
        self.assertLessEqual(st['board'] - st['rcy_end'] + HR.route_allowance(100.0), 100.0)
        self.assertGreaterEqual(feed['head_max_mm'], 20.0)        # a real USB-A head must have room (gate value)
        ids = [v['id'] for v in feed['volumes']]
        self.assertEqual(ids, ['diode_sleeve', 'option_c_reserve', 'rcy_pair'])
        oc = next(v for v in feed['volumes'] if v['id'] == 'option_c_reserve')
        self.assertIn('default pending user decision 10', oc['default'])

    def test_volume_off_its_leg_raises(self):
        c = R.rounded_path([[0, 0, 0], [40, 0, 0], [40, 40, 0]], 6.0, 0, 0)
        R.place_on_leg(c, 0, 0.0, 34.0, (7, 7), (0, 0, 1))
        with self.assertRaises(ValueError):
            R.place_on_leg(c, 0, 0.5, 34.0, (7, 7), (0, 0, 1))

    def test_feed_rows_cad_free(self):
        rows = HR.feed_volume_rows(data(), set(ST.final_state()), NO_HITS)
        self.assertEqual({r['status'] for r in rows}, {'pass'}, [r.get('problems') for r in rows])
        self.assertEqual(sorted(r['id'] for r in rows),
                         sorted('usb_5v_' + k for k in ('diode_sleeve', 'option_c_reserve', 'rcy_pair', 'donor',
                                                        'tail_2180', 'tail_2181')))


class TestPlantedFixtures(unittest.TestCase):
    def _final(self, extra):
        saved = ST.final_state
        ST.final_state = lambda steps=None: frozenset(saved(steps)) | {extra}
        return saved

    def test_planted_part_on_usb_route_fails(self):
        H = data()
        p = H['cables']['usb_5v']['points'][len(H['cables']['usb_5v']['points']) // 2]
        H['boxes']['zz_planted'] = [p[0] - 1, p[0] + 1, p[1] - 1, p[1] + 1, p[2] - 1, p[2] + 1]
        H['kinds']['zz_planted'] = 'printed'
        saved = self._final('zz_planted')
        try:
            planted = lambda spec, targets: [h for h in HR.box_hits(spec, targets) if h['obstacle'] == 'zz_planted']
            rows = HR.run_all(H, R.rounded_path, ST, hits=planted, printed_dist=lambda i, b: 9.9,
                              cots_dist=lambda i, b: 9.9)
        finally:
            ST.final_state = saved
        r = row(rows, 'usb_5v', 'cable_routes')
        self.assertEqual(r['status'], 'fail')
        self.assertIn('zz_planted', r['installed_clearance']['hits'])

    def test_cable_laid_onto_route_fails(self):
        H = data()
        H['signal_branches'].append(dict(id='zz_wire', points=[list(p) for p in H['cables']['usb_5v']['points'][40:80]],
                                         od_mm=1.6))
        rows = HR.run_all(H, R.rounded_path, ST, hits=NO_HITS, printed_dist=lambda i, b: 9.9, cots_dist=lambda i, b: 9.9)
        r = row(rows, 'usb_5v', 'cable_routes')
        self.assertEqual(r['status'], 'fail')
        self.assertTrue(any('zz_wire' in o for o in r['installed_clearance']['cable_overlaps']))

    def test_planted_part_on_rcy_volume_fails(self):
        H = data()
        v = next(v for v in H['cables']['usb_5v']['feed']['volumes'] if v['id'] == 'rcy_pair')
        cx = v['center']
        H['boxes']['zz_planted'] = [cx[0] - .5, cx[0] + .5, cx[1] - .5, cx[1] + .5, cx[2] - .5, cx[2] + .5]
        H['kinds']['zz_planted'] = 'printed'
        planted = lambda spec, targets: [h for h in HR.box_hits(dict(spec, tol=0.0), targets) if h['obstacle'] == 'zz_planted']
        rows = HR.feed_volume_rows(H, set(ST.final_state()) | {'zz_planted'}, planted)
        self.assertEqual(row(rows, 'usb_5v_rcy_pair')['status'], 'fail')


class TestBoundReport(unittest.TestCase):
    def setUp(self):
        if not REPORT.exists():
            self.skipTest('harness-checks.json not generated yet')
        self.rep = json.loads(read_text(REPORT))

    def test_binding(self):
        self.assertEqual(self.rep['manifest_sha256'], hashlib.sha256((OUT / 'manifest.json').read_bytes()).hexdigest())
        self.assertEqual(self.rep['verification_source_sha256'],
                         hashlib.sha256((CV / 'verify_harness_checks.py').read_bytes()).hexdigest())

    def test_route_rows_pass_exact(self):
        for cid in ('run_pin37', 'run_pin39', 'usb_5v', 'pack_lead'):
            r = row(self.rep['checks'], cid, 'cable_routes')
            self.assertEqual(r['status'], 'pass', (cid, r.get('problems')))
            ic = r['installed_clearance']
            self.assertEqual((ic['hits'], ic['cable_overlaps']), ({}, []), cid)
            self.assertGreater(ic['pieces'], 2)
        for cid in ('run_pin37', 'run_pin39'):
            r = row(self.rep['checks'], cid, 'cable_stow')
            self.assertEqual((r['status'], r['member_clearance']['hits']), ('pass', {}), cid)

    def test_feed_rows_pass_exact(self):
        rows = [r for r in self.rep['checks'] if r['category'] == 'feed_volumes']
        self.assertEqual(len(rows), 6)
        for r in rows:
            self.assertEqual(r['status'], 'pass', (r['id'], r.get('problems')))
            if 'hits' in r:
                self.assertEqual((r['hits'], r['method']), ({}, 'exact'), r['id'])


LIVE = ['routes.py', 'signal_routes.py', 'harness_rules.py', 'BOM-VERTICAL.md', 'BOM-VERTICAL.csv',
        'ASSEMBLY-VERTICAL.md', 'MEASUREMENTS-TO-CLOSE.md', 'README.md', 'REVIEW.md', 'WIRING-VERTICAL.md']


class TestStaleText(unittest.TestCase):
    def test_no_ko_5v_up(self):
        for rel in LIVE:
            p = CV / rel
            if p.exists():
                self.assertNotIn('ko_5v_up', read_text(p), rel)
        # the BOM generator names the inherited r7 text only to replace it in the D2-16P row
        gen = [ln for ln in read_text(CV / 'make_bom_vertical.py').splitlines() if 'ko_5v_up' in ln]
        self.assertTrue(gen)
        self.assertTrue(all("by['D2-16P']['item'].replace(" in ln or 'ko_5v_up keep-out does not exist' in ln
                            for ln in gen), gen)

    def test_no_evf_feed_ph_pair(self):
        pat = re.compile(r'(diode\s*[+/&]\s*PH|PH\s+pair|PH\s+junction|diode/PH)', re.I)
        src = read_text(CV / 'routes.py')
        usb = [ln for ln in src.splitlines() if 'usb' in ln.lower() or 'diode' in ln.lower()]
        self.assertFalse([ln for ln in usb if pat.search(ln)])
        self.assertNotIn('corrected lower USB2', src)   # the superseded-route error message is gone with the route


if __name__ == '__main__':
    unittest.main(verbosity=2)

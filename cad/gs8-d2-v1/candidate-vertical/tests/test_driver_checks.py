# SPDX-License-Identifier: MIT
"""Straight-driver audit of the candidate (review VN-23, fix FP-07). CadQuery fixtures, nothing written.

Run:  run_locked.py -- cad/gs8-d2-v1/candidate-vertical/tests/test_driver_checks.py

- Counterbore fixtures: a PT 3 x 12 head seated in a 6.0 mm counterbore fails (bit hit 14.726 mm3), 6.4 mm (the
  candidate carrier value, VN-56) fails, 7.0 mm (r7 PT cbore_d) passes with a 0.25 mm bit gap.
- Port parity: on the same fixtures, on a handle-only obstacle and on a two-solid compound, the port gives r7
  checks.check_driver's hits, volumes, nearest gaps and status.
- Strictness over r7: a shape whose boolean raises passes r7 (common() returns NaN) and fails the port.
- Pose: derive_pose recovers head point and axis of r7 cots.screw PT/M3 solids (washer, inserts) in all six axis
  directions and of the candidate model.pt_screw; a headless cylinder and a wrong screw kind are rejected.
- Contexts: rows come from steps.driver_contexts() (11 screws x build + service; strap at p_grip, gauge at
  s_c1-3, no knob_fps at the panel screws, lens at s_c4); a missing non-optional context id fails the row;
  coverage fails on an unmodelled screw row or a missing one.
- Registration: verify_candidate.py runs driver_rows once, behind want('driver'), after the tools are loaded.
- Candidate record (review-2026-10-10/fp07): complete, made by the current driver_checks.py and steps.py, bound to
  the current manifest; every pose derived from the STEP equals the pose model.py declares; for the reviewed
  manifest 53e668d4 the expected CAD-phase failures are exactly the carrier counterbores (FP-11c: bit 2.432 and
  0.405 mm3 into the carrier, build and service) and the p_grip handle clears the strap by 1.37 mm.
"""
import ast
import hashlib
import json
import sys
import types
import unittest
from pathlib import Path

CV = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CV))
from cv_io import read_text    # noqa: E402
import driver_checks as DC     # noqa: E402
import steps as ST             # noqa: E402
import cadquery as cq          # noqa: E402
import cots                    # noqa: E402  r7 screw solids (read-only)

CK, R7L = DC.CK, DC.R7L
REVIEWED_MANIFEST = '53e668d43847acd1f59d2b559a562476c54a23db0918debd482d632f0e8ceb77'
RECORD = CV / 'review-2026-10-10' / 'fp07' / 'driver-compact-kowa_lm6hc.json'
DEPTH = 3.0
HP, AX = (0.0, 0.0, 10.0 - DEPTH), (0.0, 0.0, -1.0)
EXPECTED_FAIL = {'p_carrier1@carrier_screws', 'p_carrier2@carrier_screws', 'p_carrier1@svc_carrier_screws_out',
                 'p_carrier2@svc_carrier_screws_out'}


def plate(cb_d, depth=DEPTH):
    """30 x 30 x 10 plate, 3.4 clearance hole, counterbore cb_d x depth from the top; the head bears on its floor."""
    p = cq.Solid.makeBox(30, 30, 10, cq.Vector(-15, -15, 0))
    p = p.cut(cq.Solid.makeCylinder(1.7, 12, cq.Vector(0, 0, -1)))
    return p.cut(cq.Solid.makeCylinder(cb_d / 2.0, depth + 1, cq.Vector(0, 0, 10 - depth)))


def pt_pose():
    return dict(head_point=list(HP), axis=list(AX), head_h=R7L.PT['head_h'], errors=[])


def r7_row(shape, hp=HP, ax=AX):
    Lr = types.SimpleNamespace(DRIVER=R7L.DRIVER, PT=R7L.PT, M3=R7L.M3,
                               SCREWS=[dict(id='fx', kind='PT', head_point=hp, axis=ax, step=1)])
    return CK.check_driver(Lr, {'obst': dict(shape=shape)}, audit_set_of=lambda _s: ['obst'])[0]


def port_row(shape):
    return DC.audit_screw('fx', pt_pose(), ['obst'], {'obst': shape})


class Broken:
    """A shape whose booleans raise (stands in for an OCP failure)."""
    def BoundingBox(self):
        return types.SimpleNamespace(xmin=-5, xmax=5, ymin=-5, ymax=5, zmin=8, zmax=20)

    def Solids(self):
        return []

    def intersect(self, other):
        raise RuntimeError('boolean failed')

    def distance(self, other):
        raise RuntimeError('distance failed')


class Counterbore(unittest.TestCase):
    def test_6_0_counterbore_fails(self):
        r = port_row(plate(6.0))
        self.assertEqual([(h['part'], h['tool']) for h in r['hits']], [('obst', 'bit')], r)
        self.assertAlmostEqual(r['hits'][0]['volume_mm3'], 14.726, places=2)      # pi (3.25^2 - 3^2) 3

    def test_6_4_candidate_counterbore_fails(self):
        r = port_row(plate(6.4))
        self.assertTrue(r['hits'] and r['hits'][0]['tool'] == 'bit', r)
        self.assertAlmostEqual(r['hits'][0]['volume_mm3'], 3.040, places=2)       # pi (3.25^2 - 3.2^2) 3

    def test_7_0_counterbore_passes(self):
        r = port_row(plate(7.0))
        self.assertEqual(r['hits'], [], r)
        self.assertEqual(r['errors'], [])
        self.assertAlmostEqual(r['nearest']['bit']['gap'], 0.25, places=2)


class Parity(unittest.TestCase):
    def check(self, shape):
        a, b = r7_row(shape), port_row(shape)
        self.assertEqual(sorted((h['part'], h['tool'], h['volume_mm3']) for h in a['hits']),
                         sorted((h['part'], h['tool'], h['volume_mm3']) for h in b['hits']))
        self.assertEqual(a['nearest'], b['nearest'])
        self.assertEqual(a['status'] == 'pass', not b['hits'] and not b['errors'])
        return b

    def test_counterbores(self):
        for d in (6.0, 6.4, 7.0):
            self.check(plate(d))

    def test_handle_only_obstacle(self):
        wall = cq.Solid.makeBox(10, 10, 2, cq.Vector(6, -5, 60))       # 6..16 mm off axis, 53..55 behind the head
        b = self.check(wall)
        self.assertEqual([h['tool'] for h in b['hits']], ['handle'])

    def test_two_solid_compound(self):
        c = cq.Compound.makeCompound([cq.Solid.makeBox(2, 2, 2, cq.Vector(2.5, -1, 20)),
                                      cq.Solid.makeBox(2, 2, 2, cq.Vector(-4.5, -1, 30))])
        b = self.check(c)
        self.assertEqual([h['tool'] for h in b['hits']], ['bit'])

    def test_nearest_among_several_parts(self):
        """The port's exact branch and bound picks r7's nearest part and gap (nearest part last in context order)."""
        parts = {'far': cq.Solid.makeBox(2, 2, 2, cq.Vector(9, -1, 20)),           # bit gap 5.75
                 'second': cq.Solid.makeBox(2, 2, 2, cq.Vector(-7.0, -1, 25)),     # 1.75
                 'near': cq.Solid.makeBox(2, 2, 2, cq.Vector(4.5, -1, 30))}        # 1.25
        order = ['far', 'second', 'near']
        Lr = types.SimpleNamespace(DRIVER=R7L.DRIVER, PT=R7L.PT, M3=R7L.M3,
                                   SCREWS=[dict(id='fx', kind='PT', head_point=HP, axis=AX, step=1)])
        a = CK.check_driver(Lr, {k: dict(shape=v) for k, v in parts.items()}, audit_set_of=lambda _s: order)[0]
        b = DC.audit_screw('fx', pt_pose(), order, parts)
        self.assertEqual(a['nearest'], b['nearest'])
        self.assertEqual(b['nearest']['bit'], dict(gap=1.25, part='near'))
        self.assertEqual(a['hits'], b['hits'])

    def test_boolean_failure_is_not_a_pass(self):
        self.assertEqual(r7_row(Broken())['status'], 'pass')     # the r7 hole the port closes
        b = port_row(Broken())
        self.assertTrue(b['errors'], b)


class Pose(unittest.TestCase):
    def assert_pose(self, solid, kind, hp, ax):
        p = DC.derive_pose(solid, kind)
        self.assertEqual(p['errors'], [], p)
        self.assertEqual([float(x) for x in p['axis']], [float(x) for x in ax])
        for u, v in zip(p['head_point'], hp):
            self.assertAlmostEqual(u, v, places=3)

    def test_r7_screws_all_axes(self):
        for ax in ((0, 0, -1), (0, 0, 1), (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0)):
            hp = (1.0, 2.0, 3.0)
            self.assert_pose(cots.screw(R7L, dict(id='fx', kind='PT', head_point=hp, axis=ax)), 'PT', hp, ax)
            m3 = dict(id='fx', kind='M3', length=16.0, washer=True, head_point=hp, axis=ax)
            self.assert_pose(cots.screw(R7L, m3), 'M3', hp, ax)

    def test_r7_collar_and_grip_entries(self):
        for s in R7L.SCREWS:
            if s['id'] in ('s_c1', 's_c4', 's_j'):
                self.assert_pose(cots.screw(R7L, s), s['kind'], s['head_point'], s['axis'])

    def test_candidate_pt_screw(self):
        import model
        self.assert_pose(model.pt_screw(-127.0, 69.0, 19.8), 'PT', (-127.0, 19.8, 69.0), (0, -1, 0))

    def test_rejects(self):
        self.assertTrue(DC.derive_pose(cq.Solid.makeCylinder(1.5, 12, cq.Vector(0, 0, 0)), 'PT')['errors'])
        m3 = cots.screw(R7L, dict(id='fx', kind='M3', length=10.0, washer=True, head_point=(0, 0, 0), axis=(0, 0, -1)))
        self.assertTrue(DC.derive_pose(m3, 'PT')['errors'])              # head 5.6 is not a PT head
        self.assertTrue(DC.derive_pose(m3, None)['errors'])


class Contexts(unittest.TestCase):
    def setUp(self):
        self.full = DC.screw_contexts(None)

    def test_rows_are_the_state_model(self):
        want = [r for r in ST.driver_contexts(None) if r['kind'] == 'screw']
        self.assertEqual([dict((k, v) for k, v in r.items() if k != 'missing') for r in self.full], want)
        self.assertEqual(len(self.full), 22)
        for s in ST.SCREW_IDS:
            self.assertEqual(sorted(r['phase'] for r in self.full if r['fastener'] == s), ['build', 'service'], s)

    def test_named_contexts(self):
        ctx = {(r['fastener'], r['op']): set(r['context']) for r in self.full}
        self.assertIn('strap', ctx['p_grip', 'grip_lock'])
        self.assertIn('strap', ctx['p_grip', 'svc_grip_screw_out'])
        for s in ST.COLLAR_ANCHORS:
            self.assertIn('centring_gauge', ctx[s, 'collar_tighten'])
        for s in ST.PANEL_SCREWS:
            self.assertNotIn('knob_fps', ctx[s, 'panel_screws'])
        self.assertIn('lens', ctx['s_c4', 'lens_float'])
        for (s, _op), c in ctx.items():
            self.assertNotIn(s, c)

    def test_missing_context_id_fails(self):
        everything = set(ST.final_state()) | set(ST.TOOLS)
        miss = [r for r in DC.screw_contexts(everything - {'strap'}) if r['fastener'] == 'p_grip']
        self.assertTrue(all(r['missing'] == ['strap'] for r in miss))
        solid = cots.screw(R7L, dict(id='fx', kind='PT', head_point=(0, 0, 0), axis=(0, 0, 1)))
        shapes = {s: solid for s in ST.SCREW_IDS}
        rows = {s: dict(kind='hardware', source='PT 3x12 PH1') for s in ST.SCREW_IDS}
        out = DC.driver_rows(shapes, rows, set(shapes))
        self.assertEqual(len(out), 23)
        self.assertFalse(any(r['ok'] for r in out if r['category'] != 'driver_coverage'))
        self.assertTrue(all(any('not loaded' in e for e in r['errors']) for r in out[:-1]))

    def test_coverage(self):
        rows = {s: dict(kind='hardware', source='PT 3x12 PH1') for s in ST.SCREW_IDS}
        fake = [dict(screw=s, phase=p) for s in ST.SCREW_IDS for p in ('build', 'service')]
        self.assertTrue(DC.coverage_row(rows, fake)['ok'])
        extra = dict(rows, p_extra=dict(kind='hardware', source='PT 3x12 PH1'))
        self.assertEqual(DC.coverage_row(extra, fake)['screws_not_in_state_model'], ['p_extra'])
        short = {k: v for k, v in rows.items() if k != 'p_grip'}
        self.assertFalse(DC.coverage_row(short, fake)['ok'])
        self.assertFalse(DC.coverage_row(rows, [r for r in fake if r['screw'] != 's_c4' or r['phase'] != 'service'])['ok'])


class Registration(unittest.TestCase):
    def test_verify_candidate_runs_driver_rows(self):
        src = read_text(CV / 'verify_candidate.py')
        calls = [n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Attribute) and n.attr == 'driver_rows']
        self.assertEqual(len(calls), 1)
        line = next(x for x in src.splitlines() if 'driver_rows' in x)
        self.assertIn("want('driver')", line)
        self.assertLess(src.index('avail=set(rows)'), src.index(line))


class CandidateRecord(unittest.TestCase):
    def test_record(self):
        if not RECORD.exists():
            self.skipTest('no FP-07 record yet: run verify_candidate.py --only driver --out %s' % RECORD.name)
        rec = json.loads(read_text(RECORD))
        rows = [c for c in rec['checks'] if c['category'] in DC.CATEGORIES]
        cov = next(c for c in rows if c['category'] == 'driver_coverage')
        self.assertEqual(cov['driver_source_sha256'], DC.source_sha256(), 'stale record: driver_checks.py changed')
        self.assertEqual(rec['state_model_sha256'], hashlib.sha256((CV / 'steps.py').read_bytes()).hexdigest(),
                         'stale record: steps.py changed')
        self.assertEqual(cov['status'], 'pass')
        self.assertEqual(len(rows), 23)
        cur = hashlib.sha256((CV / 'out' / rec['variant'] / 'manifest.json').read_bytes()).hexdigest()
        if rec['manifest_sha256'] != cur:
            self.fail('record binds manifest %s, current is %s: re-run' % (rec['manifest_sha256'][:8], cur[:8]))
        screw_rows = [c for c in rows if c['category'] != 'driver_coverage']
        want = declared_poses(rec['variant'])
        for c in screw_rows:                     # poses derived from the STEP == the poses model.py declares
            self.assertEqual(c['pose']['errors'], [], c['id'])
            self.assertEqual([float(x) for x in c['axis']], [float(x) for x in want[c['screw']][1]], c['id'])
            for u, v in zip(c['head_point'], want[c['screw']][0]):
                self.assertAlmostEqual(u, v, places=3, msg=c['id'])
        failing = {c['id'] for c in rows if c['status'] == 'fail'}
        if rec['manifest_sha256'] == REVIEWED_MANIFEST:
            self.assertEqual(failing, EXPECTED_FAIL)
            for c in screw_rows:
                self.assertEqual(c['errors'], [], c['id'])
                if c['id'] in EXPECTED_FAIL:
                    self.assertEqual({(h['part'], h['tool']) for h in c['hits']}, {('carrier', 'bit')}, c)
            vol = {c['id']: c['hits'][0]['volume_mm3'] for c in screw_rows if c['id'] in EXPECTED_FAIL}
            self.assertAlmostEqual(vol['p_carrier1@carrier_screws'], 2.432, places=3)    # review DES-3 / VN-56
            self.assertAlmostEqual(vol['p_carrier2@carrier_screws'], 0.405, places=3)
            for c in (c for c in screw_rows if c['screw'] == 'p_grip'):
                self.assertIn('strap', c['audit_set'])
                self.assertEqual(c['nearest']['handle'], dict(gap=1.37, part='strap'))    # VN-78 / DES-3


def declared_poses(variant):
    """screw id -> (head_point, axis) as model.py declares them (pt_screw seats parsed from model._build)."""
    import copy
    import re
    import model
    seats = [float(s) for s in re.findall(r'pt_screw\(x,z,([0-9.]+)\)', read_text(CV / 'model.py'))]
    length = 158.0 if variant.startswith('compact') else 185.0
    out = {'p_panel%d' % (i + 1): ((x, seats[0], z), (0, -1, 0)) for i, (x, z) in enumerate(model.panel_screws(length))}
    out.update({'p_carrier%d' % (i + 1): ((x, seats[1], z), (0, -1, 0)) for i, (x, z) in enumerate(model.CARRIER_SCREWS)})
    L = model.L
    oldc, olds = copy.deepcopy(L.COLLAR), copy.deepcopy(L.SCREWS)
    try:
        model.collar_setup()
        out.update({s['id']: (s['head_point'], s['axis']) for s in L.SCREWS if s['id'] in ('s_c1', 's_c2', 's_c3', 's_c4')})
    finally:
        L.COLLAR, L.SCREWS = oldc, olds
    sj = next(s for s in L.SCREWS if s['id'] == 's_j')
    out['p_grip'] = (sj['head_point'], sj['axis'])
    return out


if __name__ == '__main__':
    unittest.main(verbosity=2)

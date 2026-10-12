# SPDX-License-Identifier: MIT
"""Carrier print face, counterbores and third locating feature (review VN-54, VN-56, VN-38; fix FP-11c).

Run:  run_locked.py -- cad/gs8-d2-v1/candidate-vertical/tests/test_carrier_fp11c.py

- Bed-contact fixtures (manifold3d only, r7 PRINT_OVERHANG constants): a frame floating 2 mm above the bed on one pad
  fails with the frame area lifted; a flat plate with a closed counterbore in its bed face passes; a plate with a 0.6 mm
  45 deg bed chamfer or a 50 deg edge relief passes; a plate with a 3 mm lip that starts 1 mm above the bed fails.
- Locator fixtures (cadquery boxes): a tongue touching its seat with a 0.15 mm stop gap is credited; a 0.5 mm or a
  0.0 mm stop gap, a 0.3 mm seat gap, a seat on the wrong side or a declared point outside the contact overlap are not;
  the two-screw carrier still fails stack_retention and the credited third point passes it.
- Structural transfer: update_concealed_vent_structure.py accepts the carrier row (upper body) and refuses J4 lower
  rows; the carrier payload screen scales with the carrier mass change.
- Declarations: the carrier counterbore is 7.0 mm (r7 panel; r7 DRIVER bit 6.5) with a loaded boss wall >= r7
  MIN_WALL_LOADED; the carrier is a declared flat-bed part.
- Candidate (bound export only, never skipped into a pass): the carrier STL starts on the bed over its whole silhouette;
  the counterbore and the boss walls measured from the carrier STEP; the locator credited from the tub, panel and
  carrier STEPs; and, when the verifier reports bind the current manifest, their carrier rows pass.
"""
import hashlib
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
import print_rules as PR        # noqa: E402
import check_scope as CS        # noqa: E402
import manifold3d as m3         # noqa: E402
import layout as R7L            # noqa: E402

CK = PR.CK
VAR = 'compact-kowa_lm6hc'
OUT = CV / 'out' / VAR
FX = type('FX', (), dict(PRINT_OVERHANG=dict(R7L.PRINT_OVERHANG)))()


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rd(p):
    return json.loads(read_text(p))


def mbox(x0, x1, y0, y1, z0, z1):
    return m3.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def bed(man):
    return PR.check_bed_contact(FX, 'fx', man, face_down='-Z', why='fixture')


class BedContactFixtures(unittest.TestCase):
    def test_floating_frame_fails(self):
        frame = mbox(0, 60, 0, 40, 2, 5) - mbox(10, 50, 10, 30, 1, 6)
        man = frame + mbox(0, 10, 0, 10, 0, 2)                 # one corner pad reaches the bed
        r = bed(man)
        self.assertEqual(r['status'], 'fail')
        self.assertGreater(r['lifted_area_mm2'], 1000.0)
        self.assertEqual(r['lifted_regions'][0]['lowest_material_z_mm'], 2.0)

    def test_flat_plate_with_counterbore_passes(self):
        cb = m3.Manifold.cylinder(2.4, 3.5, 3.5, 48).translate([30, 20, -0.01])
        hole = m3.Manifold.cylinder(6, 1.7, 1.7, 48).translate([30, 20, -1])
        r = bed(mbox(0, 60, 0, 40, 0, 5) - cb - hole)
        self.assertEqual(r['status'], 'pass', r)
        self.assertLess(r['bed_contact_share'], 0.99)           # the counterbore is not bed contact ...
        self.assertAlmostEqual(r['bed_or_recess_share'], 1.0, places=3)   # ... its roof is reached from its walls

    def test_bridge_over_a_through_window_fails(self):
        ring = mbox(0, 60, 0, 40, 0, 5) - mbox(10, 50, 10, 30, -1, 6)
        r = bed(ring + mbox(10, 50, 18, 22, 2, 5))           # a bar across the 40 mm window, starting at z 2.0
        self.assertEqual(r['status'], 'fail')                # holes of the bed face are not filled
        self.assertAlmostEqual(r['lifted_area_mm2'], (40 - 2 * 3.0) * 4, delta=2.0)   # reach 1.0 + 10 x 0.2 = 3.0

    def test_bed_chamfer_passes(self):
        c = 0.6
        lo = m3.Manifold.cube([60 - 2 * c, 40 - 2 * c, 0.001]).translate([c, c, 0])
        hi = mbox(0, 60, 0, 40, c, c + 0.001)
        man = m3.Manifold.batch_hull([lo, hi]) + mbox(0, 60, 0, 40, c, 5)
        self.assertEqual(bed(man)['status'], 'pass')

    def test_raised_lip_fails(self):
        man = mbox(0, 60, 0, 40, 0, 5) + mbox(60, 63, 0, 40, 1, 5)
        r = bed(man)
        self.assertEqual(r['status'], 'fail')
        # the lip starts at layer 5 (z 1.0): reach 1.0 cantilever + 5 x 0.2 growth = 2.0 of its 3.0 mm
        self.assertAlmostEqual(r['lifted_area_mm2'], 1.0 * 40, delta=2.0)
        self.assertEqual(r['lifted_regions'][0]['lowest_material_z_mm'], 1.0)

    def test_steep_edge_relief_passes(self):
        # a 2.5 mm relief rising 3.0 mm (50 deg) from the bed edge, as the carrier's power-nut relief
        wedge = m3.Manifold.batch_hull([mbox(57.5, 61, -1, 41, -0.01, 0.0), mbox(60.0, 61, -1, 41, 3.0, 3.001)])
        r = bed(mbox(0, 60, 0, 40, 0, 5) - wedge)
        self.assertEqual(r['status'], 'pass', r)
        self.assertLess(r['bed_contact_share'], 0.97)


def cqbox(x0, x1, y0, y1, z0, z1):
    import cadquery as cq
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, y0, z0))


DECL = dict(id='fx', at=(5.0, 3.0), tongue_box=(0, 10, 17.2, 22.2, 0, 6), seat_box=(0, 10, 12, 17.2, 0, 6),
            stop_box=(0, 10, 22.2, 26, 0, 6))


def locate(seat_y1=17.2, stop_y0=22.35, at=(5.0, 3.0)):
    carrier = cqbox(-20, 30, 17.2, 22.2, 0, 20)
    seat = cqbox(1, 9, 13, seat_y1, 0, 5)
    stop = cqbox(1, 9, stop_y0, 25, 1, 6)
    return CS.locator_point(dict(DECL, at=at), carrier, seat, stop)


class LocatorFixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import checks
        cls.CK = checks

    def test_credited(self):
        r = locate()
        self.assertTrue(r['credited'], r)
        self.assertAlmostEqual(r['stop_gap_mm'], 0.15, places=6)
        self.assertAlmostEqual(r['seat_distance_mm'], 0.0, places=6)

    def test_not_credited(self):
        self.assertFalse(locate(stop_y0=22.7)['credited'])            # 0.5 mm stop gap: lift beyond r7's window
        self.assertFalse(locate(stop_y0=22.2)['credited'])            # stop touching: no window, r7 needs 0.1-0.3
        self.assertFalse(locate(seat_y1=16.9)['credited'])            # 0.3 mm seat gap: no bearing
        self.assertFalse(locate(at=(5.0, 5.5))['credited'])           # point outside the seat/stop overlap
        carrier = cqbox(-20, 30, 17.2, 22.2, 0, 20)
        wrong = CS.locator_point(DECL, carrier, cqbox(1, 9, 22.35, 25, 0, 5), cqbox(1, 9, 22.35, 25, 1, 6))
        self.assertFalse(wrong['credited'])                           # seat on the +Y side bears nothing
        self.assertFalse(CS.locator_point(dict(DECL, seat_box=(40, 50, 12, 17.2, 0, 6)), carrier,
                                          cqbox(1, 9, 13, 17.2, 0, 5), cqbox(1, 9, 22.35, 25, 1, 6))['credited'])

    def test_stack_retention_with_and_without_the_third_point(self):
        screws = [((-127., 69.), 0.), ((-25., 9.), 0.)]
        targets = [(-95.5, 10.5), (-95.5, 59.5), (-37.5, 10.5), (-37.5, 59.5)]
        self.assertFalse(CS.stack_retention(screws, (-79.5, 34.0), targets, self.CK)['passed'])
        r = CS.stack_retention(screws + [((-66.0, 5.0), 0.15)], (-79.5, 34.0), targets, self.CK)
        self.assertTrue(r['passed'], r)
        self.assertGreater(r['com_inside_hull_margin_mm'], 0.0)


class Declarations(unittest.TestCase):
    def test_counterbore_and_boss(self):
        import model
        d = 2 * model.CARRIER_CBORE_R
        self.assertGreaterEqual(d, 7.0)                                       # r7 panel counterbore
        self.assertGreaterEqual(d - R7L.DRIVER['bit_d'], 0.5 - 1e-9)           # 0.25 mm per side round the r7 bit
        self.assertGreaterEqual(model.CARRIER_EAR_R - model.CARRIER_CBORE_R, R7L.FDM['MIN_WALL_LOADED'])
        self.assertAlmostEqual(model.CARRIER_BED_Y, model.STACK_Y)            # bed face = the +Y outer surface 22.2

    def test_flat_bed_declared(self):
        self.assertIn('carrier', PR.FLAT_BED_PARTS)


def structural_module():
    import importlib.util
    path = CV / 'structural-review' / 'update_concealed_vent_structure.py'
    spec = importlib.util.spec_from_file_location('ucvs_fp11c', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class StructuralTransfer(unittest.TestCase):
    """FP-11c widened update_concealed_vent_structure.py from tub/panel to the carrier row (upper body, not J4 lower)."""

    def test_changed_rows_guard(self):
        m = structural_module()
        m.check_changed(['tub', 'panel', 'carrier'])
        # FX (verifier C2 major): lens_collar, s_c4 (C2) and eyecup are upper-body rows the transfer covers; base_grip
        # (a J4 lower row) is accepted only through the new free body from the bound STEPs. Every other lower row and
        # any other row still refuses.
        m.check_changed(['tub', 'panel', 'carrier', 'lens_collar', 's_c4', 'eyecup', 'base_grip'])
        self.assertEqual(tuple(m.ALLOWED_CHANGED_LOWER_ROWS), ('base_grip',))
        for bad in (['strap'], ['pack'], ['cap'], ['tripod_nut'], ['xt30_pair'], ['tub', 'pi5'], ['lens']):
            with self.assertRaises(AssertionError):
                m.check_changed(bad)

    def test_carrier_payload_scaling(self):
        m = structural_module()
        ref = rd(CV / 'structural-review/reference-export18-structural-binding.json')['integrated_comparison_loads']
        a = {'carrier': {'mass_est_g': 9.4}}
        same = m.carrier_section(ref, a, a, ['tub'])
        self.assertEqual(same['payload_g'], ref['carrier_payload_g'])
        self.assertEqual(same['reinforced_screen'], ref['carrier_reinforced_at_integrated_payload'])
        up = m.carrier_section(ref, a, {'carrier': {'mass_est_g': 14.0}}, ['tub', 'carrier'])
        k = (ref['carrier_payload_g'] + 4.6) / ref['carrier_payload_g']
        self.assertAlmostEqual(up['payload_g'], ref['carrier_payload_g'] + 4.6, places=9)
        for q in ('stress_MPa', 'deflection_mm'):
            self.assertAlmostEqual(up['reinforced_screen'][q], ref['carrier_reinforced_at_integrated_payload'][q] * k,
                                   places=9)

    def test_supplement_carrier_section_current(self):
        sup = rd(CV / 'structural-review/concealed-vent-structural.json')
        if sup['manifest_sha256'] != sha(OUT / 'manifest.json'):
            self.skipTest('structural supplement not regenerated for the current manifest (FP-16 refresh)')
        m = structural_module()
        ref = rd(CV / 'structural-review/reference-export18-structural-binding.json')
        old = rd(CV / 'history/reviewed-export18/manifest.json')
        a = {r['id']: r for r in old['rows']}
        b = {r['id']: r for r in manifest()['rows']}
        self.assertEqual(sup['carrier'], json.loads(json.dumps(
            m.carrier_section(ref['integrated_comparison_loads'], a, b, sup['changed_manifest_rows']))))
        print('structural carrier screen: payload %.2f g, %.3f MPa, %.3f mm' % (
            sup['carrier']['payload_g'], sup['carrier']['reinforced_screen']['stress_MPa'],
            sup['carrier']['reinforced_screen']['deflection_mm']), flush=True)


def manifest():
    return rd(OUT / 'manifest.json')


def bound(rel):
    p = OUT / rel
    if manifest()['files'].get(rel) != sha(p):
        raise AssertionError('not the manifest-bound file: %s' % rel)
    return p


class CandidateGeometry(unittest.TestCase):
    """The bound export of the current manifest; these never skip."""

    @classmethod
    def setUpClass(cls):
        import cadquery as cq
        cls.cq = cq
        cls.step = {k: cq.importers.importStep(str(bound('step/%s.step' % k))).val() for k in ('carrier', 'tub', 'panel')}

    def test_carrier_starts_on_the_bed(self):
        man = PR.manifold_from_stl(bound('stl/carrier.stl'))
        r = PR.check_bed_contact(FX, 'carrier', man, face_down='+Y', why='test')
        print('carrier bed contact: silhouette %.1f mm2, bed %.1f mm2 (share %.4f), covered recesses %.1f mm2, lifted '
              '%.2f mm2' % (r['silhouette_area_mm2'], r['bed_area_mm2'], r['bed_contact_share'],
                            r['covered_recess_area_mm2'], r['lifted_area_mm2']), flush=True)
        self.assertEqual(r['status'], 'pass', r)

    def test_counterbore_and_boss_wall_from_step(self):
        import model
        cq, s = self.cq, self.step['carrier']
        for (x, z) in model.CARRIER_SCREWS:
            for y in (20.0, 21.5):
                walls = []
                for k in range(24):
                    a = 2 * math.pi * k / 24
                    ux, uz = math.cos(a), math.sin(a)
                    e = cq.Edge.makeLine(cq.Vector(x, y, z), cq.Vector(x + 12 * ux, y, z + 12 * uz))
                    sp = sorted(s.intersect(e).Edges(), key=lambda q: min(math.hypot(v.x - x, v.z - z)
                                                                         for v in (q.startPoint(), q.endPoint())))
                    self.assertTrue(sp, (x, z, y, k))
                    r0 = min(math.hypot(v.x - x, v.z - z) for v in (sp[0].startPoint(), sp[0].endPoint()))
                    self.assertAlmostEqual(r0, model.CARRIER_CBORE_R, delta=0.01)      # 7.0 mm bore, measured
                    walls.append(sp[0].Length())
                print('carrier screw (%.1f, %.1f) y %.1f: bore r %.3f, min radial wall %.3f mm'
                      % (x, z, y, model.CARRIER_CBORE_R, min(walls)), flush=True)
                self.assertGreaterEqual(min(walls), R7L.FDM['MIN_WALL_LOADED'] - 1e-6)

    def test_locator_credited_from_steps(self):
        import model
        for d in model.CARRIER_LOCATORS:
            r = CS.locator_point(d, self.step['carrier'], self.step[d['seat_part']], self.step[d['stop_part']])
            print('locator %s: seat %.4f mm, stop gap %.4f mm, credited %s'
                  % (d['id'], r.get('seat_distance_mm', -1), r.get('stop_gap_mm', -1), r['credited']), flush=True)
            self.assertTrue(r['credited'], r)


def current(name, verifier):
    p = OUT / name
    if not p.exists():
        return None
    r = rd(p)
    if r.get('manifest_sha256') != sha(OUT / 'manifest.json') or r.get('verification_source_sha256') != sha(CV / verifier):
        return None
    return r


class Reports(unittest.TestCase):
    def test_print_rows(self):
        r = current('print-checks.json', 'verify_print_checks.py')
        if r is None:
            self.skipTest('no print-checks.json bound to the current manifest and verifier')
        for cat in ('print_overhang', 'print_bridge_direction', 'bed_contact'):
            row = {x['part']: x for x in r['results'][cat]}['carrier']
            self.assertEqual(row['status'], 'pass', (cat, row.get('error')))

    def test_driver_rows(self):
        for rel in ('review-2026-10-10/fp07/driver-compact-kowa_lm6hc.json',
                    'review-2026-10-10/fp11c/main-subset-compact-kowa_lm6hc.json'):
            p = CV / rel
            if not p.exists():
                continue
            r = rd(p)
            if r.get('manifest_sha256') != sha(OUT / 'manifest.json') or                     r.get('verification_source_sha256') != sha(CV / 'verify_candidate.py'):
                continue
            rows = {c['id']: c for c in r['checks'] if c['category'] in ('driver', 'service_driver')}
            ids = [i for i in rows if i.split('@')[0] in ('p_carrier1', 'p_carrier2')]
            self.assertEqual(len(ids), 4, rel)       # carrier_screws and svc_carrier_screws_out, both screws
            for i in ids:
                self.assertEqual(rows[i]['status'], 'pass', (rel, i, rows[i].get('hits')))
            return
        self.skipTest('no driver record bound to the current manifest and verifier')

    def test_stack_retention_row(self):
        r = current('check-scope-checks.json', 'verify_check_scope.py')
        if r is None:
            self.skipTest('no check-scope-checks.json bound to the current manifest and verifier')
        st = {c['id']: c for c in r['checks'] if c['category'] == 'stack_retention'}['vertical_carrier']
        self.assertEqual(st['status'], 'pass')
        self.assertTrue(all(l['credited'] for l in st['locators']))
        self.assertGreater(st['com_inside_hull_margin_mm'], 0.0)


if __name__ == '__main__':
    unittest.main(verbosity=2)

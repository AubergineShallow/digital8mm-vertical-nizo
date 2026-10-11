# SPDX-License-Identifier: MIT
"""Plenum trial2 and the per-part bed-edge chamfer rule (review VN-51, VN-52, VN-59, VN-37; fix FP-11a).

Run:  run_locked.py -- cad/gs8-d2-v1/candidate-vertical/tests/test_plenum_trial2.py

- BedChamfer fixtures (manifold3d only): a sharp block fails with its whole outline; r7's 0.6 mm 45 deg bed chamfer passes;
  a 0.3 mm chamfer fails; one sharp edge of four fails with about that edge's length; a sharp hole in a chamfered block
  passes and is reported (info only).
- Layout (vent_geometry data, both storage lengths): no rib lies lengthwise inside the range of any series-section plane
  family that verify_check_scope samples (so its coarse planes cannot step over a rib), every verifier mouth ray and seed
  is clear of the mullions, mouth openings are short enough for one bridge, and a roof line in z crosses at most one
  cold-row break.
- Plenum body (CadQuery; the tub shell, cavity, plenum, mouths, ports and CSI slot, i.e. everything inside the checked
  plenum sections; both storage lengths): the per-region single-direction bridge rule and r7's overhang rule pass with
  no failing region; mouth necks equal the nominal net areas; every series-section minimum taken at the verifier's own
  planes equals the minimum over every constant interval between rib faces (sampling not exploited); hot and cold
  branch parity pass (VN-37); the skin bed chamfer check passes and fails without the chamfer.
- Wiring: verify_print_checks runs bed_chamfer on every print pose; the coupon script crops all four mouths; the flow
  baseline was rewritten with a reason and reproduces from its source report.
"""
import ast
import json
import math
import re
import sys
import tempfile
import types
import unittest
from pathlib import Path

CV = Path(__file__).resolve().parents[1]
R7 = CV.parent
for _p in (str(R7), str(CV)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
from cv_io import read_text    # noqa: E402
import manifold3d as m3         # noqa: E402
import print_rules as PR        # noqa: E402
import check_scope as CS        # noqa: E402
import vent_geometry as VG      # noqa: E402
import layout as R7L            # noqa: E402  (r7 layout: PRINT_OVERHANG rule constants, read-only)

LENGTHS = (158.0, 185.0)
C = PR.dc.FDM['BED_CHAMFER']


def mbox(x0, x1, y0, y1, z0, z1):
    return m3.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def chamfered_block(w, d, h, c, sharp_x1=False):
    """w x d x h block on the bed with a 45 deg bed chamfer c (optionally the x = w edge left sharp)."""
    lo = mbox(c, w - (0 if sharp_x1 else c), c, d - c, 0, 0.001)
    hi = mbox(0, w, 0, d, c, c + 0.001)
    return m3.Manifold.batch_hull([lo, hi]) + mbox(0, w, 0, d, c, h)


class BedChamfer(unittest.TestCase):
    def test_sharp_block_fails_with_its_outline(self):
        r = PR.check_bed_chamfer('fx', mbox(0, 40, 0, 20, 0, 5))
        self.assertEqual(r['status'], 'fail')
        self.assertAlmostEqual(r['exterior_perimeter_mm'], 120.0, delta=0.5)
        self.assertAlmostEqual(r['exterior_unchamfered_mm'], 120.0, delta=2.0)

    def test_r7_chamfer_passes(self):
        r = PR.check_bed_chamfer('fx', chamfered_block(40, 20, 5, C))
        self.assertEqual(r['status'], 'pass', r)
        self.assertLess(r['exterior_unchamfered_mm'], 0.5)

    def test_half_chamfer_fails(self):
        r = PR.check_bed_chamfer('fx', chamfered_block(40, 20, 5, 0.3))
        self.assertEqual(r['status'], 'fail')

    def test_one_sharp_edge_reports_its_length(self):
        r = PR.check_bed_chamfer('fx', chamfered_block(40, 20, 5, C, sharp_x1=True))
        self.assertEqual(r['status'], 'fail')
        self.assertAlmostEqual(r['exterior_unchamfered_mm'], 20.0, delta=2.5)

    def test_sharp_hole_is_info_only(self):
        man = chamfered_block(40, 20, 5, C) - mbox(15, 25, 5, 15, -1, 6)
        r = PR.check_bed_chamfer('fx', man)
        self.assertEqual(r['status'], 'pass', r)
        self.assertAlmostEqual(r['hole_perimeter_mm'], 40.0, delta=0.5)
        self.assertGreater(r['hole_unchamfered_mm_info'], 35.0)

    def test_empty_mesh_fails(self):
        self.assertEqual(PR.check_bed_chamfer('fx', None)['status'], 'fail')


def x_bands(length):
    """Constant-x rib bands (x0, x1, z0, z1): hot z-ribs, mouth mullions (z 0..2.5)."""
    h = VG.RIB_T / 2
    out = [(x - h, x + h, a, b) for x, a, b in VG.hot_zribs()]
    out += [(x - h, x + h, 0., 2.5) for x in VG.cold_bottom_mullions(length)]
    return out


def z_bands(length):
    """Constant-z rib bands (z0, z1, x0, x1): rows of both bays and the hot left separator."""
    h = VG.RIB_T / 2
    out = [(z - h, z + h, a, b) for z, segs in VG.cold_rows(length) + VG.hot_rows(length) for a, b in segs]
    a, b, c, d = VG.HOT_LEFT_SEPARATOR
    return out + [(c, d, a, b)]


def overlap(a0, a1, b0, b1):
    return min(a1, b1) - max(a0, b0) > 1e-9


class Layout(unittest.TestCase):
    def test_no_rib_lengthwise_in_a_series_family(self):
        for L in LENGTHS:
            # verify_check_scope series families: (axis of the planes, plane range, rectangle range of the other axis)
            fam = {'cold_rear': ('x', (-L + 3., -104.), (2.5, 97.5)), 'cold_bottom': ('z', (2.6, 17.8), (-L + 2.5, -65.)),
                   'hot_bottom': ('z', (2.6, 15.8), (-62., -2.5)), 'hot_front': ('x', (-16., -2.7), (2.5, 97.5))}
            for name, (ax, (p0, p1), (u0, u1)) in fam.items():
                bands = x_bands(L) if ax == 'x' else z_bands(L)
                for b in bands:
                    self.assertFalse(overlap(b[0], b[1], p0, p1) and overlap(b[2], b[3], u0, u1),
                                     '%s: rib band %s lies along the %s planes (L %g)' % (name, b, ax, L))
            # the diagonal crosses the hot families; it must not start inside the hot underside mouth rectangle
            (x0, z0), _ = VG.HOT_DIAGONAL
            self.assertGreater(x0 - VG.RIB_T, -5.0)

    def test_mouth_rays_and_seeds_clear_of_mullions(self):
        h = VG.RIB_T / 2
        for L in LENGTHS:
            cold_x = (-L + 4. - 83.) / 2
            self.assertTrue(all(abs(x - cold_x) > h + 0.3 for x in VG.cold_bottom_mullions(L)), L)
            rear = [z for z, segs in VG.cold_rows(L) if 5 < z < 75 and segs[0][0] <= -L]
            self.assertTrue(all(abs(z - 40.) > h + 0.3 for z in rear), L)
        self.assertGreater(abs(VG.HOT_BOTTOM_MULLION_X - (-32.)), h + 0.3)
        self.assertGreater(abs(VG.HOT_FRONT_MULLION_Z - 22.5), h + 0.3)
        self.assertTrue(all(abs(x - (-32.)) > h + 0.3 for x in VG.HOT_ZRIB_X))
        # the cold port rays (x -85.5) and hot port rays (x -37.75) at the wall: no rib reaches y -28.05..-25.45 there
        self.assertLess(VG.RIB_Y[1], -27.85)

    def test_openings_bridgeable(self):
        for L in LENGTHS:
            ms = sorted(VG.cold_bottom_mullions(L))
            edges = [-L + 4.] + [v for m in ms for v in (m - VG.RIB_T / 2, m + VG.RIB_T / 2)] + [-83.]
            spans = [edges[i + 1] - edges[i] for i in range(0, len(edges), 2)]
            self.assertLessEqual(max(spans), 25.0, L)     # first lintel strand
            self.assertEqual(len(ms) % 2, 0)
            rear = sorted(z for z, segs in VG.cold_rows(L) if 5 < z < 75 and segs[0][0] <= -L)
            e = [5.] + [v for z in rear for v in (z - VG.RIB_T / 2, z + VG.RIB_T / 2)] + [75.]
            self.assertLessEqual(max(e[i + 1] - e[i] for i in range(0, len(e), 2)), 30.0)
        hb = [(-59., VG.HOT_BOTTOM_MULLION_X - VG.RIB_T / 2), (VG.HOT_BOTTOM_MULLION_X + VG.RIB_T / 2, -5.)]
        self.assertLessEqual(max(b - a for a, b in hb), 30.0)
        hf = [(5., VG.HOT_FRONT_MULLION_Z - VG.RIB_T / 2), (VG.HOT_FRONT_MULLION_Z + VG.RIB_T / 2, 40.)]
        self.assertLessEqual(max(b - a for a, b in hf), 30.0)

    def test_cold_breaks_staggered(self):
        """A roof line at constant x crosses at most one broken row before meeting a solid one."""
        for L in LENGTHS:
            rows = sorted(VG.cold_rows(L))
            xs = [x / 10.0 for x in range(int(-L * 10) + 30, -650, 5)]
            for x in xs:
                broken = [any(a <= x <= b for a, b in segs) is False and segs[0][0] <= x <= segs[-1][1]
                          for z, segs in rows]
                for i in range(len(broken) - 1):
                    self.assertFalse(broken[i] and broken[i + 1], 'x %.1f rows %d,%d (L %g)' % (x, i, i + 1, L))

    def test_post_centres_empty(self):
        self.assertEqual(VG.post_centres(158.), [])
        self.assertTrue(VG.metadata(158.)['revision'].startswith('shadow-gap'))


# ------------------------------------------------------------------------------------------- plenum body (CadQuery)
_BODY = {}


def plenum_body(L):
    """The tub shell and cavity of model.make_tub with the plenum, its mouths, the wall ports and the CSI slot: all the
    geometry the plenum sections and the plenum roof see (model.make_tub's other features lie outside y -35.6..-25.4)."""
    if L not in _BODY:
        import cadquery as cq
        outer = cq.Workplane('XY').box(L, 56, 100, centered=False).translate((-L, -28, 0)).edges('|Z').fillet(2).val()
        s = outer.cut(VG.box(-L + 2.5, -5.2, -25.5, 29, 2.5, 97.5))
        cuts = VG.mouth_cuts(L) + VG.inlet_cuts() + VG.side_exhaust_cuts()
        cuts.append(cq.Workplane(obj=VG.box(-89, -77, VG.OUTER_Y - .1, -25.4, 41, 68)).edges('|Y').fillet(1).val())
        s = s.fuse(*VG.additions(L)).cut(*cuts).clean()
        _BODY[L] = s
    return _BODY[L]


def print_manifold(shape):
    import cadquery as cq
    sh = shape.rotate((0, 0, 0), (1, 0, 0), 90)
    b = sh.BoundingBox()
    sh = sh.translate(cq.Vector(-b.xmin, -b.ymin, -b.zmin))
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / 'b.stl'
        cq.exporters.export(sh, str(p), tolerance=.06, angularTolerance=.15)
        return PR.manifold_from_stl(p)


def free(shape, axis, pos, u0, u1, v0, v1):
    """verify_shadow_plenum.free_section's Boolean (rectangle face minus the solid)."""
    import cadquery as cq
    V = cq.Vector
    pt = lambda u, v: {'x': (pos, u, v), 'y': (u, pos, v), 'z': (u, v, pos)}[axis]  # noqa: E731
    ps = [pt(u0, v0), pt(u1, v0), pt(u1, v1), pt(u0, v1)]
    face = cq.Face.makeFromWires(cq.Wire.makePolygon([V(*p) for p in ps + ps[:1]]))
    return face.cut(shape).Area()


def frange(x0, x1, dx):
    n = int(math.floor((x1 - x0) / dx + 1e-9))
    return [round(x0 + i * dx, 6) for i in range(n + 1)]


def families(L):
    """verify_check_scope's mouth planes and series families (its code, unchanged; VG.post_centres is empty)."""
    mouths = {'cold_rear': ('x', [-L + .05, -L + 1.25, -L + 2.49, -L + 2.62], -34., -28., 5., 75.),
              'cold_bottom': ('z', [.05, 1.25, 2.49, 2.62], -L + 4., -83., -34., -28.),
              'hot_bottom': ('z', [.05, 1.25, 2.49, 2.62], -59., -5., -34., -28.),
              'hot_front': ('x', [-.05, -1.25, -2.49, -2.62], -34., -28., 5., 40.)}
    series = {'cold_rear': ('x', frange(-L + 3., -104., 2.), (-L + 3., -104.), (-34., -28., 2.5, 97.5)),
              'cold_bottom': ('z', frange(2.6, 17.8, .4), (2.6, 17.8), (-L + 2.5, -65., -34., -28.)),
              'hot_bottom': ('z', frange(2.6, 15.8, .4), (2.6, 15.8), (-62., -2.5, -34., -28.)),
              'hot_front': ('x', frange(-16., -2.7, 1.), (-16., -2.7), (-34., -28., 2.5, 97.5))}
    return mouths, series


def events(L, axis, lo, hi):
    """Every rib/frame face coordinate along `axis` inside [lo, hi] (the free section is constant between them)."""
    ev = {lo, hi}
    h = VG.RIB_T / 2
    if axis == 'x':
        for z, segs in VG.cold_rows(L) + VG.hot_rows(L):
            ev |= {v for a, b in segs for v in (a, b)}
        ev |= {v for x, _, _ in VG.hot_zribs() for v in (x - h, x + h)}
        (x0, z0), (x1, z1) = VG.HOT_DIAGONAL
        ev |= {x0 - 1, x0 + 1, x1 - 1, x1 + 1}
        ev |= {-91., -75., -65., -62., -89., -77.}
    else:
        for z, segs in VG.cold_rows(L) + VG.hot_rows(L):
            ev |= {z - h, z + h}
        ev |= {VG.HOT_ZRIB_TOP, VG.HOT_LEFT_SEPARATOR[2], VG.HOT_LEFT_SEPARATOR[3], 2.4, 2.75}
        (x0, z0), (x1, z1) = VG.HOT_DIAGONAL
        ev |= {z0 - 1, z0 + 1, z1 - 1, z1 + 1}
    ev = sorted(v for v in ev if lo <= v <= hi)
    mids = [(ev[i] + ev[i + 1]) / 2 for i in range(len(ev) - 1) if ev[i + 1] - ev[i] > 0.02]
    return mids + [v + d for v in ev for d in (-0.01, 0.01) if lo <= v + d <= hi]


class PlenumBody(unittest.TestCase):
    def test_bridge_rule_and_overhang_pass(self):
        L7 = types.SimpleNamespace(PRINT_OVERHANG=dict(R7L.PRINT_OVERHANG), PARTS={'tub': dict(face_down='-Y')})
        for L in LENGTHS:
            man = print_manifold(plenum_body(L))
            ov = PR.CK.check_print_overhang(L7, 'tub', man, [], face_down='-Y')
            bd = PR.check_bridge_direction(L7, 'tub', man, [], face_down='-Y')
            print('L %g: r7 overhang %s (%s); bridge direction %s, %s failing, longest %.1f mm'
                  % (L, ov['status'], ov.get('error'), bd['status'], bd.get('failing_region_count'),
                     bd.get('longest_bridge_mm', 0)), flush=True)
            self.assertEqual(ov['status'], 'pass', ov.get('error'))
            self.assertEqual(bd['status'], 'pass', bd.get('failing_regions'))
            self.assertLessEqual(bd['longest_bridge_mm'], 30.0)
            bc = PR.check_bed_chamfer('tub', man, face_down='-Y')
            self.assertEqual(bc['status'], 'pass', bc)

    def test_sections_parity_and_sampling(self):
        for L in LENGTHS:
            s = plenum_body(L)
            mouths, series = families(L)
            nominal = VG.mouth_nominal(L)
            neck = {}
            for k, (ax, planes, *uv) in mouths.items():
                neck[k] = min(free(s, ax, p, *uv) for p in planes)
                self.assertAlmostEqual(neck[k], nominal[k]['net'], delta=0.01, msg='%s L %g' % (k, L))
            smin = {}
            for k, (ax, planes, (lo, hi), rect) in series.items():
                coarse = min(free(s, ax, p, *rect) for p in planes)
                fine = min(free(s, ax, p, *rect) for p in events(L, ax, lo, hi))
                print('L %g %s: verifier planes min %.3f, every-interval min %.3f' % (L, k, coarse, fine), flush=True)
                # the verifier's planes must not step over a smaller section (they may only be more conservative)
                self.assertLessEqual(coarse, fine + 1e-3, '%s sampling misses a smaller section' % k)
                self.assertAlmostEqual(coarse, fine, delta=1e-3, msg='%s: a verifier plane lies on a rib end face' % k)
                smin[k] = coarse
            ports = {'cold': 4 * 35 * 3., 'hot': 4 * 42.5 * 3.}
            for bay, names in (('cold', ('cold_rear', 'cold_bottom')), ('hot', ('hot_bottom', 'hot_front'))):
                r = CS.branch_parity([dict(name=n, mouth_mm2=neck[n], series_mm2=[smin[n]]) for n in names], ports[bay])
                print('L %g %s parity %.3f vs %.1f' % (L, bay, r['effective_sum_mm2'], ports[bay]), flush=True)
                self.assertTrue(r['passed'], r)

    def test_skin_without_chamfer_fails(self):
        sharp = VG.box(-158, 0, VG.OUTER_Y, VG.SKIN_INNER, 0, 100).fuse(VG.box(-158, 0, VG.SKIN_INNER - .05, -25.4, 0, 100))
        self.assertEqual(PR.check_bed_chamfer('skin', print_manifold(sharp))['status'], 'fail')
        good = VG.skin(158.).fuse(VG.box(-158, 0, VG.SKIN_INNER - .05, -25.4, 0, 100))
        self.assertEqual(PR.check_bed_chamfer('skin', print_manifold(good))['status'], 'pass')


class Wiring(unittest.TestCase):
    def test_print_verifier_runs_bed_chamfer_on_every_pose(self):
        src = read_text(CV / 'verify_print_checks.py')
        tree = ast.parse(src)
        cats = next(n.value for n in tree.body if isinstance(n, ast.Assign) and getattr(n.targets[0], 'id', '') == 'CATEGORIES')
        self.assertIn('bed_chamfer', ast.literal_eval(cats))
        self.assertIn("res['bed_chamfer'] = bed_chamfer_rows(out, manifest, print_parts)", src)
        self.assertIn("print_parts = sorted(manifest['print_poses'])", src)

    def test_coupon_crops_all_four_mouths(self):
        src = read_text(CV / 'make_shadow_plenum_coupon.py')
        self.assertIn("'all_four_mouths', [-length, 0., -35.6, -25.5, 0., 100.]", src)
        self.assertIn("length = m['core_dimensions_mm'][0]", src)
        for L in LENGTHS:
            crop = (-L, 0., -35.6, -25.5, 0., 100.)
            mouths, _ = families(L)
            for k, (ax, planes, u0, u1, v0, v1) in mouths.items():
                lo = {'x': (min(planes), u0, v0), 'z': (u0, v0, min(planes))}[ax]
                hi = {'x': (max(planes), u1, v1), 'z': (u1, v1, max(planes))}[ax]
                for i in range(3):
                    self.assertTrue(crop[2 * i] - 0.1 <= lo[i] and hi[i] <= crop[2 * i + 1] + 0.1, (k, L, i))

    def test_flow_baseline_rewritten_with_reason(self):
        b = json.loads(read_text(CV / 'review-2026-10-10/fp12/flow-network-baseline.json'))
        self.assertTrue(re.search(r'FP-11a', b['reason']), b['reason'])
        r = json.loads(read_text(CV / b['source_report']))
        el = next(c for c in r['checks'] if c['category'] == 'flow_network' and c['id'] == 'model')['elements']
        ok, det = CS.flow_drift(CS.flow_network(el), b)
        self.assertTrue(ok, det)


if __name__ == '__main__':
    unittest.main(verbosity=2)

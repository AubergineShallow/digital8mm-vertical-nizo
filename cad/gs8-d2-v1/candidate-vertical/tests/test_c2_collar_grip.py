# SPDX-License-Identifier: MIT
"""C2 regression tests: collar washer margins and LR foot support (VN-55, VN-58, FP-11d); base grip rear J4 pocket
end wall, declared pocket-floor support zone and J4 slide clearance (VN-57, FP-11e); s_j counterbore side wall
(the 0.373 mm feather edge, FP-09 note) and the 1.0 mm run-drop wall found while fixing.

Run:  run_locked.py -- cad/gs8-d2-v1/candidate-vertical/tests/test_c2_collar_grip.py

- Source (CAD, nothing written outside the temp dir): the collars from model.make_collar in the candidate layout
  context pass the r7 washer rows with r7's margins and fail them with the 9ced753 lug (negative control); the LR
  support only adds material outside the body inside the foot's cone; the r7 overhang rule passes the support and
  fails the same collar without it; the candidate print stock keeps the r7 membrane contract; r7 prepare_print's
  failure on the Fujinon collar and the corrupted input it leaves behind are pinned (PHASE1-STATUS s9).
- Grip (CAD): the end-wall blocks stay clear of the installed XT30 pair/fuse and of every rigid junction / pack
  service pose; the declared zone lies inside the neck-slot footprint, off the keyhole lips; the s_j side wall closes
  the counterbore window that the grip without it has; the wall around the bore is >= 1.2 mm.
- Bound evidence (compact-kowa_lm6hc, current manifest): print rows pass for lens_collar and base_grip (the grip
  uses its declared zone only), no unclassified thin spot on base_grip, and the canonical full audit has every
  clearance / lens_clamp washer row passing, with current manifest, verifier, steps and helper bindings.
"""
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

CV = Path(__file__).resolve().parents[1]
for _p in (str(CV.parent), str(CV), str(CV / 'structural-review')):
    if _p not in sys.path:
        sys.path.insert(0, _p)
from cv_io import read_text              # noqa: E402
from _full_audit_evidence import load_full_audit  # noqa: E402
import j7_collar_checks as J             # noqa: E402

VARIANT = 'compact-kowa_lm6hc'
OUT = CV / 'out' / VARIANT
LENSES = ('kowa_lm6hc', 'fujinon_hf6xa')


def sha(p):
    import hashlib
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


class _CK:
    @staticmethod
    def _r(x, n=3):
        return None if x is None else round(float(x), n)


def overhang(L, pid, shape, face, zones=()):
    """r7 check_print_overhang on an in-memory part in export_candidate's print pose."""
    import cadquery as cq
    import print_rules as PR
    ax, angle = {'+X': ((0, 1, 0), 90), '+Z': ((1, 0, 0), 180)}[face]
    sh = shape.rotate((0, 0, 0), ax, angle)
    b = sh.BoundingBox()
    move = (-b.xmin, -b.ymin, -b.zmin)
    sh = sh.translate(cq.Vector(*move))
    R, t = PR.pose_transform(dict(rotation_axis=ax, angle_deg=angle, translation_mm=move))
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / ('%s.stl' % pid)
        cq.exporters.export(sh, str(p), tolerance=.06, angularTolerance=.15)
        man = PR.manifold_from_stl(p)
    zz = [dict(z, box=PR.map_box(z['box'], R, t)) for z in zones]
    return PR.CK.check_print_overhang(L, pid, man, zz, face_down=face)


class Collar(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import j7_collar_checks as J
        import model as M
        import printed_collar as PC
        cls.J, cls.M, cls.PC = J, M, PC
        cls.ctx = J.candidate_layout('kowa_lm6hc')
        cls.L = cls.ctx.__enter__()
        cls.collars = {n: M.make_collar(n) for n in LENSES}
        cls.r7built = {n: PC.build_part(cls.L, 'lens_collar', n).val() for n in LENSES}

    @classmethod
    def tearDownClass(cls):
        cls.ctx.__exit__(None, None, None)

    def test_lug_values_restore_r7_margins(self):
        lug, w = self.L.COLLAR['lug'], self.L.M3['washer']['d'] / 2
        self.assertEqual((lug['y_out'], lug['screw_y'], lug['bit_relief_y']), (-30.8, -26.8, -22.8))
        s4 = next(s for s in self.L.SCREWS if s['id'] == 's_c4')
        self.assertEqual((s4['head_point'][1], s4['tip'][1]), (-26.8, -26.8))
        # relief unchanged: the analytic body wall verify_candidate reports stays >= 1.6
        self.assertGreaterEqual(math.hypot(lug['bit_relief_y'], 6) - 21.15 - 0.6, 1.6)
        fp = w + lug['washer_float'] + lug['washer_edge_min']
        # r7 layout.py COLLAR lug (the context replaces it; ContextIsRestored in test_collar_r7_mechanical pins the
        # restore): relief 0.5 past the washer, footprint 0.1 inside the lug face
        r7c = dict(y_out=-35.0, screw_y=-31.0, bit_relief_y=-27.0)
        for c in (lug, r7c):
            self.assertAlmostEqual(abs(c['bit_relief_y'] - c['screw_y']) - w, 0.5, places=9)
            self.assertAlmostEqual(abs(c['y_out'] - c['screw_y']) - fp, 0.1, places=9)

    def test_washer_rows_pass_on_model_collars(self):
        rows = {i: x for _, i, x in self.J.washer_rows(self.L, self.collars, _CK)}
        for n in LENSES:
            fs, fr = rows['washer_flat_support/%s' % n], rows['washer_free_seat/%s' % n]
            self.assertEqual((fs['status'], fr['status']), ('pass', 'pass'), n)
            self.assertEqual(fs['unsupported_mm3'], 0.0)
            self.assertEqual(fs['nominal_margins'], dict(lug_face_mm=0.1, bit_relief_mm=0.5))
            self.assertAlmostEqual(fr['min_gap_mm'], 0.3, places=3)

    def test_washer_rows_fail_on_9ced753_lug(self):
        """Negative control: the same rows on a collar built with the 9ced753 lug values fail as phase 1 measured."""
        lug = self.L.COLLAR['lug']
        old = dict(lug)
        try:
            lug.update(y_out=-30.0, screw_y=-26.3, bit_relief_y=-22.8)
            bad = {n: self.M.make_collar(n) for n in LENSES}
            rows = {i: x for _, i, x in self.J.washer_rows(self.L, bad, _CK)}
        finally:
            lug.clear()
            lug.update(old)
        for n in LENSES:
            self.assertEqual(rows['washer_flat_support/%s' % n]['status'], 'fail', n)
            self.assertEqual(rows['washer_free_seat/%s' % n]['status'], 'fail', n)
            self.assertAlmostEqual(rows['washer_free_seat/%s' % n]['worst_overlap_mm3'], 0.1564, places=3)

    def test_lr_support_adds_only_outside_the_body(self):
        import cadquery as cq
        C = self.L.COLLAR
        ly, lz = self.L.LENS_AXIS
        y, z = C['feet']['LR']
        r = C['foot_d'] / 2
        x0 = self.L.collar_spec('kowa_lm6hc')['rear_x']
        for n in LENSES:
            new, base = self.collars[n], self.r7built[n]
            self.assertTrue(new.isValid())
            self.assertEqual(len(new.Solids()), 1)
            self.assertLess(base.copy().cut(new.copy()).Volume(), 1e-6, n)
            add = new.copy().cut(base.copy())
            # 31.44 mm3 (exact GProp); Shape.Volume() of the whole union over-reads it by ~0.22 mm3 (cone faces)
            self.assertAlmostEqual(add.Volume(), 31.44, delta=0.02)
            bb = add.BoundingBox()
            self.assertGreaterEqual(bb.xmin, x0 - 1e-6)
            self.assertLessEqual(bb.xmax, x0 + r * self.M.LR_SUPPORT_RUN + 1e-6)
            inner = cq.Solid.makeCylinder(C['body_r'] - 0.5 - 1e-3, 20, cq.Vector(-5, ly, lz), cq.Vector(1, 0, 0))
            self.assertLess(add.intersect(inner).Volume(), 1e-6, n)
            foot = cq.Solid.makeCylinder(r + 1e-3, 20, cq.Vector(-5, y, z), cq.Vector(1, 0, 0))
            self.assertLess(add.cut(foot).Volume(), 1e-6, n)

    def test_lr_overhang_r7_rule(self):
        """The r7 overhang rule passes the model collar stock and finds the LR foot region without the support."""
        import print_rules as PR
        LV = PR.LayoutView(self.L, PARTS={'lens_collar': dict(self.L.PARTS.get('lens_collar') or {}, face_down='+X')})
        good = overhang(LV, 'lens_collar', self.M.collar_print_stock(self.collars['kowa_lm6hc'])['shape'], '+X')
        self.assertEqual(good['status'], 'pass', good.get('unsupported'))
        bad = overhang(LV, 'lens_collar', self.M.collar_print_stock(self.r7built['kowa_lm6hc'])['shape'], '+X')
        self.assertEqual(bad['status'], 'fail')
        self.assertEqual(len(bad['unsupported']), 1)
        self.assertAlmostEqual(bad['unsupported'][0]['area_mm2'], 11.0, delta=0.5)

    def test_candidate_print_stock_contract_on_model_collars(self):
        import cadquery as cq
        C = self.L.COLLAR
        for n, sh in self.collars.items():
            ps = self.M.collar_print_stock(sh.copy())['shape']
            self.assertTrue(ps.isValid(), n)
            self.assertEqual(len(ps.Solids()), 1, n)
            exp = 3 * math.pi * (C['hole_d'] / 2) ** 2 * C['bridge_membrane_t']
            # the added material itself (exact); the difference of the two ~11 000 mm3 Shape.Volume() reads is within
            # model.collar_print_stock's own 0.02 (it reads 5.4537 on the support-carrying collar)
            self.assertAlmostEqual(ps.copy().cut(sh.copy()).Volume(), exp, places=4)
            self.assertLess(abs(ps.Volume() - sh.Volume() - exp), 0.02)
            clears = [cq.Solid.makeCylinder(C['hole_d'] / 2, 30, cq.Vector(-10, *C['feet'][k]), cq.Vector(1, 0, 0))
                      for k in C['bolted']]
            cleared = ps.cut(*clears)
            self.assertLess(cleared.cut(sh).Volume() + sh.cut(cleared).Volume(), 0.001, n)

    def test_r7_prepare_print_corrupts_its_input(self):
        """PHASE1-STATUS s9, cause pinned (C2): r7 prepare_print runs sh.fuse(*disks).clean() on the shape it is
        given. On the candidate Fujinon collar the same-domain cleanup (ShapeUpgrade_UnifySameDomain) rewrites
        sub-shapes that the fused result still shares with `sh`, so `sh` itself turns invalid (BRepCheck). r7's own
        check sh.cut(prepared) then reports ~13052 mm3 'removed', and any later union on `sh` (model.collar_print_stock)
        fails. On a copy the cleaned stock is valid and removes nothing. The geometry is not at fault; the candidate
        print path copies its input and skips clean(), and nothing calls it after r7 prepare_print."""
        n = 'fujinon_hf6xa'
        sh = self.M.make_collar(n)
        keep = sh.copy()
        self.assertTrue(sh.isValid())
        with self.assertRaisesRegex(ValueError, 'removed finished material'):
            self.PC.prepare_print(self.L, 'lens_collar', sh)
        self.assertFalse(sh.isValid())                      # the input was modified in place
        self.assertTrue(keep.isValid())
        with self.assertRaisesRegex(ValueError, 'Invalid collar print union'):
            self.M.collar_print_stock(sh)
        self.assertAlmostEqual(self.M.collar_print_stock(keep)['added_volume_mm3'], 5.4536, places=3)
        # the same r7 preparation on a copy is sound: valid stock, nothing of the finished part removed
        C = self.L.COLLAR
        disks = [self.PC._cylx(C['hole_d'] / 2 + 0.1, C['flange_x'][1] - C['bridge_membrane_t'], C['flange_x'][1],
                               *C['feet'][k]) for k in C['bolted']]
        prep = keep.copy().fuse(*disks).clean()
        self.assertTrue(prep.isValid())
        self.assertLess(keep.copy().cut(prep.copy()).Volume(), 0.001)
        self.assertTrue(keep.isValid())


class Grip(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import cadquery as cq
        import j4_trial_geometry as JG
        import model as M
        import print_rules as PR
        cls.M, cls.cq = M, cq
        with JG.trial_layout(M.L, **PR.J4_TRIAL):
            cls.tongues = [dict(t) for t in M.L.TONGUES]
            cls.grip = M.make_base_grip()
            cls.blocks = {'pocket_end': M.grip_passage_wall(), 'run_drop': M.grip_passage_wall(M.GRIP_RUN_WALL)}
        man = json.loads(read_text(OUT / 'manifest.json'))
        cls.pair = cq.importers.importStep(str(OUT / 'step' / 'xt30_pair.step')).val()
        cls.pack = cq.importers.importStep(str(OUT / 'step' / 'pack.step')).val()
        cls.man = man

    def test_box_constant_is_power_geometry_box(self):
        import power_geometry as PG
        b = PG.grip_cuts()[-1].BoundingBox()
        self.assertEqual(tuple(round(v, 6) for v in (b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax)),
                         self.M.GRIP_PASSAGE_BOX)

    def test_blocks_clear_installed_pair(self):
        for k, b in self.blocks.items():
            self.assertGreater(b.Volume(), 1.0, k)
            self.assertLess(b.intersect(self.pair).Volume(), 1e-6, k)
            self.assertGreaterEqual(b.distance(self.pair), 1.0, k)

    def test_blocks_clear_every_service_pose(self):
        """verify_power_service's own pose construction, junction and pack, every rigid service pose."""
        cq, V = self.cq, self.cq.Vector
        snap = json.loads(read_text(CV / 'routing-snapshots/power-yaw21-270-provisional/power-270-yaw21.json'))
        c0, y0, p0 = snap['junction_center'], snap['junction_yaw_deg'], snap['junction_pitch_deg']
        local = self.pair.translate(V(*[-x for x in c0])).rotate((0, 0, 0), (0, 0, 1), -y0).rotate((0, 0, 0), (0, 1, 0), -p0)
        worst = 1e9
        for p in snap['rigid_service_poses']:
            m = p['matrix']
            pitch, yaw = math.degrees(math.atan2(-m[2][0], m[2][2])), math.degrees(math.atan2(m[1][0], m[0][0]))
            j = local.rotate((0, 0, 0), (0, 1, 0), pitch).rotate((0, 0, 0), (0, 0, 1), yaw).translate(V(*p['center']))
            for s in (j, self.pack.translate(V(*p['pack_translation']))):
                sb = s.BoundingBox()
                for b in self.blocks.values():
                    bb = b.BoundingBox()
                    if sb.xmin > bb.xmax + 3 or sb.xmax < bb.xmin - 3 or sb.zmin > bb.zmax + 3 or sb.zmax < bb.zmin - 3:
                        continue
                    self.assertLess(s.intersect(b).Volume(), 1e-6)
                    worst = min(worst, s.distance(b))
        self.assertGreaterEqual(worst, 1.0)

    def test_support_zone_inside_neck_slot_and_off_lips(self):
        zs = self.M.grip_support_zones(self.tongues)
        self.assertEqual([z['id'] for z in zs], ['grip_rear_pocket_passage_band'])
        x0, x1, y0, y1, z0, z1 = zs[0]['box']
        t = next(t for t in self.tongues if t['id'] == 'tongue_r')
        nk, win, pk = t['base_neck_slot'], t['base_window'], t['base_pocket']
        self.assertTrue(nk['y'][0] < y0 < y1 < nk['y'][1])            # lips are |y| > neck slot half width
        self.assertTrue(pk['x'][0] < x0 < x1 <= win['x'][1])
        self.assertTrue(z0 < pk['z'][0] < z1 < pk['z'][1])            # the pocket floor only
        self.assertLess(y1, self.M.GRIP_PASSAGE_WALL['y'][0] + 0.25)  # only the band without the end wall

    def test_zone_needed_and_sufficient(self):
        """r7 overhang rule on the in-memory grip: fails without the declared zone (the y < -4 band of the pocket floor
        has no +X anchor), passes with it and uses only it. The bound report row (print_bridge_direction) is checked
        in BoundEvidence and reproduced without the zone by tests/test_print_checks.py."""
        import print_rules as PR
        L = self.M.L
        LV = PR.LayoutView(L, PARTS={'base_grip': dict(L.PARTS['base_grip'], face_down='+Z')})
        zones = self.M.grip_support_zones(self.tongues)
        bad = overhang(LV, 'base_grip', self.grip, '+Z')
        good = overhang(LV, 'base_grip', self.grip, '+Z', zones)
        self.assertEqual(bad['status'], 'fail')
        self.assertEqual(good['status'], 'pass', good.get('unsupported'))
        self.assertEqual(sorted(good['supports_used']), ['grip_rear_pocket_passage_band'])

    def test_end_wall_present_and_pocket_open(self):
        V = self.cq.Vector
        g = self.grip
        for y in (-3.0, 0.0, 5.0, 8.5):
            self.assertTrue(g.isInside(V(-64.0, y, -5.45)), y)     # wall past the pocket end, at the floor layer
            self.assertTrue(g.isInside(V(-65.4, y, -5.45)), y)     # floor carried to the wall under the pocket
            self.assertFalse(g.isInside(V(-65.4, y, -4.0)), y)     # the pocket itself stays open
        self.assertFalse(g.isInside(V(-65.4, -8.0, -5.45)))       # the fuse / junction band stays open
        self.assertTrue(g.isInside(V(-35.3, 7.5, -5.0)))          # run-drop wall now 1.6 mm (x -35.6..-34.0)
        self.assertTrue(g.isInside(V(-34.2, 7.5, -5.0)))
        self.assertFalse(g.isInside(V(-35.8, 7.5, -5.0)))
        self.assertFalse(g.isInside(V(-35.3, 4.0, -5.0)))         # below y 6.25 the switch drop joins them: no slab
        self.assertEqual(self.M.GRIP_RUN_WALL['y'][0], 6.25)

    def test_sj_counterbore_closed(self):
        V = self.cq.Vector
        g = self.grip
        x, y = self.M.L.J4_LOCK['c']
        for z in (-7.5, -5.0, -3.0):
            self.assertFalse(g.isInside(V(x, y, z)))                # counterbore open
            self.assertFalse(g.isInside(V(x, y - 3.4, z)))
            for xx in (x - 1.9, x, x + 1.9):
                self.assertTrue(g.isInside(V(xx, -26.2, z)), (xx, z))    # was the window (x) / feather (x +- 1.9)
            self.assertTrue(g.isInside(V(x - 1.9, -25.3, z)))             # the old 0.24 mm feather is now wall
        self.assertFalse(g.isInside(V(x, y, -1.0)))                # clearance hole open
        self.assertTrue(g.isInside(V(x, y - 2.5, -1.0)))           # head seat material

    def test_front_bed_chamfer_restored(self):
        V = self.cq.Vector
        x1 = self.M.L.BASE['x'][1]
        for y in (-19.0, 0.0, 19.0, 22.0):
            self.assertFalse(self.grip.isInside(V(x1 - 0.15, y, -0.15)), y)   # inside the 0.6 x 45 deg chamfer
            self.assertTrue(self.grip.isInside(V(x1 - 0.15, y, -0.8)), y)     # face below it
            self.assertTrue(self.grip.isInside(V(x1 - 0.8, y, -0.1)), y)      # top face behind it

    def test_sj_wall_thickness(self):
        V = self.cq.Vector
        x, y = self.M.L.J4_LOCK['c']
        rb = 3.5
        for a in range(200, 341, 10):
            dx, dy = math.cos(math.radians(a)), math.sin(math.radians(a))
            for z in (-7.0, -4.5):
                p = V(x + (rb + 1.15) * dx, y + (rb + 1.15) * dy, z)
                self.assertTrue(self.grip.isInside(p), (a, z))


class BoundEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.msha = sha(OUT / 'manifest.json')
        cls.pc = json.loads(read_text(OUT / 'print-checks.json'))

    def test_print_rows(self):
        self.assertEqual(self.pc['manifest_sha256'], self.msha)
        res = self.pc['results']
        for cat in ('print_overhang', 'print_bridge_direction'):
            rows = {r['part']: r for r in res[cat]}
            for pid in ('lens_collar', 'base_grip'):
                self.assertEqual(rows[pid]['status'], 'pass', (cat, pid, rows[pid].get('error')))
            used = rows['base_grip']['supports_used']
            self.assertEqual(sorted(used), ['grip_rear_pocket_passage_band'], cat)
            self.assertGreater(used['grip_rear_pocket_passage_band'], 0.0)
            self.assertEqual(rows['lens_collar']['supports_used'], {})
        self.assertFalse([s for s in res.get('unclassified_thin_spots', []) if s['part'] in ('base_grip', 'lens_collar')])
        bc = {r['part']: r for r in res['bed_chamfer']}
        self.assertEqual(bc['base_grip']['status'], 'pass', bc['base_grip'].get('error'))

    def test_main_audit_c2_record(self):
        rec = load_full_audit(self, CV, VARIANT)
        self.assertEqual(rec['manifest_sha256'], self.msha)
        rows = rec['checks']
        cl = [r for r in rows if r['category'] == 'clearance']
        self.assertEqual(sorted(r['id'] for r in cl),
                         ['J4 tongue_f in base pocket', 'J4 tongue_f slide path',
                          'J4 tongue_r in base pocket', 'J4 tongue_r slide path'])
        for r in cl:
            self.assertEqual(r['status'], 'pass', r)
            self.assertGreaterEqual(r['min_gap'], r['need'])
        # The original C2 failure contract now covers every category in the full audit.
        self.assertEqual([r['id'] for r in rows if r['status'] == 'fail'], ['pi5/cooler'])   # VN-69 hardware only
        # Preserve all categories previously emitted by --only j7, including its unconditional checks.
        j7_categories = set(J.CATEGORIES) | {'integrity', 'roundtrip', 'source_binding',
                                           'nominal_features', 'step_aperture_probes', 'physical'}
        j7_rows = [r for r in rows if r['category'] in j7_categories]
        self.assertEqual({r['category'] for r in j7_rows}, j7_categories)
        washer = [r for r in j7_rows if r['category'] == 'lens_clamp' and r['id'].startswith('washer_')]
        self.assertEqual(len(washer), 4)
        self.assertTrue(all(r['status'] == 'pass' for r in washer), washer)
        self.assertFalse([r for r in j7_rows if r['status'] == 'fail'])


if __name__ == '__main__':
    unittest.main(verbosity=2)

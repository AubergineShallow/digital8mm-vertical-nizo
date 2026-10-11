# SPDX-License-Identifier: MIT
"""T2 tub fixes (review 2026-10-10: FP-11b / VN-53 tab catch, VN-34 EVF -Z restraint, VN-25 tub print minors).

Run:  run_locked.py -- cad/gs8-d2-v1/candidate-vertical/tests/test_tub_print_t2.py

- Data (no CAD): the print slope is steeper than r7's 45 deg allowance; the +Y tine joint plane and the ceiling over the
  slot sit above every lock-tab position (r7 CAM tab top 82.1, the tab corner's highest point at any roll, plus the
  roll_catch lateral case offset and r7's 0.3 mm window gap); the VN-34 relief covers the r7 receptacle zone's y range
  (moved with the board by EY - 16) and reaches the PCB face plus the PCB's groove clearance.
- Split (CadQuery boxes): the stub keeps the r7 tab_catch_boxes faces below the joint, its tenon's -Y face lies on the
  catch-face plane (datum, no clearance) and the pocket holds the tenon with the stated clearances on the other sides.
- Built tub (CadQuery, both storage lengths, model.build's layout state): the bonded tub is one valid solid; the print
  stock in its -Y-down pose passes r7's print_overhang and the single-direction bridge rule with only the two declared
  J4 wing zones and NO unsupported region; the stub in its -Z-down pose passes both and the bed-chamfer rule; negative
  control: the same tub with the stub left integral (no split) still fails on the +Y catch face (the check sees it).
- EVF (compact): r7 check_evf_restraint, unchanged and in the r7 frame exactly as verify_check_scope runs it, on the
  built tub with the selected export's evf_board and panel: -Z passes with no connector or plug zone near the PCB's
  first contact; negative control: the relief filled back fails -Z on the HDMI receptacle zone.
Nothing here is a measurement; the stub bond is a physical gate (G-V-PRINT tine coupon).
"""
import copy
import json
import math
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
import layout as R7L            # noqa: E402  (r7 layout constants, read-only)

LENGTHS = (158.0, 185.0)
SEL = CV / 'out' / 'compact-kowa_lm6hc'
HDMI_SNAPSHOT = CV / 'routing-snapshots/hdmi-export17-selected-20261009-0704/input.json'   # as verify_check_scope
FX = types.SimpleNamespace(PRINT_OVERHANG=dict(R7L.PRINT_OVERHANG), PARTS={'fx': dict(face_down='-Z')})


def _model():
    import model
    return model


class Data(unittest.TestCase):
    def test_slope_steeper_than_r7_allowance(self):
        M = _model()
        self.assertGreater(M.TUB_PRINT_SLOPE_DEG, R7L.PRINT_OVERHANG['overhang_deg'])

    def test_joint_and_ceiling_clear_every_tab_position(self):
        """The ceiling (bottom = joint plane) is never reached by the lock tab or a screw head at ANY roll angle with
        the roll_catch lateral case offset raising the camera, and keeps r7's window gap at the window angle."""
        M = _model()
        cam, (ly, lz) = R7L.CAM['tab'], R7L.LENS_AXIS
        top = lz + cam['top_r']
        lat = R7L.COLLAR['gauge']['centring_worst_mm'] + R7L.HOOD_TO_TUB_LATERAL   # roll_catch lateral case offset
        corner = math.hypot(cam['top_r'], cam['w'] / 2)                           # tab top corner radius
        head = math.hypot(cam['screw_z'] - lz + cam['head_d'] / 2, cam['w'] / 2 + cam['head_h'])   # head top, outer
        self.assertAlmostEqual(M.TAB_CATCH_SPLIT_Z - top, 1.4, places=6)
        self.assertGreater(M.TAB_CATCH_SPLIT_Z, lz + max(corner, head) + lat)      # highest point at any roll
        a = math.radians(R7L.ROLL_CATCH['window_deg'])
        at_window = cam['top_r'] * math.cos(a) + cam['w'] / 2 * math.sin(a)
        self.assertGreaterEqual(M.TAB_CATCH_SPLIT_Z - (lz + at_window + lat), R7L.ROLL_CATCH['window_gap'])
        self.assertGreater(M.TAB_CATCH_CEILING_TOP, M.TAB_CATCH_SPLIT_Z)

    def test_evf_relief_covers_the_receptacle_zone(self):
        M = _model()
        self.assertEqual(M.EVF_HDMI_RECEPTACLE_Y, (4.0, 17.0))          # r7 checks._evf_board_zones
        import checks as CK
        z = CK._evf_board_zones(R7L)['hdmi receptacle']
        self.assertEqual((z[2], z[3]), M.EVF_HDMI_RECEPTACLE_Y)
        self.assertEqual(R7L.EVF['board_pcb_x'][0], z[1])               # zone ends at the PCB face


class Split(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.M = _model()
        cls.sp = cls.M.tab_catch_split()
        cls.tc = {(b['side'], b['kind']): b for b in cls.M.L.tab_catch_boxes()}

    def bb(self, s):
        b = s.BoundingBox()
        return [b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax]

    def test_stub_is_the_tine_below_the_joint(self):
        wp, fp = self.tc[(1, 'web')], self.tc[(1, 'flange')]
        T = self.M.TAB_CATCH_TENON
        b = self.bb(self.sp['stub'])
        want = [wp['x'][0], wp['x'][1], wp['y'][0], fp['y'][1], wp['z'][0], self.M.TAB_CATCH_SPLIT_Z + T['h']]
        for got, w in zip(b, want):
            self.assertAlmostEqual(got, w, delta=0.02)
        self.assertTrue(self.sp['stub'].isValid())
        self.assertEqual(len(self.sp['stub'].Solids()), 1)

    def test_tenon_datum_and_pocket_clearances(self):
        M, wp = self.M, self.tc[(1, 'web')]
        T, C = M.TAB_CATCH_TENON, M.TAB_CATCH_POCKET_CLEAR
        p = self.bb(self.sp['pocket'])
        self.assertAlmostEqual(p[2], wp['y'][0], places=6)                         # datum: catch-face plane
        self.assertAlmostEqual(p[3], wp['y'][0] + T['t'] + C['y'], places=6)
        self.assertAlmostEqual(p[0], T['x'][0] - C['x'], places=6)
        self.assertAlmostEqual(p[1], T['x'][1] + C['x'], places=6)
        self.assertAlmostEqual(p[5], M.TAB_CATCH_SPLIT_Z + T['h'] + C['z'], places=6)
        self.assertGreater(T['x'][0] - C['x'], wp['x'][0] + 0.5)                   # pocket closed at both x ends
        self.assertLess(T['x'][1] + C['x'], wp['x'][1] - 0.5)
        # pocket +Y wall: web + pad thickness beyond the pocket >= r7 MIN_WALL (1.2)
        self.assertGreaterEqual(round(wp['y'][1] + 1.2 - p[3], 6), R7L.FDM['MIN_WALL'] if 'MIN_WALL' in R7L.FDM else 1.2)


def _tub_parts(length):
    import copy as _c
    M = _model()                     # model puts structural-review/ (j4_trial_geometry) on sys.path
    import j4_trial_geometry as JG
    L = M.L
    with JG.trial_layout(L, lip=2.4, head=2.4):
        L.LENS = 'kowa_lm6hc'
        oldc, olds = _c.deepcopy(L.COLLAR), _c.deepcopy(L.SCREWS)
        try:
            M.collar_setup()
            tub = M.make_tub(length)
            tongues = _c.deepcopy(L.TONGUES)
        finally:
            L.COLLAR, L.SCREWS = oldc, olds
    stock, stub = M.tub_print_parts(tub)
    return tub, stock, stub, tongues


def _posed_manifold(shape, axis, angle):
    import cadquery as cq
    import print_rules as PR
    sh = shape.rotate((0, 0, 0), axis, angle)
    b = sh.BoundingBox()
    move = (-b.xmin, -b.ymin, -b.zmin)
    sh = sh.translate(cq.Vector(*move))
    with tempfile.TemporaryDirectory() as t:
        p = Path(t) / 'part.stl'
        cq.exporters.export(sh, str(p), tolerance=.06, angularTolerance=.15)
        man = PR.manifold_from_stl(p)
    R = [[1, 0, 0], [0, 0, -1], [0, 1, 0]] if axis == (1, 0, 0) and angle == 90 else [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    return man, R, list(move)


class BuiltTub(unittest.TestCase):
    def check_both(self, pid, man, zones, face_down):
        import checks as CK
        import print_rules as PR
        ov = CK.check_print_overhang(FX, pid, man, zones, face_down=face_down)
        bd = PR.check_bridge_direction(FX, pid, man, zones, face_down=face_down)
        return ov, bd

    def test_tub_stock_and_stub_print_without_support(self):
        import print_rules as PR
        for length in LENGTHS:
            with self.subTest(length=length):
                tub, stock, stub, tongues = _tub_parts(length)
                self.assertTrue(tub.isValid() and len(tub.Solids()) == 1)
                man, R, t = _posed_manifold(stock, (1, 0, 0), 90)
                zones = [dict(z, box=PR.map_box(z['box'], R, t)) for z in PR.j4_wing_zones(tongues)]
                ov, bd = self.check_both('fx', man, zones, '-Y')
                print('L %.0f tub stock: overhang %s (%d unsupported), bridge %s (%s failing), longest %.1f mm'
                      % (length, ov['status'], len(ov.get('unsupported') or []), bd['status'],
                         bd.get('failing_region_count'), bd.get('longest_bridge_mm') or 0), flush=True)
                self.assertEqual(ov['unsupported'], [], ov.get('unsupported'))
                self.assertEqual(ov['status'], 'pass')
                self.assertEqual(bd['status'], 'pass', bd.get('failing_regions'))
                self.assertEqual(sorted(ov['supports_used']), sorted(z['id'] for z in zones))
                sm, _, _ = _posed_manifold(stub, (0, 0, 1), 0)
                ov, bd = self.check_both('fx', sm, [], '-Z')
                self.assertEqual((ov['status'], bd['status']), ('pass', 'pass'), (ov.get('unsupported'), bd.get('failing_regions')))
                ch = PR.check_bed_chamfer('tab_catch_insert', sm)
                self.assertEqual(ch['status'], 'pass', ch)

    def test_negative_control_integral_stub_fails(self):
        import print_rules as PR
        tub, stock, stub, tongues = _tub_parts(LENGTHS[0])
        integral = stock.fuse(_model().tab_catch_split()['envelope']).clean()     # the +Y stub left on the tub
        man, R, t = _posed_manifold(integral, (1, 0, 0), 90)
        zones = [dict(z, box=PR.map_box(z['box'], R, t)) for z in PR.j4_wing_zones(tongues)]
        ov, _ = self.check_both('fx', man, zones, '-Y')
        PR.annotate_regions(ov, R, t, 0.2)
        catch = [u for u in ov['unsupported'] if u['bbox_assembly'][2] > 7.5 and u['bbox_assembly'][3] < 9.0]
        print('integral stub control: %s' % [(u['area_mm2'], u['bbox_assembly']) for u in catch], flush=True)
        self.assertEqual(ov['status'], 'fail')
        self.assertTrue(catch and max(u['area_mm2'] for u in catch) > 20.0)


class EvfRestraint(unittest.TestCase):
    def run_check(self, tub):
        import cadquery as cq
        import checks as CK
        import print_rules as PR
        M = _model()
        length = LENGTHS[0]
        man = json.loads(read_text(SEL / 'manifest.json'))
        self.assertEqual(float(man['core_dimensions_mm'][0]), length)
        want = (154.0 - length, M.EY - 16.0, 0.0)
        back = cq.Vector(-want[0], -want[1], -want[2])
        rows = {'tub': dict(shape=tub.translate(back))}
        for n in ('evf_board', 'panel'):
            rows[n] = dict(shape=cq.importers.importStep(str(SEL / 'step' / ('%s.step' % n))).val().translate(back))
        snap = json.loads(read_text(HDMI_SNAPSHOT))
        hb = {c['id']: c for c in snap['connectors']}['p_hdmi_evf']['box']
        keep = dict(getattr(M.L, 'KEEPOUTS', {}) or {})
        keep['ko_hdmi_evf'] = {k: (hb[k][0] - w, hb[k][1] - w) for k, w in zip('xyz', want)}
        R = dict(part='evf_board', arrest=['tub', 'panel'], limit_mm=0.6, max_travel_mm=8.0)
        res = CK.check_evf_restraint(PR.LayoutView(M.L, EVF_RESTRAINT=R, KEEPOUTS=keep), rows)
        return {r['direction']: r for r in res}

    def test_minus_z_on_the_pcb_and_control(self):
        import cadquery as cq
        M = _model()
        tub, stock, stub, tongues = _tub_parts(LENGTHS[0])
        rz = self.run_check(tub)['-Z']
        print('-Z', rz['status'], rz.get('gap_mm'), rz.get('first_contact_by_zone'), flush=True)
        self.assertEqual(rz['status'], 'pass', rz)
        self.assertEqual(rz['arresting'], 'tub')
        self.assertIsNone(rz.get('connector_stop'))
        zones = rz['first_contact_by_zone']
        self.assertIsNone(zones['hdmi receptacle'])
        self.assertAlmostEqual(zones['pcb']['gap_mm'], 0.25, delta=0.02)
        # control: the shelf strip under the receptacle filled back (the pre-T2 shelf edge at f+15.5)
        f = -LENGTHS[0]
        ry0 = M.EVF_HDMI_RECEPTACLE_Y[0] - 16 + M.EY - .5
        ry1 = M.EVF_HDMI_RECEPTACLE_Y[1] - 16 + M.EY + .5
        fill = cq.Solid.makeBox(f + 15.85 - (f + 15.5), ry1 - ry0, 63.75 - 62.9, cq.Vector(f + 15.5, ry0, 62.9))
        rc = self.run_check(tub.fuse(fill).clean())['-Z']
        print('-Z control', rc['status'], rc.get('connector_stop'), flush=True)
        self.assertEqual(rc['status'], 'fail')
        self.assertIn('hdmi receptacle', rc.get('connector_stop') or {})


if __name__ == '__main__':
    unittest.main(verbosity=2)

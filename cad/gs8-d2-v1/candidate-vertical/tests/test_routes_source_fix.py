# SPDX-License-Identifier: MIT
"""Evidence for the two corrected assertions in candidate-vertical/test_routes_source.py (review FP-15).

Run:  run_locked.py -- cad/gs8-d2-v1/candidate-vertical/tests/test_routes_source_fix.py

test_routes_source.py failed 2 of 10 tests on Windows, identically on the unchanged 9ced753 snapshot. Both were
wrong tests, not wrong geometry (FIX-LOG 'D2 FP-15 test_routes_source'):

1. test_full_rigid_connectors_retained asserted p_usb_pi x == [-153, -122] and z == [44.75, 60.25]. Those are
   the Ethernet-row placement that routes.py rejects ("Old Ethernet-row placement is rejected"); the plug now
   follows the official Pi 5 STEP's GPIO-side USB2 landmark (routing-snapshots/.../port-landmarks.json). Only
   the x assertion ever ran (it failed first); the z assertions behind it would fail by 36.5 mm. The corrected
   test binds the box to the landmark (exact x, z centre) and keeps the full 31 x 9.8 x 15.5 allowance.
2. test_frozen_mechanical_geometry_unchanged compared the recomputed rigid service poses with the frozen JSON by
   exact float equality. The JSON was written where libm's sin/cos are correctly rounded (the frozen
   -0.7071067811865475 is the correctly rounded sin(radians(45))); this platform's sin returns the neighbouring
   double; the difference propagates through the pose and core-polyline arithmetic (largest observed absolute
   difference 1.42e-14 mm, 1 ulp at 68 mm; largest relative 8 ulp, 3.6e-15 mm at 3.0 mm). Every other key is still compared exactly; the poses and core points are compared element
   by element within 1e-12 mm (the evidence tolerance elsewhere is 1e-6 mm), with structure, lengths, the z < 5
   point selection, strings and ints exact.
These tests prove each claim and that the corrected comparisons still catch a real change.
"""
from decimal import Decimal, getcontext
from pathlib import Path
import json
import math
import sys
import unittest

CV = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(CV), str(CV.parent)]
from cv_io import read_text  # noqa: E402
import test_routes_source as TRS  # noqa: E402  (the candidate's own test module, for its comparison helper)

LANDMARKS = CV / 'routing-snapshots/hdmi-ck1044-clear-20261009-0524/official-fpc-sources/port-landmarks.json'


def correctly_rounded_sin(x):
    """sin(x) for the double x, rounded once to the nearest double (Taylor series in 60-digit decimal)."""
    getcontext().prec = 60
    X = Decimal(x)
    term, s, n = X, X, 1
    while abs(term) > Decimal(10) ** -55:
        term = -term * X * X / ((2 * n) * (2 * n + 1))
        s += term
        n += 1
    return float(s)


def overlap(a, b):
    return min(a[1], b[1]) - max(a[0], b[0])


class TestUsbPlugPlacement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import routes
        cls.plug = {p['id']: p for p in routes.build()['plugs']}['p_usb_pi']
        cls.lm = json.loads(read_text(LANDMARKS))['objects']

    def test_box_is_the_usb2_landmark(self):
        b, u = self.plug['box'], self.lm['usb2']['bbox_candidate_mm']
        self.assertEqual(b['x'][1], u[0])                                   # mating face on the receptacle face, exact
        self.assertAlmostEqual((b['z'][0] + b['z'][1]) / 2, (u[4] + u[5]) / 2, places=9)
        self.assertTrue(u[2] <= (b['y'][0] + b['y'][1]) / 2 <= u[3])         # centre on the stacked receptacle's height
        self.assertAlmostEqual(b['x'][1] - b['x'][0], 31.0, places=9)       # full exterior allowance kept
        self.assertAlmostEqual(b['z'][1] - b['z'][0], 15.5, places=9)
        self.assertAlmostEqual(b['y'][1] - b['y'][0], 9.8, places=9)
        TRS.assert_usb_plug_on_landmark(self, self.plug, self.lm)          # the corrected test's own helper

    def test_old_constants_are_the_rejected_ethernet_row(self):
        old = dict(x=[-153.0, -122.0], z=[44.75, 60.25])
        eth, usb2 = self.lm['ethernet']['bbox_candidate_mm'], self.lm['usb2']['bbox_candidate_mm']
        self.assertGreater(overlap(old['z'], eth[4:6]), 15.0)               # the old box sits on the Ethernet row
        self.assertLess(overlap(old['z'], usb2[4:6]), 0.0)                  # and misses the USB2 receptacle
        self.assertIn('Ethernet-row placement is rejected', self.plug['note'])
        self.assertAlmostEqual(old['z'][0] - self.plug['box']['z'][0], 36.5, delta=0.01)

    def test_helper_rejects_the_old_box(self):
        bad = dict(self.plug, box=dict(self.plug['box'], x=[-153.0, -122.0], z=[44.75, 60.25]))
        with self.assertRaises(AssertionError):
            TRS.assert_usb_plug_on_landmark(self, bad, self.lm)


class TestFrozenPoseComparison(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import routes
        cls.p = routes.build()['power_geometry']
        ref = cls.p['mechanical_snapshot']
        cls.old = json.loads(read_text(Path(routes.__file__).parent / ref['path']))

    def test_frozen_value_is_correctly_rounded_and_differences_are_libm(self):
        x = math.radians(45)
        cr = correctly_rounded_sin(x)
        self.assertEqual(-cr, self.old['rigid_service_poses'][0]['matrix'][2][0])   # frozen = correctly rounded
        self.assertEqual(-math.sin(x), self.p['rigid_service_poses'][0]['matrix'][2][0])  # recomputed = this libm
        diffs = TRS.float_differences(self.p['rigid_service_poses'], self.old['rigid_service_poses'])
        self.assertTrue(all(d['abs'] <= TRS.TOL_MM for d in diffs), diffs[:3])
        if math.sin(x) == cr:
            self.assertEqual(diffs, [])

    def test_core_points_differ_only_at_libm_level(self):
        diffs = TRS.float_differences(self.p['cores'][1]['local_points'], self.old['cores'][1]['local_points'])
        self.assertTrue(all(d['abs'] <= TRS.TOL_MM for d in diffs), [d for d in diffs if d['abs'] > TRS.TOL_MM][:3])
        self.assertLess(max((d['abs'] for d in diffs), default=0.0), 1e-13)   # observed 1.42e-14 mm (1 ulp at 68 mm)
        for c, oc in zip(self.p['cores'], self.old['cores']):
            sel = lambda pts: [x for x in pts if x[2] < 5]
            self.assertEqual(len(sel(c['local_points'])), len(sel(oc['local_points'])))   # same points selected
            TRS.assert_same_within_tol(self, sel(c['local_points']), sel(oc['local_points']))
        import copy
        bad = copy.deepcopy(self.p['cores'][1]['local_points']); bad[len(bad) // 2][0] += 1e-9
        with self.assertRaises(AssertionError):
            TRS.assert_same_within_tol(self, bad, self.old['cores'][1]['local_points'])

    def test_exact_keys_and_structure(self):
        for key in ['junction_center', 'junction_yaw_deg', 'junction_pitch_deg', 'fuse']:
            self.assertEqual(self.p[key], self.old[key])
        self.assertEqual(len(self.p['rigid_service_poses']), len(self.old['rigid_service_poses']))

    def test_comparison_still_catches_real_changes(self):
        import copy
        for path, delta in ((('matrix', 0, 2), 1e-11), (('fuse_end', 2), 1e-9), (('center', 0), 1e-6)):
            bad = copy.deepcopy(self.p['rigid_service_poses'])
            row = bad[7]
            tgt = row[path[0]]
            for k in path[1:-1]:
                tgt = tgt[k]
            tgt[path[-1]] += delta
            with self.assertRaises(AssertionError):
                TRS.assert_same_within_tol(self, bad, self.old['rigid_service_poses'])
        bad = copy.deepcopy(self.p['rigid_service_poses']); bad[3]['phase'] = 'other'
        with self.assertRaises(AssertionError):
            TRS.assert_same_within_tol(self, bad, self.old['rigid_service_poses'])
        bad = copy.deepcopy(self.p['rigid_service_poses']); bad.pop()
        with self.assertRaises(AssertionError):
            TRS.assert_same_within_tol(self, bad, self.old['rigid_service_poses'])
        TRS.assert_same_within_tol(self, self.p['rigid_service_poses'], self.old['rigid_service_poses'])


if __name__ == '__main__':
    unittest.main()

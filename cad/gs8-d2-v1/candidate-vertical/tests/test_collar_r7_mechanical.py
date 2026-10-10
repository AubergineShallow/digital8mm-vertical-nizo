# SPDX-License-Identifier: MIT
"""r7 test_mechanical_refinements.py on the candidate collar values (review VN-24 / VN-55, fix FP-08).

Run:  run_locked.py -- cad/gs8-d2-v1/candidate-vertical/tests/test_collar_r7_mechanical.py

The r7 test class (../../test_mechanical_refinements.py, read-only, byte-identical to upstream d38468e) runs
unchanged inside the candidate layout context (j7_collar_checks.candidate_layout: model.py's layout edits,
JG.trial_layout, model.collar_setup), so its setUpClass builds the candidate collars for every lens and every test
reads the candidate COLLAR / SCREWS values.

Expected failures (VN-55, CAD fix FP-11d), marked expectedFailure so a fixed collar reports an unexpected success
and the marker must then be removed:
- test_washer_flat_support_with_float_and_margin: the r 3.9 footprint reaches y -30.2, 0.2 past the lug face y -30;
- test_washer_has_free_seat_at_every_float_extreme: at dy +0.2 the 7.0 washer enters the bit-relief wall (y -22.8).
- test_print_stock_is_exactly_three_removable_membranes: r7 printed_collar.prepare_print (fuse + clean) raises
  "print preparation removed finished material" on the candidate Fujinon collar (Kowa passes). The candidate does not
  print through it: model.collar_print_stock keeps the uncleaned union for this reason (its docstring). That path is
  held to the same r7 contract by test_candidate_print_stock_meets_r7_contract below, which must pass.
Every other r7 test must pass on the candidate values. Each test gets deep copies of the class collars (setUp):
prepare_print's clean() leaves the shape it was given unusable for a later union (found 2026-10-11: after it,
model.collar_print_stock rejects the same Fujinon shape; a fresh one gives added 5.44752 = expected, lost 0.0).
"""
import math
import sys
import unittest
from pathlib import Path

CV = Path(__file__).resolve().parents[1]
for _p in (str(CV.parent), str(CV)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import j7_collar_checks as J            # noqa: E402
import test_mechanical_refinements as R7  # noqa: E402  r7 test module (read-only)

LENS = 'kowa_lm6hc'
EXPECTED_FAILURES = ('test_washer_flat_support_with_float_and_margin',
                     'test_washer_has_free_seat_at_every_float_extreme',
                     'test_print_stock_is_exactly_three_removable_membranes')


class CandidateCollarR7Mechanical(R7.MechanicalRefinements):
    """r7 MechanicalRefinements with the candidate layout entered before r7's setUpClass builds the collars."""
    _ctx = None

    @classmethod
    def setUpClass(cls):
        cls._ctx = J.candidate_layout(LENS)
        L = cls._ctx.__enter__()
        assert L.COLLAR['lug']['screw_y'] == -26.3 and L.COLLAR['feet']['LL'] == (18.0, 30.0), L.COLLAR['lug']
        super().setUpClass()
        cls.pristine = dict(cls.collars)

    @classmethod
    def tearDownClass(cls):
        cls._ctx.__exit__(None, None, None)
        super().tearDownClass()

    def setUp(self):
        self.collars = {n: s.copy() for n, s in self.pristine.items()}

    @unittest.expectedFailure
    def test_print_stock_is_exactly_three_removable_membranes(self):
        super().test_print_stock_is_exactly_three_removable_membranes()

    def test_candidate_print_stock_meets_r7_contract(self):
        """The r7 membrane contract on the candidate's own print path (model.collar_print_stock), every lens."""
        import cadquery as cq
        import layout as L
        import model as M
        V = cq.Vector
        for name, sh in self.collars.items():
            ps = M.collar_print_stock(sh)['shape']
            self.assertTrue(ps.isValid(), name)
            self.assertEqual(len(ps.Solids()), 1, name)
            expected = 3 * math.pi * (L.COLLAR['hole_d'] / 2) ** 2 * L.COLLAR['bridge_membrane_t']
            self.assertAlmostEqual(ps.Volume() - sh.Volume(), expected, places=4)
            self.assertLess(sh.cut(ps).Volume(), 0.001)
            clears = [cq.Solid.makeCylinder(L.COLLAR['hole_d'] / 2, 30, V(-10, *L.COLLAR['feet'][k]), V(1, 0, 0))
                      for k in L.COLLAR['bolted']]
            cleared = ps.cut(*clears)
            self.assertLess(cleared.cut(sh).Volume() + sh.cut(cleared).Volume(), 0.001, name)

    @unittest.expectedFailure
    def test_washer_flat_support_with_float_and_margin(self):
        super().test_washer_flat_support_with_float_and_margin()

    @unittest.expectedFailure
    def test_washer_has_free_seat_at_every_float_extreme(self):
        super().test_washer_has_free_seat_at_every_float_extreme()


class ContextIsRestored(unittest.TestCase):
    """The candidate context never leaks: r7 values are back after it (the r7 suite itself stays valid)."""

    def test_restored(self):
        import layout as L
        before = (L.COLLAR['body_r'], L.COLLAR['feet']['LL'], L.COLLAR['lug']['screw_y'],
                  next(s['head_point'] for s in L.SCREWS if s['id'] == 's_c3'))
        with J.candidate_layout(LENS) as C:
            self.assertEqual((C.COLLAR['body_r'], C.COLLAR['feet']['LL'], C.COLLAR['lug']['screw_y']),
                             (25.0, (18.0, 30.0), -26.3))
        after = (L.COLLAR['body_r'], L.COLLAR['feet']['LL'], L.COLLAR['lug']['screw_y'],
                 next(s['head_point'] for s in L.SCREWS if s['id'] == 's_c3'))
        self.assertEqual(before, after)
        self.assertEqual(after[:3], (30.0, (28.0, 36.0), -31.0))

    def test_expected_failures_are_the_washer_tests_only(self):
        marked = sorted(n for n, f in vars(CandidateCollarR7Mechanical).items()
                        if getattr(f, '__unittest_expecting_failure__', False))
        self.assertEqual(marked, sorted(EXPECTED_FAILURES))
        r7 = sorted(n for n in dir(R7.MechanicalRefinements) if n.startswith('test_'))
        self.assertTrue(set(EXPECTED_FAILURES) <= set(r7) and len(r7) == 12, r7)


if __name__ == '__main__':
    unittest.main(verbosity=2)

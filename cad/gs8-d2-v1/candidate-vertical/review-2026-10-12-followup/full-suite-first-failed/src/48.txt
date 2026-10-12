# SPDX-License-Identifier: MIT
"""Terminal-entry rule of the static power-wire check (fixup-1 of FP-12 / VN-30). Pure Python.

Run:  run_locked.py -- cad/gs8-d2-v1/candidate-vertical/tests/test_wire_terminal_rules.py

The FP-12 rule let a wire touch its terminal part in one run from each end with no length limit; for
positive_fuse_to_housing both terminals are xt30_pair, so a wire lying inside the XT30 proxy end to end passed.
"""
from pathlib import Path
import json
import math
import sys
import unittest

CV = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CV))
import wire_terminal_rules as WT  # noqa: E402

SNAP = json.loads((CV / 'routing-snapshots/power-csi-clear-20261009-0358/power-270-csi-clear.json').read_text(encoding='utf-8'))


def core(cid):
    c = next(c for c in SNAP['cores'] if c['id'] == cid)
    return dict(c, core_id=cid)


def per(hit_flags, part='xt30_pair'):
    """Pieces in station order (ball, cylinder, ball, ...): flags say which pieces touch `part`."""
    return [(k / 2.0, {part: 9.0} if f else {}, None) for k, f in enumerate(hit_flags)]


class TerminalRule(unittest.TestCase):
    def test_limits_come_from_the_snapshot(self):
        lim = WT.entry_limits(SNAP, core('positive'))
        self.assertEqual(lim['root'][0], core('positive')['unmodeled_root_joint_allowance_mm'])
        self.assertAlmostEqual(lim['fuse'][0], math.dist(SNAP['fuse']['start'], SNAP['fuse']['end']))
        hb = SNAP['junction_housing_original_box']
        self.assertEqual(lim['housing'][0], max(hb[k][1] - hb[k][0] for k in 'xyz'))
        self.assertTrue(all(g for _l, _s, g in lim.values()))

    def test_entries_at_both_ends_pass(self):
        pts = [[0, 0, 0], [10, 0, 0]]
        excl, runs, probs = WT.terminal_runs(per([1, 0, 1]), pts, 'positive_fuse_to_housing', ('xt30_pair', 'xt30_pair'),
                                             WT.entry_limits(SNAP, core('positive')))
        self.assertEqual(probs, [])
        self.assertEqual([r['status'] for r in runs], ['pass', 'pass'])
        self.assertEqual(excl, {(0, 'xt30_pair'), (2, 'xt30_pair')})

    def test_wire_inside_the_part_end_to_end_fails(self):
        pts = [[0, 0, 0], [2, 0, 0]]          # short enough to stay under every length limit
        _e, _r, probs = WT.terminal_runs(per([1, 1, 1]), pts, 'positive_fuse_to_housing', ('xt30_pair', 'xt30_pair'),
                                         WT.entry_limits(SNAP, core('positive')))
        self.assertTrue(any('runs from both ends meet' in p for p in probs), probs)

    def test_entry_longer_than_its_limit_fails(self):
        lim = WT.entry_limits(SNAP, core('negative'))
        n = int(lim['root'][0]) + 3            # a run along the board edge longer than the root allowance
        pts = [[float(i), 0, 0] for i in range(n + 2)]
        flags = [1] * (2 * n + 1) + [0, 0, 0]  # balls and cylinders from the start
        p = [(k / 2.0, {'x1203': 9.0} if f else {}, None) for k, f in enumerate(flags)]
        _e, runs, probs = WT.terminal_runs(p, pts, 'negative_complete', ('x1203', 'xt30_pair'), lim)
        self.assertEqual(runs[0]['status'], 'fail')
        self.assertTrue(any('longer than its declared max entry' in q for q in probs), probs)

    def test_verifier_uses_the_rule(self):
        src = (CV / 'verify_wire_solids.py').read_text(encoding='utf-8')
        self.assertIn('WT.terminal_runs(per,points,core', src)
        self.assertIn("fixture_buried_xt30_wire", src)
        self.assertIn("status='pass' if not hits and not term_probs else 'fail'", src)


if __name__ == '__main__':
    unittest.main(verbosity=2)

# SPDX-License-Identifier: MIT
"""Generated check coverage (VN-21) and r7 gate / BX mapping (VN-50), review fix FP-15.

Run:  run_locked.py -- cad/gs8-d2-v1/candidate-vertical/tests/test_coverage_gates.py

CAD-free. Checks:
- make_coverage_vertical: COVERAGE-VERTICAL.md, the README/REVIEW coverage blocks and CHECKPOINT-STATUS.json
  main_summary/check_coverage are current; the main-audit totals equal the verifier's own summary; every report
  category has a kind and every r7 category a mapping; geometric and bookkeeping rows are counted apart; an
  unclassified category or an unmapped r7 category is reported (negative controls);
- make_gates_vertical: GATES-VERTICAL.md and the README/REVIEW gates blocks are current; every r7 receipt gate and
  every BX item is mapped exactly once with a valid word; r7-withdrawn gates are retired; replaced gates name a
  G-V-* gate that exists in REVIEW.md; each rule fails on a planted violation.
"""
from pathlib import Path
import collections
import copy
import json
import sys
import unittest

CV = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CV))
import make_coverage_vertical as MC  # noqa: E402
import make_gates_vertical as MG  # noqa: E402
import gate_map as GM  # noqa: E402


class TestCoverage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.col, cls.out = MC.outputs()

    def test_outputs_current(self):
        for name, text in self.out.items():
            self.assertEqual((CV / name).read_text(encoding='utf-8'), text, '%s stale: run make_coverage_vertical.py --write' % name)

    def test_main_totals_equal_verifier_summary(self):
        v = json.loads((CV / MC.SEL / 'verification.json').read_text(encoding='utf-8'))
        tot = collections.Counter()
        for n in self.col['reports']['main']['counts'].values():
            tot.update(n)
        self.assertEqual({s: tot.get(s, 0) for s in v['summary']}, v['summary'])
        st = json.loads((CV / 'CHECKPOINT-STATUS.json').read_text(encoding='utf-8'))
        self.assertEqual(st['main_summary'], {s: v['summary'].get(s, 0) for s in ('pass', 'fail', 'info')})

    def test_every_category_classified_and_mapped(self):
        self.assertEqual(self.col['unclassified'], [])
        self.assertEqual(self.col['unmapped'], [])
        self.assertEqual(self.col['stale_map'], [])
        self.assertEqual(self.col['missing'], [])

    def test_kinds_are_separate(self):
        t = MC.tally(self.col['reports'], 'main')
        self.assertGreater(sum(t[MC.BOOK].values()), 0)
        self.assertGreater(sum(t[MC.GEO].values()), 0)
        cats = self.col['reports']['main']['counts']
        self.assertEqual(sum(t[MC.BOOK].values()), sum(sum(cats[c].values()) for c in ('integrity', 'roundtrip', 'source_binding') if c in cats))

    def test_negative_controls(self):
        saved_kind, saved_map = dict(MC.KIND), dict(MC.R7_MAP)
        try:
            del MC.KIND[('main', 'interference')]
            del MC.R7_MAP['sweeps']
            col = MC.collect()
            self.assertIn('main/interference', col['unclassified'])
            self.assertIn('sweeps', col['unmapped'])
            self.assertEqual(MC.main(['--check']), 1)
        finally:
            MC.KIND.clear(); MC.KIND.update(saved_kind)
            MC.R7_MAP.clear(); MC.R7_MAP.update(saved_map)


class TestGates(unittest.TestCase):
    def test_no_problem_and_current(self):
        self.assertEqual(MG.problems(), [])
        for name, text in MG.outputs().items():
            self.assertEqual((CV / name).read_text(encoding='utf-8'), text, '%s stale: run make_gates_vertical.py --write' % name)

    def test_counts_add_up(self):
        n = MG.counts()
        gates = MG.r7_gates()
        self.assertEqual(n['total'], len(gates))
        self.assertEqual(sum(n['by_word'].values()), n['total'])
        self.assertEqual(n['open_r7_still_required'] + n['open_r7_retired'], n['open_r7'])
        self.assertEqual(sum(n['bx_by_word'].values()), n['bx_total'])
        self.assertEqual(n['bx_total'], len(MG.r7_bx()))
        for g in GM.GATES:
            if GM.GATES[g][0] == 'retired' and gates[g].startswith('open'):
                self.assertTrue(any(p in GM.GATES[g][2] for p in ('hood', 'keeper', 'plunger', 'sleeve')), g)

    def test_rules_fail_on_planted_violations(self):
        saved_g, saved_b = copy.deepcopy(GM.GATES), copy.deepcopy(GM.BX)
        try:
            del GM.GATES['G-W1']
            GM.GATES['G-SKIRT-1'] = ('carried', None, 'x')
            GM.GATES['G-PI-1'] = ('replaced', 'main/driver', 'x')
            GM.GATES['G-CAP-1'] = ('kept', None, 'x')
            GM.GATES['G-NOPE'] = ('carried', None, 'x')
            GM.BX['BX-3'] = ('carried', 'G-V-NONE', 'x')
            del GM.BX['BX-17']
            codes = {c for c, _ in MG.problems()}
            self.assertTrue({'gate_unmapped', 'withdrawn_not_retired', 'replaced_without_gate', 'bad_word', 'gate_unknown',
                             'g_v_unknown', 'bx_unmapped'} <= codes, codes)
        finally:
            GM.GATES.clear(); GM.GATES.update(saved_g)
            GM.BX.clear(); GM.BX.update(saved_b)


if __name__ == '__main__':
    unittest.main()

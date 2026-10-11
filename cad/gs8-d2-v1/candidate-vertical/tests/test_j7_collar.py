# SPDX-License-Identifier: MIT
"""J7-R float, roll catch, lens support / clamp, collar gauge and insert checks on the candidate (review VN-24,
fix FP-08). Nothing is written.

Run:  run_locked.py -- cad/gs8-d2-v1/candidate-vertical/tests/test_j7_collar.py

- Registration: verify_candidate.py calls j7_collar_checks.j7_rows once, behind want('j7'); the module's info rows
  are in evidence_rules.MAIN_AUDIT_INFO; the module imports without CadQuery; model.py still grows the catch to 98.0.
- Adapter units (no geometry): centring rows add the location term to the panel only (a split panel#k too) and fail
  below r7 J7_RUNNING; obstacle minima fold id#k to id; 'hood' is renamed back to 'tub'; emit maps stub to fail;
  the lens records come from steps.py (hold only when the op text names the tab catch); r7 lens_turn_back_lint
  passes on the candidate steps and fails when the turn-back sentence moves after "snug s_c4".
- Geometry (manifest-bound STEPs of compact-kowa_lm6hc): a lateral bump 0.3 from the camera housing fails the body
  row with per-obstacle gaps (min_lateral 0.3 to the bump); a panel#9 bump at 0.6 passes r7's 0.5 rule but fails the
  centring row with the panel location term (0.6 - 0.30 - 0.25 = 0.05 < 0.1); the catch boxes are tub material and a
  hole cut in a tine is found; the tine root is the roof underside; a part 0.3 from the seated gauge fails the gauge
  row; the washer rows pass on the candidate collar with r7's margins (lug face 0.1, relief 0.5, free-seat gap 0.3
  at the 0.2 float; since C2 / FP-11d; on the 9ced753 collar they failed: lug face -0.2, relief 0.0, 0.1564 mm3 at
  dy +0.2) and pass on the r7 collar with the same values.
- Record (review-2026-10-10/fp08): made by the current j7_collar_checks.py for the current manifest; every category
  present; body / bfar rows carry per-obstacle gaps; the failing rows are exactly EXPECTED_FAILURES (empty since C2:
  the four FP-11d washer rows were its only entries).
"""
import ast
import copy
import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

CV = Path(__file__).resolve().parents[1]
for _p in (str(CV.parent), str(CV)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
from cv_io import read_text              # noqa: E402
import j7_collar_checks as J             # noqa: E402
import steps as ST                       # noqa: E402

VARIANT = 'compact-kowa_lm6hc'
OUT = CV / 'out' / VARIANT
RECORD = CV / 'review-2026-10-10' / 'fp08' / ('j7-%s.json' % VARIANT)
# CAD-phase failures on the reviewed geometry (filled from the first full record; each names its fix step).
# C2 (FP-11d) removed the four VN-55 washer rows (washer_flat_support / washer_free_seat, Kowa and Fujinon): they
# pass on the fixed collar, so the set is empty and any failing FP-08 row now fails test_record.
EXPECTED_FAILURES = {}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


class Registration(unittest.TestCase):
    def test_verify_candidate_line(self):
        lines = [ln for ln in read_text(CV / 'verify_candidate.py').splitlines() if 'j7_collar_checks' in ln]
        self.assertEqual(len(lines), 1, lines)
        self.assertIn("want('j7')", lines[0])
        self.assertIn('j7_rows(shapes,rows,meta,a.variant)', lines[0].replace(' ', ''))

    def test_info_rows_registered(self):
        import evidence_rules as EVR
        exp = EVR.expected_main_info()
        self.assertTrue(J.INFO_ROWS <= exp, sorted(J.INFO_ROWS - exp))
        self.assertFalse(J.INFO_ROWS & EVR.MAIN_AUDIT_INFO)   # static set = the committed verification.json (FP-16)
        self.assertTrue(all(c in J.CATEGORIES for c, _ in J.INFO_ROWS))

    def test_cad_free_import(self):
        code = ('import sys; sys.path[:0]=[%r,%r]; import j7_collar_checks, evidence_rules; '
                'evidence_rules.expected_main_info(); print("cadquery" in sys.modules)') % (str(CV.parent), str(CV))
        out = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, encoding='utf-8',
                             timeout=120)
        self.assertEqual(out.stdout.strip(), 'False', out.stderr)

    def test_catch_source_pin(self):
        src = read_text(CV / 'model.py').replace(' ', '')
        self.assertIn(J.CATCH_SOURCE.replace(' ', ''), src)
        self.assertIn("L.COLLAR['lug'].update(y_out=COLLAR_LUG_Y_OUT,screw_y=COLLAR_SCREW_Y,"
                      "bit_relief_y=COLLAR_BIT_RELIEF_Y)", src)
        self.assertIn('COLLAR_LUG_Y_OUT=-30.8', src)       # C2 / FP-11d (was the literal y_out -30.0)
        self.assertIn('COLLAR_SCREW_Y=-26.8', src)         # C2 / FP-11d (was the literal screw_y -26.3)
        self.assertIn('COLLAR_BIT_RELIEF_Y=-22.8', src)    # unchanged relief (body wall 1.83 analytic)


class _CK:
    J7_RUNNING, J7_TOL = 0.1, 1e-3

    @staticmethod
    def _r(x, n=3):
        return None if x is None else round(float(x), n)


class AdapterUnits(unittest.TestCase):
    L = type('L', (), dict(COLLAR=dict(gauge=dict(centring_worst_mm=0.30, stack_without_gauge=dict(worst_mm=0.60))),
                           HOOD_TO_TUB_LATERAL=0.25))

    def _out(self):
        g = lambda lat: dict(overall=lat, lateral=lat, axial=None, overlap_mm3=0.0)    # noqa: E731
        return [dict(mover='body', s=0.0, status='pass', per_obstacle={'tub': g(0.6), 'panel#9': g(0.6)}),
                dict(mover='body', s=3.0, status='fail', offending_obstacles=['pi5#3'],
                     per_obstacle={'tub': g(0.7), 'pi5#3': g(0.2), 'pi5#4': g(0.9)})]

    def test_centring_location_term(self):
        rows = {(r['of'], r['obstacle']): r for r in J.centring_rows(self.L, self._out(), _CK)}
        self.assertEqual(rows[('body', 'tub')]['remaining_mm'], 0.3)
        self.assertEqual(rows[('body', 'tub')]['status'], 'pass')
        self.assertIsNone(rows[('body', 'tub')]['location_extra_mm'])
        p = rows[('body', 'panel#9')]
        self.assertEqual((p['location_extra_mm'], p['remaining_mm'], p['status']), (0.25, 0.05, 'fail'))
        self.assertEqual(rows[('body', 'pi5#3')]['status'], 'fail')

    def test_obstacle_minima_fold(self):
        m = J.obstacle_minima(self._out())
        self.assertEqual(m['status'], 'fail')
        self.assertEqual(sorted(m['per_obstacle']), ['panel', 'pi5', 'tub'])
        self.assertEqual(m['per_obstacle']['pi5']['lateral'], dict(gap=0.2, mover='body', s=3.0, solid='pi5#3'))
        self.assertEqual(m['per_obstacle']['tub']['lateral']['gap'], 0.6)
        self.assertEqual(m['offending_obstacles'], ['pi5'])

    def test_unalias_and_emit(self):
        r = J._unalias(dict(metal_to=['hood'], gaps={'hood': 1}, error='metal meets hood at 1 deg', note='hoods'))
        self.assertEqual(r, dict(metal_to=['tub'], gaps={'tub': 1}, error='metal meets tub at 1 deg', note='hoods'))
        e = J.emit('j7_float', 'x', dict(status='stub', kind='j7_float', s=(1, 2)))
        self.assertEqual((e['ok'], e['r7_status'], e['s'], 'status' in e), (False, 'stub', [1, 2], False))
        self.assertIsNone(J.emit('j7_float', 'x', dict(status='info'))['ok'])

    def test_lens_records_from_steps(self):
        steps, last, ins, rem = J.lens_records(None, ST)
        self.assertEqual([(r['id'], r['hold']) for r in ins], [('lens_in', 'hood_tab_catch')])
        self.assertEqual([(r['id'], r['hold'], r['off']) for r in rem], [('svc_lens_out', 'hood_tab_catch',
                                                                          ['cap', 'pack'])])
        self.assertEqual(last[ins[0]['step']], ST.STEPS[[o['step'] for o in ST.STEPS].index('3') - 1]['id'])
        fake = type('ST', (), {k: getattr(ST, k) for k in ('SERVICE', 'service_sequence', 'final_state')})
        fake.STEPS = copy.deepcopy(ST.STEPS)
        o = next(o for o in fake.STEPS if o['id'] == 'lens_in')
        o['doc'] = o['doc'].replace('tab catch', 'housing')
        self.assertEqual([r['hold'] for r in J.lens_records(None, fake)[2]], [None])

    def test_turn_back_lint(self):
        import checks as CK
        import layout as L
        steps, last, ins, rem = J.lens_records(L, ST)
        view = J.LayoutView(L, STEPS=steps, INSERTIONS=ins)
        self.assertEqual(CK.lens_turn_back_lint(view), [])
        bad = copy.deepcopy(steps)
        st = next(s for s in bad if s['step'] == ins[0]['step'])
        st['action'] = st['action'].replace(L.LENS_TURN_BACK, 'x') + ' ' + L.LENS_TURN_BACK
        self.assertTrue(CK.lens_turn_back_lint(J.LayoutView(L, STEPS=bad, INSERTIONS=ins)))


GEOM_IDS = ('tub', 'panel', 'lens_collar', 'c_cs_adapter', 'lens', 'gs_camera', 'carrier', 'base_grip',
            's_c1', 's_c2', 's_c3', 's_c4')


class Geometry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import cadquery as cq
        import checks as CK
        cls.cq, cls.CK = cq, CK
        cls.meta = json.loads(read_text(OUT / 'manifest.json'))
        rows = {r['id']: r for r in cls.meta['rows']}
        cls.shapes = {}
        for k in GEOM_IDS + ('centring_gauge',):
            rel = 'step/%s.step' % k
            assert sha(OUT / rel) == cls.meta['files'][rel], rel
            cls.shapes[k] = cq.importers.importStep(str(OUT / rel)).val()
        cls.rows = {k: rows[k] for k in GEOM_IDS}
        cls.rr = J.r7_rows(cls.shapes, cls.rows)

    def box(self, x0, x1, y0, y1, z0, z1):
        return self.cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, self.cq.Vector(x0, y0, z0))

    def test_planted_lateral_bumps(self):
        with J.candidate_layout('kowa_lm6hc') as L:
            ly, lz = L.LENS_AXIS
            r = L.CAM['housing']['d'] / 2
            rr = dict(self.rr, planted=dict(shape=self.box(-12, -9, ly - r - 0.8, ly - r - 0.3, lz - 1, lz + 1)),
                      **{'panel#9': dict(shape=self.box(-12, -9, ly + r + 0.6, ly + r + 1.1, lz - 1, lz + 1))})
            out = {i: x for _, i, x in J.j7_float_rows(L, rr, self.CK, s_values=(L.CAM['s_nom'],))}
        body = out['body@s%.2f' % L.CAM['s_nom']]
        self.assertEqual(body['status'], 'fail')
        self.assertEqual(body['min_lateral'], dict(gap=0.3, to='planted'))
        self.assertIn('planted', body['offending_obstacles'])
        self.assertNotIn('panel#9', body['offending_obstacles'])
        self.assertEqual(body['per_obstacle']['panel#9']['lateral'], 0.6)
        self.assertTrue({'tub', 'lens_collar'} <= set(body['per_obstacle']))
        mn = out['obstacle_minima']
        self.assertEqual((mn['status'], mn['per_obstacle']['planted']['lateral']['gap']), ('fail', 0.3))
        self.assertIn('panel', mn['per_obstacle'])
        c = out['centring:body/panel#9']
        self.assertEqual((c['status'], c['location_extra_mm'], c['remaining_mm']), ('fail', 0.25, 0.05))
        self.assertEqual(out['centring:body/planted']['status'], 'fail')

    def test_catch_material_and_root(self):
        tub = self.shapes['tub']
        with J.candidate_layout('kowa_lm6hc') as L:
            boxes, hood = J.candidate_catch_boxes(L)
            self.assertEqual({b['z'][1] for b in boxes}, {J.CATCH_TOP_Z})
            self.assertEqual(J.catch_material(L, tub, boxes), [])
            w = next(b for b in boxes if b['kind'] == 'web')
            c = [sum(w[a]) / 2 for a in 'xyz']
            holed = tub.cut(self.box(c[0] - 0.5, c[0] + 0.5, c[1] - 0.5, c[1] + 0.5, c[2] - 0.5, c[2] + 0.5))
            self.assertTrue(J.catch_material(L, holed, boxes))
            root, slot = J.tine_root(J.LayoutView(L, HOOD=hood), tub, self.CK)
        self.assertAlmostEqual(root, 97.5, places=3)
        self.assertLess(slot, root)

    def test_gauge_other_present(self):
        g = self.shapes['centring_gauge']
        b = g.BoundingBox()
        with J.candidate_layout('kowa_lm6hc') as L:
            rr = dict(self.rr, strap=dict(shape=self.box(b.xmin, b.xmax, b.ymax + 0.3, b.ymax + 1.3, 59, 61)))
            out = {i: x for _, i, x in J.gauge_rows(L, rr, g, self.CK, ST)}
        o = out['centring_gauge/other_present']
        self.assertEqual(o['status'], 'fail')
        self.assertEqual(o['offending_obstacles'], ['strap'])
        self.assertAlmostEqual(o['gaps']['strap']['gap'], 0.3, places=3)
        self.assertGreaterEqual(o['gaps']['base_grip']['gap'], 0.5)
        self.assertEqual(out['centring_gauge/tub']['status'], 'pass')

    def test_washer_rows(self):
        import layout as L7
        import printed_collar as PC
        with J.candidate_layout('kowa_lm6hc') as L:
            cand = {i: x for _, i, x in J.washer_rows(L, {'kowa_lm6hc': self.shapes['lens_collar']}, self.CK)}
        fs, fr = cand['washer_flat_support/kowa_lm6hc'], cand['washer_free_seat/kowa_lm6hc']
        # C2 / FP-11d: the bound collar now has r7's margins (it failed with -0.2 / 0.0 and 0.1564 mm3 at dy +0.2)
        self.assertEqual((fs['status'], fr['status']), ('pass', 'pass'))
        self.assertEqual(fs['nominal_margins'], dict(lug_face_mm=0.1, bit_relief_mm=0.5))
        self.assertEqual(fs['unsupported_mm3'], 0.0)
        self.assertEqual([c for c in fr['cases'] if c['overlap_mm3'] >= 0.001], [])
        self.assertAlmostEqual(fr['min_gap_mm'], 0.3, places=3)
        r7c = PC.build_part(L7, 'lens_collar', lens='kowa_lm6hc').val()
        r7 = {i: x for _, i, x in J.washer_rows(L7, {'kowa_lm6hc': r7c}, self.CK)}
        self.assertEqual(r7['washer_flat_support/kowa_lm6hc']['status'], 'pass')
        self.assertEqual(r7['washer_free_seat/kowa_lm6hc']['status'], 'pass')
        self.assertAlmostEqual(r7['washer_free_seat/kowa_lm6hc']['min_gap_mm'], 0.3, places=3)


class Record(unittest.TestCase):
    def test_record(self):
        rec = json.loads(read_text(RECORD))
        self.assertEqual(rec['manifest_sha256'], sha(OUT / 'manifest.json'))
        self.assertEqual(rec['scope'], 'j7')
        rows = [c for c in rec['checks'] if c.get('port') == 'FP-08']
        ctx = next(c for c in rows if c['id'] == 'camera_model_match')
        self.assertEqual(ctx['j7_collar_checks_sha256'], J.source_sha256())
        self.assertEqual(ctx['steps_sha256'], sha(CV / 'steps.py'))
        self.assertEqual({c['category'] for c in rows}, set(J.CATEGORIES))
        ids = {(c['category'], c['id']) for c in rows}
        self.assertEqual(len(ids), len(rows))
        svals = (0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0)
        for m in ('body', 'bfar'):
            for s in svals:
                r = next(c for c in rows if c['id'] == '%s@s%.2f' % (m, s))
                self.assertTrue(r['per_obstacle'] and r['min_lateral'] and r['min_axial'], r['id'])
        self.assertTrue(J.INFO_ROWS <= {(c['category'], c['id']) for c in rows if c['status'] == 'info'})
        self.assertFalse([c for c in rows if c['id'].startswith('section_error')])
        for i in ('kowa_lm6hc/collar_context_match', 'fujinon_hf6xa/collar_context_match'):
            r = next(c for c in rows if c['id'] == i)
            self.assertEqual((r['status'], r['symmetric_difference_mm3']), ('pass', 0.0), i)
        fails = {(c['category'], c['id']) for c in rows if c['status'] == 'fail'}
        self.assertEqual(fails, set(EXPECTED_FAILURES), sorted(fails ^ set(EXPECTED_FAILURES)))


if __name__ == '__main__':
    unittest.main(verbosity=2)

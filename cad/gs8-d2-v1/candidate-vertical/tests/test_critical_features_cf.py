# SPDX-License-Identifier: MIT
"""Critical-feature re-nomination of the candidate (review VN-21 / VN-25, phase-2 lane CF).

Run:  run_locked.py -- cad/gs8-d2-v1/candidate-vertical/tests/test_critical_features_cf.py

- Accounting (no STEP): every r7 CRITICAL_FEATURES id is kept, re-nominated or retired exactly once; every r7
  exception and joint is accounted for; retired probes carry a reason and name only existing candidate entries.
- Limits: a kept or re-nominated id keeps r7's min_mm, structural flag and graded minimum (class floor); an added
  entry never asks for less than its r7 analog or its class floor. r7's REQUIRED_JOINT_IDS is untouched.
- Joints: fork joints require the union of their own ids and the superseded r7 ids minus RETIRE (r7 fork rule).
- Bound report: print-checks.json binds this module; every probe measures its design value (DESIGN, from model.py
  numbers) or, for a kept id, r7's own measured value; the thin-spot gate passes; the kit-boss rim exception
  quotes a value that a fresh chord reproduces; the r7 origins of re-nominated probes are stale on the candidate.
- carrier_tie_bar_3 was cut to 0.877 mm at the bed face by the FP-11c power-nut relief (slot (-34, 25)); FX moved the
  slot to (-35, 25) and the bar passes (its expected-failure mark is removed). FX also retired the kit-boss lead-in rim
  exception with its geometry and added the tub print-stock tenon-pocket walls (print_rules.TUB_STOCK).
"""
import json
import sys
import unittest
from pathlib import Path

CV = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CV))
from cv_io import read_text   # noqa: E402
import print_rules as PR      # noqa: E402
import critical_features_vertical as CFV   # noqa: E402

CK = PR.CK
import layout as R7L          # noqa: E402  r7 layout (registries are import-time constants; model does not edit them)
VARIANT = 'compact-kowa_lm6hc'
OUT = CV / 'out' / VARIANT
J4_TRIAL_IDS = {'tub_tongue_%s_wing_%s' % (t, s) for t in 'fr' for s in 'lr'} | \
               {'base_keyhole_lip_%s_%s' % (t, s) for t in 'fr' for s in 'lr'}
# design values (mm) from the model numbers named in critical_features_vertical.py; long chords pinned as measured
DESIGN = {
    'tub_front_wall_seat': 2.5, 'tub_j4_lock_boss': 2.75, 'tub_insert_boss_ll': 2.0,
    'tub_evf_groove_wall_bot_px': 1.3, 'tub_evf_groove_wall_top_mx': 1.3, 'tub_evf_groove_wall_top_px': 1.3,
    'tub_evf_groove_floor_bot': 2.25, 'tub_evf_groove_roof_top': 1.25, 'tub_evf_groove_end_bot': 23.7,
    'tub_evf_groove_end_top': 24.7, 'tub_evf_collar_radial': 24.35, 'tub_evf_collar_axial': 4.4,  # FX: groove_end_top 31.3 -> 24.7 (the z 92 cold row is now a windowed beam; the chord no longer runs on through it)
    'panel_wall': 2.8, 'panel_evf_clamp_prong': 3.233, 'panel_evf_stop': 2.6,
    'panel_encoder_hook_side_l': 1.6, 'panel_encoder_hook_side_r': 1.6, 'panel_encoder_hook_top': 1.6,
    'panel_encoder_hook_tooth_top': 1.62, 'panel_encoder_hook_tooth_left': 1.62, 'panel_encoder_hook_tooth_right': 1.62,
    'collar_foot_ll': 2.1, 'collar_lug_upper': 2.3, 'collar_lug_lower': 2.0, 'collar_wall_min': 2.434,
    'base_strap_bridge': 4.0, 'base_strap_web': 4.0, 'base_sj_head_floor': 2.0,
    'grip_strap_bar': 3.5, 'grip_heel_slot_end': 3.5,
    'tub_roof_plate': 2.5, 'tub_wall_minus_y': 2.5, 'tub_wall_rear': 2.5,
    **{'panel_boss_p%d_head_floor' % i: 2.1 for i in range(1, 5)}, **{'tub_panel_boss_p%d' % i: 3.25 for i in range(1, 5)},
    'tub_panel_landing_rear': 5.188,
    **{'carrier_kit_boss_%s_head_floor' % k: 3.0 for k in 'abcd'},
    'carrier_ear_c1_head_floor': 2.6, 'carrier_ear_c2_head_floor': 2.6, 'tub_carrier_boss_c1': 3.55,
    'tub_carrier_boss_c2': 3.55, 'carrier_arm': 8.0, 'carrier_tie_bar_1': 2.6, 'carrier_tie_bar_2': 4.361,
    'carrier_tie_bar_3': 1.877, 'carrier_tie_bar_4': 3.1, 'carrier_locator_tongue': 5.0, 'tub_locator_seat': 2.425,
    'tub_stock_tenon_pocket_wall_xm': 1.5, 'tub_stock_tenon_pocket_wall_xp': 1.5,
    'panel_locator_stop': 5.65, 'tub_foot_recess_tl': 5.2, 'tub_foot_recess_tr': 5.2, 'tub_foot_recess_ll': 5.591,
    'tub_foot_recess_lr': 2.289, 'tub_tab_catch_n': 10.621, 'insert_tab_catch_p': 2.85, 'insert_tab_catch_tenon': 1.6,
    'tub_evf_floor_relief': 1.4, 'tub_evf_collar_ring_end': 2.359,
}
REAL_DEFECTS = set()     # FX: carrier_tie_bar_3 fixed (slot moved to x -35); none left


def _sha(p):
    import hashlib
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _state():
    return PR.candidate_state(json.loads(read_text(OUT / 'manifest.json')))


class Accounting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.st = _state()
        cls.v = cls.st['layout']
        cls.r7 = {f['id']: f for f in CK.registry(R7L, 'CRITICAL_FEATURES')}
        cls.cand = {f['id']: f for f in CK.registry(cls.v, 'CRITICAL_FEATURES')}
        cls.ren = set(cls.st['cf_registry']['renominate'])

    def test_partition(self):
        groups = [set(CFV.KEEP), self.ren, set(CFV.RETIRE)]
        self.assertEqual(sum(len(g) for g in groups), len(self.r7))
        self.assertEqual(set().union(*groups), set(self.r7))
        self.assertEqual(CK.duplicate_ids(self.v), {})
        self.assertFalse(set(CFV.RETIRE) & set(self.cand))
        self.assertEqual(set(self.cand), (set(self.r7) - set(CFV.RETIRE)) | set(self.st['cf_registry']['added']))

    def test_limits_never_lower(self):
        for fid, e in self.cand.items():
            cls_c, need_c, err = CK.feature_class(self.v, e)
            self.assertIsNone(err, fid)
            if fid in self.r7:
                r = self.r7[fid]
                self.assertEqual((e.get('min_mm'), e.get('structural', True)), (r.get('min_mm'), r.get('structural', True)), fid)
                self.assertEqual((cls_c, need_c), CK.feature_class(R7L, r)[:2], fid)
            else:
                an = self.r7[e['analog']]
                self.assertGreaterEqual(need_c, CK.feature_class(R7L, an)[1] - 1e-9, fid)
                self.assertGreaterEqual(need_c, R7L.FEATURE_CLASS_MIN[e['cls']], fid)

    def test_retire_reasons_and_successors(self):
        for fid, (why, succ) in CFV.RETIRE.items():
            self.assertGreater(len(why), 20, fid)
            for s in succ:
                self.assertIn(s, self.cand, (fid, s))
        for fid, why in CFV.KEEP.items():
            self.assertGreater(len(why), 10, fid)
        for fid, r in self.st['cf_registry']['renominate'].items():   # a new origin, or a new section direction
            moved = r['origin'] != r['r7_origin']
            turned = tuple(self.cand[fid]['direction']) != tuple(self.r7[fid]['direction'])
            self.assertTrue(moved or turned, fid)
            self.assertTrue(r['why'], fid)

    def test_joints(self):
        r7j = {j['id']: j for j in CK.registry(R7L, 'CRITICAL_JOINTS')}
        cj = {j['id']: j for j in CK.registry(self.v, 'CRITICAL_JOINTS')}
        self.assertEqual(tuple(self.v.REQUIRED_JOINT_IDS), tuple(R7L.REQUIRED_JOINT_IDS))
        sup = {s: fj['id'] for fj in CFV.FORK_JOINTS for s in fj['supersedes']}
        gone = set(CFV.RETIRE)
        for jid, j in r7j.items():
            if jid in sup:
                fj = cj[sup[jid]]
                self.assertIn(jid, fj['replaces'])
                self.assertFalse([i for i in j['required'] if i not in gone and i not in fj['required']], jid)
            else:
                add = CFV.JOINT_ADDITIONS.get(jid, {}).get('required', [])
                self.assertEqual(cj[jid]['required'], [i for i in j['required'] if i not in gone] + add, jid)
        for j in cj.values():
            for fid in j['required']:
                self.assertIn(fid, self.cand, (j['id'], fid))
        lb = [p for p in self.v.LOAD_BEARING_PARTS if p in self.v.PARTS]
        self.assertEqual(sorted(set(lb)), sorted({'tub', 'panel', 'base_grip', 'cap', 'lens_collar', 'carrier',
                                                  'tab_catch_insert'}))
        for p in lb:
            self.assertTrue(any(p in j['parts'] for j in cj.values()), p)

    def test_exceptions_and_tie_slots(self):
        import harness_rules as HR
        self.assertEqual({e['id'] for e in CK.registry(R7L, 'NONSTRUCTURAL_EXCEPTIONS')},
                         set(CFV.EXCEPTION_RETIRE) | set(CFV.EXCEPTION_RENOMINATE))
        self.assertFalse(set(CFV.EXCEPTION_RETIRE) & set(CFV.EXCEPTION_RENOMINATE))
        self.assertEqual([e['id'] for e in self.v.NONSTRUCTURAL_EXCEPTIONS], ['exposure_label_glyph_ridge'])
        self.assertIn('kit_boss_lead_in_rim', CFV.RETIRED_EXCEPTIONS)      # FX: retired with the lead-in
        for e in self.v.NONSTRUCTURAL_EXCEPTIONS:
            self.assertGreater(len(e['why']), 40, e['id'])
        self.assertEqual([tuple(p) for p in HR.TIE_SLOTS_XZ], list(CFV.CARRIER_TIE_SLOTS))
        self.assertEqual(HR.TIE_SLOT_HALF[0], CFV.CARRIER_TIE_SLOT_HALF_X)
        self.assertEqual(self.v.EXPECT_OUTSIDE, {})


class BoundReport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rep = json.loads(read_text(OUT / 'print-checks.json'))
        cls.rows = {r['id']: r for r in cls.rep['results']['critical_features'] if r.get('kind') == 'feature'}
        cls.joints = {r['id']: r for r in cls.rep['results']['critical_features'] if r.get('kind') == 'joint'}
        cls.r7meas = {r['id']: r for r in json.loads(read_text(PR.ROOT / 'out' / 'checks.json'))['results']
                      ['critical_features'] if r.get('kind') == 'feature'}

    def test_bound(self):
        self.assertEqual(self.rep['manifest_sha256'], _sha(OUT / 'manifest.json'))
        self.assertEqual(self.rep['check_sources']['candidate-vertical/critical_features_vertical.py'],
                         _sha(CV / 'critical_features_vertical.py'))
        self.assertEqual(json.loads(json.dumps(_state()['cf_registry'])), self.rep['critical_feature_registry'])

    def test_design_values(self):
        for fid, mm in DESIGN.items():
            self.assertAlmostEqual(self.rows[fid]['measured_mm'], mm, delta=0.011, msg=fid)
        for fid in CFV.KEEP:
            want = 2.4 if fid in J4_TRIAL_IDS else self.r7meas[fid]['measured_mm']
            self.assertAlmostEqual(self.rows[fid]['measured_mm'], want, delta=0.011, msg=fid)

    def test_rows_pass(self):
        bad = {k: r.get('error') or r['measured_mm'] for k, r in self.rows.items()
               if r['status'] not in ('pass', 'info') and k not in REAL_DEFECTS}
        self.assertEqual(bad, {})
        info = sorted(k for k, r in self.rows.items() if r['status'] == 'info')
        self.assertEqual(info, ['grip_cap_detent_arm', 'grip_cap_detent_dimple_wall', 'grip_cap_groove_corner'])
        for k in REAL_DEFECTS:
            self.assertEqual(self.rows[k]['status'], 'fail', k)
        jbad = {k: r.get('error') for k, r in self.joints.items()
                if r['status'] not in ('pass', 'info')}
        self.assertEqual(jbad, {})
        cov = [r for r in self.rep['results']['critical_features'] if r.get('kind') == 'coverage']
        self.assertFalse([r['part'] for r in cov if r['status'] == 'fail'])

    def test_thin_spot_gate(self):
        res = self.rep['results']
        self.assertEqual(res['unclassified_thin_spots'], [])
        gate = [r for r in res['critical_features'] if r.get('id') == 'thin_spot_classification'][0]
        self.assertEqual(gate['status'], 'pass')
        # each candidate exception quotes a value the bound report or a design number gives
        exc = {r['id']: r for r in res['critical_features'] if r.get('kind') == 'exception'}
        lbl = exc['exposure_label_glyph_ridge']
        panel = [r for r in res['thin_wall'] if r['part'] == 'panel'][0]
        hit = [s for s in panel.get('below_min_wall', []) if [round(v, 2) for v in s['at']] == list(lbl['at'])]
        # FX: the quoted value is a fresh chord along z on the bound panel (the sampler found no sample on this export);
        # a sampler hit at the point, when present, must be thin too
        import cadquery as cq
        t = CK.chord(cq.importers.importStep(str(OUT / 'step/panel.step')).val(), tuple(lbl['at']), (0, 0, 1))[0]
        self.assertAlmostEqual(t, lbl['measured_mm'], delta=0.011)
        self.assertTrue(all(s['t'] < 1.2 for s in hit), hit)

    def test_carrier_tie_bar_3_passes(self):
        self.assertEqual(self.rows['carrier_tie_bar_3']['status'], 'pass')

    def test_fresh_chords(self):
        import cadquery as cq
        shp = {p: cq.importers.importStep(str(OUT / 'step' / ('%s.step' % p))).val() for p in ('carrier', 'panel')}
        t = CK.chord(shp['carrier'], (-99.2, 22.15, 59.5), (1, 0, 0))[0]          # FX: kit-boss rim, no lead-in
        self.assertGreaterEqual(t, 1.2)                                              # was 0.6 (retired exception)
        self.assertEqual([e['id'] for e in CFV.exceptions(CK, R7L, PR_model())], ['exposure_label_glyph_ridge'])
        st = _state()['cf_registry']['renominate']
        for fid in ('panel_wall', 'panel_evf_stop', 'panel_encoder_hook_top'):    # r7 origins are stale on the panel
            self.assertIsNotNone(CK.chord(shp['panel'], tuple(st[fid]['r7_origin']), (0, 1, 0))[3], fid)
        self.assertIsNotNone(CK.chord(shp['panel'], (-155.1, 25.5, 78.0), (0, 1, 0))[3])   # clamp crown strip removed
        self.assertGreaterEqual(CK.chord(shp['panel'], (-155.1, 25.0, 72.6), (0, 1, 0))[0], 1.2)
        self.assertAlmostEqual(CK.chord(shp['panel'], (-155.1, 19.3, 64.0), (0, 0, 1))[0], 3.233, delta=0.011)


def PR_model():
    import model
    return model


if __name__ == '__main__':
    unittest.main()

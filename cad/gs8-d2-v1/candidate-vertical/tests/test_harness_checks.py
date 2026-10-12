# SPDX-License-Identifier: MIT
"""Harness and power checks of the candidate (review VN-26, VN-28; check parts of VN-47 / VN-62; fix FP-10).

Run:  run_locked.py -- cad/gs8-d2-v1/candidate-vertical/tests/test_harness_checks.py

- r7 port: constants and helper math equal r7 checks.py / layout.py (d38468e copies in ../).
- Families: the stretched QT / run routes are recomputed from their own knots; the solver bounds are the literals in
  signal_routes.py; the family minima match the routes of record (QT 203.5 since the H2 fan-in and top-run family,
  239.1 before; run 183.3 / 171.6 mm since the H1 re-route behind the carrier boss, 214.3 / 209.5 on 9ced753).
- Regression fixtures: a lead shortened 10 mm fails mate_reach (QT plug row, run plug row, J2 inline halves); a
  pigtail 10 mm shorter loses face_out; a tie slot moved onto a core is 'on route'; drop rows reproduce the
  candidate's own 60 C model at the low end and fail at the hot-fuse high end, a cold short path passes; overlapping
  header housings and a COTS box on a housing fail; a longest lead beyond the loop family fails cable_stow.
- Bound report: out/<variant>/harness-checks.json binds the current manifest, verifier and dependencies; its key
  numbers are reproduced CAD-free; its failing set is the documented expected set (CAD / docs phase, user decisions).
- Registration and the archived orphan route report.
"""
import copy
import hashlib
import json
import math
import sys
import unittest
from pathlib import Path

CV = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CV))
sys.path.insert(0, str(CV.parent))
from cv_io import read_text   # noqa: E402
import harness_rules as HR    # noqa: E402
import routes as R            # noqa: E402
import steps as ST            # noqa: E402

VARIANT = 'compact-kowa_lm6hc'
OUT = CV / 'out' / VARIANT
REPORT = OUT / 'harness-checks.json'
NO_HITS = lambda spec, targets: []   # noqa: E731  isolates the length rules in fixtures
_CACHE = {}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def data():
    if 'H' not in _CACHE:
        meta = json.loads(read_text(OUT / 'manifest.json'))
        _CACHE['out'] = R.build()
        _CACHE['rows'] = {r['id']: r for r in meta['rows']}
        _CACHE['H'] = HR.collect(_CACHE['out'], _CACHE['rows'], R.L, ST)
    return copy.deepcopy(_CACHE['H'])


def row(rows, rid, cat=None):
    return next(r for r in rows if r['id'] == rid and (cat is None or r['category'] == cat))


class TestR7Port(unittest.TestCase):
    def setUp(self):
        import checks as CK   # r7 checks.py (imports cadquery)
        import layout as L7
        self.CK, self.L7 = CK, L7

    def test_constants(self):
        CK, L7 = self.CK, self.L7
        self.assertEqual(HR.ROUTE_ALLOWANCE, CK.ROUTE_ALLOWANCE)
        self.assertEqual(HR.ROUTE_END_TOL, CK.ROUTE_END_TOL)
        for k in ('TAIL_D', 'SWEEP_TOL', 'STOW_FILL', 'MATE_POSE_TOL'):
            self.assertEqual(getattr(HR, k), getattr(CK, k), k)
        self.assertEqual(HR.MATE_MARGIN, L7.MATE_MARGIN)
        self.assertEqual(HR.HAND_ENVELOPES, L7.HAND_ENVELOPES)
        self.assertEqual(HR.HDR_MIN_GAP, L7.HDR_HOUSING['min_gap'])
        self.assertEqual(HR.FACE_OUT_MIN, L7.PIGTAIL['face_out_min'])
        D = L7.PIGTAIL['drop']
        self.assertEqual((HR.DROP['i_peak_a'], HR.DROP['limit_v'], HR.DROP['xt30_mohm']),
                         (D['i_peak_a'], D['limit_v'], D['xt30_mohm']))
        self.assertEqual(HR.DROP['fuse_cold_mohm'], L7.PIGTAIL_FUSE['cold_mohm'])

    def test_helpers_equal_r7(self):
        CK, L7 = self.CK, self.L7
        for n in (50, 60, 99, 150, 240, 250, 270, 300):
            self.assertEqual(HR.reach_margin(n), CK.reach_margin(L7, n))
        for rear, axis, rw, env in [((1, 2, 3), (1, 0, 0), (0, 0, 1), (30, 20, 24)),
                                    ((-72, 74.8, 77), (0.6, 0.8, 0), (0, 0, 1), (35, 22, 26)),
                                    ((5, -5, 9), (0, 0, -1), (1, 0, 0), (40, 30, 30))]:
            self.assertEqual([round(v, 9) for v in HR.hand_box(rear, axis, rw, env)],
                             [round(v, 9) for v in CK._hand_box(rear, axis, rw, env)])
        for b, oo in [((0, 1, 30, 40, 0, 1), ('+y', 28.0, 0.0)), ((0, 1, 0, 1, -150, -125), ('-z', -110.0, 15.0))]:
            self.assertAlmostEqual(HR.out_of_mm(list(b), oo), CK._out_of_mm(b, oo))
        path = [(0, 70, 0), (0, 0, 0)]
        for d in ((0, 60, 0), (0, 60.5, 0.02), (1, 0, 0)):
            self.assertEqual(HR.on_path(path, d), CK._on_path(path, d))


class TestFamilies(unittest.TestCase):
    def test_bounds_are_source_literals(self):
        src = read_text(CV / 'signal_routes.py')
        self.assertIn('lo,hi=44.,55.2', src)   # H2: was 'lo,hi=34.,50.' (low run)
        self.assertNotIn('lo,hi=34.,50.', src)
        self.assertIn('_solve_top(make,250,35,80)', src)
        self.assertEqual(HR.FAMILIES['qt']['bound'], (44.0, 55.2))
        self.assertEqual(HR.FAMILIES['run_pin37']['bound'], (35.0, 80.0))

    def test_recompute_and_minima(self):
        H = data()
        rows = HR.family_rows(H, R.rounded_path)
        self.assertEqual({r['status'] for r in rows}, {'pass'})
        mins = {cid: HR.min_route(H, H['cables'][cid], R.rounded_path)[0] for cid in HR.FAMILIES}
        self.assertAlmostEqual(mins['qt'], 203.54, delta=0.05)   # H2 fan-in + top-run family (239.14 before)
        # H1 (VN-26): run-lead loop re-routed behind the carrier boss (FIX-LOG); 9ced753 values were 214.31 / 209.54
        self.assertAlmostEqual(mins['run_pin37'], 183.27, delta=0.05)
        self.assertAlmostEqual(mins['run_pin39'], 171.63, delta=0.05)

    def test_tampered_family_fails(self):
        H = data()
        H['cables']['qt']['curve']['knots'][4][2] += 1.0   # the two loop knots no longer share the variable
        self.assertEqual(row(HR.family_rows(H, R.rounded_path), 'family_qt')['status'], 'fail')


class TestMateReach(unittest.TestCase):
    def _rows(self, H, lengths=None):
        return HR.mate_reach_rows(H, R.rounded_path, ST, NO_HITS, lengths)[0]

    def _plug_fixture(self, rid, cable):
        H = data()
        r = row(self._rows(H), rid)
        fl = r.get('free_lead')   # H2: a lead free at its mate (documented order) is judged on its free route
        raw = fl['fixed_mm'] + fl['route_mm'] if fl else r['fixed_mm'] + r['tail_mm']
        need = raw / (1 - HR.ROUTE_ALLOWANCE[1])   # L >= fixed + tail (or free route) + 0.1 L
        L_pass = math.ceil(max(need, raw + HR.MATE_MARGIN)) + 5
        ok = row(self._rows(H, {cable: L_pass}), rid)
        bad = row(self._rows(H, {cable: L_pass - 10}), rid)     # the same lead shortened 10 mm
        self.assertFalse([p for p in ok['problems'] if 'lead short' in p], ok['problems'])
        self.assertTrue([p for p in bad['problems'] if 'lead short' in p], bad['problems'])
        self.assertEqual(bad['status'], 'fail')

    def test_qt_shortened_10mm_fails(self):
        self._plug_fixture('qt_enc', 'qt')

    def test_run_lead_shortened_10mm_fails(self):
        self._plug_fixture('run_pi_37', 'run_pin37')

    def test_j2_halves_shortened_10mm_fail(self):
        H = data()
        r = row(self._rows(H), 'j2_btn')
        fl = r.get('free_lead')   # H2: the documented order (J2 free at panel_prop) places the junction on the free route
        if fl and fl.get('junction_s_mm') is not None:
            raw_b, raw_f = fl['junction_s_mm'], fl['route_mm'] - fl['junction_s_mm']
        else:
            raw_b = r['fixed_mm'] + math.dist(r['anchor_pt'], r['junction_at'])   # body side: anchor path + to junction
            raw_f = math.dist(r['junction_at'], r['far_pose'])                   # far side: junction to the switch
        L = math.ceil(max(x for raw in (raw_b, raw_f) for x in (raw + HR.MATE_MARGIN, raw / 0.9))) + 5
        ok = row(self._rows(H, {'power_button': (('a', L, 0.0), ('b', L, 0.0))}), 'j2_btn')
        bad = row(self._rows(H, {'power_button': (('a', L - 10, 0.0), ('b', L - 10, 0.0))}), 'j2_btn')
        unreachable = lambda p: 'junction' in p and 'cannot' in p   # noqa: E731  (secured or free-route wording)
        self.assertFalse([p for p in ok['problems'] if unreachable(p)], ok['problems'])
        self.assertTrue([p for p in bad['problems'] if unreachable(p)], bad['problems'])

    def test_qt_documented_order(self):
        r = row(self._rows(data()), 'qt_enc')
        # FX-H (verifier H2 minor): the free lead decides the row, so the secured-lane figures live in secured_lane_case
        self.assertLess(r['secured_lane_case']['slack_mm'], 0)   # secured-lane case: lanes secured, then propped 60 mm
        self.assertEqual(r['slack_mm'], r['free_lead']['slack_mm'])
        self.assertLess(r['info_free_lead_need_mm'], 240)  # free-lead lower bound only (not obstacle-checked)
        self.assertEqual(r['pose'], [0.0, 60.0, 0.0])
        # fixup-1: steps.py leaves QT and J2 free until panel_in. Without a free-lead route the rows fail on the HOLD
        # and the secured-lane shortfall is kept, labelled (negative control, unchanged).
        H = data()
        H['free_leads'] = {}
        for rid in ('qt_enc', 'j2_btn'):
            r0 = row(self._rows(H), rid)
            self.assertEqual(r0['status'], 'fail', rid)
            self.assertTrue(r0['lead_state'].startswith('free at panel_prop; laid into its lanes at panel_in'), r0)
            self.assertIn('no obstacle-checked free-lead route', r0['problems'][0])
        self.assertTrue(any(p.startswith('secured-lane case') and 'lead short' in p
                            for p in row(self._rows(H), 'qt_enc')['problems']))
        # H2: the declared free-lead routes decide (tests/test_h2_harness.py): QT passes on its free route with the
        # secured-lane shortfall kept in secured_lane_case; J2 fails on the FPC envelope at its hypothetical pads.
        q = row(self._rows(data()), 'qt_enc')
        self.assertEqual(q['status'], 'pass', q['problems'])
        self.assertTrue(any('lead short' in p for p in q['secured_lane_case']['problems']))
        self.assertEqual(row(self._rows(data()), 'j2_btn')['status'], 'fail')

    def test_qt_secured_before_prop_is_the_old_shortfall(self):
        saved = ST.STEPS
        try:   # mutation: the superseded order (QT and J2 secured at evf_mate) brings the plain shortfall back
            ST.STEPS = copy.deepcopy(saved)
            for o in ST.STEPS:
                if o['id'] == 'evf_mate':
                    o['secures'] = o['secures'] + ['qt', 'j2']
                if o['id'] == 'panel_in':
                    o['secures'] = []
            self.assertIn('SECURE_BEFORE_MATE', [c for c, _m in ST.lint()])
            r = row(self._rows(data()), 'qt_enc')
            self.assertTrue(r['lead_state'].startswith('secured in its lanes at evf_mate'), r['lead_state'])
            self.assertTrue([p for p in r['problems'] if p.startswith('lead short')], r['problems'])
            self.assertEqual(r['status'], 'fail')
        finally:
            ST.STEPS = saved


class TestFamilyMemberClearance(unittest.TestCase):
    """fixup-1 (FP-10): the bound family members behind cable_stow 'loop' and cable_routes family-minimum passes are
    swept as cable-OD capsules; a planted part on the member turns the pass into a fail."""

    def _run(self, H, hits):
        return HR.run_all(H, R.rounded_path, ST, hits=hits, printed_dist=lambda i, b: 9.9, cots_dist=lambda i, b: 9.9)

    def test_clear_member_keeps_its_status_and_records_the_sweep(self):
        rows = self._run(data(), NO_HITS)
        r = row(rows, 'qt', 'cable_stow')
        self.assertEqual(r['status'], 'pass')
        mc = r['member_clearance']
        self.assertEqual((mc['variable'], mc['value'], mc['od_mm']), ('low', 44.0, 3.2))   # H2 (was low 34)
        self.assertGreater(mc['pieces'], 2)
        self.assertIn('pi5', mc['exempt'])
        for rid in ('run_pin37', 'run_pin39'):
            self.assertEqual(row(rows, rid, 'cable_stow')['member_clearance']['value'], 80.0)
            rr = row(rows, rid, 'cable_routes')
            if rr['status'] == 'pass':
                self.assertEqual(rr['member_clearance']['value'], 35.0)

    def test_planted_part_on_the_bound_member_fails(self):
        H = data()
        c = H['cables']['qt']
        mem = HR.family_eval(R.rounded_path, c['curve'], c['family'], 44.0)['points']   # H2: longest member
        p = mem[len(mem) // 2]
        H['boxes']['zz_planted'] = [p[0] - 1, p[0] + 1, p[1] - 1, p[1] + 1, p[2] - 1, p[2] + 1]
        H['kinds']['zz_planted'] = 'printed'
        saved = ST.final_state
        try:
            ST.final_state = lambda steps=None: frozenset(saved(steps)) | {'zz_planted'}
            planted = lambda spec, targets: [h for h in HR.box_hits(spec, targets) if h['obstacle'] == 'zz_planted']
            r = row(self._run(H, planted), 'qt', 'cable_stow')
        finally:
            ST.final_state = saved
        self.assertEqual(r['status'], 'fail')
        self.assertIn('zz_planted', r['member_clearance']['hits'])
        self.assertTrue(any('longest member (the spare home)' in x for x in r['problems']))


class TestLeadAccess(unittest.TestCase):
    def test_ties_off_route_and_slot_fixture(self):
        H = data()
        rows = HR.pigtail_reach_rows(H, R.rounded_path)
        self.assertEqual(row(rows, 'pigtail_ties_on_route')['status'], 'fail')
        self.assertEqual(row(rows, 'pigtail_xt30_mouth')['status'], 'fail')
        self.assertEqual(row(rows, 'pigtail_xt30_mouth_rtv_only')['status'], 'info')
        saved = (HR.TIE_SLOTS_XZ, HR.TIE_SLOT_Y)
        try:   # a slot put on the negative core at (-35.82, 12.39, 47.0) binds it
            HR.TIE_SLOTS_XZ, HR.TIE_SLOT_Y = [(-35.82, 47.0)], (11.4, 13.4)
            t = row(HR.pigtail_reach_rows(H, R.rounded_path), 'pigtail_ties_on_route')
            self.assertTrue([x for x in t['ties'] if x['core'] == 'negative' and x['on_route']])
        finally:
            HR.TIE_SLOTS_XZ, HR.TIE_SLOT_Y = saved

    def test_rtv_matches_candidate_study_and_shorter_pigtail_loses(self):
        H = data()
        study = R.pigtail_16_study()
        neg = HR.corridor(H, 'negative', HR.FACE_OUT_MIN, R.rounded_path)['rounded_length_mm']
        self.assertAlmostEqual(neg, study['service_route_mm'] - study['solder_exit_stub_mm'], delta=0.5)
        rtv = row(HR.pigtail_reach_rows(H, R.rounded_path), 'pigtail_xt30_mouth_rtv_only')['cores']
        saved = HR.PIGTAIL_LENGTH
        try:
            HR.PIGTAIL_LENGTH = saved - 10.0
            short = row(HR.pigtail_reach_rows(H, R.rounded_path), 'pigtail_xt30_mouth_rtv_only')['cores']
        finally:
            HR.PIGTAIL_LENGTH = saved
        for c in HR.POWER_CORES:   # 10 mm shorter costs 10 - 1 (allowance 27 -> 26) mm of face out
            self.assertAlmostEqual(rtv[c]['face_out_mm'] - short[c]['face_out_mm'], 9.0, delta=0.2)

    def test_retention_switch_moves_the_gate(self):
        rows = HR.pigtail_reach_rows(data(), R.rounded_path, retention='rtv_only')
        self.assertTrue(row(rows, 'pigtail_xt30_mouth_rtv_only')['gating'])
        self.assertEqual(row(rows, 'pigtail_xt30_mouth')['status'], 'info')
        self.assertEqual(row(rows, 'pigtail_ties_on_route')['status'], 'info')


class TestDrop(unittest.TestCase):
    def test_low_end_is_the_candidate_model_and_hot_fuse_fails(self):
        r = HR.pigtail_drop_row()
        self.assertAlmostEqual(HR.drop_v(HR.DROP['awg16_mm2'], 1.0, HR.DROP['awg18_mm2'], 1.0), 0.142810903056,
                               delta=2e-4)   # make_bom_vertical hot_drop uses 13.17 / 21 mohm/m (AWG tables)
        self.assertEqual(r['status'], 'fail')
        self.assertGreater(r['drop_hi_v'], 0.150)
        self.assertLess(r['cases']['lo']['drop_v'], 0.150)
        self.assertGreater(r['cases']['nominal_hot_fuse']['drop_v'], 0.150)   # the hot fuse alone breaks it

    def test_limit_never_relaxed_and_short_cold_path_passes(self):
        self.assertEqual(HR.DROP['limit_v'], 0.15)
        D = dict(HR.DROP, pigtail_path_mm=225.0, fuse_hot_factor_range=(1.0, 1.0))
        self.assertEqual(HR.pigtail_drop_row(D)['status'], 'pass')
        self.assertEqual(HR.pigtail_drop_row(dict(HR.DROP, pigtail_path_mm=230.0))['status'], 'fail')   # hot fuse: max 225.4


class TestHeaderStowRoutes(unittest.TestCase):
    def test_header_fixtures(self):
        H = data()
        final = set(ST.final_state())
        base = {r['id']: r for r in HR.header_housing_rows(H, final, printed_dist=lambda i, b: 5.0,
                                                          cots_dist=lambda i, b: 5.0)}
        self.assertTrue(all(not [p for p in r['problems'] if 'overlaps housing' in p] for r in base.values()))
        h = H['housings']
        h['hdr_qt_3']['box'] = list(h['hdr_qt_1']['box'])                      # two housings on one pin
        H['boxes']['cooler'] = list(h['hdr_qt_5']['box'])                     # a COTS box on a housing
        rows = {r['id']: r for r in HR.header_housing_rows(H, final, printed_dist=lambda i, b: 5.0)}
        self.assertTrue([p for p in rows['hdr_qt_1']['problems'] if 'overlaps housing' in p])
        self.assertTrue([p for p in rows['hdr_qt_5']['problems'] if 'to COTS cooler' in p])

    def test_stow_and_route_fixtures(self):
        H = data()
        st = row(HR.cable_stow_rows(H, R.rounded_path), 'qt')
        self.assertEqual(st['status'], 'pass')
        H['cables']['qt']['length_range'] = (240.0, st['family_max_mm'] + 1.0)
        self.assertEqual(row(HR.cable_stow_rows(H, R.rounded_path), 'qt')['status'], 'fail')
        cr = row(HR.cable_routes_rows(data(), R.rounded_path), 'qt')
        self.assertFalse([p for p in cr['problems'] if 'shortest route' in p])   # H2: 203.5 + 25 <= 240
        H = data()
        H['cables']['qt']['length_range'] = (200.0, 260.0)                     # a 200 mm minimum lead fails
        self.assertTrue([p for p in row(HR.cable_routes_rows(H, R.rounded_path), 'qt')['problems']
                         if 'shortest route' in p])
        H = data()
        H['cables']['qt']['length_range'] = (270.0, 280.0)
        self.assertFalse([p for p in row(HR.cable_routes_rows(H, R.rounded_path), 'qt')['problems']
                          if 'shortest route' in p])


class TestBoundReport(unittest.TestCase):
    def setUp(self):
        if not REPORT.exists():
            self.skipTest('harness-checks.json not generated yet')
        self.rep = json.loads(read_text(REPORT))

    def test_bindings(self):
        self.assertEqual(self.rep['manifest_sha256'], sha(OUT / 'manifest.json'))
        self.assertEqual(self.rep['verification_source_sha256'], sha(CV / 'verify_harness_checks.py'))
        for rel, h in self.rep['verification_dependency_sha256'].items():
            self.assertEqual(sha(CV / rel), h, rel)

    def test_numbers_reproduced(self):
        H = data()
        rows = HR.run_all(H, R.rounded_path, ST, hits=NO_HITS, printed_dist=lambda i, b: 9.9, cots_dist=lambda i, b: 9.9)
        for cat, rid, keys in [('mate_reach', 'qt_enc', ('fixed_mm', 'route_mm', 'slack_mm')),   # FX-H: free-lead figures
                               ('mate_reach', 'run_pi_37', ('fixed_mm', 'tail_mm', 'slack_mm')),
                               ('cable_routes', 'qt', ('min_route_mm', 'slack_mm')),
                               ('lead_access', 'pigtail_drop', ('drop_lo_v', 'drop_hi_v')),
                               ('lead_access', 'pigtail_xt30_mouth_rtv_only', ('cores',)),
                               ('lead_access', 'pigtail_xt30_mouth', ('cores',))]:
            a, b = row(rows, rid, cat), row(self.rep['checks'], rid, cat)
            for k in keys:
                self.assertEqual(a[k], b[k], (rid, k))
        a, b = row(rows, 'qt_enc', 'mate_reach'), row(self.rep['checks'], 'qt_enc', 'mate_reach')
        for k in ('fixed_mm', 'tail_mm', 'slack_mm'):   # FX-H: the secured-lane figures moved into secured_lane_case
            self.assertEqual(a['secured_lane_case'][k], b['secured_lane_case'][k], k)

    def test_failing_set(self):
        got = self.rep['failing']
        self.assertEqual(got, EXPECTED_FAILING)
        import evidence_rules as ER
        self.assertEqual(ER.EXPECTED_HARNESS_FAILURES, {})
        self.assertTrue(ER.harness_failure_findings(self.rep))   # failures stay visible to the reconciler


class TestRegistrationAndArchive(unittest.TestCase):
    def test_registration(self):
        self.assertIn("('harness',[P/'verify_harness_checks.py'])", read_text(CV / 'run_shadow_checks.py'))
        rec = read_text(CV / 'reconcile_review_evidence.py')
        self.assertIn("'out/compact-kowa_lm6hc/harness-checks.json', 'verify_harness_checks.py'", rec)
        self.assertIn('harness_failure_findings', rec)
        self.assertIn("'harness-checks.json':'verify_harness_checks.py'", read_text(CV / 'review_docs_audit.py'))

    def test_orphan_archived(self):
        idx = json.loads(read_text(CV / 'history/orphan-signal-routes-2026-10-11/INDEX.json'))
        self.assertFalse((CV / 'signal_routes_review.json').exists())
        for m in idx['moved']:
            self.assertEqual(sha(CV / m['to']), m['sha256'])
        self.assertEqual(idx['recorded_bindings']['power_source_sha256'][:8], '3b7db74a')
        paths = json.loads(read_text(CV / 'delivery-core-paths.json'))
        self.assertNotIn('cad/gs8-d2-v1/candidate-vertical/signal_routes_review.json', paths)
        self.assertIn('cad/gs8-d2-v1/candidate-vertical/history/orphan-signal-routes-2026-10-11/signal_routes_review.json',
                      paths)


# Rows that fail on the reviewed geometry by design (manifest 53e668d4), until the CAD / docs phase or a user
# decision: QT shortest route + allowance > 240 and fan-in gap; no installed EVF feed (VN-60) or pack-lead route;
# pigtail cores carry less stored slack than the r7 allowance; QT propped-panel reach after the lanes are secured;
# carrier ties not on the drawn cores (VN-47); positive core face out < 15 (VN-47 / VN-72); hot-fuse drop (VN-62).
# fixup-1: QT and J2 are free at panel_prop (steps.py secures them at panel_in) and no obstacle-checked free-lead route
# exists yet (j2_btn joins qt_enc); the run-lead family members (both bounds, and the recorded route itself, probe
# 2026-10-11) intersect the tub (floor lay at centreline z 4.9 and the riser), so their cable_routes / cable_stow rows fail.
# H1 (VN-26 routes, FP-11f): run leads re-routed behind the carrier boss, installed usb_5v and pack_lead routes with
# exact installed-clearance sweeps and the feed_volumes rows: those six rows pass and leave this set.
# H2 (VN-28): QT fan-in modeled and the top-run family re-solved (shortest route 203.5 + 25 <= 240); qt_enc passes on
# its declared free-lead route (exact sweep clear) and leaves this set. cable_routes qt still fails, now on the
# installed-route sweep H2 added: the 250 mm solve puts the top run (Z79.2) against the HDMI ribbon's U-turn bottom
# (Y-22.35, Z80.15..85.85); j2_btn fails on its free route (cooler fin at the hypothetical pads, FPC envelope; VN-73);
# the pigtail service corridor is now obstacle-checked (microsd, tub, run leads, FPC envelope) and stays failing with
# the pigtail rows (user decisions 4 and 6).
# FX-H (phase-2 verifier findings 1-3, 5; stricter checks, each newly failing row is honest and logged in FIX-LOG):
# cable_stow qt (the members storing 250 / 260 mm of the purchased QT lead meet the HDMI U-turn cells; 240 is clear);
# cable_stow power_button_j2_pair (new row: the V-28 class pair does not fit routes.py power_stow, user decision 13);
# cable_routes power_button (installed sweep added: cooler and pi5 at the J2 pad hypothesis, VN-73 / G-V-POWER), fan
# (the estimated native-lead route runs inside the cooler model beyond its 10 mm terminal zone), fpc and oled_flex
# (ribbon round-envelope screen: not proof of a conflict, clearance unproven). Corrective 2026-10-12 removes
# the QT route/stow and qt_enc failures only after exact stored/free sweeps, with old-geometry negative controls.
EXPECTED_FAILING = {
    'cable_routes': ['fan', 'fpc', 'oled_flex', 'pigtail_negative', 'pigtail_positive', 'power_button'],
    'cable_stow': ['power_button_j2_pair'],
    'lead_access': ['pigtail_drop', 'pigtail_ties_on_route', 'pigtail_xt30_mouth'],
    'mate_reach': ['j2_btn', 'xt30_pack'],
}

if __name__ == '__main__':
    unittest.main(verbosity=2)

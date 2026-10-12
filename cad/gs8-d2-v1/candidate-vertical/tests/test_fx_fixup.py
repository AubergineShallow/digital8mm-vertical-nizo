# SPDX-License-Identifier: MIT
"""Regression tests for the FX fix-up of the phase-2 verifier findings (review 2026-10-10). Run through ../run_locked.py.

CAD-free: plenum_flow (path-aware min cut) fixtures and the selected trial4 geometry, with the rejected trial3 numbers
and a trial2-like choke as negative controls; vent_geometry layout rules; model data for the FPS bundle lane, tenon pocket walls, tie slots, kit-boss
rim, locator crush ridge and grip scar allowance; bed-chamfer exceptions; verify_fps_integrated exit code; per-variant
flow baselines. CAD: the cavity inventory (an undeclared 1 mm3 block fails, a missing declared addition is stale), the
J4 direct free body against the export18 transfer, and the bound reports of the FX refresh.
"""
import json
import math
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

CV = Path(__file__).resolve().parents[1]
R7 = CV.parent
REPO = R7.parent.parent
for _p in (str(R7), str(CV), str(CV / 'structural-review')):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import plenum_flow as PF          # noqa: E402
import vent_geometry as VG        # noqa: E402

VAR = 'compact-kowa_lm6hc'
OUT = CV / 'out' / VAR


def rd(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))


def toy(boxes, ports, mouths, x=(0., 10.), z=(0., 10.)):
    bx = [v for b in boxes for v in b[:2]] + [v for p in ports for v in p[:2]]
    bz = [v for b in boxes for v in b[4:]] + [v for p in ports for v in p[2:]]
    xs, zs = PF.subdivide(bx, *x), PF.subdivide(bz, *z)
    return PF.min_cut(xs, zs, PF.mask_from_boxes(xs, zs, boxes), ports, mouths)


def port_cut_consistent(nominal,empty):
    """Nominal/empty consistency for port-limited cuts, using only their accumulated integer-rounding bounds.

    Both cuts are known source-port sets, so their selected-cut error bounds apply to the same geometric surface.
    Independent grid subdivisions can reverse their graph totals by 1e-5 mm2. No acceptance gate uses this helper.
    """
    for cut in (nominal,empty):
        if cut['cut_composition_mm2']['internal'] or cut['cut_composition_mm2']['mouth']:
            raise ValueError('This comparison requires both selected cuts to be the port faces')
    allowance=sum(cut['quantization']['selected_cut_abs_error_bound_mm2'] for cut in (nominal,empty))
    return nominal['min_cut_mm2']<=empty['min_cut_mm2']+allowance


# ------------------------------------------------------------------------------------------- plenum_flow (CAD-free)
class MinCutFixtures(unittest.TestCase):
    PORT = [(0., 10., 7., 9.)]          # 20 mm2 of port face
    MOUTH = {'b': ('z_min', 0., 10.)}   # 60 mm2 of mouth face (6 mm gap x 10 mm)

    def test_open_bay_is_port_limited(self):
        r = toy([], self.PORT, self.MOUTH)
        self.assertAlmostEqual(r['min_cut_mm2'], 20.0, places=3)
        self.assertAlmostEqual(r['cut_composition_mm2']['port'], 20.0, places=3)

    def test_full_depth_row_blocks(self):
        r = toy([(0., 10., -35., -27., 4.4, 5.6)], self.PORT, self.MOUTH)
        self.assertAlmostEqual(r['min_cut_mm2'], 0.0, places=6)

    def test_gap_in_row_is_the_cut(self):
        r = toy([(0., 4., -35., -27., 4.4, 5.6), (6., 10., -35., -27., 4.4, 5.6)], self.PORT, self.MOUTH)
        self.assertAlmostEqual(r['min_cut_mm2'], 12.0, places=3)        # 2 mm x 6 mm
        self.assertGreater(r['cut_composition_mm2']['internal'], 11.99)

    def test_hanging_beam_passes_air_under_it(self):
        r = toy([(0., 10., -29., -27., 4.4, 5.6)], self.PORT, self.MOUTH)   # 5 mm window under a 1 mm beam
        self.assertAlmostEqual(r['min_cut_mm2'], 20.0, places=3)
        r = toy([(0., 10., -29., -27., 4.4, 5.6)], [(0., 10., 8., 18.)], self.MOUTH, z=(0., 20.))
        self.assertAlmostEqual(r['min_cut_mm2'], 50.0, places=3)            # 10 mm x 5 mm window (port 100, mouth 60)

    def test_port_behind_material_is_blocked(self):
        r = toy([(2., 4., -28.5, -27., 7., 9.)], self.PORT, self.MOUTH)
        self.assertAlmostEqual(r['port_face_blocked_mm2'], 4.0, places=3)
        self.assertAlmostEqual(r['min_cut_mm2'], 16.0, places=3)

    def test_quantization_allowance_rejects_a_larger_excess(self):
        reference=toy([],self.PORT,self.MOUTH)
        allowance=2*reference['quantization']['selected_cut_abs_error_bound_mm2']
        self.assertTrue(port_cut_consistent(reference,reference))
        excess=dict(reference,min_cut_mm2=reference['min_cut_mm2']+allowance+1/PF.SCALE)
        self.assertFalse(port_cut_consistent(excess,reference))

    def test_levels_follow_breaks(self):
        c, w = PF.levels_from_breaks([-29.0, -28.4])
        self.assertAlmostEqual(sum(w), 6.0, places=9)
        self.assertTrue(any(abs(a - (-29.0)) < 1e-9 for a in [x - t / 2 for x, t in zip(c, w)]))
        self.assertLessEqual(max(w), PF.LEVEL_DY + 1e-9)


class Trial3Nominal(unittest.TestCase):
    """Selected nominal cut and retained trial3 negative controls; the gate itself runs on the saved STEP."""

    def test_cold_reaches_the_ports(self):
        for L in (158., 185.):
            r = PF.nominal_min_cut(VG, L, 'cold')
            self.assertGreaterEqual(r['min_cut_mm2'], 420.0 - PF.TOL_MM2, L)

    def test_hot_value_and_empty_bay_bound(self):
        r = PF.nominal_min_cut(VG, 158., 'hot')
        self.assertGreaterEqual(r['min_cut_mm2'],510.0-PF.TOL_MM2)
        e = PF.nominal_min_cut(VG, 158., 'hot', ribs=False)
        self.assertGreaterEqual(e['min_cut_mm2'],510.0-PF.TOL_MM2)
        # Both selected cuts must be the complete port faces. Compare their geometric areas, not independently
        # quantized graph totals (510.0000052 vs 509.999995); the original 1e-6 comparison tolerance is retained.
        for cut in (r,e):
            self.assertEqual(cut['cut_composition_mm2']['internal'],0.)
            self.assertEqual(cut['cut_composition_mm2']['mouth'],0.)
            self.assertAlmostEqual(cut['port_face_mm2'],510.,delta=1e-6)
        self.assertLessEqual(r['port_face_mm2'],e['port_face_mm2']+1e-6)
        self.assertTrue(port_cut_consistent(r,e))

    def test_rejected_trial3_bound_is_retained(self):
        with mock.patch.multiple(VG,HOT_FRONT_Z=(5.,40.),HOT_FRONT_STEP_Z=40.,HOT_FRONT_MULLION_ZS=(21.,)):
            r=PF.nominal_min_cut(VG,158.,'hot')
            e=PF.nominal_min_cut(VG,158.,'hot',ribs=False)
        self.assertAlmostEqual(r['min_cut_mm2'],444.5,delta=.05)
        self.assertAlmostEqual(e['min_cut_mm2'],493.2,delta=.05)
        self.assertLess(e['min_cut_mm2'],510.)

    def test_trial2_like_rows_choke_the_hot_bay(self):
        """Negative control: full-depth rows across the port band and the upper bay, as trial2 had, cut the path."""
        y0, y1 = VG.RIB_Y
        rows = [(-59.8, -17.3, y0, y1, z - .6, z + .6) for z in (21., 28., 35.)]
        rows += [(-62.1, -41.5, y0, y1, z - .6, z + .6) for z in (43., 59., 75., 91.)]
        rows += [(-38.5, -2.4, y0, y1, z - .6, z + .6) for z in (43., 59., 75., 91.)]
        orig = VG.rib_boxes
        try:
            VG.rib_boxes = lambda L: orig(L) + rows
            with mock.patch.multiple(VG,HOT_FRONT_Z=(5.,40.),HOT_FRONT_STEP_Z=40.,HOT_FRONT_MULLION_ZS=(21.,)):
                r = PF.nominal_min_cut(VG, 158., 'hot')
        finally:
            VG.rib_boxes = orig
        self.assertLess(r['min_cut_mm2'], 300.0)


class Trial3Layout(unittest.TestCase):
    def test_no_rib_in_front_of_a_wall_port(self):
        ports = [(-103., -68., z, z + 3.) for z in VG.SIDE_Z] + [(-59., -16.5, z, z + 3.) for z in VG.HOT_Z]
        for L in (158., 185.):
            for b in VG.rib_boxes(L):
                if b[3] <= PF.GAP_Y[1] - 0.5:
                    continue           # not reaching the wall-side level
                for p in ports:
                    ov = min(b[1], p[1]) - max(b[0], p[0]) > 1e-6 and min(b[5], p[3]) - max(b[4], p[2]) > 1e-6
                    self.assertFalse(ov, ('rib in front of port', b, p))

    def test_beams_and_pillars(self):
        P, W = VG.PILLAR_L, VG.WINDOW_MAX
        self.assertGreaterEqual(VG.WALL_OUTER - VG.BEAM_Y0, 0.6)          # >= 3 layers of beam
        self.assertGreaterEqual(VG.BEAM_Y0 - VG.SKIN_INNER, 4.5)          # >= 4.5 mm flow window under the beam
        for lo, hi, solid in ((0., 50., ()), (0., 13., ()), (-158., -64.9, ((-158., -155.4),))):
            pil = VG._windowed(lo, hi, (), solid)
            self.assertAlmostEqual(pil[0][0], lo)
            self.assertAlmostEqual(pil[-1][1], hi)
            gaps = [b[0] - a[1] for a, b in zip(pil, pil[1:])]
            self.assertTrue(all(g <= W + 1e-6 for g in gaps), gaps)
            self.assertTrue(all(b - a >= P - 1e-6 for a, b in pil))

    def test_cold_window_keeps_pillars_out(self):
        """FX note: the keep-out is applied only to cold rows that end left of the CSI block (x <= -65: rows 43-67);
        rows ending at -64.9 keep their regular pillars (vent_geometry.rib_boxes 'if b<=-65'). The vent_geometry comment
        overstates it; the gate is the saved-STEP cold path min cut (420 = ports)."""
        a, b = VG.COLD_WINDOW_X
        self.assertLessEqual(b - a, VG.WINDOW_MAX + 1e-9)
        y0, y1 = VG.RIB_Y
        for x0, x1, by0, by1, z0, z1 in VG.rib_boxes(158.):
            if by0 <= y0 + 1e-9 and z1 - z0 < 2. and x1 - x0 < 2.:        # a cold-row pillar
                if -158. < x0 < -65. and any(abs(z - (z0 + z1) / 2) < 1e-6 and segs[-1][1] <= -65.
                                             for z, segs in VG.cold_rows(158.)):
                    self.assertFalse(a + 1e-6 < x0 < b - 1e-6 and a + 1e-6 < x1 < b - 1e-6, (x0, x1))

    def test_metadata_names_trial4(self):
        self.assertIn('trial4',VG.metadata(158.)['revision'])
        self.assertIn('trial4',VG.support_summary(158.)['revision'])


# ------------------------------------------------------------------------------------------- model data (CAD-free import)
class ModelData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import model
        cls.m = model

    def test_tie_slots_agree(self):
        import harness_rules as HR
        import critical_features_vertical as CFV
        self.assertEqual([tuple(p) for p in self.m.CARRIER_TIE_SLOTS], [tuple(p) for p in HR.TIE_SLOTS_XZ])
        self.assertEqual(tuple(tuple(p) for p in self.m.CARRIER_TIE_SLOTS), tuple(CFV.CARRIER_TIE_SLOTS))
        self.assertIn((-35.0, 25.0), [tuple(p) for p in self.m.CARRIER_TIE_SLOTS])
        # the bar outside slot 3 against the power-nut relief cone at the bed face (cone r 11.8 about (-20, 25.5))
        r_bed = self.m.POWER_NUT_RESERVE_R + 0.8 + .1 / 1.2
        x_bar_out = -35.0 + 1.5
        d = math.hypot(x_bar_out - self.m.POWER_NUT_AXIS_XZ[0], 25.0 - self.m.POWER_NUT_AXIS_XZ[1])
        self.assertGreaterEqual(d - r_bed, 1.6 - 0.02)

    def test_fps_bundle_lane(self):
        x0, x1, z0 = self.m.FPS_BUNDLE_LANE
        bundle = (-134.8, -132.2, 78.4)           # integrated-fps-checks.json d848d413: static bundle hit bbox
        self.assertGreaterEqual(bundle[0] - x0, 0.3)
        self.assertGreaterEqual(x1 - bundle[1], 0.3)
        self.assertGreaterEqual(bundle[2] - z0, 0.3)
        self.assertLessEqual(x1 - x0, 3.6 + 1e-9)  # the guide face over the lane bridges <= 3.6 mm

    def test_tenon_pocket_walls(self):
        tc = {(b['side'], b['kind']): b for b in self.m.L.tab_catch_boxes()}
        web = tc[(1, 'web')]
        T, C = self.m.TAB_CATCH_TENON, self.m.TAB_CATCH_POCKET_CLEAR
        self.assertGreaterEqual((T['x'][0] - C['x']) - web['x'][0], 1.2 + 0.25)
        self.assertGreaterEqual(web['x'][1] - (T['x'][1] + C['x']), 1.2 + 0.25)
        self.assertGreaterEqual(self.m.TAB_CATCH_CEILING_TOP - self.m.TAB_CATCH_SPLIT_Z - T['h'] - C['z'], 1.6 - 1e-9)

    def test_kit_boss_rim_and_exception_retired(self):
        import critical_features_vertical as CFV
        self.assertGreaterEqual(CFV.KIT_BOSS['rim_mm'], 1.2)
        self.assertIn('kit_boss_lead_in_rim', CFV.RETIRED_EXCEPTIONS)
        src = (CV / 'model.py').read_text(encoding='utf-8')
        self.assertNotIn("cyl('y',3.35,top-.7", src)

    def test_locator_crush_ridge(self):
        r = self.m.LOCATOR_CRUSH_RIDGE
        self.assertAlmostEqual(r['h'], 0.2)                       # one 0.2 mm layer
        self.assertLessEqual(r['z'][1] - r['z'][0], 1.0)
        lo, hi = self.m.CARRIER_LOCATORS[0]['tongue_box'][4:6]
        self.assertTrue(lo < r['z'][0] < r['z'][1] < hi)

    def test_grip_scar_allowance_inside_zone(self):
        self.assertAlmostEqual(self.m.GRIP_SCAR_ALLOWANCE, 0.2)


# ------------------------------------------------------------------------------------------- check-side wiring (CAD-free)
class CheckWiring(unittest.TestCase):
    def test_fps_integrated_exits_nonzero_on_fail(self):
        src = (CV / 'verify_fps_integrated.py').read_text(encoding='utf-8')
        self.assertIn("raise SystemExit(0 if result['status']=='geometric_pass_only' else 1)", src)

    def test_flow_baseline_per_variant(self):
        src = (CV / 'verify_check_scope.py').read_text(encoding='utf-8')
        self.assertIn('def flow_baseline(variant)', src)
        self.assertIn("no flow-network baseline for this variant", src)
        for v in ('compact-kowa_lm6hc', 'compact-fujinon_hf6xa', 'original-kowa_lm6hc'):
            p = (CV / 'review-2026-10-10/fp12/flow-network-baseline.json' if v == VAR else
                 CV / ('review-2026-10-10/fp12/flow-network-baseline-%s.json' % v))
            self.assertTrue(p.exists(), p)
            b = rd(p)
            self.assertEqual(b.get('variant', VAR), v)
            self.assertGreater(len(b['reason']), 80)

    def test_series_planes_cover_the_port_band(self):
        src = (CV / 'verify_check_scope.py').read_text(encoding='utf-8')
        import ast
        tree = ast.parse(src)
        series = [n.value for n in ast.walk(tree) if isinstance(n, ast.Assign)
                  and any(isinstance(t, ast.Name) and t.id == 'series' for t in n.targets)]
        self.assertEqual(len(series), 1)
        hot = [v for k, v in zip(series[0].keys, series[0].values)
               if isinstance(k, ast.Constant) and k.value == 'hot_bottom']
        self.assertEqual(len(hot), 1)
        calls = []
        for n in ast.walk(hot[0]):
            if (isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'planes'
                    and len(n.args) == 4 and isinstance(n.args[0], ast.Call)
                    and isinstance(n.args[0].func, ast.Name) and n.args[0].func.id == 'frange'):
                calls.append((tuple(ast.literal_eval(a) for a in n.args[0].args),
                              *(ast.literal_eval(a) for a in n.args[1:])))
        self.assertIn(((16.05, 42.95, 0.5), 'z', 16.05, 42.95), calls)
        self.assertIn("_path_min_cut", src)

    def test_bed_chamfer_exceptions(self):
        import manifold3d as m3
        import print_rules as PR
        blk = m3.Manifold.cube([30., 20., 5.])                     # sharp block: 100 mm of sharp bed outline
        r = PR.check_bed_chamfer('fix', blk, exceptions=[dict(id='e', box2=(-1., -1., 31., 21.), max_mm=200.)])
        self.assertEqual(r['status'], 'pass', r)
        r = PR.check_bed_chamfer('fix', blk, exceptions=[dict(id='e', box2=(-1., -1., 31., 21.), max_mm=50.)])
        self.assertEqual(r['status'], 'fail')                      # over its max
        r = PR.check_bed_chamfer('fix', blk, exceptions=[dict(id='e', box2=(100., 100., 101., 101.), max_mm=5.)])
        self.assertEqual(r['status'], 'fail')                      # stale (and the outline still sharp)
        self.assertTrue(r['exceptions'][0]['stale'])
        ex = PR.BED_CHAMFER_EXCEPTIONS['lens_collar'][0]
        self.assertIn('washer_flat_support', ex['tie'])
        self.assertLessEqual(ex['max_mm'], 8.5)

    def test_cavity_inventory_pinned(self):
        import cavity_rules as CR
        self.assertEqual(sorted(CR.INVENTORY), sorted([
            'carrier_locator_seat', 't2_minus_y_tine_flange', 't2_minus_y_tine_fill', 't2_ll_insert_boss_cone',
            't2_rear_landing_wedge', 't2_fps_guide_corbel', 't2_tab_catch_ceiling', 't2_tab_catch_pad']))
        self.assertEqual(CR.TOL_MM3, 1e-5)


# ------------------------------------------------------------------------------------------- CAD
class CavityRule(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import cadquery as cq
        import cavity_rules as CR
        import model
        cls.cq, cls.CR = cq, CR
        man = rd(OUT / 'manifest.json')
        cls.L = man['core_dimensions_mm'][0]
        cls.tub = cq.importers.importStep(str(OUT / 'step/tub.step')).val()
        cls.old = cq.importers.importStep(str(CV / 'history/reviewed-export18/tub.step')).val()
        cls.cav = cq.Solid.makeBox(-5.3 - (-cls.L + 2.6), 25.1 + 25.4, 97.4 - 2.6, cq.Vector(-cls.L + 2.6, -25.4, 2.6))
        cls.decl = CR.declared_additions(model, cls.L, man.get('lens', 'kowa_lm6hc'))

    def test_saved_tub_passes(self):
        r = self.CR.undeclared_material(self.tub, self.old, self.cav, self.decl)
        self.assertTrue(r['passed'], r)
        self.assertGreater(r['added_mm3'], 100.0)                  # the declared additions are really there

    def test_undeclared_block_fails(self):
        blk = self.cq.Solid.makeBox(1., 1., 1., self.cq.Vector(-60., -20., 60.))
        self.assertGreater(blk.intersect(self.tub).Volume() * -1 + 1.0, 0.99)   # the block lies in free cavity
        r = self.CR.undeclared_material(self.tub.fuse(blk), self.old, self.cav, self.decl)
        self.assertFalse(r['passed'])
        self.assertAlmostEqual(r['undeclared_mm3'], 1.0, delta=0.01)

    def test_missing_declared_addition_is_stale(self):
        bogus = self.decl + [('carrier_locator_seat_moved', self.decl[0][1].translate(self.cq.Vector(0, 0, 30)))]
        self.CR.INVENTORY['carrier_locator_seat_moved'] = 'test only'
        try:
            r = self.CR.undeclared_material(self.tub, self.old, self.cav, bogus)
        finally:
            del self.CR.INVENTORY['carrier_locator_seat_moved']
        self.assertFalse(r['passed'])
        self.assertIn('carrier_locator_seat_moved', r['stale'])


class J4DirectFreeBody(unittest.TestCase):
    """check_scope.j4_direct (complete manifest minus the lower rows from their STEPs) reproduces the export18
    first-moment transfer on the phase-1 export 44f8131, whose J4 lower rows equal export18's."""

    def test_direct_equals_transfer_on_phase1(self):
        import cadquery as cq
        import check_scope as CS
        import evidence_rules as ER
        ref = rd(CV / 'structural-review/reference-export18-structural-binding.json')
        old = rd(CV / 'history/reviewed-export18/manifest.json')
        rel = 'cad/gs8-d2-v1/candidate-vertical/out/compact-kowa_lm6hc/'
        show = lambda p: subprocess.run(['git', '-C', str(REPO), 'show', '44f8131:' + rel + p],  # noqa: E731
                                        capture_output=True, check=True).stdout
        man = json.loads(show('manifest.json').decode('utf-8'))
        with tempfile.TemporaryDirectory(prefix='fx-j4-') as td:
            d = Path(td)
            (d / 'step').mkdir()
            for i in CS.J4_LOWER_IDS:
                (d / 'step' / ('%s.step' % i)).write_bytes(show('step/%s.step' % i))
            import hashlib
            sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()  # noqa: E731

            def centre(p):
                c = cq.importers.importStep(str(p)).val().Center()
                return (c.x, c.y, c.z)
            lf = CS.lower_first_moments(man, d, centre, sha)
        res = CS.j4_screen(ref, old, man, ER.changed_rows, lower_first=lf)
        self.assertTrue(res['valid'])
        self.assertEqual(res['method'], 'export18 first-moment transfer')
        direct = CS.j4_direct(ref, man, lf)
        rel_err = abs(direct['floor_moment_5g_Nmm'] - res['floor_moment_5g_Nmm']) / res['floor_moment_5g_Nmm']
        self.assertLess(rel_err, 1e-9, (direct['floor_moment_5g_Nmm'], res['floor_moment_5g_Nmm']))
        self.assertLess(abs(direct['upper_mass_g'] - res['upper_mass_g']), 1e-6)


class BoundReports(unittest.TestCase):
    """The FX refresh reports, bound to the current compact manifest (they fail when stale)."""

    @classmethod
    def setUpClass(cls):
        import hashlib
        cls.msha = hashlib.sha256((OUT / 'manifest.json').read_bytes()).hexdigest()

    def bound(self, rel, key='manifest_sha256'):
        r = rd(OUT / rel) if not rel.startswith('..') else rd(CV / rel[3:])
        self.assertEqual(r.get(key), self.msha, rel)
        return r

    def test_fps_integrated_passes(self):
        r = self.bound('../out/fps-service-study/integrated-fps-checks.json', 'mechanical_manifest_sha256')
        self.assertEqual(r['status'], 'geometric_pass_only')
        self.assertFalse([q['item'] for q in r['static_and_carried_checks'] if q['hits']])

    def test_plenum_cavity_row(self):
        r = self.bound('shadow-plenum-checks.json')
        c = {q['id']: q for q in r['checks']}['no_added_material_in_original_cavity']
        self.assertEqual(c['status'], 'pass', c)
        self.assertLess(c['undeclared_mm3'], 1e-5)
        self.assertEqual(c['stale_declarations'], [])
        self.assertEqual(r['summary']['fail'], 0)

    def test_print_checks(self):
        r = self.bound('print-checks.json')
        self.assertTrue(all(v['fail'] == 0 for v in r['summary'].values()), r['failing'])
        tw = {q['part']: q for q in r['results']['thin_wall']}
        self.assertEqual(tw['tub_print_stock']['status'], 'pass')
        cf = {q['id']: q for q in r['results']['critical_features'] if q.get('kind') == 'feature'}
        for k in ('carrier_tie_bar_3', 'tub_stock_tenon_pocket_wall_xm', 'tub_stock_tenon_pocket_wall_xp'):
            self.assertEqual(cf[k]['status'], 'pass', k)
        bc = {q['part']: q for q in r['results']['bed_chamfer']}
        self.assertEqual([e['id'] for e in bc['lens_collar']['exceptions']], ['collar_upper_lug_top_A1'])

    def test_check_scope_path_rows(self):
        r = self.bound('check-scope-checks.json')
        rows = {(q['category'], q['id']): q for q in r['checks']}
        cold, hot = rows[('area_parity', 'cold_path_min_cut')], rows[('area_parity', 'hot_path_min_cut')]
        self.assertEqual(cold['status'], 'pass', cold)
        # Trial4 changes the actual outlet geometry; the 510 mm2 gate and tolerance stay unchanged.
        self.assertEqual(hot['status'],'pass')
        self.assertTrue(hot['empty_bay_bound_reaches_ports'])
        self.assertGreaterEqual(hot['empty_bay_bound_nominal_mm2'],hot['wall_ports_mm2']-PF.TOL_MM2)
        self.assertGreaterEqual(hot['min_cut_mm2'],hot['wall_ports_mm2']-PF.TOL_MM2)
        for v in ('compact-kowa_lm6hc', 'compact-fujinon_hf6xa', 'original-kowa_lm6hc'):
            self.assertTrue(rows[('j4_screen', v)]['valid'], v)
        self.assertEqual(rows[('flow_network', 'baseline_drift')]['status'], 'pass')

    def test_roll_catch_stub_stackup_rows(self):
        import j7_collar_checks as J7
        self.assertAlmostEqual(math.tan(math.radians(math.degrees(math.atan(0.1 / 3.5)))) * 3.5, 0.1, places=9)
        self.assertEqual([c[0] for c in J7.STUB_CASES],
                         ['x+0.1', 'x-0.1', 'film+y0.05', 'tilt_on_joint_edge', 'tilt_on_tenon_top_edge'])
        r = self.bound('verification.json')
        rc = [q for q in r['checks'] if q['category'] == 'roll_catch' and str(q['id']).startswith('stub_')]
        for case in [c[0] for c in J7.STUB_CASES]:
            win = [q for q in rc if q['id'].startswith('stub_%s:window@' % case)]
            self.assertTrue(win, case)
            self.assertTrue(all(q['status'] in ('pass', 'fail') for q in win))


if __name__ == '__main__':
    unittest.main(verbosity=2)

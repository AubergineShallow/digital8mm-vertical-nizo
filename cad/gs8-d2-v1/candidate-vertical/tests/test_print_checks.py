# SPDX-License-Identifier: MIT
"""Print gates of the candidate (review VN-25, fix FP-09).

Run:  run_locked.py -- cad/gs8-d2-v1/candidate-vertical/tests/test_print_checks.py

- Fixtures (manifold3d only): a 40 mm two-ended bridge fails both rules and reports its span; a 20 mm one passes
  both; a region whose two arms need crossing bridge directions passes r7's best-of-8 per pixel but fails the
  single-direction rule; a declared zone over the long bridge passes and is reported as used; a zone nothing
  needs fails as stale.
- Declarations: j4_wing_zones() reproduces r7's declared tongue boxes from r7's TONGUES; J4_TRIAL equals the
  trial_layout keywords model.build() uses; the pose transform matches the manifest poses and r7's convention.
- r7 proof: the upstream r7 tub STL (sha bound by r7 out/print-manifest.json) passes r7 print_overhang AND the
  single-direction rule with r7's 4 declared zones, each used.
- Candidate: out/<variant>/print-checks.json is bound to the current manifest, complete, and its bridge rows are
  reproduced by a fresh computation; for the reviewed manifest 53e668d4 the known defects fail (tub, carrier,
  base_grip, lens_collar) and the J4 wing zones are used with no unsupported pixel under the tongues.
"""
import ast
import hashlib
import json
import sys
import types
import unittest
from pathlib import Path

CV = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CV))
from cv_io import read_text   # noqa: E402
import print_rules as PR      # noqa: E402
import manifold3d as m3       # noqa: E402

CK, ROOT = PR.CK, PR.ROOT
import layout as R7L          # noqa: E402  (r7 layout; PRINT_SUPPORT_ZONES / TONGUES are import-time constants)
VARIANT = 'compact-kowa_lm6hc'
OUT = CV / 'out' / VARIANT
REVIEWED_MANIFEST = '53e668d43847acd1f59d2b559a562476c54a23db0918debd482d632f0e8ceb77'
KNOWN_FAIL = ('base_grip', 'carrier', 'lens_collar', 'tub')
FX = types.SimpleNamespace(PRINT_OVERHANG=dict(R7L.PRINT_OVERHANG), PARTS={'fx': dict(face_down='-Z')})


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def box(x0, x1, y0, y1, z0, z1):
    return m3.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def bridge(gap):
    """Two 10 x 10 x 10 pillars `gap` apart under a 2 mm slab (y 0..10): one two-ended bridge of about `gap`."""
    return box(0, 10, 0, 10, 0, 10) + box(10 + gap, 20 + gap, 0, 10, 0, 10) + box(0, 20 + gap, 0, 10, 10, 12)


def two_arms():
    """Closed block with a roof over two 22 mm wide rooms joined by a 1.6 mm slot: room A runs along x (60 long),
    room B along y (70 long). Each room alone is bridged across its width; no single direction serves both."""
    blk = box(0, 110, 0, 110, 0, 14)
    return blk - (box(10, 70, 10, 32, 2, 12) + box(78, 100, 26, 96, 2, 12) + box(69, 79, 28, 29.6, 2, 12))


def run(man, zones=()):
    return (CK.check_print_overhang(FX, 'fx', man, zones, face_down='-Z'),
            PR.check_bridge_direction(FX, 'fx', man, zones, face_down='-Z'))


class Fixtures(unittest.TestCase):
    def test_long_bridge_fails_both_rules(self):
        r7, sd = run(bridge(40.0))
        self.assertEqual(r7['status'], 'fail')
        self.assertEqual(sd['status'], 'fail')
        self.assertEqual(sd['failing_region_count'], 1)
        span = sd['failing_regions'][0]['min_single_direction_span_mm']
        self.assertGreater(span, 39.0)
        self.assertLess(span, 40.5)

    def test_short_bridge_passes_both_rules(self):
        r7, sd = run(bridge(20.0))
        self.assertEqual((r7['status'], sd['status']), ('pass', 'pass'))
        self.assertGreater(sd['longest_bridge_mm'], 19.0)
        self.assertLessEqual(sd['longest_bridge_mm'], 20.5)
        self.assertEqual(sd['regions_by_span'][0]['direction_deg'], 0.0)

    def test_crossing_directions_pass_r7_but_fail_single_direction(self):
        r7, sd = run(two_arms())
        self.assertEqual(r7['status'], 'pass', r7.get('error'))
        self.assertEqual(sd['status'], 'fail')
        w = sd['failing_regions'][0]
        self.assertGreater(w['bad_area_mm2'], 50.0)
        self.assertGreater(w['min_single_direction_span_mm'], 30.0)

    def test_declared_zone_and_stale_zone(self):
        zone = dict(id='fixture_support', box=(10.0, 50.0, -1.0, 11.0, 9.0, 13.0), why='fixture')
        r7, sd = run(bridge(40.0), [zone])
        self.assertEqual((r7['status'], sd['status']), ('pass', 'pass'), sd.get('error'))
        self.assertGreater(sd['supports_used']['fixture_support'], 100.0)
        stale = dict(id='nowhere', box=(200.0, 210.0, 0.0, 10.0, 0.0, 20.0), why='fixture')
        r7, sd = run(bridge(20.0), [stale])
        self.assertEqual((r7['status'], sd['status']), ('fail', 'fail'))
        self.assertIn('stale', sd['error'])


class Declarations(unittest.TestCase):
    def test_wing_zone_formula_reproduces_r7(self):
        mine = {z['id']: z['box'] for z in PR.j4_wing_zones(R7L.TONGUES)}
        r7 = {z['id']: z['box'] for z in R7L.PRINT_SUPPORT_ZONES['tub'] if z['id'].startswith('tongue_')}
        self.assertEqual(sorted(mine), sorted(r7))
        for k, b in r7.items():
            want = tuple(v for ax in 'xyz' for v in b[ax])
            for u, v in zip(mine[k], want):
                self.assertAlmostEqual(u, v, places=9, msg=k)

    def test_j4_trial_matches_model_build(self):
        tree = ast.parse(read_text(CV / 'model.py'))
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'build')
        call = next(n for n in ast.walk(fn) if isinstance(n, ast.Call) and ast.unparse(n.func) == 'JG.trial_layout')
        self.assertEqual({k.arg: ast.literal_eval(k.value) for k in call.keywords}, PR.J4_TRIAL)

    def test_pose_transform(self):
        man = json.loads(read_text(OUT / 'manifest.json'))
        R, t = PR.pose_transform(man['print_poses']['tub'])
        p = (-80.0, -18.0, -3.0)            # reviewer's map: X = x + 158, Y = 100 - z, Z = y + 35.6
        q = [sum(R[i][k] * p[k] for k in range(3)) + t[i] for i in range(3)]
        for u, v in zip(q, (78.0, 103.0, 17.6)):
            self.assertAlmostEqual(u, v, places=6)
        b = (-83.0, -75.0, -18.5, -12.5, -5.25, 0.2)
        back = PR.unmap_box(PR.map_box(b, R, t), R, t)
        for u, v in zip(back, b):
            self.assertAlmostEqual(u, v, places=2)
        for fd, pose in ((p_['face_down'], p_) for p_ in man['print_poses'].values()):
            R2, _ = PR.pose_transform(pose)
            ref, _ = CK.dc.print_pose_transform(types.SimpleNamespace(BoundingBox=lambda: types.SimpleNamespace(
                xmin=0, xmax=1, ymin=0, ymax=1, zmin=0, zmax=1)), fd)
            self.assertEqual([[round(v) for v in r] for r in R2], [[round(v) for v in r] for r in ref], fd)

    def test_runner_registers_verifier(self):
        self.assertIn("('print',[P/'verify_print_checks.py'])", read_text(CV / 'run_shadow_checks.py'))


class R7Tub(unittest.TestCase):
    def test_r7_tub_passes_both_rules(self):
        import cadquery as cq
        stl = ROOT / 'out' / 'stl' / 'tub.stl'
        pm = json.loads(read_text(ROOT / 'out' / 'print-manifest.json'))
        row = next(r for r in pm['parts'] if r['id'] == 'tub')
        self.assertEqual(sha(stl), row['stl_sha256'])
        shape = cq.importers.importStep(str(ROOT / 'out' / 'step' / 'parts' / 'tub.step')).val()
        R, t = CK.dc.print_pose_transform(shape, row['face_down'])
        lo, hi = PR.stl_bbox(stl)
        for u, v in zip(hi, row['print_bbox_mm']):
            self.assertAlmostEqual(u, v, delta=0.05)
        self.assertLess(max(abs(v) for v in lo), 0.05)
        zones = [dict(z, box=CK.dc.map_box(z['box'], R, t)) for z in R7L.PRINT_SUPPORT_ZONES['tub']]
        man = PR.manifold_from_stl(stl)
        L = types.SimpleNamespace(PRINT_OVERHANG=dict(R7L.PRINT_OVERHANG), PARTS={'tub': dict(face_down='-Y')})
        r7 = CK.check_print_overhang(L, 'tub', man, zones, face_down='-Y')
        sd = PR.check_bridge_direction(L, 'tub', man, zones, face_down='-Y')
        print('r7 tub: r7 rule', r7['status'], r7['longest_bridge_mm'], r7['supports_used'],
              '| single direction', sd['status'], sd['longest_bridge_mm'], sd['supports_used'],
              sd['regions_by_span'][:3], flush=True)
        self.assertEqual(r7['status'], 'pass', r7.get('error'))
        self.assertEqual(sd['status'], 'pass', sd.get('error'))
        self.assertEqual(sorted(sd['supports_used']), sorted(z['id'] for z in zones))
        self.assertLessEqual(sd['longest_bridge_mm'], R7L.PRINT_OVERHANG['bridge_max'])


class Candidate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(read_text(OUT / 'print-checks.json'))
        cls.manifest = json.loads(read_text(OUT / 'manifest.json'))

    def test_report_bound_and_complete(self):
        r = self.report
        self.assertEqual(r['manifest_sha256'], sha(OUT / 'manifest.json'), 'print-checks.json is not current')
        self.assertTrue(r['complete'])
        self.assertEqual(r['verification_source_sha256'], sha(CV / 'verify_print_checks.py'))
        self.assertEqual(r['check_sources']['candidate-vertical/print_rules.py'], sha(CV / 'print_rules.py'))
        parts = sorted(self.manifest['print_poses'])
        for cat in ('print_overhang', 'print_bridge_direction'):
            self.assertEqual(sorted(x['part'] for x in r['results'][cat]), parts, cat)
        self.assertEqual(sorted(x['part'] for x in r['results']['thin_wall']), [p for p in parts if p != PR.GAUGE])
        cov = [x for x in r['results']['critical_features'] if x.get('kind') == 'coverage' and x['part'] == 'carrier']
        self.assertEqual(len(cov), 1)
        gate = [x for x in r['results']['critical_features'] if x.get('id') == 'thin_spot_classification']
        self.assertEqual(len(gate), 1)
        self.assertEqual(gate[0]['unclassified_count'], len(r['results']['unclassified_thin_spots']))

    def test_bridge_rows_reproduce_and_known_defects(self):
        state = {'zones': {}}
        import model  # noqa: F401  (candidate layout state for the tongue rows)
        import j4_trial_geometry as JG
        with JG.trial_layout(model.L, **PR.J4_TRIAL):
            state['zones']['tub'] = PR.j4_wing_zones(model.L.TONGUES)
            # C2 (VN-57): the verifier's candidate_state also declares the base grip pocket-floor zone; reproduce the
            # report rows under the same declarations (tests/test_c2_collar_grip.py shows the grip fails without it)
            state['zones']['base_grip'] = model.grip_support_zones(model.L.TONGUES)
        rows = {x['part']: x for x in self.report['results']['print_bridge_direction']}
        r7rows = {x['part']: x for x in self.report['results']['print_overhang']}
        for pid in KNOWN_FAIL:
            pose = self.manifest['print_poses'][pid]
            R, t = PR.pose_transform(pose)
            zones = [dict(z, box=PR.map_box(z['box'], R, t)) for z in state['zones'].get(pid, [])]
            man = PR.manifold_from_stl(OUT / 'stl' / ('%s.stl' % pid))
            sd = PR.check_bridge_direction(FX, pid, man, zones, face_down=pose['face_down'])
            self.assertEqual((sd['status'], sd.get('failing_region_count')),
                             (rows[pid]['status'], rows[pid].get('failing_region_count')), pid)
            if self.report['manifest_sha256'] == REVIEWED_MANIFEST:
                self.assertEqual(sd['status'], 'fail', pid)
                self.assertEqual(r7rows[pid]['status'], 'fail', pid)
        if self.report['manifest_sha256'] == REVIEWED_MANIFEST:
            tub = r7rows['tub']
            self.assertEqual(sorted(tub['supports_used']), ['tongue_f_minus_y_wing', 'tongue_r_minus_y_wing'])
            for u in tub['unsupported']:      # nothing left under the tongues (assembly z < 0)
                self.assertGreater(u['bbox_assembly'][5], 0.0, u)
            # negative control: r7's own tongue boxes (1.8 mm head) leave the candidate's 2.4 mm head unsupported
            pose = self.manifest['print_poses']['tub']
            R, t = PR.pose_transform(pose)
            r7z = [dict(z, box=CK.dc.map_box(z['box'], R, t)) for z in R7L.PRINT_SUPPORT_ZONES['tub']
                   if z['id'].startswith('tongue_')]
            man = PR.manifold_from_stl(OUT / 'stl' / 'tub.stl')
            ov = PR.annotate_regions(CK.check_print_overhang(FX, 'tub', man, r7z, face_down='-Y'), R, t, 0.2)
            under = [u for u in ov['unsupported'] if u['bbox_assembly'][5] <= 0.0]
            print('candidate tub with r7 tongue boxes: %d unsupported region(s) under the tongues, %.2f mm2'
                  % (len(under), sum(u['area_mm2'] for u in under)), flush=True)
            self.assertEqual(len(under), 2)


if __name__ == '__main__':
    unittest.main(verbosity=2)

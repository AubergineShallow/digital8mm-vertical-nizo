# SPDX-License-Identifier: MIT
"""Innomaker validator regression tests; synthetic fixtures, not assembly approval.

Run:  run_locked.py -- cad/gs8-d2-v1/candidate-vertical/tests/test_innomaker_validation.py

Moved from candidate-vertical/ into tests/ on 2026-10-13 (review A-14) and extended with negative controls:
the Innomaker model delta fails closed when the official model.py changes in a patched region; the verifiers
refuse an output folder inside their input; the gating static targets include the collar screws.
"""
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import numpy as np
CV = Path(__file__).resolve().parents[1]
for _p in (str(CV.parent), str(CV)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
from cv_io import write_text  # noqa: E402
from verify_innomaker_stl import analyze_binary_stl, verify_bindings, sha  # noqa: E402
from verify_innomaker import regularize, uncovered_volume, common_components, insertion_poses, crop_fixed_scene, region_contains_bounds, screen_mover
import cadquery as cq


def tetra(offset=(0,0,0),scale=1):
    v=np.array([[0,0,0],[1,0,0],[0,1,0],[0,0,1]],float)*scale+offset
    return v[[[0,2,1],[0,1,3],[0,3,2],[1,2,3]]]


def binary(tris):
    return bytes(80)+struct.pack('<I',len(tris))+b''.join(struct.pack('<12fH',0,0,0,*tri.reshape(-1),0) for tri in tris)


class BinarySTLTests(unittest.TestCase):
    def run_mesh(self,tri):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'m.stl';p.write_bytes(binary(tri));return analyze_binary_stl(p)
    def test_closed_tetra(self):
        r=self.run_mesh(tetra());self.assertTrue(r['topology_pass']);self.assertAlmostEqual(r['signed_volume_mm3'],1/6)
    def test_open_surface(self):
        r=self.run_mesh(tetra()[:-1]);self.assertFalse(r['topology_pass']);self.assertEqual(r['boundary_edges'],3)
    def test_bad_winding(self):
        t=tetra();t[0]=t[0][::-1];r=self.run_mesh(t);self.assertFalse(r['topology_pass']);self.assertGreater(r['inconsistent_winding_edges'],0)
    def test_inverted_shell(self):
        self.assertFalse(self.run_mesh(tetra()[:,::-1])['topology_pass'])
    def test_duplicate_faces(self):
        t=tetra();r=self.run_mesh(np.concatenate([t,t[:1]]));self.assertEqual(r['duplicate_faces'],1);self.assertFalse(r['topology_pass'])
    def test_vertex_only_nonmanifold(self):
        # Reflection through origin reverses orientation; reverse triangles too.
        t=np.concatenate([tetra(),(-tetra())[:,::-1]])
        r=self.run_mesh(t);self.assertEqual(r['nonmanifold_edges'],0);self.assertEqual(r['invalid_vertex_links'],1);self.assertFalse(r['topology_pass'])
    def test_nonfinite(self):
        t=tetra();t[0,0,0]=np.nan
        with self.assertRaises(ValueError):self.run_mesh(t)
    def test_degenerate_triangle(self):
        t=tetra();t[0,0]=t[0,1];self.assertGreater(self.run_mesh(t)['degenerate_triangles'],0)
    def test_disjoint_shells(self):
        r=self.run_mesh(np.concatenate([tetra(),tetra((3,0,0))]));self.assertTrue(r['topology_pass'])
    def test_bad_length(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'m.stl';p.write_bytes(binary(tetra())[:-1])
            with self.assertRaises(ValueError):analyze_binary_stl(p)


class CADHelperTests(unittest.TestCase):
    def test_regularized_overlap(self):
        a=cq.Solid.makeBox(2,2,2);b=cq.Solid.makeBox(2,2,2,cq.Vector(1,0,0))
        u,cert=regularize([a,b],'test');self.assertEqual(len(u.Solids()),1);self.assertAlmostEqual(u.Volume(),12)
        self.assertLessEqual(cert['input_uncovered_mm3'],1e-6);self.assertEqual(cert['output_pair_overlap_mm3'],0)
    def test_uncovered_box(self):
        a=cq.Solid.makeBox(2,2,2);b=cq.Solid.makeBox(1,2,2)
        self.assertAlmostEqual(uncovered_volume(a,b),4)
    def test_individual_intersections(self):
        a=cq.Solid.makeBox(2,2,2);b=cq.Solid.makeBox(2,2,2,cq.Vector(1,0,0));c=cq.Solid.makeBox(1,1,1,cq.Vector(10,0,0))
        self.assertAlmostEqual(common_components(a,b)['component_overlap_sum_mm3'],4)
        self.assertTrue(common_components(a,c)['clear'])
    def test_padded_crop_retains_intersection(self):
        fixed=cq.Solid.makeBox(5,5,5,cq.Vector(-2,-2,-2))
        moving=cq.Solid.makeBox(1,1,1)
        cropped,cert=crop_fixed_scene({'fixed':fixed},[-.01,1.01,-.01,1.01,-.01,1.01])
        self.assertAlmostEqual(common_components(moving,fixed)['component_overlap_sum_mm3'],common_components(moving,cropped['fixed'])['component_overlap_sum_mm3'])
        self.assertTrue(all(s.isValid() for s in cropped['fixed'].Solids()))
    def test_empty_crop(self):
        fixed=cq.Solid.makeBox(1,1,1,cq.Vector(10,10,10))
        cropped,cert=crop_fixed_scene({'fixed':fixed},[-1,1,-1,1,-1,1])
        self.assertEqual(cropped,{})
    def test_aggregate_small_intersections(self):
        a=cq.Solid.makeBox(4,1,1)
        b=cq.Compound.makeCompound([cq.Solid.makeBox(1.5,1,1),cq.Solid.makeBox(1.5,1,1,cq.Vector(2,0,0))])
        result=common_components(a,b,eps=2.)
        self.assertAlmostEqual(result['component_overlap_sum_mm3'],3.)
        self.assertFalse(result['clear'])
    def test_region_fails_closed_nonfinite_or_inverted(self):
        region=[-1,2,-1,2,-1,2]
        self.assertTrue(region_contains_bounds(region,[0,1,0,1,0,1]))
        self.assertFalse(region_contains_bounds(region,[0,float('nan'),0,1,0,1]))
        self.assertFalse(region_contains_bounds(region,[0,float('inf'),0,1,0,1]))
        self.assertFalse(region_contains_bounds(region,[1,0,0,1,0,1]))
    def test_actual_mover_outside_crop_rejected(self):
        moving=cq.Solid.makeBox(1,1,1)
        poses=[dict(index=0,offset_mm=[2,0,0])]
        with self.assertRaises(ValueError):screen_mover(moving,{},poses,[-.01,1.01,-.01,1.01,-.01,1.01])
    def test_actual_mover_inside_crop_logged(self):
        moving=cq.Solid.makeBox(1,1,1)
        result=screen_mover(moving,{},[dict(index=0,offset_mm=[0,0,0])],[-.01,1.01,-.01,1.01,-.01,1.01])
        self.assertTrue(result[0]['crop_bounds_containment_checked'])
        self.assertEqual(result[0]['status'],'PASS')
    def test_44_unique_poses(self):
        p=insertion_poses();self.assertEqual(len(p),44);self.assertEqual(len({tuple(r['offset_mm']) for r in p}),44)
        self.assertEqual(p[0]['offset_mm'],[-6.2,60.,0.]);self.assertEqual(p[-1]['offset_mm'],[0.,0.,0.])


class HashTests(unittest.TestCase):
    def test_verify_and_reject_mutation(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);s=root/'cad';o=root/'out';s.mkdir();o.mkdir()
            write_text(s/'x.py','x');write_text(o/'x.step','y')
            m={'sources':{'x.py':sha(s/'x.py')},'files':{'x.step':sha(o/'x.step')}}
            self.assertEqual(len(verify_bindings(m,s,o)),2)
            write_text(o/'x.step','changed')
            with self.assertRaises(ValueError):verify_bindings(m,s,o)
    def test_path_escape_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);s=root/'cad';o=root/'out';s.mkdir();o.mkdir()
            m={'sources':{'../../escape':'a'*64},'files':{'x.step':'a'*64}}
            with self.assertRaises(ValueError):verify_bindings(m,s,o)



class InnomakerModelDeltaTests(unittest.TestCase):
    def test_delta_reproduces_delivered_fork_model(self):
        import innomaker_model as IM
        self.assertTrue(IM.delta_matches_delivered_fork())

    def test_official_model_unchanged_by_branch(self):
        import innomaker_model as IM
        # Official manifests bind this exact model.py; the Innomaker delta lives only in innomaker_model.py.
        manifest = json.loads((CV / 'out/compact-kowa_lm6hc/manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['sources']['candidate-vertical/model.py'], sha(IM.OFFICIAL))

    def test_delta_fails_closed_when_official_region_changes(self):
        import innomaker_model as IM
        original = IM.OFFICIAL
        with tempfile.TemporaryDirectory() as d:
            text = original.read_text(encoding='utf-8')
            old = IM.PATCHES[3][0]
            self.assertEqual(text.count(old), 1)
            changed = Path(d) / 'model.py'
            write_text(changed, text.replace(old, old.replace('cuts', 'cutz', 1)))
            IM.OFFICIAL = changed
            try:
                with self.assertRaises(RuntimeError):
                    IM.patched_source()
            finally:
                IM.OFFICIAL = original


class VerifierOutputSeparationTests(unittest.TestCase):
    def test_report_folder_inside_export_rejected(self):
        import verify_innomaker as VI
        import verify_innomaker_stl as VS
        with tempfile.TemporaryDirectory() as d:
            export = Path(d) / 'export'
            export.mkdir()
            for main in (VI.main, VS.main):
                with self.assertRaises(ValueError):
                    main(['--export', str(export), '--out', str(export / 'checks')])
                with self.assertRaises(ValueError):
                    main(['--export', str(export), '--out', str(export)])

    def test_gating_static_targets_include_collar_screws(self):
        import verify_innomaker as VI
        for name in ('s_c1', 's_c2', 's_c3', 's_c4', 'tub', 'panel', 'lens_collar'):
            self.assertIn(name, VI.STATIC_TARGETS)

    def test_nonzero_thread_proxy_is_not_clear(self):
        a = cq.Solid.makeBox(2, 2, 2)
        b = cq.Solid.makeBox(2, 2, 2, cq.Vector(1.9, 0, 0))
        self.assertFalse(common_components(a, b)['clear'])


if __name__=='__main__': unittest.main()

# SPDX-License-Identifier: MIT
"""Pure-numpy guide rasterizer (review VN-12, fix FP-15).

Run:  run_locked.py -- cad/gs8-d2-v1/candidate-vertical/tests/test_raster_fallback.py

- guide/raster_numpy.raster equals a line-by-line scalar port of guide/raster.cpp (raster_reference) bit for bit on
  random scenes with overlapping triangles, exact depth ties (first triangle wins), degenerate and off-image
  triangles, triangles touching the image edge, and every chunking path (tiny chunks, one triangle per chunk,
  a large triangle split into row bands);
- the scalar port itself is pinned to raster.cpp's text (the formulas and constants it transliterates);
- guide/run_with_numpy_raster.py imports the unchanged software_lineart.py without a compiler, routes only the
  raster.so load to the numpy backend, restores subprocess.run and ctypes.CDLL afterwards, and
  software_lineart.render through it equals the scalar port on a small vtk scene;
- software_lineart.py and raster.cpp are not edited (the guide receipt binds them).
Needs numpy and vtk from the pinned CAD environment; no CadQuery.
"""
from pathlib import Path
import ctypes
import json
import subprocess
import sys
import unittest

import numpy as np

CV = Path(__file__).resolve().parents[1]
G = CV / 'guide'
sys.path[:0] = [str(G), str(CV)]
import raster_numpy as RN  # noqa: E402


def scene(seed, n=60, w=37, h=29, ties=True):
    rng = np.random.default_rng(seed)
    p = np.empty((n, 3, 3))
    p[:, :, 0] = rng.uniform(-8, w + 8, (n, 3))
    p[:, :, 1] = rng.uniform(-8, h + 8, (n, 3))
    p[:, :, 2] = rng.choice([1.0, 2.0, 3.0], (n, 3)) if ties else rng.uniform(0, 10, (n, 3))
    p[3] = [[1, 1, 5], [1, 1, 5], [1, 1, 5]]                     # degenerate
    p[4] = [[w + 3, 2, 1], [w + 9, 5, 1], [w + 4, 9, 1]]          # fully off the image
    p[5] = [[0, 0, 0.5], [w - 1, 0, 0.5], [0, h - 1, 0.5]]        # touches the edges
    p[6] = p[5]                                                   # exact duplicate: first must win the tie
    colors = rng.integers(0, 256, (n, 3), dtype=np.uint8)
    colors[6] = 255 - colors[5]
    return p, colors, w, h


def run(fn, p, colors, w, h, **k):
    img = np.full((h, w, 3), 255, dtype=np.uint8)
    z = np.full((h, w), 1e9, dtype=np.float64)
    fn(p, colors, w, h, img, z, **k)
    return img, z


class TestEquivalence(unittest.TestCase):
    def check(self, p, colors, w, h, **k):
        a_img, a_z = run(RN.raster_reference, p, colors, w, h)
        b_img, b_z = run(RN.raster, p, colors, w, h, **k)
        self.assertTrue(np.array_equal(a_img, b_img), 'colour buffer differs')
        self.assertTrue(np.array_equal(a_z, b_z), 'depth buffer differs (bitwise)')
        return a_img, a_z

    def test_random_scenes_all_chunkings(self):
        covered = 0
        for seed in range(6):
            p, c, w, h = scene(seed, ties=seed % 2 == 0)
            for chunk in (RN.CHUNK, 1, 7, 64, 500):
                img, z = self.check(p, c, w, h, chunk=chunk)
            covered += int((z < 1e9).sum())
        self.assertGreater(covered, 1000)

    def test_duplicate_triangle_keeps_first_colour(self):
        p, c, w, h = scene(11)
        img, z = run(RN.raster, p[[5, 6]], c[[5, 6]], w, h)
        hit = z < 1e9
        self.assertTrue(hit.any())
        self.assertTrue((img[hit] == c[5]).all())
        img2, _ = run(RN.raster, p[[6, 5]], c[[6, 5]], w, h)
        self.assertTrue((img2[hit] == c[6]).all())

    def test_large_triangle_row_bands(self):
        p = np.array([[[-5, -5, 2.0], [80, -3, 1.0], [-4, 70, 3.0]], [[10, 10, 0.5], [30, 12, 0.5], [12, 40, 0.5]]])
        c = np.array([[10, 20, 30], [200, 100, 50]], dtype=np.uint8)
        self.check(p, c, 64, 48, chunk=100)       # the first triangle (~3000 candidates) is split into bands
        self.check(p, c, 64, 48)

    def test_running_buffer_is_respected(self):
        p, c, w, h = scene(3)
        img = np.full((h, w, 3), 255, dtype=np.uint8); z = np.full((h, w), 1.5)
        img2, z2 = img.copy(), z.copy()
        RN.raster_reference(p, c, w, h, img, z)
        RN.raster(p, c, w, h, img2, z2, chunk=9)
        self.assertTrue(np.array_equal(img, img2) and np.array_equal(z, z2))

    def test_reference_mirrors_raster_cpp_text(self):
        cpp = (G / 'raster.cpp').read_text(encoding='utf-8')
        for frag in ('fabs(det)<1e-10', 'u< -1e-8||v< -1e-8||u+v>1.00000001', 'z=u*p[2]+v*p[5]+(1-u-v)*p[8]',
                     'if(z<depth[k])', '(x+.5-cx)', '(y+.5-cy)', 'det=(by-cy)*(ax-cx)+(cx-bx)*(ay-cy)'):
            self.assertIn(frag, cpp)


class Cam:
    def project(self, v):
        return np.column_stack((v[:, 0] * 3.0 + 4.0, v[:, 1] * 2.5 + 3.0))

    def depth(self, v):
        return v[:, 2]


def vtk_scene():
    import vtk
    pts = vtk.vtkPoints()
    for xyz in [(0, 0, 1), (9, 0, 1), (0, 9, 1), (2, 1, 2), (11, 3, 0), (3, 10, 4), (0, 0, 1), (9, 0, 1), (0, 9, 1)]:
        pts.InsertNextPoint(*xyz)
    polys = vtk.vtkCellArray()
    for tri in ((0, 1, 2), (3, 4, 5), (6, 7, 8)):
        polys.InsertNextCell(3, tri)
    col = vtk.vtkUnsignedCharArray(); col.SetNumberOfComponents(3)
    for rgb in ((200, 10, 10), (10, 200, 10), (10, 10, 200)):
        col.InsertNextTuple3(*rgb)
    pd = vtk.vtkPolyData(); pd.SetPoints(pts); pd.SetPolys(polys); pd.GetCellData().SetScalars(col)
    return pd


class TestLauncher(unittest.TestCase):
    def test_software_lineart_through_numpy_backend(self):
        real_run, real_cdll = subprocess.run, ctypes.CDLL
        had_lib = (G / 'raster.so').exists()
        import run_with_numpy_raster as L
        sl = L.import_software_lineart()
        self.assertIsInstance(sl.lib, L.NumpyRasterLib)
        self.assertIs(subprocess.run, real_run)
        self.assertIs(ctypes.CDLL, real_cdll)
        self.assertEqual((G / 'raster.so').exists(), had_lib, 'the launcher must not build raster.so')
        self.assertTrue(L._is_raster_build(['g++', '-O3', '-shared', '-fPIC', str(G / 'raster.cpp'), '-o', 'x']))
        self.assertFalse(L._is_raster_build(['git', 'status']))
        pd = vtk_scene(); W, H = 40, 34
        img, _ = sl.render([(pd, (0.5, 0.25, 0.0))], Cam(), W, H)
        img2, z2 = sl.render([(pd, (0.5, 0.25, 0.0))], Cam(), W, H, zbuf=True)
        # the same scene through the scalar port of raster.cpp
        from vtk.util.numpy_support import vtk_to_numpy
        v = vtk_to_numpy(pd.GetPoints().GetData()).astype(float) + np.asarray((0.5, 0.25, 0.0))
        faces = vtk_to_numpy(pd.GetPolys().GetData()).reshape(-1, 4)[:, 1:]
        p = np.column_stack((Cam().project(v), 2000 - Cam().depth(v)))[faces]
        ref_img, ref_z = run(RN.raster_reference, p, vtk_to_numpy(pd.GetCellData().GetScalars()), W, H)
        self.assertTrue(np.array_equal(img, ref_img))
        self.assertTrue(np.array_equal(img2, ref_img) and np.array_equal(z2, ref_z))
        self.assertTrue((ref_img == (200, 10, 10)).all(axis=2).any())    # tie: the first copy of the duplicate wins
        self.assertFalse((ref_img == (10, 10, 200)).all(axis=2).any())

    def test_bound_guide_sources_unchanged(self):
        rec = json.loads((G / 'out-concealed-vents/guide-receipt.json').read_text(encoding='utf-8'))
        import hashlib
        for name in ('software_lineart.py', 'raster.cpp'):
            key = next(k for k in rec['sources'] if k.endswith('guide/' + name))
            self.assertEqual(hashlib.sha256((G / name).read_bytes()).hexdigest(), rec['sources'][key], name)


if __name__ == '__main__':
    unittest.main()

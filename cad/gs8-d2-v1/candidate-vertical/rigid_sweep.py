# SPDX-License-Identifier: MIT
"""Rigid translation sweeps with the same sampling, crop and Pi handling as verify_candidate.py's motion rows
(FP-12, VN-29). Used by verify_microsd_service.py for the dog-leg window probes and the rejected straight path, so
those diagnostics see exactly the obstacle sets steps.py derives for the rigid batch row. Run under run_locked.py."""
import hashlib
import math
import sys
from pathlib import Path

import cadquery as cq
import numpy as np
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.gp import gp_Pnt
from OCP.TopAbs import TopAbs_IN

ROOT = Path(__file__).resolve().parent
HIT_MM3 = .05          # verify_candidate.py motion threshold


def bb(s):
    b = s.BoundingBox()
    return [b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax]


def broad(a, b):
    return all(min(a[i + 1], b[i + 1]) - max(a[i], b[i]) > 1e-7 for i in (0, 2, 4))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


class Scene:
    """Manifest-bound saved STEPs (pi5 as verify_candidate's component set; its STEP is hash-checked only)."""

    def __init__(self, out, meta, names):
        self.rows = {r['id']: r for r in meta['rows']}
        self.shapes, self.bindings = {}, {}
        for n in sorted(set(names)):
            p = out / 'step' / ('%s.step' % n)
            h = sha(p)
            ok = h == meta['files'].get('step/%s.step' % n)
            self.bindings[n] = dict(step_sha256=h, manifest_file_binding=ok)
            if not ok:
                raise ValueError('STEP binding mismatch: ' + n)
            if n != 'pi5':
                self.shapes[n] = cq.importers.importStep(str(p)).val()
        self.pi = None
        if 'pi5' in names:
            sys.path.insert(0, str(ROOT.parent))
            import layout as PiL                  # noqa: E402  same construction as verify_candidate.py
            import official_pi5_assembly as PiA   # noqa: E402
            self.pi = PiA.build_parts(PiL)
            self.pi_bounds = {k: bb(q) for k, q in self.pi.items()}
        self.faces, self.cls = {}, {}

    def possible(self, key, shape, b):
        if key not in self.faces:
            self.faces[key] = np.array([bb(f) for f in shape.Faces()])
        f = self.faces[key]
        mask = np.ones(len(f), dtype=bool)
        for i in (0, 2, 4):
            mask &= (np.minimum(f[:, i + 1], b[i + 1]) - np.maximum(f[:, i], b[i])) >= -1e-7
        if mask.any():
            return True
        if key not in self.cls:
            self.cls[key] = [BRepClass3d_SolidClassifier(q.wrapped) for q in shape.Solids()]
        p = gp_Pnt(*[(b[i] + b[i + 1]) / 2 for i in (0, 2, 4)])
        for c in self.cls[key]:
            c.Perform(p, 1e-7)
            if c.State() == TopAbs_IN or c.IsOnAFace():
                return True
        return False

    def overlap(self, moved, fixed, obstacle, key):
        bm = bb(moved)
        if fixed != 'pi5':
            return moved.intersect(obstacle).Volume() if self.possible(key, obstacle, bm) else 0.0
        v = 0.0
        for cn, comp in self.pi.items():
            if not broad(bm, self.pi_bounds[cn]) or not self.possible('pi/' + cn, comp, bm):
                continue
            v += moved.intersect(comp).Volume()   # components may overlap: an upper bound of the union volume
        return v

    def sweep(self, moving, fixed, knots, step=2.0):
        """verify_candidate.py motion loop: samples every `step` mm along the knot polyline (plus the last knot),
        printed obstacles cropped to the translated-knot envelope + 0.01 mm. -> (worst_mm3, hits, samples)."""
        pts = []
        for u, v in zip(knots, knots[1:]):
            n = max(1, math.ceil(math.dist(u, v) / step))
            pts += [[u[j] + (v[j] - u[j]) * i / n for j in range(3)] for i in range(n)]
        pts.append(list(knots[-1]))
        regions = {}
        for name in moving:
            b = bb(self.shapes[name])
            env = []
            for i in range(3):
                env += [b[2 * i] + min(t[i] for t in knots) - .01, b[2 * i + 1] + max(t[i] for t in knots) + .01]
            for fn in fixed:
                if fn == 'pi5':
                    regions[name, fn] = 'pi-components'
                elif not broad(env, self.rows[fn]['bbox_mm']):
                    regions[name, fn] = None
                elif self.rows[fn]['kind'] != 'printed':
                    regions[name, fn] = self.shapes.get(fn)
                else:
                    box = cq.Solid.makeBox(env[1] - env[0], env[3] - env[2], env[5] - env[4],
                                           cq.Vector(env[0], env[2], env[4]))
                    crop = self.shapes[fn].intersect(box)
                    regions[name, fn] = crop if crop.Solids() and crop.Volume() > 1e-10 else None
        worst, hits = 0.0, []
        for t in pts:
            for name in moving:
                sm = self.shapes[name].translate(cq.Vector(*t))
                bm = bb(sm)
                for fn in fixed:
                    if not broad(bm, self.rows[fn]['bbox_mm']):
                        continue
                    if fn != 'pi5' and regions[name, fn] is None:
                        continue
                    v = self.overlap(sm, fn, regions[name, fn], (tuple(map(tuple, knots)), name, fn))
                    worst = max(worst, v)
                    if v > HIT_MM3:
                        hits.append(dict(moving=name, fixed=fn, offset=[round(c, 6) for c in t], overlap_mm3=v))
        return worst, hits, len(pts)

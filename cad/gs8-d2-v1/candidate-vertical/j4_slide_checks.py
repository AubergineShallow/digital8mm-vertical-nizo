# SPDX-License-Identifier: MIT
"""J4 keyhole slide clearance rows for the main audit (review 2026-10-10 VN-57, fix C2 / FP-11e).

verify_candidate.py runs them behind want('clearance') on the manifest-bound tub and base_grip STEPs, in the
candidate layout (model.py's import-time edits + JG.trial_layout(lip 2.4, head 2.4), exactly as model.build).
Two kinds of row, category 'clearance':
- 'J4 <tongue> in base pocket': r7 checks.check_clearances (../checks.py, read-only, unchanged) for the two J4
  zones of r7 checks.clearance_zones (pocket box +1 in x and y, z pocket floor -0.5 .. -0.05), stated L.FDM SLIDE,
  pass at min gap >= 0.9 x stated. The other r7 zones name parts the candidate does not have (hood, keeper,
  plunger) or are j7_float's (J7); they are not reported here.
- 'J4 <tongue> slide path': the candidate's own sweep of the same relative motion as r7 INSERTIONS base_on
  (tongue drops through the window BASE_SLIDE ahead of its seat, then slides -X onto it): the tub material inside
  the r7 zone (the tongue) is moved (+s, 0, 0) for s = 0 .. BASE_SLIDE and (BASE_SLIDE, 0, dz) for dz up to the
  head bottom clearing the base top, against the base grip near the keyhole; pass when no sample overlaps and the
  smallest gap is >= 0.9 x SLIDE (the r7 clearance need). Step SLIDE_STEP mm.
No measurement: print sag, support scars on the pocket floor and the PT lock stay physical gates.
This module is CAD-free at import.
"""
import hashlib
from pathlib import Path

CV = Path(__file__).resolve().parent
CATEGORY = 'clearance'
SLIDE_STEP = 0.5
J4_TRIAL = dict(lip=2.4, head=2.4)


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rows(shapes, step=SLIDE_STEP):
    """[dict(category, id, ok, **fields)] from shapes {'tub': Shape, 'base_grip': Shape} (assembly frame)."""
    import sys
    for p in (str(CV.parent), str(CV), str(CV / 'structural-review')):
        if p not in sys.path:
            sys.path.insert(0, p)
    import cadquery as cq
    import checks as CK
    import j4_trial_geometry as JG
    import model as M
    L = M.L
    V = cq.Vector
    out = []
    tub, grip = shapes['tub'], shapes['base_grip']
    srcs = dict(r7_checks_sha256=_sha(CV.parent / 'checks.py'), j4_slide_checks_sha256=_sha(Path(__file__)))
    with JG.trial_layout(L, **J4_TRIAL):
        rr = {'tub': dict(shape=tub), 'base_grip': dict(shape=grip)}
        for r in CK.check_clearances(L, rr):
            if not r['check'].startswith('J4 '):
                continue
            ok = r['status'] == 'pass'
            out.append(dict(category=CATEGORY, id=r['check'], ok=ok,
                            **{k: v for k, v in r.items() if k not in ('status', 'check')},
                            rule='r7 checks.check_clearances J4 zone: min gap >= 0.9 x FDM SLIDE', **srcs))
        sl = L.FDM['SLIDE']
        need = 0.9 * sl
        for t in L.TONGUES:
            p = t['base_pocket']
            zb = (p['x'][0] - 1, p['x'][1] + 1, p['y'][0] - 1, p['y'][1] + 1, p['z'][0] - 0.5, -0.05)
            zone = cq.Solid.makeBox(zb[1] - zb[0], zb[3] - zb[2], zb[5] - zb[4], V(zb[0], zb[2], zb[4]))
            tongue = tub.intersect(zone)
            near = grip.intersect(cq.Solid.makeBox(zb[1] - zb[0] + L.BASE_SLIDE + 4, zb[3] - zb[2] + 2, 7.5,
                                                   V(zb[0] - 2, zb[2] - 1, zb[4] - 1.0)))
            head_bottom = t['head']['z'][0]
            n = int(round(L.BASE_SLIDE / step))
            moves = [(i * step, 0.0) for i in range(n + 1)]
            nz = int(-head_bottom / step) + 2           # head bottom clears the base top (z 0) + one step
            moves += [(L.BASE_SLIDE, j * step) for j in range(1, nz + 1)]
            worst, worst_at, overlaps = None, None, []
            for dx, dz in moves:
                m = tongue.translate(V(dx, 0, dz))
                v, _ = CK.common(m, near)
                if v > 1e-6:
                    overlaps.append(dict(dx=dx, dz=dz, overlap_mm3=CK._r(v, 4)))
                    continue
                d = m.distance(near)
                if worst is None or d < worst:
                    worst, worst_at = d, (dx, dz)
            ok = not overlaps and worst is not None and worst >= need - 1e-6
            out.append(dict(category=CATEGORY, id='J4 %s slide path' % t['id'], ok=ok, pair=['tub', 'base_grip'],
                            samples=len(moves), step_mm=step, slide_mm=L.BASE_SLIDE, min_gap=CK._r(worst),
                            min_gap_at=dict(dx=worst_at[0], dz=worst_at[1]) if worst_at else None, overlaps=overlaps,
                            stated=sl, need=CK._r(need), tongue_volume_mm3=CK._r(tongue.Volume(), 3),
                            rule='tongue (tub inside the r7 J4 zone) moved +X 0..BASE_SLIDE then up through the '
                                 'window until the head clears the base top: no overlap, min gap >= 0.9 x SLIDE',
                            **srcs))
    return out

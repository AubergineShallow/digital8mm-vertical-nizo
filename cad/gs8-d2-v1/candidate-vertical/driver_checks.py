# SPDX-License-Identifier: MIT
"""Straight-driver audit of the vertical candidate (review 2026-10-10, VN-23; fix FP-07).

Rows for the main audit (verify_candidate.py, categories `driver`, `service_driver`, `driver_coverage`), one row per
(screw, op). Port of r7 checks.check_driver (../checks.py, read-only, byte-identical to upstream r7) and of r7's
service-driver use of it (check_removals unscrew rows and layout.SERVICE_DRIVER):
- tool: r7 layout.DRIVER, the largest admitted straight PH1 driver. The bit (dia 6.5 x 40) runs from the head
  bearing face back along the screw axis, so it covers the head zone and a counterbore narrower than the bit fails;
  the handle (dia 30 x 100) follows behind the bit;
- a hit is an exact OCP boolean common above r7 checks.VOL_TOL (0.05 mm3) with any solid present at that moment;
- nearest gaps as r7: the bit behind the head (from head_h + 0.1 back) and the handle, to the nearest present solid
  whose box lies within 15 mm of the tool box.
Differences from r7, each stricter, never looser:
- contexts come from the assembly-state model steps.driver_contexts() (FP-05): build = the body at the end of the op
  that tightens the screw (other screws, tools such as the centring gauge, and the strap at p_grip included; r7 left
  every s_* screw out of its audit sets); service = the body before the op that loosens or removes it. A context id
  that is not loaded fails the row unless steps.OPTIONAL names it (never a partial set);
- a boolean or distance that raises or returns a non-finite value fails the row (r7 checks.common() returns NaN,
  which compares False with the tolerance: a silent pass);
- multi-solid shapes (the detailed pi5 assembly, any compound) are tested solid by solid and the volumes add
  (overlaps between solids of one part count twice: conservative);
- the screw pose (head point, advance axis) is not typed: it is derived from the screw's own manifest-bound STEP
  solid (bbox long axis; head end = the end with the larger cross-section; head top = the extreme planar face) and
  the derived head height is verified with two cross-section slabs against r7 PT / M3 head_d. A screw whose pose
  cannot be derived fails.
Coverage (`driver_coverage/screws`): every manifest hardware row whose source names a PT or M3 screw is in
steps.SCREW_IDS, every SCREW_IDS id is a manifest row, and each has at least one build and one service row.
Nuts (fps_nut, power_nut_reserve) are driven with a deep socket whose envelope is unknown until receipt (VN-46);
they are not audited here and no socket envelope is invented.
"""
import hashlib
import math
import sys
from pathlib import Path

CV = Path(__file__).resolve().parent
for _p in (str(CV.parent), str(CV)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import checks as CK          # noqa: E402  r7 checks.py (read-only): VOL_TOL, bb_tuple, bb_overlap, _r
import d2_common as dc       # noqa: E402  r7 cyl_along (read-only)
import layout as R7L         # noqa: E402  r7 DRIVER / PT / M3 (import-time constants, read-only)
import steps as ST           # noqa: E402  FP-05 assembly-state model

CATEGORIES = ('driver', 'service_driver', 'driver_coverage')
NEAR_MM = 15.0               # r7 check_driver nearest-solid search margin
HEAD_D_TOL = 0.05            # mm: measured head disc vs r7 head_d
SLAB = (0.1, 0.4)            # mm: cross-section slabs this far either side of the derived head bearing face
END_SLAB = (1.5, 1.8)        # mm in from each end: head end vs tip end (below the deepest PH recess, 1.2 mm)
METHOD = ('r7 check_driver port: exact OCP boolean per solid, tol %.2f mm3; bit dia %.1f x %.0f from the head bearing '
          'face back, handle dia %.0f x %.0f behind it; contexts from steps.driver_contexts()'
          % (CK.VOL_TOL, R7L.DRIVER['bit_d'], R7L.DRIVER['bit_len'], R7L.DRIVER['handle_d'], R7L.DRIVER['handle_len']))


def source_sha256():
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def screw_kind(row):
    """'PT' | 'M3' | None from a manifest row's `source` text (model.py writes 'PT 3x12 PH1' / 'M3 x 10 ISO 7045 ...')."""
    src = (row or {}).get('source') or ''
    return 'PT' if src.startswith('PT ') else ('M3' if src.startswith('M3 ') else None)


def head_spec(kind, L=R7L):
    return L.PT if kind == 'PT' else L.M3


def _solids(shape):
    try:
        s = list(shape.Solids())
    except Exception:  # noqa: BLE001  (not a cadquery shape: test it whole)
        s = []
    return s or [shape]


def _bb(shape):
    return CK.bb_tuple(shape)


def _slab_d(shape, origin, axis, t0, t1, r=20.0):
    """Equivalent disc diameter of `shape` between t0 and t1 along axis from origin (exact boolean volume / length)."""
    tool = dc.cyl_along(r, t0, t1, origin, axis)
    v = sum(s.intersect(tool).Volume() for s in _solids(shape) if CK.bb_overlap(_bb(s), _bb(tool)))
    return 2.0 * math.sqrt(max(v, 0.0) / (t1 - t0) / math.pi)


def derive_pose(shape, kind, L=R7L):
    """Head point (head bearing face on the axis) and advance axis of one axis-aligned screw solid.
    -> dict(head_point, axis, head_top, length, head_d_above, d_below, errors)."""
    err = []
    if kind not in ('PT', 'M3'):
        return dict(head_point=None, axis=None, errors=['not a PT or M3 screw row (kind %r)' % (kind,)])
    spec = head_spec(kind, L)
    b = _bb(shape)
    ext = [b[1] - b[0], b[3] - b[2], b[5] - b[4]]
    i = max(range(3), key=lambda k: ext[k])
    others = [ext[k] for k in range(3) if k != i]
    if ext[i] - max(others) < 1.0:
        return dict(head_point=None, axis=None, errors=['ambiguous long axis, extents %s' % [round(e, 3) for e in ext]])
    centre = [(b[2 * k] + b[2 * k + 1]) / 2.0 for k in range(3)]
    unit = [1.0 if k == i else 0.0 for k in range(3)]
    lo, hi = list(centre), list(centre)
    lo[i], hi[i] = b[2 * i], b[2 * i + 1]
    a_lo = _slab_d(shape, lo, unit, END_SLAB[0], END_SLAB[1])
    a_hi = _slab_d(shape, hi, [-u for u in unit], END_SLAB[0], END_SLAB[1])
    if max(a_lo, a_hi) < 1.2 * min(a_lo, a_hi):
        return dict(head_point=None, axis=None, errors=['head end not distinct: end diameters %.3f / %.3f' % (a_lo, a_hi)])
    head_high = a_hi > a_lo
    axis = tuple((-u if head_high else u) + 0.0 for u in unit)      # + 0.0: no -0.0 in the record
    tops = []                                      # planar faces normal to the axis: exact head-top coordinate
    for f in shape.Faces():
        if f.geomType() != 'PLANE':
            continue
        n = f.normalAt()
        if abs((n.x, n.y, n.z)[i]) > 0.999:
            tops.append(f.Center().toTuple()[i])
    if not tops:
        return dict(head_point=None, axis=None, errors=['no planar face normal to the screw axis'])
    top = max(tops) if head_high else min(tops)
    if abs(top - (b[2 * i + 1] if head_high else b[2 * i])) > 0.01:
        err.append('extreme planar face %.4f is not the bbox end' % top)
    head_top = list(centre)
    head_top[i] = top
    hp = tuple(head_top[k] + axis[k] * spec['head_h'] for k in range(3))
    d_above = _slab_d(shape, hp, axis, -SLAB[1], -SLAB[0])
    d_below = _slab_d(shape, hp, axis, SLAB[0], SLAB[1])
    if abs(d_above - spec['head_d']) > HEAD_D_TOL:
        err.append('head disc %.3f mm at the derived head zone, r7 %s head_d %.2f' % (d_above, kind, spec['head_d']))
    if abs(d_below - spec['head_d']) <= HEAD_D_TOL:
        err.append('head continues past the derived bearing face (head_h %.2f does not fit the solid)' % spec['head_h'])
    return dict(head_point=[CK._r(x, 4) for x in hp], axis=list(axis), head_top=[CK._r(x, 4) for x in head_top],
                length=CK._r(ext[i], 4), head_d_above=CK._r(d_above, 3), d_below=CK._r(d_below, 3),
                head_h=spec['head_h'], head_d=spec['head_d'], errors=err)


def audit_screw(screw_id, pose, context, shapes, L=R7L):
    """r7 check_driver for one screw at one moment. pose from derive_pose; context = ids present (the screw itself
    excluded); shapes: id -> cadquery shape. -> dict(hits, nearest, errors)."""
    D = L.DRIVER
    hp, ax = pose['head_point'], pose['axis']
    bit = dc.cyl_along(D['bit_d'] / 2, -D['bit_len'], 0.0, hp, ax)
    handle = dc.cyl_along(D['handle_d'] / 2, -D['bit_len'] - D['handle_len'], -D['bit_len'], hp, ax)
    bit_back = dc.cyl_along(D['bit_d'] / 2, -D['bit_len'], -pose['head_h'] - 0.1, hp, ax)   # behind the head
    hits, errors = [], []
    for pid in context:
        shp = shapes.get(pid)
        if shp is None:
            errors.append('context part %s has no shape' % pid)
            continue
        for nm, tool in (('bit', bit), ('handle', handle)):
            tb, v, bad = _bb(tool), 0.0, None
            for s in _solids(shp):
                if not CK.bb_overlap(_bb(s), tb):
                    continue
                try:
                    vv = float(s.intersect(tool).Volume())
                except Exception as e:  # noqa: BLE001
                    bad = 'boolean %s/%s raised %s' % (pid, nm, type(e).__name__)
                    break
                if not math.isfinite(vv):
                    bad = 'boolean %s/%s gave a non-finite volume' % (pid, nm)
                    break
                v += vv
            if bad:
                errors.append(bad)
            elif v > CK.VOL_TOL:
                hits.append(dict(part=pid, tool=nm, volume_mm3=CK._r(v, 3)))
    nearest = {}
    for nm, tool in (('bit', bit_back), ('handle', handle)):
        tb, cand, best = _bb(tool), [], None
        for order, pid in enumerate(context):
            shp = shapes.get(pid)
            if shp is None:
                continue
            for s in _solids(shp):
                sb = _bb(s)
                if CK.bb_overlap(sb, tb, NEAR_MM):
                    cand.append((_bb_gap(sb, tb), order, pid, s))
        # Exact branch and bound: the true distance is never below the box gap, so solids whose box gap exceeds the
        # best distance found cannot be nearest. Ties go to the earlier context id, as in r7's strict '<' scan.
        for lb, order, pid, s in sorted(cand, key=lambda c: (c[0], c[1])):
            if best is not None and (lb > best[0] or (lb == best[0] and order >= best[2])):
                continue
            try:
                d = float(s.distance(tool))
            except Exception as e:  # noqa: BLE001
                errors.append('distance %s/%s raised %s' % (pid, nm, type(e).__name__))
                continue
            if not math.isfinite(d):
                errors.append('distance %s/%s non-finite' % (pid, nm))
                continue
            if best is None or d < best[0] or (d == best[0] and order < best[2]):
                best = (d, pid, order)
        nearest[nm] = None if best is None else dict(gap=CK._r(best[0], 2), part=best[1])
    return dict(hits=hits, nearest=nearest, errors=errors)


def _bb_gap(a, b):
    """Euclidean gap between two boxes (x0, x1, y0, y1, z0, z1); 0 when they touch or overlap."""
    return math.sqrt(sum(max(a[2 * k] - b[2 * k + 1], b[2 * k] - a[2 * k + 1], 0.0) ** 2 for k in range(3)))


def screw_contexts(available, steps=ST):
    """steps.driver_contexts() screw rows with the ids each context lacks in `available`: -> [dict(row, missing)]."""
    full = steps.driver_contexts(None)
    have = steps.driver_contexts(available)
    out = []
    for f, h in zip(full, have):
        if f['kind'] != 'screw':
            continue
        out.append(dict(h, missing=sorted(set(f['context']) - set(h['context']))))
    return out


def coverage_row(manifest_rows, rows, steps=ST):
    screwlike = sorted(k for k, r in manifest_rows.items() if r.get('kind') == 'hardware' and screw_kind(r))
    ids = set(steps.SCREW_IDS)
    phases = {(r['screw'], r['phase']) for r in rows}
    gaps = dict(screws_not_in_state_model=sorted(set(screwlike) - ids),
                state_model_screws_not_in_manifest=sorted(ids - set(manifest_rows)),
                no_build_row=sorted(s for s in ids if (s, 'build') not in phases),
                no_service_row=sorted(s for s in ids if (s, 'service') not in phases))
    return dict(category='driver_coverage', id='screws', ok=not any(gaps.values()), screws=sorted(ids),
                manifest_screw_rows=screwlike, rows=len(rows), **gaps, driver_source_sha256=source_sha256(),
                nuts_not_audited=sorted(steps.NUT_IDS),
                note='nuts are driven with a deep socket whose envelope is a receipt gate (VN-46); none invented')


def driver_rows(shapes, manifest_rows, available, L=R7L, steps=ST):
    """All driver rows for one variant: shapes id -> cadquery shape (manifest rows plus loaded tools), manifest_rows
    id -> manifest row, available = ids the verifier loaded. Each row: dict(category, id, ok, **evidence)."""
    poses = {}
    for sid in sorted(steps.SCREW_IDS):
        if sid not in shapes or sid not in manifest_rows:
            poses[sid] = dict(head_point=None, axis=None, errors=['screw %s is not a loaded manifest row' % sid])
            continue
        try:
            poses[sid] = derive_pose(shapes[sid], screw_kind(manifest_rows[sid]), L)
        except Exception as e:  # noqa: BLE001
            poses[sid] = dict(head_point=None, axis=None, errors=['pose derivation raised %s: %s' % (type(e).__name__, e)])
    out = []
    D = L.DRIVER
    for c in screw_contexts(available, steps):
        sid = c['fastener']
        pose = poses.get(sid) or dict(head_point=None, axis=None, errors=['not in steps.SCREW_IDS'])
        errors = ['pose: ' + e for e in pose['errors']]
        errors += ['context id %s not loaded' % i for i in c['missing'] if i not in steps.OPTIONAL]
        res = dict(hits=[], nearest={}, errors=[])
        if pose.get('head_point') is not None:
            res = audit_screw(sid, pose, c['context'], shapes, L)
        errors += res['errors']
        out.append(dict(category='driver' if c['phase'] == 'build' else 'service_driver', id='%s@%s' % (sid, c['op']),
                        ok=not res['hits'] and not errors, screw=sid,
                        kind=screw_kind(manifest_rows.get(sid)), phase=c['phase'], route=c['route'], op=c['op'],
                        step=c['step'], where=c['where'], tool_text=c['tool'], bit=[D['bit_d'], D['bit_len']],
                        handle=[D['handle_d'], D['handle_len']], axis=pose.get('axis'),
                        head_point=pose.get('head_point'), pose=pose, audit_set=c['context'],
                        optional_absent=[i for i in c['missing'] if i in steps.OPTIONAL], hits=res['hits'],
                        nearest=res['nearest'], errors=errors, method=METHOD))
    out.append(coverage_row(manifest_rows, out, steps))
    return out

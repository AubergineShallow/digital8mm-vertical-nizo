# SPDX-License-Identifier: MIT
"""Print checks for the vertical candidate (review VN-25, fix FP-09).

r7's computed print gates are reused unchanged from ../checks.py (imported read-only, never copied):
check_print_overhang (r7 rule: per pixel, an anchored bridge in ANY of 8 directions), thin_wall and
check_critical_features. This module adds what the candidate needs around them:

- check_bridge_direction: the stricter per-region rule. A slicer lays ONE bridge direction per connected
  bridge region, so for every unsupported region of every layer one raster direction is chosen (of the same
  8) and every pixel that is not a short overhang (<= cantilever_max from supported material) must lie on a
  run in THAT direction that is anchored at both ends (or anchor + enclosed hole, as r7) and is at most
  bridge_max long. r7's best-of-8 per pixel accepts a roof whose pixels each find some short run in some
  direction (VN-25: the plenum bay roofs pass r7 at exactly 30.0 mm); this rule does not.
- declared support zones for the candidate (the J4 T-tongue -Y wings), derived from the same layout rows the
  model builds the tongues from, in the assembly frame, mapped to the print frame with the manifest pose.
- candidate loaded zones for thin_wall (screw bosses, insert bosses, catches), from the model's own numbers.
- a layout view for check_critical_features: the candidate's printed parts as PARTS, the carrier and the bonded
  tab-catch insert added to LOAD_BEARING_PARTS, and the candidate's CRITICAL_FEATURES / CRITICAL_JOINTS /
  NONSTRUCTURAL_EXCEPTIONS from critical_features_vertical.py (phase 2, lane CF: every r7 entry kept, re-nominated
  with the same limit, or retired with a reason; carrier and other candidate entries added; fork joints by r7's
  own supersede rule).

Nothing here weakens an r7 rule: same layer, 45 deg allowance, cantilever 1.0, bridge 30, edge_tol 0.3,
px 0.1, 8 directions, min_area 0.05, nozzle sliver filter.
"""
import copy
import math
import sys
from pathlib import Path

import numpy as np

CV = Path(__file__).resolve().parent
ROOT = CV.parent
for _p in (str(ROOT), str(CV)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import checks as CK          # noqa: E402  r7 checks.py (read-only)
import d2_common as dc       # noqa: E402

# J4 coordinated joint of the candidate: model.build() runs _build inside JG.trial_layout(L, lip=2.4, head=2.4).
# tests/test_print_checks.py asserts these equal the keywords of that call, so the zones cannot drift from it.
J4_TRIAL = dict(lip=2.4, head=2.4)
GAUGE = 'centring_gauge'
# FX (verifier T2 major): the tub prints as the tub stock (model.tub_print_parts: bonded +Y stub removed, tenon pocket
# open); thin_wall and critical_features also run on that stock under this part id (same PARTS row and loaded boxes as
# the tub), so the pocket walls the bonded STEP fills with adhesive are graded.
TUB_STOCK = 'tub_print_stock'
# FX (verifier T1 minor): written bed_chamfer exceptions, per part, assembly-frame boxes mapped by the print pose. Only
# the unchamfered outline inside a box is excepted, at most max_mm of it; an exception that excepts nothing is stale
# (fails). One entry: the collar's upper-lug top edge on the bed face, left sharp on purpose by r7
# (printed_collar._outer_bed_chamfer, review A1): the s_c4 washer footprint (r 3.9) reaches the front face there, so
# a 0.6 mm chamfer would leave part of it unsupported (lens_clamp washer_flat_support; C2 computed 1.69 mm2); the tie
# is tested in tests/test_fx_fixup.py.
BED_CHAMFER_EXCEPTIONS = {
    'lens_collar': [dict(id='collar_upper_lug_top_A1', box=(7.4, 9.4, -31.4, -21.8, 64.8, 66.8), max_mm=8.5,
                         why='r7 review A1: the upper lug top edge stays sharp to keep the s_c4 washer bearing plane',
                         tie='lens_clamp washer_flat_support (j7_collar_checks)')]}


# ------------------------------------------------------------------------------------------- frames
def pose_transform(pose):
    """Manifest print pose (rotation_axis, angle_deg, translation_mm; export_candidate.print_pose) -> (R, t) with
    p_print = R p + t. Quarter turns only, so cos/sin are rounded and a box maps to a box."""
    ax = np.asarray(pose['rotation_axis'], float)
    ax = ax / np.linalg.norm(ax)
    a = math.radians(float(pose['angle_deg']))
    c, s = round(math.cos(a)), round(math.sin(a))
    if abs(c) + abs(s) != 1:
        raise ValueError('print pose is not a quarter turn: %r' % pose)
    K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
    R = np.eye(3) * c + s * K + (1 - c) * np.outer(ax, ax)
    return np.round(R).tolist(), [float(v) for v in pose['translation_mm']]


def map_box(box, R, t):
    """Assembly-frame box (x0, x1, y0, y1, z0, z1) or B dict -> print-frame (x0, x1, y0, y1, z0, z1)."""
    b = box if isinstance(box, dict) else dict(x=box[0:2], y=box[2:4], z=box[4:6])
    return dc.map_box(b, R, t)


def unmap_box(pbox, R, t):
    """Print-frame (x0, x1, y0, y1, z0, z1) -> assembly-frame box (inverse of map_box; R orthonormal)."""
    Ri = np.asarray(R, float).T
    tt = np.asarray(t, float)
    pts = [Ri @ (np.array([x, y, z]) - tt) for x in pbox[0:2] for y in pbox[2:4] for z in pbox[4:6]]
    P = np.array(pts)
    return [round(float(v), 2) for i in range(3) for v in (P[:, i].min(), P[:, i].max())]


def annotate_regions(row, R, t, h):
    """Add bbox_assembly to every region record of a print row (r7 bbox is print x0, y0, x1, y1 at layer z)."""
    for key in ('unsupported', 'bridges', 'failing_regions', 'regions_by_span'):
        recs = row.get(key)
        for u in recs if isinstance(recs, list) else []:
            bb, z = u.get('bbox'), u.get('z')
            if bb is None or z is None:
                continue
            u['bbox_assembly'] = unmap_box((bb[0], bb[2], bb[1], bb[3], z, z + h), R, t)
    return row


# ------------------------------------------------------------------------------------------- declarations
def j4_wing_zones(tongues):
    """Paint-on support zones under the -Y wing of every J4 T-tongue head (assembly frame). Same construction as
    r7 layout._tw (head x +-0.5, y from the head -Y end -0.5 to the neck -Y end +0.5, z from the head bottom -0.2
    to the floor +0.2), but read from the tongue rows themselves, so the candidate's taller 2.4 mm head (and its
    missing -Y chamfer, model.make_tub chamfer_minus_y=False) is covered. For r7's TONGUES it reproduces r7's
    declared boxes exactly (tests)."""
    out = []
    for t in tongues:
        hd, nk = t['head'], t['neck']
        out.append(dict(id='tongue_%s_minus_y_wing' % t['id'][-1], kind='support',
                        box=(hd['x'][0] - 0.5, hd['x'][1] + 0.5, hd['y'][0] - 0.5, nk['y'][0] + 0.5,
                             hd['z'][0] - 0.2, nk['z'][1] + 0.2),
                        why='J4 keyhole T-head -Y wing (the T undercut cannot face the bed; candidate tongue has '
                            'no -Y chamfer): paint-on support from the bed, as r7 PRINT_SUPPORT_ZONES'))
    return out


class LayoutView:
    """The r7 layout module with candidate overrides; every other attribute falls through to the module."""

    def __init__(self, base, **over):
        self.__dict__['_base'] = base
        self.__dict__.update(over)

    def __getattr__(self, k):
        return getattr(self.__dict__['_base'], k)


def candidate_state(manifest):
    """Candidate layout facts the checks need, computed in the same layout state model._build uses (model import
    mutations + JG.trial_layout + model.collar_setup), restored afterwards. -> dict."""
    import model
    import j4_trial_geometry as JG
    L = model.L
    length = float(manifest['core_dimensions_mm'][0])
    with JG.trial_layout(L, **J4_TRIAL):
        tongues = copy.deepcopy(L.TONGUES)
    oldc, olds = copy.deepcopy(L.COLLAR), copy.deepcopy(L.SCREWS)
    try:
        model.collar_setup()
        collar = copy.deepcopy(L.COLLAR)
        lens_spec = L.collar_spec(manifest.get('lens') or L.LENS)   # CF: the variant's collar (critical features)
        collar_boxes = [tuple(float(v) for v in b) for b in CK.loaded_boxes(L, 'lens_collar')]
    finally:
        L.COLLAR, L.SCREWS = oldc, olds
    j = L.J4_LOCK
    loaded = {'lens_collar': collar_boxes, 'tub': [], 'panel': [], 'carrier': []}
    for x, z in model.CARRIER_SCREWS:          # make_tub: cyl y r 4.8, y -25.55..17.2 (carrier screw bosses)
        loaded['tub'].append((x - 4.8, x + 4.8, -25.55, 17.2, z - 4.8, z + 4.8))
    for x, z in model.panel_screws(length):    # make_tub: cyl y r 4.5, y -25.55..23.5 (panel screw bosses)
        loaded['tub'].append((x - 4.5, x + 4.5, -25.55, 23.5, z - 4.5, z + 4.5))
    for k in collar['bolted']:                 # make_tub: cyl x r 4, x -7.6..-5.1 (collar insert bosses)
        y, z = collar['feet'][k]
        loaded['tub'].append((-7.6, -5.1, y - 4.0, y + 4.0, z - 4.0, z + 4.0))
    r = j['od'] / 2                            # make_tub: J4 independent lock boss, z 2.4..top
    loaded['tub'].append((j['c'][0] - r, j['c'][0] + r, j['c'][1] - r, j['c'][1] + r, 2.4, j['top']))
    for x, z in model.panel_screws(length):    # make_panel: cyl y r 5.2, y 20.5..25, then +3 y
        loaded['panel'].append((x - 5.2, x + 5.2, 23.5, 28.0, z - 5.2, z + 5.2))
    loaded['panel'].append((-30.67, -27.34, 4.0, 25.6, 66.0, 76.0))   # make_panel camera cover catch (+3 y)
    for hx, hy in L.PI['holes']:               # make_carrier: kit bosses cyl y r 4.5, y 16.2..bed face (FP-11c)
        x, _, z = model.rp((hx, hy, 6))
        loaded['carrier'].append((x - 4.5, x + 4.5, 16.2, model.CARRIER_BED_Y, z - 4.5, z + 4.5))
    for x, z in model.CARRIER_SCREWS:          # make_carrier: ear bosses cyl y r CARRIER_EAR_R, y 17.2..bed face
        r = model.CARRIER_EAR_R
        loaded['carrier'].append((x - r, x + r, 17.2, model.CARRIER_BED_Y, z - r, z + r))
    parts = {}
    for pid, pose in manifest['print_poses'].items():
        if pid == GAUGE:
            continue                           # r7 checks the gauge's print pose only (no PARTS row)
        base = dict(L.PARTS.get(pid) or dict(module='candidate-vertical/model.py', material='ASA', owner=pid,
                                             infill='shell', supports='none declared'))
        base['face_down'] = pose['face_down']
        parts[pid] = base
    if 'tub' in parts:                         # FX: the tub print stock is graded as its own row (TUB_STOCK)
        parts[TUB_STOCK] = dict(parts['tub'], owner=TUB_STOCK)
        loaded[TUB_STOCK] = list(loaded['tub'])
    # CF (VN-21 / VN-25, phase 2): the candidate's critical-feature, joint and exception registries replace r7's in
    # the view (critical_features_vertical.py accounts for every r7 entry); r7 checks.py and layout.py are unchanged.
    import critical_features_vertical as CFV
    reg = CFV.build(CK, L, model, length, collar, lens_spec)
    lb = [p for p in CK.registry(L, 'LOAD_BEARING_PARTS')] + list(CFV.ADDED_LOAD_BEARING)   # carrier, tab-catch insert
    view = LayoutView(L, PARTS=parts, LOAD_BEARING_PARTS=lb, **reg['layout'])
    # C2 (FP-11e, VN-57): the base grip's declared pocket-floor support zone is design data in model.py
    # (grip_support_zones, derived from the same trial tongue rows); a zone no region needs still fails as stale.
    return dict(layout=view, tongues=tongues, collar=collar, loaded=loaded, length=length,
                zones={'tub': j4_wing_zones(tongues), 'base_grip': model.grip_support_zones(tongues)},
                cf_registry=reg['record'])


# ------------------------------------------------------------------------------------------- single direction
def _runs(Rr, Ar, Hr, Fr, max_px):
    """Row runs of a rotated region mask Rr. Ar anchor, Hr enclosed holes, Fr = pixels of Rr beyond cantilever
    reach. -> (ok mask: pixels of accepted runs, need: longest accepted run holding an Fr pixel, longest: longest
    two-ended run of any length holding an Fr pixel, open: an Fr pixel lies on a run with an open end)."""
    h, w = Rr.shape
    P = np.zeros((h, w + 2), bool)
    P[:, 1:-1] = Rr
    d = np.diff(P.astype(np.int8), axis=1)
    rs, a_ = np.nonzero(d == 1)
    _, b_ = np.nonzero(d == -1)
    Ap, Hp = np.zeros((h, w + 2), bool), np.zeros((h, w + 2), bool)
    Ap[:, 1:-1], Hp[:, 1:-1] = Ar, Hr
    C = np.zeros((h, w + 1), np.int64)
    C[:, 1:] = np.cumsum(Fr, axis=1)
    ok = np.zeros(Rr.shape, bool)
    need = longest = 0
    opened = False
    for r, a, b in zip(rs, a_, b_):
        n = int(b - a)
        far = C[r, b] - C[r, a] > 0
        la, lh, ra, rh = Ap[r, a], Hp[r, a], Ap[r, b + 1], Hp[r, b + 1]
        anchored = (la and ra) or (la and rh) or (lh and ra)
        if anchored and n <= max_px:
            ok[r, a:b] = True
            if far:
                need = max(need, n)
        if far:
            if anchored:
                longest = max(longest, n)
            else:
                opened = True
    return ok, need, longest, opened


def classify_single_direction(region, anchor, opts):
    """Per direction (same 8 as r7) the bad mask of one unsupported region when every bridge in it runs in that one
    direction. Raster frame, anchor, enclosed holes, cantilever reach, edge_tol growth and the nozzle sliver filter
    are r7 _classify's. -> dict(x0, y0, px, area, dirs=[dict(deg, bad (bool mask), need_px, longest_px, open)])."""
    import manifold3d as m3
    px = opts['px']
    m = 2 * px + opts['edge_tol']
    bx0, by0, bx1, by1 = region.bounds()
    x0, y0 = bx0 - m, by0 - m
    nx, ny = int(math.ceil((bx1 - bx0 + 2 * m) / px)), int(math.ceil((by1 - by0 + 2 * m) / px))
    win = m3.CrossSection.square([nx * px, ny * px]).translate([x0, y0])
    R = CK._raster(region, x0, y0, nx, ny, px)
    A = CK._grow(CK._raster(anchor ^ win, x0, y0, nx, ny, px), 1) & ~R
    H = CK._enclosed(~R & ~A)
    near = CK._reach(A, R, int(math.ceil(opts['cantilever_max'] / px)))
    far = R & ~near
    max_px = int(opts['bridge_max'] / px)
    half = max(1, int(round(0.5 * dc.FDM['NOZZLE'] / px)))
    grow = int(math.ceil(opts['edge_tol'] / px))
    dirs = []
    for k in range(opts['directions']):
        deg = 180.0 * k / opts['directions']
        okr, need, longest, opened = _runs(CK._rot(R, deg), CK._rot(A, deg), CK._rot(H, deg), CK._rot(far, deg),
                                           max_px)
        acc = near | (CK._unrot(okr, deg, R.shape) & R)
        acc = CK._reach(acc, R, grow) | acc
        bad = R & ~acc
        core = bad.copy()
        for i in range(half):
            core = ~CK._grow(~core, 0)
        bad = CK._reach(core, bad, half) | core
        dirs.append(dict(deg=deg, bad=bad, need_px=need, longest_px=longest, open=opened))
    return dict(x0=x0, y0=y0, px=px, area=float(R.sum()) * px * px, dirs=dirs)


def check_bridge_direction(L, pid, man, zones=(), opts=None, face_down=None):
    """One part in print pose (manifold3d Manifold, Z0 = bed). Same slicing, allowance and region decomposition as
    r7 check_print_overhang; each region that is not a short overhang is classified by classify_single_direction
    and the direction with the least bad area outside the declared zones (then the shortest needed span) is the
    region's raster direction. FAIL: any bad pixel outside the zones in the chosen direction, or a declared zone
    no region uses (stale). -> row dict (kind print_bridge_direction)."""
    import manifold3d as m3
    o = dict(getattr(L, 'PRINT_OVERHANG', {}) or {}, **(opts or {}))
    h, allow = o['layer'], o['layer'] * math.tan(math.radians(o['overhang_deg']))
    pxa = o['px'] ** 2
    row = dict(kind='print_bridge_direction', part=pid, face_down=face_down or L.PARTS[pid]['face_down'],
               rule=dict(layer=h, overhang_deg=o['overhang_deg'], cantilever_max=o['cantilever_max'],
                         bridge_max=o['bridge_max'], edge_tol=o['edge_tol'], directions=o['directions'], px=o['px'],
                         single_direction_per_region=True))
    if man is None or man.is_empty():
        row.update(status='fail', error='no print-pose mesh')
        return row
    zmax = man.bounding_box()[5]
    n = int(math.floor(zmax / h + 1e-9))
    regions, short, used, records = 0, 0, {}, []
    prev = man.slice(0.5 * h)
    for k in range(1, n):
        S = man.slice((k + 0.5) * h)
        supp = prev.offset(allow, m3.JoinType.Round)
        U = S - supp
        prev = S
        if U.area() < o['min_area']:
            continue
        anchor = S ^ supp
        near = anchor.offset(o['cantilever_max'], m3.JoinType.Round)
        zb = k * h
        for comp in U.decompose():
            if comp.area() < o['min_area']:
                continue
            regions += 1
            if (comp - near).area() < o['min_area']:
                short += 1
                continue
            c = classify_single_direction(comp, anchor, o)
            live = [zn for zn in zones if zn['box'][4] - h <= zb <= zn['box'][5] + h]
            best = None
            for dd in c['dirs']:
                jj, ii = np.nonzero(dd['bad'])
                xs, ys = c['x0'] + (ii + 0.5) * c['px'], c['y0'] + (jj + 0.5) * c['px']
                inside = np.zeros(len(xs), bool)
                use = {}
                for zn in live:
                    x0, x1, y0, y1 = zn['box'][:4]
                    sel = (xs >= x0) & (xs <= x1) & (ys >= y0) & (ys <= y1) & ~inside
                    if sel.any():
                        use[zn['id']] = float(sel.sum()) * pxa
                        inside |= sel
                key = (int((~inside).sum()), dd['need_px'] if not (~inside).any() else dd['longest_px'])
                if best is None or key < best[0]:
                    best = (key, dd, xs[~inside], ys[~inside], use)
            (nbad, _), dd, bx, by, use = best
            for zid, a in use.items():
                used[zid] = used.get(zid, 0.0) + a
            rec = dict(z=CK._r(zb, 2), area_mm2=CK._r(c['area'], 2), direction_deg=dd['deg'],
                       span_mm=CK._r(dd['need_px'] * o['px'], 2),
                       longest_two_ended_run_mm=CK._r(dd['longest_px'] * o['px'], 2), open_ended_run=dd['open'],
                       bad_area_mm2=CK._r(nbad * pxa, 2), bbox=[CK._r(v, 1) for v in comp.bounds()])
            if nbad:
                rec['bad_bbox'] = [CK._r(float(bx.min()), 1), CK._r(float(by.min()), 1),
                                   CK._r(float(bx.max()), 1), CK._r(float(by.max()), 1)]
                # what each direction would need: its longest two-ended run over far pixels, whether a far pixel
                # sits on an open-ended run (a cantilever no direction can bridge), its bad area (zones ignored)
                rec['per_direction'] = [[d2['deg'], CK._r(d2['longest_px'] * o['px'], 1), bool(d2['open']),
                                         CK._r(float(d2['bad'].sum()) * pxa, 1)] for d2 in c['dirs']]
                spans = [d2['longest_px'] for d2 in c['dirs'] if d2['longest_px']]
                rec['min_single_direction_span_mm'] = CK._r(min(spans) * o['px'], 2) if spans else None
                rec['open_in_every_direction'] = all(d2['open'] for d2 in c['dirs'])
            records.append(rec)
    stale = sorted(zn['id'] for zn in zones if zn['id'] not in used)
    fails = sorted((r for r in records if r['bad_area_mm2'] > 0), key=lambda r: -r['bad_area_mm2'])
    probs = []
    if fails:
        w = fails[0]
        probs.append('%d region(s) need more than one bridge direction or a bridge over %.0f mm (largest %.1f mm2 '
                     'at z %.2f)' % (len(fails), o['bridge_max'], w['bad_area_mm2'], w['z']))
    if stale:
        probs.append('declared support zone(s) %s are never needed (stale declaration)' % ', '.join(stale))
    passing = [r for r in records if r['bad_area_mm2'] == 0]
    row.update(layers=n, regions=regions, short_overhangs=short, bridge_regions=len(records),
               longest_bridge_mm=max((r['span_mm'] for r in passing), default=0.0),
               failing_region_count=len(fails), failing_regions=fails[:20],
               regions_by_span=sorted(passing, key=lambda r: -r['span_mm'])[:12],
               supports_used={k: CK._r(v, 2) for k, v in sorted(used.items())},
               declared_zones=[dict(id=zn['id'], why=zn.get('why', '')) for zn in zones],
               status='fail' if probs else 'pass')
    if probs:
        row['error'] = '; '.join(probs)
    return row


# ------------------------------------------------------------------------------------------- meshes
def manifold_from_stl(path):
    """Binary STL -> manifold3d Manifold (vertices welded on a 1e-6 mm grid, no repair; empty -> None)."""
    import manifold3d as m3
    data = Path(path).read_bytes()
    n = int(np.frombuffer(data, '<u4', 1, 80)[0])
    if len(data) != 84 + 50 * n:
        raise ValueError('not a binary STL with an exact record count: %s' % path)
    rec = np.frombuffer(data, np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')]), n, 84)
    V = rec['v'].reshape(-1, 3).astype(np.float64)
    key = np.round(V / 1e-6).astype(np.int64)
    _, idx, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
    F = inv.reshape(-1, 3)
    F = F[(F[:, 0] != F[:, 1]) & (F[:, 1] != F[:, 2]) & (F[:, 0] != F[:, 2])]
    mesh = m3.Mesh(vert_properties=np.ascontiguousarray(V[idx], np.float32),
                   tri_verts=np.ascontiguousarray(F, np.uint32))
    man = m3.Manifold(mesh)
    if man.is_empty():
        mesh.merge()
        man = m3.Manifold(mesh)
    return None if man.is_empty() else man


def stl_bbox(path):
    data = Path(path).read_bytes()
    n = int(np.frombuffer(data, '<u4', 1, 80)[0])
    rec = np.frombuffer(data, np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')]), n, 84)
    V = rec['v'].reshape(-1, 3)
    return V.min(axis=0).tolist(), V.max(axis=0).tolist()


def thin_spot_gate(spots):
    """r7 build_d2.unclassified_thin_spot_gate, same semantics (build_d2 is not imported: it is the r7 build): every
    sampled thin region on a load-bearing part needs a structural CRITICAL_FEATURES entry or a named exception."""
    valid = isinstance(spots, list)
    ok = valid and not spots
    return dict(id='thin_spot_classification', part='load_bearing_parts', status='pass' if ok else 'fail',
                unclassified_count=len(spots) if valid else None,
                error=None if ok else ('unclassified thin spots require geometry-backed classification'
                                       if valid else 'unclassified thin-spot report must be a list'),
                method='classification coverage of the sampled secondary thin-wall screen; no threshold waiver')


# ------------------------------------------------------------------------------------------- bed contact (VN-54, FP-11c)
# Parts whose print orientation claims a flat bed face: the whole part starts on that face. Only declared parts get the
# gated row (a part that prints on a smaller face with 45 deg growth outside it is judged by print_overhang alone).
FLAT_BED_PARTS = {
    'carrier': 'prints +Y face down on its continuous bed face at assembly y 22.2: frame rails, ears, kit and ear '
               'bosses and the diagonal arm all start on the bed (review VN-54, fix FP-11c)',
}


def _hole_filled(cs):
    """CrossSection -> the same region with every hole filled (union of its positive, counter-clockwise rings)."""
    import manifold3d as m3
    rings = []
    for q in cs.to_polygons():
        q = np.asarray(q, float)
        if len(q) < 3:
            continue
        x, y = q[:, 0], q[:, 1]
        if 0.5 * float(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)) > 0:
            rings.append(q)
    return m3.CrossSection(rings) if rings else m3.CrossSection()


def check_bed_contact(L, pid, man, opts=None, face_down=None, why=None):
    """A part declared to print flat on one face must start on that face: every column of its silhouette must begin on
    the bed or grow to its first layer from the bed face within r7's printable reach.

    In print pose (Z0 = bed): B = first-layer section (slice at layer / 2). Layer by layer, the material that appears
    over a column with no material below it (slice_k minus the union of the slices below) must lie within
    cantilever_max + k * layer * tan(overhang_deg) of B (r7 PRINT_OVERHANG: 1.0 mm cantilever, 45 deg growth per
    layer): a bed-edge chamfer, a 45 deg relief or the roof of a small recess in the bed face (a counterbore or head
    pocket, reached from its own walls) starts on the bed face; a region that starts higher with no bed face reaching it
    is lifted, also over a through-opening of the bed face (holes of B are not filled). FAIL when any lifted region of at
    least min_area remains (the VN-54 defect: the frame starting 2 mm above the bed, 1963 mm2 unsupported). Same r7
    constants; nothing relaxed. Reports the silhouette, bed and bed-outline areas. -> row dict (kind bed_contact)."""
    import manifold3d as m3
    o = dict(getattr(L, 'PRINT_OVERHANG', {}) or {}, **(opts or {}))
    h, cant, amin = float(o['layer']), float(o['cantilever_max']), float(o['min_area'])
    grow = h * math.tan(math.radians(float(o['overhang_deg'])))
    row = dict(kind='bed_contact', part=pid, face_down=face_down, declared=why,
               rule=dict(first_layer_z_mm=0.5 * h, layer_mm=h, cantilever_max_mm=cant, growth_per_layer_mm=grow,
                         overhang_deg=o['overhang_deg'], min_area_mm2=amin,
                         pass_rule='material first appearing over a column at layer k lies within cantilever_max + '
                                   'k * growth_per_layer of the first-layer section'))
    if man is None or man.is_empty():
        row.update(status='fail', error='no print-pose mesh')
        return row
    S = man.project()
    B = man.slice(0.5 * h)
    if B.is_empty():
        row.update(status='fail', error='no bed face at z %.2f' % (0.5 * h))
        return row
    zmax = man.bounding_box()[5]
    below = m3.CrossSection()
    lifted = []
    for k in range(int(math.floor(zmax / h + 1e-9)) + 1):
        Sk = man.slice((k + 0.5) * h)
        new = Sk - below if k else m3.CrossSection()
        if new.area() >= amin:
            bad = new - B.offset(cant + k * grow, m3.JoinType.Round)
            lifted += [(k * h, c) for c in bad.decompose() if c.area() >= amin]
        below = below + Sk
    lifted.sort(key=lambda zc: -zc[1].area())
    total = sum(c.area() for _, c in lifted)
    recess = (_hole_filled(B) - B) ^ S          # holes of the bed face with material above them (info)
    s_area, b_area, r_area = S.area(), B.area(), recess.area()
    ok = not lifted
    row.update(status='pass' if ok else 'fail', silhouette_area_mm2=CK._r(s_area, 2), bed_area_mm2=CK._r(b_area, 2),
               covered_recess_area_mm2=CK._r(r_area, 2),
               bed_contact_share=CK._r(b_area / s_area if s_area else 0.0, 4),
               bed_or_recess_share=CK._r((b_area + r_area) / s_area if s_area else 0.0, 4),
               lifted_area_mm2=CK._r(total, 2), lifted_region_count=len(lifted),
               lifted_regions=[dict(area_mm2=CK._r(c.area(), 2), lowest_material_z_mm=CK._r(z, 2),
                                    bbox=[CK._r(v, 1) for v in c.bounds()]) for z, c in lifted[:12]])
    if not ok:
        row['error'] = '%d region(s), %.2f mm2 of the silhouette start above the bed out of reach of the bed face' % (
            len(lifted), total)
    return row


# ------------------------------------------------------------------------------------------- bed-edge chamfer (VN-59)
def _signed_rings(cs):
    """CrossSection -> [(signed area, Nx2 ring)]; exterior rings are positive (CCW), hole rings negative."""
    out = []
    for q in cs.to_polygons():
        q = np.asarray(q, float)
        if len(q) < 3:
            continue
        x, y = q[:, 0], q[:, 1]
        out.append((0.5 * float(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)), q))
    return out


def _exterior(cs):
    """Holes filled: the union of the exterior rings of a CrossSection."""
    import manifold3d as m3
    rings = [q for a, q in _signed_rings(cs) if a > 0]
    return m3.CrossSection(rings) if rings else m3.CrossSection()


def check_bed_chamfer(pid, man, chamfer=None, layer=None, tol=0.15, max_unchamfered_mm=2.0, face_down=None,
                      exceptions=()):
    """r7 FDM rule BED_CHAMFER (layout.FDM: a 45 deg chamfer of 0.6 mm on the bed-face edges, no fillets on the bed face; r7
    builds it into each printed part but has no computed row for it) as a per-part gate (review VN-59).

    In print pose (Z0 = bed) the exterior outline of the first layer (slice at z_lo = layer / 2) must lie inside the outline
    at z_hi = chamfer + layer / 2, shrunk by (chamfer - z_lo - tol): a 45 deg chamfer of `chamfer` sets the bed outline in by
    chamfer - z_lo at z_lo; a sharp bed edge sets it in by nothing. What is left outside is the unchamfered band; its length
    is reported as band area / (chamfer - z_lo - tol), i.e. as the equivalent length of fully sharp edge. FAIL when the
    exterior outline carries more than max_unchamfered_mm of it. Outlines of holes in the bed face are measured the same
    way (a chamfered hole is wider at z_lo) and reported, not gated: r7 chamfers the exterior bed edges (printed_tub '|X'),
    and a chamfer on a functional through-hole (the tub CSI slot) would change that hole's checked section.
    exceptions (FX): dicts (id, box2 = print-pose (x0, y0, x1, y1), max_mm, why, tie): the unchamfered band inside a box
    is reported as excepted, not counted, up to max_mm; more than max_mm, or nothing inside the box (stale), FAILS.
    -> row dict (kind bed_chamfer)."""
    import manifold3d as m3
    c = float(dc.FDM['BED_CHAMFER'] if chamfer is None else chamfer)
    h = float(dc.FDM['LAYER'] if layer is None else layer)
    z_lo, z_hi = 0.5 * h, c + 0.5 * h
    band_w = c - z_lo - tol
    row = dict(kind='bed_chamfer', part=pid, face_down=face_down,
               rule=dict(chamfer_mm=c, angle_deg=45.0, z_lo_mm=z_lo, z_hi_mm=z_hi, tol_mm=tol,
                         band_width_mm=band_w, max_unchamfered_mm=max_unchamfered_mm,
                         source='r7 layout.FDM BED_CHAMFER (45 deg, exterior bed-face edges)'))
    if man is None or man.is_empty():
        row.update(status='fail', error='no print-pose mesh')
        return row
    s_lo, s_hi = man.slice(z_lo), man.slice(z_hi)
    e_lo, e_hi = _exterior(s_lo), _exterior(s_hi)
    if e_lo.is_empty():
        row.update(status='fail', error='no bed footprint at z %.2f' % z_lo)
        return row
    inner = e_hi.offset(-band_w, m3.JoinType.Miter, 20.0)
    band = e_lo - inner
    ext_len = band.area() / band_w
    perim = sum(float(np.linalg.norm(np.roll(q, -1, axis=0) - q, axis=1).sum())
                for a, q in _signed_rings(e_lo) if a > 0)
    holes_lo, holes_hi = e_lo - s_lo, e_hi - s_hi
    hole_band = (holes_hi.offset(band_w, m3.JoinType.Miter, 20.0) - holes_lo) ^ e_lo
    hole_len = hole_band.area() / band_w
    hole_perim = sum(float(np.linalg.norm(np.roll(q, -1, axis=0) - q, axis=1).sum())
                     for a, q in _signed_rings(s_lo) if a < 0)
    exc_rows, exc_ok = [], True
    for ex in exceptions:
        x0, y0, x1, y1 = ex['box2']
        win = m3.CrossSection.square([x1 - x0, y1 - y0]).translate([x0, y0])
        inside = band ^ win
        mm = inside.area() / band_w
        stale, over = mm < 0.05, mm > ex['max_mm']
        exc_ok = exc_ok and not stale and not over
        exc_rows.append(dict(id=ex['id'], excepted_mm=CK._r(mm, 2), max_mm=ex['max_mm'], stale=stale, over_max=over,
                             box2=[CK._r(v, 2) for v in ex['box2']], why=ex.get('why'), tie=ex.get('tie')))
        band = band - win
    if exceptions:
        ext_len = band.area() / band_w
    bad = band.decompose()
    worst = sorted(bad, key=lambda b: -b.area())[:8]
    ok = ext_len <= max_unchamfered_mm and exc_ok
    row.update(status='pass' if ok else 'fail',
               bed_area_mm2=CK._r(s_lo.area(), 2), exterior_perimeter_mm=CK._r(perim, 2),
               exterior_unchamfered_mm=CK._r(ext_len, 2),
               exterior_unchamfered_share=CK._r(ext_len / perim if perim else 0.0, 4),
               hole_perimeter_mm=CK._r(hole_perim, 2), hole_unchamfered_mm_info=CK._r(hole_len, 2),
               unchamfered_bands=[dict(area_mm2=CK._r(b.area(), 3), bbox=[CK._r(v, 1) for v in b.bounds()])
                                  for b in worst if b.area() > 1e-4], exceptions=exc_rows)
    if not ok:
        row['error'] = ('%.1f mm of the exterior bed outline (of %.1f mm) has no %.1f mm 45 deg chamfer'
                        % (ext_len, perim, c)) + ('' if exc_ok else '; a declared exception is stale or over its max')
    return row

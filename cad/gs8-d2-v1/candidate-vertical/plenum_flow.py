# SPDX-License-Identifier: MIT
"""Path-aware plenum section gate (review 2026-10-10 fix-up FX, VN-37). CAD-free core.

The shadow plenum is a 6 mm gap (y -34..-28) between the outer skin and the old side wall. Air enters (hot bay) or
leaves (cold bay) through the wall ports and leaves/enters through the edge mouths. The planar section rows
(area_parity) sample chosen planes; they cannot see a choke that lies between the ports and a mouth along a path the
planes do not cross (the trial2 rows did exactly that). This module computes the minimum cut (= maximum flow,
Ford-Fulkerson) between the port set and the mouth set of a bay on a rectilinear grid of the x-z plane:

- every grid cell carries the set of free y levels inside the gap; the level boundaries are the geometry's own y
  breakpoints (beam bottoms, lintel lands and slope ends, the gap faces) subdivided to LEVEL_DY, each level sampled at
  its mid plane (exact for prismatic slabs and for planar slopes, whose mid-plane section is the slab average);
- two neighbouring cells exchange flow through their shared edge: capacity = edge length x the summed thickness of the
  y levels free in BOTH cells;
- the source feeds every port cell through its wall face: capacity = cell area if the top level (next to the wall) is
  free, else 0 (a rib or beam under the port blocks that part of the port exit);
- each mouth cell drains through the mouth face: capacity = face length x free depth of the cell.

The result is the minimum, over all surfaces separating the ports from the mouths, of the free area crossed: the
port faces themselves are one such surface, so min_cut <= port area, and min_cut >= port area means that no internal
section anywhere is smaller than the wall ports. Area is not flow, pressure loss or cooling.

The grid lines are the geometry's own breakpoints (vertex coordinates of the sections) subdivided to MAX_CELL, so
axis-aligned material is resolved exactly; cells crossed by a slanted edge are centre-sampled (reported as
`slanted_edge_cells`).
"""
from collections import deque

GAP_Y = (-34.0, -28.0)
LEVEL_DY = 0.5
LEVELS = [GAP_Y[0] + LEVEL_DY * (k + 0.5) for k in range(int(round((GAP_Y[1] - GAP_Y[0]) / LEVEL_DY)))]
TOP_LEVEL = len(LEVELS) - 1          # the level next to the wall (y -28.25): a port exits through it
MAX_CELL = 0.5
SCALE = 1e7                          # integer capacities in 1e-7 mm2 (summed rounding < 1e-3 mm2)
TOL_MM2 = 0.002                      # same tolerance as the area_parity rows


def popcount(v):
    return bin(v).count('1')


def subdivide(breaks, lo, hi, max_cell=MAX_CELL):
    """Sorted unique grid lines in [lo, hi] containing every break, no cell wider than max_cell."""
    b = sorted({round(v, 6) for v in breaks if lo - 1e-9 <= v <= hi + 1e-9} | {round(lo, 6), round(hi, 6)})
    out = [b[0]]
    for a, c in zip(b, b[1:]):
        if c - a < 1e-6:
            continue
        n = max(1, int(-(-(c - a) // max_cell)))
        out.extend(round(a + (c - a) * (i + 1) / n, 6) for i in range(n))
    return out


class FlowGraph:
    """Directed graph with paired residual edges (e and e ^ 1) and Dinic's maximum flow."""

    def __init__(self, n):
        self.n, self.adj, self.to, self.cap = n, [[] for _ in range(n)], [], []

    def add(self, u, v, c, c_back=0):
        if c <= 0 and c_back <= 0:
            return
        self.adj[u].append(len(self.to)); self.to.append(v); self.cap.append(int(round(c)))
        self.adj[v].append(len(self.to)); self.to.append(u); self.cap.append(int(round(c_back)))

    def max_flow(self, s, t):
        to, cap, adj, n = self.to, self.cap, self.adj, self.n
        self.cap0 = list(cap)
        flow = 0
        while True:
            level = [-1] * n
            level[s] = 0
            q = deque([s])
            while q:
                u = q.popleft()
                for e in adj[u]:
                    if cap[e] > 0 and level[to[e]] < 0:
                        level[to[e]] = level[u] + 1
                        q.append(to[e])
            if level[t] < 0:
                return flow
            it = [0] * n
            stack, path = [s], []
            while stack:   # blocking flow: iterative DFS with current-arc pointers
                u = stack[-1]
                if u == t:
                    f = min(cap[e] for e in path)
                    for e in path:
                        cap[e] -= f
                        cap[e ^ 1] += f
                    flow += f
                    stack, path = [s], []
                    continue
                a = adj[u]
                k = it[u]
                lu = level[u] + 1
                while k < len(a) and not (cap[a[k]] > 0 and level[to[a[k]]] == lu):
                    k += 1
                it[u] = k
                if k == len(a):
                    level[u] = -1          # dead end
                    stack.pop()
                    if path:
                        path.pop()
                        it[stack[-1]] += 1
                    continue
                stack.append(to[a[k]])
                path.append(a[k])

    def reachable(self, s):
        seen = [False] * self.n
        seen[s] = True
        q = deque([s])
        while q:
            u = q.popleft()
            for e in self.adj[u]:
                if self.cap[e] > 0 and not seen[self.to[e]]:
                    seen[self.to[e]] = True
                    q.append(self.to[e])
        return seen


def levels_from_breaks(ys, max_dy=LEVEL_DY):
    """Level boundaries in the gap from y breakpoints -> (centres, thicknesses), lowest y first."""
    b = subdivide([y for y in ys if GAP_Y[0] < y < GAP_Y[1]], GAP_Y[0], GAP_Y[1], max_dy)
    return [0.5 * (a + c) for a, c in zip(b, b[1:])], [c - a for a, c in zip(b, b[1:])]


def min_cut(xs, zs, masks, ports, mouths, debug=False, level_w=None):
    """xs, zs: grid lines; masks[i][j]: free-level bitmask of cell (xs[i]..xs[i+1], zs[j]..zs[j+1]); level_w: the
    level thicknesses (default: the uniform LEVELS); the last level lies against the wall (port exits).
    ports: list of (x0, x1, z0, z1) wall-port rectangles (a cell is a port cell if its centre is inside one).
    mouths: dict name -> (face, lo, hi) with face in {'x_min', 'x_max', 'z_min'} (the bay boundary the mouth lies on)
    and lo..hi the mouth extent along that face. -> dict with the cut in mm2 and its composition."""
    nx, nz = len(xs) - 1, len(zs) - 1
    idx = lambda i, j: i * nz + j   # noqa: E731
    S, T = nx * nz, nx * nz + 1
    G = FlowGraph(nx * nz + 2)
    lw = list(level_w) if level_w is not None else [LEVEL_DY] * len(LEVELS)
    top = len(lw) - 1
    memo = {}

    def depth(m):
        if m not in memo:
            memo[m] = sum(w for k, w in enumerate(lw) if m >> k & 1)
        return memo[m]
    port_mm2 = blocked_port_mm2 = 0.0
    mouth_face = {k: 0.0 for k in mouths}
    for i in range(nx):
        dx, xc = xs[i + 1] - xs[i], 0.5 * (xs[i] + xs[i + 1])
        for j in range(nz):
            dz, zc = zs[j + 1] - zs[j], 0.5 * (zs[j] + zs[j + 1])
            m = masks[i][j]
            if i + 1 < nx:
                c = depth(m & masks[i + 1][j]) * dz
                G.add(idx(i, j), idx(i + 1, j), c * SCALE, c * SCALE)
            if j + 1 < nz:
                c = depth(m & masks[i][j + 1]) * dx
                G.add(idx(i, j), idx(i, j + 1), c * SCALE, c * SCALE)
            if any(p[0] <= xc <= p[1] and p[2] <= zc <= p[3] for p in ports):
                a = dx * dz
                if m >> top & 1:
                    port_mm2 += a
                    G.add(S, idx(i, j), a * SCALE)
                else:
                    blocked_port_mm2 += a
            for name, (face, lo, hi) in mouths.items():
                on = ((face == 'x_min' and i == 0) or (face == 'x_max' and i == nx - 1)) and lo <= zc <= hi
                on = on or (face == 'z_min' and j == 0 and lo <= xc <= hi)
                if on:
                    c = depth(m) * (dz if face != 'z_min' else dx)
                    mouth_face[name] += c
                    G.add(idx(i, j), T, c * SCALE)
    f = G.max_flow(S, T) / SCALE
    seen = G.reachable(S)
    # cut composition: original capacity of every edge from the source side to the sink side
    comp = dict(port=0.0, mouth=0.0, internal=0.0)
    cut_list = []
    box = [None, None, None, None]
    for e in range(len(G.to)):
        u, v = G.to[e ^ 1], G.to[e]
        if seen[u] and not seen[v] and G.cap0[e] > 0:
            kind = 'port' if u == S else ('mouth' if v == T else 'internal')
            comp[kind] += G.cap0[e] / SCALE
            if kind == 'internal':
                if debug:
                    iu, ju = divmod(u, nz); iv, jv = divmod(v, nz)
                    cut_list.append(('x' if iu != iv else 'z', 0.5 * (xs[max(iu, iv)] + xs[max(iu, iv)]) if iu != iv else 0.5 * (xs[iu] + xs[iu + 1]),
                                     zs[max(ju, jv)] if ju != jv else 0.5 * (zs[ju] + zs[ju + 1]), G.cap0[e] / SCALE))
                for w in (u, v):
                    i, j = divmod(w, nz)
                    x, z = 0.5 * (xs[i] + xs[i + 1]), 0.5 * (zs[j] + zs[j + 1])
                    box = [x if box[0] is None else min(box[0], x), x if box[1] is None else max(box[1], x),
                           z if box[2] is None else min(box[2], z), z if box[3] is None else max(box[3], z)]
    free_cells = sum(1 for i in range(nx) for j in range(nz) if masks[i][j])
    return dict(min_cut_mm2=f, port_face_mm2=port_mm2, port_face_blocked_mm2=blocked_port_mm2,
                mouth_face_mm2=mouth_face, grid=dict(nx=nx, nz=nz, free_cells=free_cells, max_cell_mm=MAX_CELL,
                                                    levels=len(lw), level_thickness_mm=[round(w, 6) for w in lw]),
                cut_composition_mm2={k: round(v, 4) for k, v in comp.items()},
                internal_cut_bbox_xz=[None if v is None else round(v, 3) for v in box],
                **({'cut_edges': cut_list} if debug else {}))


def mask_from_boxes(xs, zs, boxes, polys=(), levels=None):
    """CAD-free nominal raster: every cell starts free over all levels (centres `levels`, default LEVELS); each
    material box (x0, x1, y0, y1, z0, z1) clears the levels whose centre lies in [y0, y1] for cells whose centre lies in
    the box's x-z rectangle. polys: (pts_xz, y0, y1) convex polygons (centre test)."""
    lvs = list(levels) if levels is not None else LEVELS
    full = (1 << len(lvs)) - 1

    def lv(y0, y1):
        return sum(1 << k for k, y in enumerate(lvs) if y0 <= y <= y1)
    nx, nz = len(xs) - 1, len(zs) - 1
    xc = [0.5 * (xs[i] + xs[i + 1]) for i in range(nx)]
    zc = [0.5 * (zs[j] + zs[j + 1]) for j in range(nz)]
    M = [[full] * nz for _ in range(nx)]
    import bisect
    for x0, x1, y0, y1, z0, z1 in boxes:
        b = lv(y0, y1)
        if not b:
            continue
        i0, i1 = bisect.bisect_left(xc, x0), bisect.bisect_right(xc, x1)
        j0, j1 = bisect.bisect_left(zc, z0), bisect.bisect_right(zc, z1)
        for i in range(i0, i1):
            row = M[i]
            for j in range(j0, j1):
                row[j] &= ~b
    for pts, y0, y1 in polys:
        b = lv(y0, y1)
        xmin, xmax = min(p[0] for p in pts), max(p[0] for p in pts)
        zmin, zmax = min(p[1] for p in pts), max(p[1] for p in pts)
        n = len(pts)
        for i in range(bisect.bisect_left(xc, xmin), bisect.bisect_right(xc, xmax)):
            for j in range(bisect.bisect_left(zc, zmin), bisect.bisect_right(zc, zmax)):
                x, z = xc[i], zc[j]
                s = [(pts[(k + 1) % n][0] - pts[k][0]) * (z - pts[k][1]) - (pts[(k + 1) % n][1] - pts[k][1]) * (x - pts[k][0])
                     for k in range(n)]
                if all(v >= 0 for v in s) or all(v <= 0 for v in s):
                    M[i][j] &= ~b
    return M



# ------------------------------------------------------------------------------------------- bays (verifier rectangles)
def bays(length):
    """The two bays with the plenum verifiers' own port and mouth rectangles (verify_shadow_plenum / check_scope
    area_parity, unchanged): name -> dict(x=(x0, x1), z=(0, 100), ports=[(x0, x1, z0, z1)], mouths={name: (face, lo, hi)},
    wall_ports_mm2)."""
    return {
        'cold': dict(x=(-length, -65.0), z=(0.0, 100.0),
                     ports=[(-103.0, -68.0, z, z + 3.0) for z in (18.0, 24.0, 30.0, 36.0)],
                     mouths={'cold_rear': ('x_min', 5.0, 75.0), 'cold_bottom': ('z_min', -length + 4.0, -83.0)},
                     wall_ports_mm2=420.0),
        'hot': dict(x=(-62.0, 0.0), z=(0.0, 100.0),
                    ports=[(-59.0, -16.5, z, z + 3.0) for z in (16.0, 23.0, 30.0, 37.0)],
                    mouths={'hot_bottom': ('z_min', -59.0, -5.0), 'hot_front': ('x_max', 5.0, 40.0)},
                    wall_ports_mm2=510.0)}


def nominal_frame_boxes(VG, length):
    """CAD-free nominal gap-region material other than the ribs: frame (with the mouth openings, their mullions and the
    cold-mouth lintel lands stepped at LEVEL_DY), divider and CSI block, from vent_geometry's own numbers. Used for the
    nominal (design) min cut and the empty-bay bound only; the gate itself runs on the saved STEP."""
    y0, y1 = VG.RIB_Y
    land = VG.WALL_OUTER - VG.LINTEL
    xs = -length
    b = [(xs, xs + 2.5, y0, y1, 0, 5), (xs, xs + 2.5, y0, y1, 75, 100),
         (-2.5, 0, y0, y1, 0, 5), (-2.5, 0, y0, y1, 40, 100),
         (xs, xs + 4, y0, y1, 0, 2.5), (-83, -59, y0, y1, 0, 2.5), (-5, 0, y0, y1, 0, 2.5),
         (xs, 0, y0, y1, 97.5, 100), (-65, -62, y0, y1, 2.4, 97.6), (-91, -75, y0, y1, 39, 70)]
    w, s = VG.LINTEL_LAND, VG.LINTEL     # cold lintels: flat land, then the 45 deg slope in 4 steps (nominal only)
    b += [(xs, xs + w, land, y1, 5, 75), (xs + 4, -83, land, y1, 0, w)]
    for k in range(4):
        yk = land + s * (k + 0.5) / 4
        b += [(xs + w, xs + w + s * (k + 0.5) / 4, yk, y1, 5, 75), (xs + 4, -83, yk, y1, w, w + s * (k + 0.5) / 4)]
    rear = [z for z, segs in VG.cold_rows(length) if 5 < z < 75 and segs[0][0] <= -length]
    h = VG.RIB_T / 2
    b += [(xs, xs + 2.6, y0, y1, z - h, z + h) for z in rear]
    b += [(x - h, x + h, y0, y1, 0, 2.6) for x in VG.cold_bottom_mullions(length)]
    b.append((VG.HOT_BOTTOM_MULLION_X - h, VG.HOT_BOTTOM_MULLION_X + h, y0, y1, 0, 2.6))
    b.append((-2.6, 0, y0, y1, VG.HOT_FRONT_MULLION_Z - h, VG.HOT_FRONT_MULLION_Z + h))
    return b


def nominal_min_cut(VG, length, which, ribs=True):
    """CAD-free nominal min cut of one bay from vent_geometry (ribs=False: the empty-bay bound, i.e. the best any
    internal rib layout can reach with these ports, mouths, mullions and frame)."""
    B = bays(length)[which]
    boxes = nominal_frame_boxes(VG, length)
    polys = []
    if ribs:
        boxes = boxes + list(VG.rib_boxes(length))
        polys = list(VG.rib_polys(length))
    bx = [v for q in boxes for v in q[:2]] + [p for q in B['ports'] for p in q[:2]] + list(B['x'])
    bz = [v for q in boxes for v in q[4:]] + [p for q in B['ports'] for p in q[2:]] + list(B['z'])
    for m in B['mouths'].values():
        (bz if m[0] != 'z_min' else bx).extend(m[1:])
    for pts, _, _ in polys:
        bx += [p[0] for p in pts]
        bz += [p[1] for p in pts]
    xs, zs = subdivide(bx, *B['x']), subdivide(bz, *B['z'])
    lc, lw = levels_from_breaks([v for q in boxes for v in q[2:4]] + [v for q in polys for v in q[1:3]])
    r = min_cut(xs, zs, mask_from_boxes(xs, zs, boxes, polys, lc), B['ports'], B['mouths'], level_w=lw)
    r.update(wall_ports_mm2=B['wall_ports_mm2'], bay=which, nominal=True, ribs=ribs)
    return r


# ------------------------------------------------------------------------------------------- saved-STEP adapter (CadQuery)
def _wire_polyline(wire, n_curve=24):
    """Ordered (x, z) polyline of an OCC wire lying in a y plane; curved edges sampled."""
    from OCP.BRepTools import BRepTools_WireExplorer
    from OCP.BRepAdaptor import BRepAdaptor_Curve
    from OCP.GeomAbs import GeomAbs_Line
    from OCP.TopAbs import TopAbs_REVERSED
    pts = []
    ex = BRepTools_WireExplorer(wire.wrapped)
    while ex.More():
        e = ex.Current()
        c = BRepAdaptor_Curve(e)
        t0, t1 = c.FirstParameter(), c.LastParameter()
        ts = [t0, t1] if c.GetType() == GeomAbs_Line else [t0 + (t1 - t0) * k / n_curve for k in range(n_curve + 1)]
        if e.Orientation() == TopAbs_REVERSED:
            ts = ts[::-1]
        seg = [c.Value(t) for t in ts]
        pts.extend((p.X(), p.Z()) for p in seg[:-1])
        ex.Next()
    return pts


def _inside(poly, X, Z):
    """Even-odd ray casting: boolean array, True where (X, Z) lies inside the closed polygon."""
    import numpy as np
    P = np.asarray(poly, float)
    x0, z0 = P[:, 0], P[:, 1]
    x1, z1 = np.roll(x0, -1), np.roll(z0, -1)
    out = np.zeros(X.shape, bool)
    for a, b, c, d in zip(x0, z0, x1, z1):
        if b == d:
            continue
        cond = (b > Z) != (d > Z)
        xi = a + (Z - b) * (c - a) / (d - b)
        out ^= cond & (X < xi)
    return out


def step_masks(tub, x_range, z_range, extra_x=(), extra_z=()):
    """Free-level masks of the gap region of one bay from the saved tub solid: at every LEVELS y, the face
    rect(y; x_range x z_range) minus the tub (the same face Boolean as verify_shadow_plenum.free_section) gives the
    free faces; their vertices are the grid breakpoints and each cell centre is classified by even-odd containment.
    -> (xs, zs, masks, info)."""
    import numpy as np
    import cadquery as cq
    V = cq.Vector
    x0, x1 = x_range
    z0, z1 = z_range
    level_faces, bx, bz, slanted = [], list(extra_x) + [x0, x1], list(extra_z) + [z0, z1], 0
    bb = tub.BoundingBox()
    ys = [v.Y for v in tub.Vertices() if GAP_Y[0] < v.Y < GAP_Y[1] and x0 - 1 <= v.X <= x1 + 1]
    lc, lw = levels_from_breaks(ys)
    del bb
    for y in lc:
        ps = [V(x0, y, z0), V(x1, y, z0), V(x1, y, z1), V(x0, y, z1)]
        face = cq.Face.makeFromWires(cq.Wire.makePolygon(ps + ps[:1]))
        free = face.cut(tub)
        rings = []
        for f in free.Faces():
            outer = _wire_polyline(f.outerWire())
            inner = [_wire_polyline(w) for w in f.innerWires()]
            rings.append((outer, inner))
            for poly in [outer] + inner:
                bx += [p[0] for p in poly]
                bz += [p[1] for p in poly]
                n = len(poly)
                slanted += sum(1 for k in range(n) if abs(poly[k][0] - poly[(k + 1) % n][0]) > 1e-6
                               and abs(poly[k][1] - poly[(k + 1) % n][1]) > 1e-6)
        level_faces.append(rings)
    xs, zs = subdivide(bx, x0, x1), subdivide(bz, z0, z1)
    xc = np.array([0.5 * (xs[i] + xs[i + 1]) for i in range(len(xs) - 1)])
    zc = np.array([0.5 * (zs[j] + zs[j + 1]) for j in range(len(zs) - 1)])
    X, Z = np.meshgrid(xc, zc, indexing='ij')
    M = np.zeros(X.shape, np.int64)
    for k, rings in enumerate(level_faces):
        lv = np.zeros(X.shape, bool)
        for outer, inner in rings:
            m = _inside(outer, X, Z)
            for h in inner:
                m &= ~_inside(h, X, Z)
            lv |= m
        M |= lv.astype(np.int64) << k
    masks = [[int(v) for v in row] for row in M]
    return xs, zs, masks, dict(levels=len(lc), level_thickness_mm=[round(w, 6) for w in lw],
                               slanted_edge_segments=int(slanted), cells=int(X.size))


def step_min_cut(tub, length, which):
    """Gate computation on the saved tub: min cut of one bay between its wall ports and its mouths (verifier
    rectangles). -> dict(min_cut_mm2, wall_ports_mm2, ...)."""
    B = bays(length)[which]
    ex_x = [p for q in B['ports'] for p in q[:2]] + [v for m in B['mouths'].values() if m[0] == 'z_min' for v in m[1:]]
    ex_z = [p for q in B['ports'] for p in q[2:]] + [v for m in B['mouths'].values() if m[0] != 'z_min' for v in m[1:]]
    xs, zs, masks, info = step_masks(tub, B['x'], B['z'], ex_x, ex_z)
    r = min_cut(xs, zs, masks, B['ports'], B['mouths'], level_w=info['level_thickness_mm'])
    r.update(wall_ports_mm2=B['wall_ports_mm2'], bay=which, step_grid=info)
    return r

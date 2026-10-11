"""Pure-numpy fallback for raster.cpp (review 2026-10-10 VN-12, FP-15): the same triangle Z-buffer, no compiler.

raster.cpp needs a 64-bit C++ compiler that matches the Python interpreter; the 32-bit MinGW g++ on the review
machine builds a library 64-bit CPython cannot load, so the guide could not be rebuilt on Windows. This module
gives the same result with numpy only.

Equivalence with raster.cpp (tested in tests/test_raster_fallback.py against a line-by-line scalar port):
- the same per-pixel arithmetic in the same operation order (double precision): the edge weights u, v at the
  pixel centre (x + .5, y + .5), the inclusion test u >= -1e-8, v >= -1e-8, u + v <= 1.00000001, the interpolated
  depth z = u*z_a + v*z_b + (1-u-v)*z_c, the same bounding box (floor/ceil clipped to the image), the same
  degenerate-triangle skip (|det| < 1e-10);
- the same painter rule. raster.cpp writes a pixel when z < depth (strict), triangle by triangle in input order,
  so the final depth of a pixel is the minimum z of every triangle covering it, and its colour is the colour of
  the FIRST triangle (lowest index) that reaches that minimum. This module computes exactly that reduction in
  vectorised chunks (lexsort on pixel, z, triangle index), processing chunks in ascending triangle order with the
  same strict comparison against the running buffer.
Bit identity holds against an x86-64 build of raster.cpp (no fused multiply-add: g++ only contracts a*b+c into
an FMA when the target has one, and the default x86-64 target does not). A native build for an FMA target
(for example aarch64, or -march=native on a recent x86-64) may differ in the last bit of u, v or z.
Non-finite vertex coordinates are skipped here; raster.cpp has undefined behaviour for them.
"""
import math

import numpy as np

CHUNK = 1 << 18   # candidate (triangle, pixel) pairs per vectorised chunk; about 40 MB peak at this size (RAM-tight machine)


def _boxes(p, w, h):
    ax, ay, bx, by, cx, cy = p[:, 0, 0], p[:, 0, 1], p[:, 1, 0], p[:, 1, 1], p[:, 2, 0], p[:, 2, 1]
    det = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
    with np.errstate(invalid='ignore'):
        x0 = np.maximum(0, np.floor(np.minimum(np.minimum(ax, bx), cx)))
        x1 = np.minimum(w - 1, np.ceil(np.maximum(np.maximum(ax, bx), cx)))
        y0 = np.maximum(0, np.floor(np.minimum(np.minimum(ay, by), cy)))
        y1 = np.minimum(h - 1, np.ceil(np.maximum(np.maximum(ay, by), cy)))
    finite = np.isfinite(p.reshape(len(p), -1)).all(axis=1)
    ok = finite & ~(np.abs(det) < 1e-10) & (x1 >= x0) & (y1 >= y0)
    nx = np.where(ok, x1 - x0 + 1, 0).astype(np.int64)
    ny = np.where(ok, y1 - y0 + 1, 0).astype(np.int64)
    return det, np.where(ok, x0, 0).astype(np.int64), np.where(ok, y0, 0).astype(np.int64), nx, ny


def _candidates(p, det, tri, x0, y0, nx, ny, w):
    """(pixel index, z, triangle index) of every covered pixel of the triangles `tri` (bounding boxes x0/y0/nx/ny)."""
    counts = nx * ny
    total = int(counts.sum())
    if total == 0:
        return None
    rep = np.repeat(np.arange(len(tri)), counts)
    start = np.repeat(np.cumsum(counts) - counts, counts)
    local = np.arange(total, dtype=np.int64) - start
    X = x0[rep] + local % nx[rep]
    Y = y0[rep] + local // nx[rep]
    q = p[tri][rep]
    ax, ay, az = q[:, 0, 0], q[:, 0, 1], q[:, 0, 2]
    bx, by, bz = q[:, 1, 0], q[:, 1, 1], q[:, 1, 2]
    cx, cy, cz = q[:, 2, 0], q[:, 2, 1], q[:, 2, 2]
    d = det[tri][rep]
    px = X.astype(np.float64) + .5 - cx          # C++: x+.5-cx with int x promoted to double, left to right
    py = Y.astype(np.float64) + .5 - cy
    u = ((by - cy) * px + (cx - bx) * py) / d
    v = ((cy - ay) * px + (ax - cx) * py) / d
    inside = ~((u < -1e-8) | (v < -1e-8) | (u + v > 1.00000001))
    z = u * az + v * bz + (1 - u - v) * cz
    k = Y * w + X
    return k[inside], z[inside], tri[rep][inside]


def _apply(k, z, t, colors, image, depth):
    """Per pixel keep min z, ties to the lowest triangle index; write where it beats the running buffer (strict)."""
    if k is None or not len(k):
        return
    order = np.lexsort((t, z, k))
    k, z, t = k[order], z[order], t[order]
    first = np.ones(len(k), dtype=bool)
    first[1:] = k[1:] != k[:-1]
    k, z, t = k[first], z[first], t[first]
    flat_d = depth.reshape(-1)
    win = z < flat_d[k]
    k, z, t = k[win], z[win], t[win]
    flat_d[k] = z
    image.reshape(-1, 3)[k] = colors[t]


def raster(pts, colors, w, h, image, depth, chunk=CHUNK):
    """In-place triangle Z-buffer. pts (n, 3, 3) float64 screen x, y and depth per vertex (or (n, 9));
    colors (n, 3) uint8; image (h, w, 3) uint8 and depth (h, w) float64 are updated like raster.cpp's buffers."""
    p = np.asarray(pts, dtype=np.float64).reshape(-1, 3, 3)
    colors = np.asarray(colors, dtype=np.uint8).reshape(-1, 3)
    if image.shape != (h, w, 3) or depth.shape != (h, w) or not image.flags.c_contiguous or not depth.flags.c_contiguous:
        raise ValueError('image must be C-contiguous (h, w, 3) uint8 and depth C-contiguous (h, w) float64')
    if not len(p):
        return
    det, x0, y0, nx, ny = _boxes(p, w, h)
    counts = nx * ny
    i, n = 0, len(p)
    while i < n:
        if counts[i] > chunk:                      # one large triangle: disjoint row bands, still in order
            rows = max(1, chunk // max(1, int(nx[i])))
            for r0 in range(0, int(ny[i]), rows):
                r = min(rows, int(ny[i]) - r0)
                tri = np.array([i])
                res = _candidates(p, det, tri, x0[tri], y0[tri] + r0, nx[tri], np.array([r]), w)
                if res is not None:
                    _apply(*res, colors, image, depth)
            i += 1
            continue
        j, acc = i, 0
        while j < n and counts[j] <= chunk and acc + counts[j] <= chunk:
            acc += int(counts[j])
            j += 1
        tri = np.arange(i, j)
        res = _candidates(p, det, tri, x0[tri], y0[tri], nx[tri], ny[tri], w)
        if res is not None:
            _apply(*res, colors, image, depth)
        i = j


def raster_reference(pts, colors, w, h, image, depth):
    """Line-by-line scalar port of raster.cpp (slow; the oracle for the tests)."""
    p = np.asarray(pts, dtype=np.float64).reshape(-1, 9)
    for i in range(len(p)):
        ax, ay, az, bx, by, bz, cx, cy, cz = (float(v) for v in p[i])
        det = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if not all(math.isfinite(v) for v in p[i]) or abs(det) < 1e-10:
            continue
        x0 = max(0, math.floor(min(ax, bx, cx))); x1 = min(w - 1, math.ceil(max(ax, bx, cx)))
        y0 = max(0, math.floor(min(ay, by, cy))); y1 = min(h - 1, math.ceil(max(ay, by, cy)))
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                u = ((by - cy) * (x + .5 - cx) + (cx - bx) * (y + .5 - cy)) / det
                v = ((cy - ay) * (x + .5 - cx) + (ax - cx) * (y + .5 - cy)) / det
                if u < -1e-8 or v < -1e-8 or u + v > 1.00000001:
                    continue
                z = u * az + v * bz + (1 - u - v) * cz
                if z < depth[y, x]:
                    depth[y, x] = z
                    image[y, x] = colors[i]

# SPDX-License-Identifier: MIT
"""Separate source-bound bonded catch study; run through ../run_locked.py.

Copies the exact production insert and crops only the matching tub print stock.
No production geometry, export or acceptance threshold is changed. Geometry-only
local seating/tilt/adhesion evidence cannot qualify whole-tub torque or strength.
"""
from pathlib import Path
import sys
P = Path(__file__).resolve().parent
C = P.parent
sys.path[:0] = [str(C), str(P), str(C.parent)]
from cv_io import read_text, relpath_posix, write_text
import argparse
import collections
import hashlib
import json
import math
import shutil
import struct
import cadquery as cq
import export_cache as EC
import verify_print_checks as VPC
import print_rules as PR
import model


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def volume(shape):
    if shape is None or shape.isNull():
        return 0.0
    return sum(s.Volume() for s in shape.Solids())


def bounds(shape):
    b = shape.BoundingBox()
    return [b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax]


def mesh_check(path, expected):
    """Same stated geometric rules as verify_print_meshes, without changing that checker."""
    data = path.read_bytes()
    n = struct.unpack_from('<I', data, 80)[0]
    assert len(data) == 84 + 50*n, 'Not an exact binary STL: ' + path.name
    edges, winding = collections.Counter(), collections.Counter()
    lo, hi, signed = [math.inf]*3, [-math.inf]*3, 0.0
    for i in range(n):
        vals = struct.unpack_from('<12fH', data, 84 + 50*i)
        vertices = [tuple(vals[3+3*k:6+3*k]) for k in range(3)]
        a, b, c = vertices
        signed += (a[0]*(b[1]*c[2]-b[2]*c[1]) + a[1]*(b[2]*c[0]-b[0]*c[2]) +
                   a[2]*(b[0]*c[1]-b[1]*c[0]))/6
        keys = [tuple(round(x, 6) for x in p) for p in vertices]
        for u, v in zip(keys, keys[1:]+keys[:1]):
            edge = tuple(sorted((u, v)))
            edges[edge] += 1
            winding[edge] += 1 if u < v else -1
        for p in vertices:
            for k in range(3):
                lo[k], hi[k] = min(lo[k], p[k]), max(hi[k], p[k])
    bad = sum(x != 2 for x in edges.values())
    wrong = sum(x != 0 for x in winding.values())
    size = [hi[k]-lo[k] for k in range(3)]
    bed = min(size[0], size[1]) <= 210 and max(size[0], size[1]) <= 250 and size[2] <= 220
    error = abs(signed-expected)
    ok = bad == wrong == 0 and signed > 0 and error <= max(1.0, .005*expected) and bed and abs(lo[2]) < .002
    result = dict(pass_geometry_only=ok, triangles=n, nonmanifold_edges=bad, inconsistent_edge_winding=wrong,
                  signed_volume_mm3=signed, source_volume_mm3=expected, volume_error_mm3=error,
                  print_bounds_mm=[lo, hi], print_dimensions_mm=size, fits_250x210x220=bed,
                  bed_z_zero=abs(lo[2]) < .002,
                  rules='Unmodified verify_print_meshes numerical rules: vertex weld 1e-6 mm; positive closed winding; '
                        'volume difference <= max(1 mm3, 0.5%); bed Z < 0.002 mm; 250x210x220 envelope. No slicer test.')
    assert ok, 'Coupon mesh geometry failed: ' + json.dumps(result)
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--variant', default='compact-kowa_lm6hc')
    ap.add_argument('--dest', type=Path, default=P/'bonded-catch-coupon')
    a = ap.parse_args()
    D, O = C/'out'/a.variant, a.dest
    mf = D/'manifest.json'
    mh = sha(mf)
    m = json.loads(read_text(mf))
    assert m.get('tab_catch_joint'), 'Selected manifest must expose the actual bonded joint dimensions'
    assert not m['tab_catch_joint']['physical_qualified']
    source_hashes = {relpath_posix((C.parent/n).resolve(), C): h for n, h in m['sources'].items()}
    for name in ('verify_print_checks.py', 'print_rules.py', 'cv_io.py', 'export_cache.py',
                 'structural-review/make_bonded_catch_coupon.py'):
        source_hashes[name] = sha(C/name)
    for name, expected in source_hashes.items():
        assert sha(C/name) == expected, 'Source changed since the selected export: ' + name
    files = ['step/tub.step', 'stl/tub.stl', 'step/tab_catch_insert.step', 'stl/tab_catch_insert.stl']
    inputs = {relpath_posix(mf, C): mh}
    for name in files:
        assert sha(D/name) == m['files'][name], 'Unbound production input: ' + name
        inputs[relpath_posix(D/name, C)] = sha(D/name)
    t = m['tab_catch_joint']['tenon_mm']
    assert list(model.TAB_CATCH_TENON['x']) == t['x'] and model.TAB_CATCH_TENON['h'] == t['h']
    assert model.TAB_CATCH_TENON['t'] == t['t'] and model.TAB_CATCH_POCKET_CLEAR == m['tab_catch_joint']['pocket_clearance_mm']
    assert model.TAB_CATCH_CEILING_TOP == m['tab_catch_joint']['ceiling_top_z_mm']
    tub = cq.importers.importStep(str(D/'step/tub.step')).val()
    insert = cq.importers.importStep(str(D/'step/tab_catch_insert.step')).val()
    assert tub.isValid() and insert.isValid() and len(tub.Solids()) == len(insert.Solids()) == 1
    stock = VPC.tub_stock(tub, D, m)
    stock_volume = volume(stock)
    stl_volume = PR.manifold_from_stl(D/'stl/tub.stl').volume()
    bb = stock.BoundingBox()
    crop_bounds = [-20.0, 0.0, bb.ymin, bb.ymax, 76.0, 100.0]
    ib = bounds(insert)
    assert all(crop_bounds[2*k] <= ib[2*k]+1e-6 and crop_bounds[2*k+1] >= ib[2*k+1]-1e-6 for k in range(3)), 'Crop would truncate the insert region'
    x0, x1, y0, y1, z0, z1 = crop_bounds
    host = stock.intersect(cq.Solid.makeBox(x1-x0, y1-y0, z1-z0, cq.Vector(x0, y0, z0)))
    assert host.isValid() and len(host.Solids()) == 1, 'Host crop invalid/disconnected; do not invent supports'
    pocket = model.tab_catch_split()['pocket']
    pocket_bounds = bounds(pocket)
    assert all(crop_bounds[2*k] <= pocket_bounds[2*k]+1e-6 and
               crop_bounds[2*k+1] >= pocket_bounds[2*k+1]-1e-6 for k in range(3)), 'Crop truncates the production pocket'
    pocket_material = volume(host.intersect(pocket))
    assert pocket_material < 1e-6, 'The complete production pocket must remain empty in the cropped host'
    overlap = volume(host.intersect(insert))
    assert overlap < 1e-6, 'Nominal host and insert overlap in the source assembly frame'
    pose = m['print_poses']['tub']
    assert pose['face_down'] == '-Y' and m['print_poses']['tab_catch_insert']['face_down'] == '-Z'
    posed = host.rotate((0, 0, 0), tuple(pose['rotation_axis']), pose['angle_deg'])
    pb = posed.BoundingBox()
    translation = [-pb.xmin, -pb.ymin, -pb.zmin]
    posed = posed.translate(cq.Vector(*translation))
    O.mkdir(parents=True, exist_ok=True)
    hp, hs = O/'catch-host-coupon.step', O/'catch-host-coupon.stl'
    ip, ins = O/'catch-insert.step', O/'catch-insert.stl'
    EC.export_step(host, hp)
    check = cq.importers.importStep(str(hp)).val()
    assert check.isValid() and len(check.Solids()) == 1 and abs(volume(check)-volume(host)) < .001
    cq.exporters.export(posed, str(hs), tolerance=.04, angularTolerance=.12)
    shutil.copyfile(D/'step/tab_catch_insert.step', ip)
    shutil.copyfile(D/'stl/tab_catch_insert.stl', ins)
    assert sha(ip) == m['files']['step/tab_catch_insert.step'] and sha(ins) == m['files']['stl/tab_catch_insert.stl']
    host_mesh, insert_mesh = mesh_check(hs, volume(host)), mesh_check(ins, volume(insert))
    receipt = dict(
        status='GEOMETRY ONLY: separate local bonded-catch study; not print released',
        variant=a.variant, manifest_sha256=mh, built_utc=EC.UNRECORDED, runtime=EC.runtime(),
        input_sha256=inputs, source_sha256=source_hashes, joint=m['tab_catch_joint'],
        crop_bounds_mm=crop_bounds, production_geometry_changed=False, physical_qualified=False,
        piece_count=2, production_part_count_change=0, replaces_earlier_coupon_set=False,
        purpose='Local joint seating, datum-tilt, adhesion and warm-creep screening in the production layer orientations',
        limitations=[
            'Cropped host and fixture omit whole-tub compliance, complete lens/camera constraints and service loads.',
            'No whole-camera or whole-tub 0.5 N m torque qualification follows from this coupon.',
            'The full Y span retains the original bed-side skin, ceiling, pad, both catch faces and roof connection; cut edges still change stiffness.',
            'Exact epoxy SKU, surface preparation, bondline, full cure, conditioning and specimen/test protocol remain unqualified.',
            'No slicer, print, bond, load, deflection, creep, impact, fatigue or failure test has been performed.'],
        tub_stock_check=dict(step_volume_mm3=stock_volume, bound_stl_volume_mm3=stl_volume,
                             relative_difference=abs(stock_volume-stl_volume)/stl_volume,
                             rule='Existing verify_print_checks.tub_stock bound-STL 0.5% tessellation rule'),
        nominal_host_insert_overlap_mm3=overlap,
        pocket_preservation=dict(source_pocket_bounds_mm=pocket_bounds, entire_pocket_inside_crop=True,
                                 host_material_in_pocket_mm3=pocket_material),
        geometry_overlap_tolerance_mm3=1e-6,
        parts=[dict(id='catch-host-coupon', valid=True, solid_count=1, step_reimport_valid=True,
                    volume_mm3=volume(host), source_bounds_mm=bounds(host), face_down='-Y',
                    rotation_axis=pose['rotation_axis'], angle_deg=pose['angle_deg'], translation_mm=translation,
                    mesh=host_mesh),
               dict(id='catch-insert', valid=True, solid_count=1, exact_production_step_and_stl_copy=True,
                    volume_mm3=volume(insert), source_bounds_mm=ib,
                    face_down='-Z', production_print_pose=m['print_poses']['tab_catch_insert'], mesh=insert_mesh)],
        files={f.name: sha(f) for f in (hp, hs, ip, ins)})
    for name, expected in {**inputs, **source_hashes}.items():
        assert sha(C/name) == expected, 'Input changed during local coupon generation: ' + name
    write_text(O/'receipt.json', json.dumps(receipt, indent=2, sort_keys=True)+'\n')
    print(json.dumps({k: receipt[k] for k in ('status', 'manifest_sha256', 'crop_bounds_mm', 'nominal_host_insert_overlap_mm3')}, indent=2))
    print('Host print dimensions:', host_mesh['print_dimensions_mm'])
    print('Insert print dimensions:', insert_mesh['print_dimensions_mm'])


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Read-only binary STL topology/bounds check. Requires NumPy, never trimesh.

No repair is attempted. This is an edge/vertex-link and finite-bounds check, not
an intersection detector, slicer check, material-strength check, or print release.
All manifest source and file hashes are checked before and after validation.
"""
from __future__ import annotations
import argparse
from cv_io import write_text
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def json_load(path):
    def pairs(items):
        d = {}
        for k, v in items:
            if k in d:
                raise ValueError('Duplicate JSON key: ' + k)
            d[k] = v
        return d
    return json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=pairs,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError('Nonfinite JSON: '+x)))


def safe_path(root, relative, ceiling=None):
    root = Path(root).resolve()
    ceiling = Path(ceiling).resolve() if ceiling else root
    if not isinstance(relative, str) or Path(relative).is_absolute() or '\\' in relative:
        raise ValueError('Invalid relative path: ' + repr(relative))
    target = (root / relative).resolve()
    if not target.is_relative_to(ceiling):
        raise ValueError('Path escapes allowed source/output root: ' + relative)
    return target


def verify_bindings(manifest, source_root, out):
    checks = []
    # The baseline binds ../gs8-pxl-v3/cad-requirements-lock.txt. Permit only
    # the common CAD parent, never arbitrary filesystem traversal.
    for category, root, ceiling in [('sources', source_root, source_root.parent), ('files', out, out)]:
        mapping = manifest.get(category)
        if not isinstance(mapping, dict) or not mapping:
            raise ValueError('Manifest lacks nonempty ' + category)
        for rel, expected in sorted(mapping.items()):
            if not isinstance(expected, str) or not re.fullmatch('[a-f0-9]{64}', expected):
                raise ValueError('Invalid SHA-256 for ' + category + '/' + rel)
            p = safe_path(root, rel, ceiling)
            actual = sha(p)
            if actual != expected:
                raise ValueError('Hash mismatch: ' + category + '/' + rel)
            checks.append({'category': category, 'path': rel, 'sha256': actual})
    return checks


def analyze_binary_stl(path, weld_mm=1e-6):
    data = Path(path).read_bytes()
    if len(data) < 84:
        raise ValueError('Binary STL header is incomplete')
    n = struct.unpack_from('<I', data, 80)[0]
    if n == 0 or len(data) != 84 + 50*n:
        raise ValueError('Binary STL must have nonzero exact triangle record count')
    dtype = np.dtype([('normal', '<f4', (3,)), ('v', '<f4', (3, 3)), ('attr', '<u2')])
    records = np.frombuffer(data, dtype=dtype, count=n, offset=84)
    tri = records['v'].astype(np.float64)
    if not np.isfinite(tri).all() or not np.isfinite(records['normal']).all():
        raise ValueError('Nonfinite STL coordinate or normal')
    points = tri.reshape(-1, 3)
    if np.max(np.abs(points))/weld_mm > np.iinfo(np.int64).max/2:
        raise ValueError('Coordinates exceed safe quantization range')
    quantized = np.rint(points / weld_mm).astype(np.int64)
    unique, inv = np.unique(quantized, axis=0, return_inverse=True)
    f = inv.reshape(-1, 3)
    edge_directed = np.concatenate([f[:, [0,1]], f[:, [1,2]], f[:, [2,0]]])
    edge_sorted = np.sort(edge_directed, axis=1)
    _, edge_inv, counts = np.unique(edge_sorted, axis=0, return_inverse=True, return_counts=True)
    orientation = np.bincount(edge_inv, weights=np.where(edge_directed[:,0]<edge_directed[:,1], 1, -1))
    area2 = np.linalg.norm(np.cross(tri[:,1]-tri[:,0], tri[:,2]-tri[:,0]), axis=1)
    degenerate = np.logical_or(area2 <= weld_mm*weld_mm,
                              (f[:,0]==f[:,1]) | (f[:,1]==f[:,2]) | (f[:,2]==f[:,0]))
    _, face_counts = np.unique(np.sort(f,axis=1), axis=0, return_counts=True)
    # A watertight edge set can still have two surfaces meeting at only a
    # vertex. Check each vertex's link is one connected, degree-two cycle.
    links = defaultdict(list)
    for a,b,c in f.tolist():
        links[a].append((b,c)); links[b].append((c,a)); links[c].append((a,b))
    bad_links = 0
    for edges in links.values():
        adjacency = defaultdict(list)
        for a,b in edges:
            adjacency[a].append(b); adjacency[b].append(a)
        if not adjacency or any(len(v)!=2 for v in adjacency.values()):
            bad_links += 1
            continue
        seen = set(); pending = [next(iter(adjacency))]
        while pending:
            p = pending.pop()
            if p in seen: continue
            seen.add(p); pending.extend(adjacency[p])
        if len(seen) != len(adjacency): bad_links += 1
    # Signed volume is descriptive; for multiple shells it is not proof of
    # valid non-overlapping occupied material.
    volume = float(np.einsum('ij,ij->i', tri[:,0], np.cross(tri[:,1],tri[:,2])).sum()/6)
    low,high = points.min(axis=0),points.max(axis=0)
    result = dict(triangles=int(n), welded_vertices=len(unique), weld_tolerance_mm=weld_mm,
                  boundary_edges=int(np.count_nonzero(counts==1)),
                  nonmanifold_edges=int(np.count_nonzero(counts!=2)),
                  inconsistent_winding_edges=int(np.count_nonzero(orientation!=0)),
                  degenerate_triangles=int(np.count_nonzero(degenerate)),
                  duplicate_faces=int(np.sum(face_counts-1)), invalid_vertex_links=bad_links,
                  signed_volume_mm3=volume, bounds_mm=[low.tolist(),high.tolist()],
                  dimensions_mm=(high-low).tolist(), sha256=hashlib.sha256(data).hexdigest(),
                  self_intersections_checked=False, physical_print_release=False)
    result['topology_pass'] = all(result[k]==0 for k in
        ('nonmanifold_edges','inconsistent_winding_edges','degenerate_triangles','duplicate_faces','invalid_vertex_links')) and volume>0
    return result


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    here=Path(__file__).resolve().parent
    p.add_argument('--cad-dir', type=Path, default=here.parent)
    p.add_argument('--export', type=Path, default=here/'innomaker/out/compact-kowa_lm6hc', help='read-only export folder (input)')
    p.add_argument('--out', type=Path, default=here/'innomaker/checks/compact-kowa_lm6hc', help='report folder; never the export folder')
    p.add_argument('--manifest',default='manifest.json')
    p.add_argument('--report',type=Path)
    args=p.parse_args(argv); out=args.export.resolve(); source=args.cad_dir.resolve(); report_dir=args.out.resolve()
    if report_dir==out or out in report_dir.parents: raise ValueError('--out must be outside the export folder')
    mf=out/args.manifest; initial=sha(mf); m=json_load(mf)
    before=verify_bindings(m,source,out)
    rows=[]
    for rel in sorted(m['files']):
        if not rel.lower().endswith('.stl'): continue
        row=analyze_binary_stl(safe_path(out,rel)); name=Path(rel).stem
        row.update(id=name,path=rel,role='production print' if rel in m.get('production_prints',{}).get('files',[]) else ('centring gauge' if name=='centring_gauge' else 'auxiliary STL'))
        pose=m.get('print_poses',{}).get(name)
        if pose:
            expected=pose.get('footprint_mm')
            row['recorded_print_dimensions_mm']=expected
            row['dimensions_match_print_pose']=bool(expected and np.allclose(row['dimensions_mm'],expected,rtol=0,atol=.02))
            row['bed_z_zero']=abs(row['bounds_mm'][0][2])<=.002
            dx,dy,dz=row['dimensions_mm']
            row['fits_250x210x220_mm']=min(dx,dy)<=210.002 and max(dx,dy)<=250.002 and dz<=220.002
            row['status']='PASS' if row['topology_pass'] and row['dimensions_match_print_pose'] and row['bed_z_zero'] and row['fits_250x210x220_mm'] else 'FAIL'
        else:
            row['status']='PASS' if row['topology_pass'] else 'FAIL'
            row['bounds_scope']='Finite geometry bounds only: no manifest print pose for this auxiliary STL'
        rows.append(row)
    if not rows: raise ValueError('No manifest-bound STL files to validate')
    after=verify_bindings(m,source,out)
    if sha(mf)!=initial or before!=after: raise ValueError('Inputs changed during validation')
    report=dict(scope='Manifest-bound binary STL edge/vertex-link topology and finite bounds only; no repair, self-intersection test, slicer, layer strength, or physical release.',
                status='PASS' if all(r['status']=='PASS' for r in rows) else 'FAIL',
                manifest_sha256=initial,validator_sha256=sha(__file__),numpy_version=np.__version__,
                checked_source_count=len(m['sources']),checked_file_count=len(m['files']),
                all_bindings_rechecked_at_end=True,production_print_count=sum(r['role']=='production print' for r in rows),centring_gauge_count=sum(r['role']=='centring gauge' for r in rows),rows=rows,physical_print_release=False)
    target=(args.report or report_dir/'innomaker-stl-checks.json').resolve()
    if out in target.parents: raise ValueError('Report must be written outside the export folder')
    if target.resolve() in [mf.resolve(),Path(__file__).resolve()]+[safe_path(out,r) for r in m['files']]+[safe_path(source,r,source.parent) for r in m['sources']]:
        raise ValueError('Report must not overwrite a manifest-bound input')
    target.parent.mkdir(parents=True,exist_ok=True);write_text(target,json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':report['status'],'stl_files':len(rows),'report':target.name}))
    return int(report['status']!='PASS')


if __name__=='__main__':
    try: raise SystemExit(main())
    except Exception as exc:
        print(type(exc).__name__+': '+str(exc),file=sys.stderr);raise SystemExit(2)

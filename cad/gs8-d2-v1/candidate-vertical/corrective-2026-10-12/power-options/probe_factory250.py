#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Isolated 250 mm factory-lead service-corridor screen; never a fit release.

Default mode is CAD-free. --cad reads current manifest-bound STEP solids and
must run through run_locked.py. Selected sources and exports are never changed.
Wire OD, roots, connector face spacing and usable stock length are CONDITIONAL.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import sys

HERE = Path(__file__).resolve().parent
CV = HERE.parents[1]
ROOT = CV.parents[2]
sys.path.insert(0, str(CV))
from cv_io import read_text, write_text
import routes as R
import harness_rules as HR
import steps as ST

KNOTS = {
    "positive": [[-65.5, 8.3, 63], [-32, 8.3, 25], [-32, -5.8, 10],
                 [-51.2, -5.8, -8], [-51.2, -5.8, -125]],
    "negative": [[-65.5, 12.7, 63], [-31.5, 12.7, 20], [-31.5, -.8, 3],
                 [-51.2, -.8, -8], [-51.2, -.8, -125]],
}
OD = 3.7
RADIUS = 9.25
STEP = .4


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cad', action='store_true')
    ap.add_argument('--out', type=Path)
    args = ap.parse_args()
    target = args.out or HERE / ('factory250-cad.json' if args.cad else 'factory250-proxy.json')
    meta_path = CV / 'out/compact-kowa_lm6hc/manifest.json'
    meta = json.loads(read_text(meta_path))
    rows = {r['id']: r for r in meta['rows']}
    out = R.build()
    H = HR.collect(out, rows, R.L, ST)
    HR.neighbour_context(H, out, json.loads(read_text(CV / 'out/fps-service-study/mated-carry-input.json')))
    present, _moving = HR.pose_state(ST, HR.CORRIDOR_OP)
    excluded = {'x1203', 'xt30_pair', 'pack'}
    targets = HR._targets(H, present, set(), (0., 0., 0.), excluded)
    # Same end-part exceptions as the selected corridor check; no new exceptions.
    targets += [dict(id='plug ' + pid, kind='keepout', disp=(0., 0., 0.), box=b)
                for pid, b in H['plugs'].items()
                if H.get('plug_cable', {}).get(pid) not in ('pigtail', 'pack_lead', None)]
    targets += [dict(id='housing ' + hid, kind='keepout', disp=(0., 0., 0.), box=h['box'])
                for hid, h in H['housings'].items()]
    result = {
        'status': 'EXPLORATORY ONLY; service corridor screen, not an installed or deployment pass',
        'source_paths_relative_to_repository': True,
        'inputs': {p.relative_to(ROOT).as_posix(): sha(p) for p in
                   (meta_path, CV / 'routes.py', CV / 'power_routes.py', CV / 'signal_routes.py',
                    CV / 'harness_rules.py', CV / 'steps.py', Path(__file__).resolve())},
        'supplier_lead': 'Pimoroni CAB0244, nominal 250 mm / 14 AWG; actual usable length, OD and resistance unknown',
        'conditional_od_mm': OD, 'analysis_radius_mm': RADIUS,
        'sampling_step_max_mm': STEP,
        'curve_chord_radial_error_bound_mm': STEP * STEP / (8 * RADIUS),
        'screen_radius_mm': OD / 2 + HR.MEMBER_TOL,
        'service_allowance_mm': HR.reach_margin(250),
        'face_out_mm': 15, 'pose': HR.CORRIDOR_OP,
        'existing_endpoint_exemptions': sorted(excluded),
        'unresolved': ['supplier dimensions and resistance', 'actual pad/root construction',
                       'installed slack storage and retention', 'full deployment sweep and hand access',
                       'CAB0244 actual housing and cross-mating with received pack',
                       'positive fuse and negative fuse-bypass local construction',
                       'printed passages, valid solids and loaded ligaments after any proposed change'],
        'cores': [],
    }
    shapes = {}
    if args.cad:
        import cadquery as cq
        from OCP.BRepExtrema import BRepExtrema_DistShapeShape
        def solid(t):
            if t['kind'] == 'keepout':
                b = t['box']
                return cq.Solid.makeBox(b[1]-b[0], b[3]-b[2], b[5]-b[4], cq.Vector(b[0],b[2],b[4]))
            name = t['id'].split(' ')[0]
            if name not in shapes:
                p = CV / 'out/compact-kowa_lm6hc/step' / (name + '.step')
                if sha(p) != meta['files']['step/' + name + '.step']:
                    raise ValueError('Manifest/STEP drift: ' + name)
                shapes[name] = cq.importers.importStep(str(p)).val()
                result['inputs'][p.relative_to(ROOT).as_posix()] = sha(p)
            return shapes[name].translate(cq.Vector(*t['disp'])) if any(t['disp']) else shapes[name]
    curves = {}
    for cid, knots in KNOTS.items():
        curve = R.rounded_path(knots, RADIUS, 8, 24 if cid == 'positive' else 4, STEP)
        if curve['errors']:
            raise ValueError(curve['errors'])
        points = curve['sampled_centerline']
        curves[cid] = points
        root_allowance = math.dist(knots[0], [-65.5, 14.6, 63])
        row = dict(id=cid, knots=knots, corridor_mm=curve['rounded_length_mm'],
                   unmeasured_root_allowance_mm=root_allowance,
                   allocated_length_mm=250,
                   margin_after_unchanged_allowance_mm=250-root_allowance-curve['rounded_length_mm']-HR.reach_margin(250),
                   final_axial_straight_mm=math.dist(points[-1], knots[-2])-curve['corner_trim_mm'][-2],
                   source_proxy_hits=[], cable_neighbours=[], broad_phase_targets=[], cad_distances=[])
        for o in out['obstacles']:
            if o['id'] in ('pack', 'xt30_selected_housing') or o['id'].startswith('ups_'):
                continue
            if any(R.obstacle_overlap({a:[p[i]-OD/2-HR.MEMBER_TOL,p[i]+OD/2+HR.MEMBER_TOL]
                                       for i,a in enumerate('xyz')}, o) for p in points):
                row['source_proxy_hits'].append(o['id'])
        for name, pts, diameter in HR.neighbour_cables(H, 'pigtail_' + cid):
            if name.split(':')[0] in ('pigtail_positive','pigtail_negative','pack_lead'):
                continue
            d = HR.polyline_distance(points, pts, HR.SEPARATION_TOL)
            need = (OD + diameter) / 2
            row['cable_neighbours'].append(dict(id=name, centerline_distance_mm=d, need_mm=need, margin_mm=d-need))
        row['cable_neighbours'].sort(key=lambda r:r['margin_mm'])
        radius = OD / 2 + HR.MEMBER_TOL
        bounds = [v for i in range(3) for v in (min(p[i] for p in points)-radius, max(p[i] for p in points)+radius)]
        possible = [t for t in targets if HR.boxes_overlap(bounds,t['box'])]
        row['broad_phase_targets'] = [t['id'] for t in possible]
        if args.cad:
            wire = cq.Compound.makeCompound([cq.Edge.makeLine(cq.Vector(*a),cq.Vector(*b))
                                            for a,b in zip(points,points[1:]) if math.dist(a,b)>1e-10])
            for t in possible:
                dss = BRepExtrema_DistShapeShape(wire.wrapped, solid(t).wrapped)
                if not dss.IsDone():
                    raise RuntimeError('Distance solver failed: ' + t['id'])
                d = dss.Value()
                witness = dss.PointOnShape1(1)
                row['cad_distances'].append(dict(id=t['id'], kind=t['kind'], minimum_distance_mm=d,
                    envelope_margin_mm=d-radius, on_curve_xyz=[witness.X(),witness.Y(),witness.Z()]))
                print(cid, t['id'], round(d-radius,4), flush=True)
        result['cores'].append(row)
    result['pair_centerline_distance_mm'] = HR.polyline_distance(curves['positive'],curves['negative'],.05)
    result['pair_insulation_gap_mm'] = result['pair_centerline_distance_mm'] - OD
    result['method'] = ('Kernel minimum distance from sampled polyline to manifest-bound solids/keepout boxes; '
                        'radius includes existing MEMBER_TOL, larger than arc chord error. '
                        'This rejects or retains one service pose only; no selected gate is changed.')
    write_text(target, json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(target.relative_to(ROOT).as_posix())
    print(json.dumps({r['id']: dict(margin_mm=r['margin_after_unchanged_allowance_mm'],
          source_hits=r['source_proxy_hits'], cable_hits=[n for n in r['cable_neighbours'] if n['margin_mm']<0])
          for r in result['cores']}, indent=2))


if __name__ == '__main__':
    main()

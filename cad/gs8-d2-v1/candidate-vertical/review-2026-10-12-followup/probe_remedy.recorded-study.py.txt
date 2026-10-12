#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""One isolated factory250 passage/storage/run-wire remedy; not a release.

--cad must run under run_locked.py. Its only STEP writes are variant-step below
this report directory. All candidate wires and actual CAB0244 dimensions remain
conditional. A rejected run-wire pair is kept as evidence, never waived.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import sys
import factory250_variant as V

HERE, CV = V.HERE, V.CV
ROOT = CV.parents[2]
from cv_io import read_text, write_text
import routes as R
import harness_rules as HR
import steps as ST

RUN_KNOTS = {
    'run_pin37': [[-87.99,-15.4,11.77],[-87.99,-23.3,11.77],[-87.99,-23.3,63.01558761391789],
        [-41,-23.3,63.01558761391789],[-41,-16,66.01558761391789],[-41,8,66.01558761391789],
        [-41,21.4,63.01558761391789],[-41,21.4,5.8],[-41,2.5,5.8],[-30,2.5,5.8],[-30,5.25,-14.2]],
    'run_pin39': [[-90.53,-15.4,11.77],[-90.53,-21.6,11.77],[-90.53,-21.6,64.75281049404293],
        [-41,-21.6,64.75281049404293],[-41,-16,67.75281049404293],[-41,8,67.75281049404293],
        [-41,23.6,64.75281049404293],[-41,23.6,4],[-41,7.5,4],[-32,7.5,4],[-32,5.25,-14.2]],
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def box_for_points(points, radius):
    return [v for i in range(3) for v in (min(p[i] for p in points)-radius,max(p[i] for p in points)+radius)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cad', action='store_true')
    args = ap.parse_args()
    meta_path = CV/'out/compact-kowa_lm6hc/manifest.json'
    meta = json.loads(read_text(meta_path))
    rows = {r['id']:r for r in meta['rows']}
    out = R.build()
    h = HR.collect(out,rows,R.L,ST)
    HR.neighbour_context(h,out,json.loads(read_text(CV/'out/fps-service-study/mated-carry-input.json')))
    variant = V.build()
    result = dict(status='BLOCKED EXPLORATORY REMEDY; no selected design or purchased part changed',
        conditional_inputs=dict(lead='Pimoroni CAB0244',finished_path_per_polarity_mm=250,
            od_mm=V.OD,analysis_radius_mm=V.RADIUS,connector_exit_pitch_mm=5,
            connector_pose='selected hypothetical XT30U pose retained only as a study datum',
            service_allowance_mm=25,face_out_mm=15,loaded_neck_distance_requirement_mm=1.6,
            actual_wire_dimensions_resistance_and_usable_length_measured=False),
        inputs={p.relative_to(ROOT).as_posix():sha(p) for p in
                (meta_path,CV/'routes.py',CV/'power_routes.py',CV/'signal_routes.py',CV/'harness_rules.py',
                 CV/'steps.py',HERE/'factory250_variant.py',Path(__file__).resolve())},
        variant=variant, proposed_run_curves={}, checks=[], printed_remedy=[], neck_screen=[],
        open_gates=['CAB0244 metrology, copper/factory-joint resistance and usable-length convention',
                    'actual pack contact role/polarity/protection and cross-mating',
                    'pad and connector root construction','retention and complete flexible deployment',
                    'complete other-cable service and hand access','all loaded-wall/strength qualification',
                    '8.6A hot assembly voltage-drop measurement'], artifacts=[])
    runs = {}
    for name,knots in RUN_KNOTS.items():
        curve = R.rounded_path(knots,3.2,3,3,.4)
        if curve['errors']:
            raise ValueError(curve['errors'])
        runs[name] = curve['sampled_centerline']
        result['proposed_run_curves'][name] = curve
    a,b = variant['cores']
    for state,key in [('installed','installed_points'),('service','service_curve')]:
        pa = a[key] if state=='installed' else a[key]['sampled_centerline']
        pb = b[key] if state=='installed' else b[key]['sampled_centerline']
        distance = HR.polyline_distance(pa,pb,.05)
        result['checks'].append(dict(id=state+'_power_pair',centerline_distance_mm=distance,
                                    required_mm=V.OD,insulation_margin_mm=distance-V.OD))
    distance = HR.polyline_distance(runs['run_pin37'],runs['run_pin39'],.05)
    unsimplified = HR.polyline_distance(runs['run_pin37'],runs['run_pin39'],0)
    result['checks'].append(dict(id='proposed_run_pair',centerline_distance_mm=distance,
        method='Conservative simplified-polyline lower bound; unsimplified distance is also reported',
        unsimplified_polyline_distance_mm=unsimplified,
        arc_distance_upper_bound_mm=unsimplified+2*(.4*.4/(8*3.2)),
        required_mm=1.6,insulation_margin_mm=distance-1.6,
        status='fail' if distance<1.6 else 'geometric-only',
        note='This pair was the best bounded attempt; any overlap remains a hard blocker.'))
    for c in variant['cores']:
        for state,points in [('installed',c['installed_points']),('service',c['service_curve']['sampled_centerline'])]:
            rr = dict(id=state+'_'+c['id'],source_hits=[],neighbour_margins=[],cad_distances=[])
            for o in out['obstacles']:
                if o['id']=='xt30_selected_housing' or o['id'].startswith('ups_') or (state=='service' and o['id']=='pack'):
                    continue
                if any(R.obstacle_overlap({ax:[p[i]-1.95,p[i]+1.95] for i,ax in enumerate('xyz')},o) for p in points):
                    rr['source_hits'].append(o['id'])
            for name,pts,diameter in HR.neighbour_cables(h,'pigtail_'+c['id']):
                if name.split(':')[0] in ('pigtail_positive','pigtail_negative','pack_lead'):
                    continue
                pts = runs.get(name,pts)
                d = HR.polyline_distance(points,pts,.05)
                rr['neighbour_margins'].append(dict(id=name,centerline_distance_mm=d,
                    required_mm=(V.OD+diameter)/2,margin_mm=d-(V.OD+diameter)/2))
            rr['neighbour_margins'].sort(key=lambda q:q['margin_mm'])
            result['checks'].append(rr)
    if args.cad:
        import cadquery as cq
        from OCP.BRepExtrema import BRepExtrema_DistShapeShape
        shapes = {}
        def box(b):
            return cq.Solid.makeBox(b[1]-b[0],b[3]-b[2],b[5]-b[4],cq.Vector(b[0],b[2],b[4]))
        def shape(name):
            if name not in shapes:
                f = CV/'out/compact-kowa_lm6hc/step'/(name+'.step')
                if sha(f)!=meta['files']['step/'+name+'.step']:
                    raise ValueError('STEP drift: '+name)
                shapes[name] = cq.importers.importStep(str(f)).val()
                result['inputs'][f.relative_to(ROOT).as_posix()] = sha(f)
            return shapes[name]
        def bbox(s):
            b=s.BoundingBox()
            return [b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax]
        tools = []
        radius = 2.20  # OD/2 + .30 passage reserve + .05 polyline simplification reserve
        for c in variant['cores']:
            for pts in (c['local_points'],c['service_curve']['sampled_centerline']):
                pts = HR.simplify_polyline(pts,.05)
                for p,q in zip(pts,pts[1:]):
                    if min(p[2],q[2])-radius>=3 or max(p[2],q[2])+radius<=-12:
                        continue
                    delta=cq.Vector(*q)-cq.Vector(*p)
                    if delta.Length>1e-9:
                        tools.append(cq.Solid.makeCylinder(radius,delta.Length,cq.Vector(*p),delta.normalized()))
                for p in pts:
                    if -12-radius<p[2]<3+radius:
                        tools.append(cq.Solid.makeSphere(radius,cq.Vector(*p),angleDegrees1=-90,angleDegrees2=90))
        baseline_tub = shape('tub')
        print('checking new cutter distance to loaded necks',flush=True)
        for tongue in R.L.TONGUES:
            neck = baseline_tub.intersect(box(HR.bb(tongue['neck'])))
            # Intersecting the original tub retains its actual corner relief.
            if not neck.Solids():
                raise ValueError('No loaded neck found: '+tongue['id'])
            d = min(neck.distance(tool) for tool in tools)
            result['neck_screen'].append(dict(id=tongue['id'],minimum_new_tool_to_existing_neck_mm=d,
                required_mm=1.6,status='pass-distance-bound' if d>=1.6 else 'fail',
                note='Distance bound only; does not replace complete wall, load, fatigue or strength checks.'))
        for name in ('tub','base_grip'):
            old=shape(name);new=old;count=0
            # Match the selected passage helper's reversed sequential ordering.
            for index,tool in enumerate(reversed(tools)):
                if index%25==0:
                    print('passage tools',name,index,'of',len(tools),flush=True)
                if not HR.boxes_overlap(bbox(new),bbox(tool)) or new.intersect(tool).Volume()<1e-8:
                    continue
                new=new.cut(tool)
                if not new.isValid() or len(new.Solids())!=1:
                    raise ValueError('Isolated passage cut broke single-solid validity: '+name)
                count+=1
            shapes[name]=new
            directory=HERE/'variant-step';directory.mkdir(exist_ok=True)
            f=directory/(name+'.step');cq.exporters.export(new,str(f))
            result['artifacts'].append(dict(path=f.relative_to(ROOT).as_posix(),sha256=sha(f)))
            result['printed_remedy'].append(dict(id=name,valid_single_solid=True,cuts=count,
                removed_mm3=old.Volume()-new.Volume(),old_bbox_mm=bbox(old),new_bbox_mm=bbox(new),
                bbox_unchanged=max(abs(x-y) for x,y in zip(bbox(old),bbox(new)))<1e-6,
                note='Unchanged bounding box alone is not exterior-surface or strength qualification.'))
            print('isolated passage',name,count,flush=True)
        present,_=HR.pose_state(ST,HR.CORRIDOR_OP)
        for c in variant['cores']:
            for state,points in [('installed',c['installed_points']),('service',c['service_curve']['sampled_centerline'])]:
                rr=next(x for x in result['checks'] if x['id']==state+'_'+c['id'])
                exclude={'x1203','xt30_pair'} | ({'pack'} if state=='service' else set())
                targets=HR._targets(h,present,set(),(0.,0.,0.),exclude)
                targets += [dict(id='plug '+pid,kind='keepout',box=bb)
                    for pid,bb in h['plugs'].items()
                    if h.get('plug_cable',{}).get(pid) not in ('pigtail','pack_lead',None)]
                targets += [dict(id='housing '+hid,kind='keepout',box=hh['box'])
                            for hid,hh in h['housings'].items()]
                wire=cq.Compound.makeCompound([cq.Edge.makeLine(cq.Vector(*p),cq.Vector(*q))
                    for p,q in zip(points,points[1:]) if math.dist(p,q)>1e-9])
                bounds=box_for_points(points,1.95)
                for t in targets:
                    if not HR.boxes_overlap(bounds,t['box']):
                        continue
                    obstacle=box(t['box']) if t['kind']=='keepout' else shape(t['id'])
                    dss=BRepExtrema_DistShapeShape(wire.wrapped,obstacle.wrapped)
                    if not dss.IsDone():
                        raise ValueError('Kernel distance failed: '+t['id'])
                    witness=dss.PointOnShape1(1);d=dss.Value()
                    rr['cad_distances'].append(dict(id=t['id'],distance_mm=d,
                        nominal_insulation_clearance_mm=d-V.OD/2,screen_margin_mm=d-1.95,
                        on_curve_xyz=[witness.X(),witness.Y(),witness.Z()]))
                print(state,c['id'],'distances complete',flush=True)
        fuse=cq.Solid.makeCylinder(2.5,20,cq.Vector(*variant['fuse_start']),
            (cq.Vector(*variant['fuse_end'])-cq.Vector(*variant['fuse_start'])).normalized())
        result['fuse_installed'] = {name:dict(distance_mm=fuse.distance(shape(name)),
            intersection_mm3=fuse.intersect(shape(name)).Volume()) for name in ('tub','base_grip','pack')}
        negative=next(c for c in variant['cores'] if c['id']=='negative')['installed_points']
        negative_wire=cq.Compound.makeCompound([cq.Edge.makeLine(cq.Vector(*p),cq.Vector(*q))
            for p,q in zip(negative,negative[1:]) if math.dist(p,q)>1e-9])
        result['negative_wire_to_fuse_nominal_insulation_clearance_mm']=negative_wire.distance(fuse)-V.OD/2
    filename='factory250-remedy-cad.json' if args.cad else 'factory250-remedy-proxy.json'
    result['input_drift_during_run'] = [rel for rel,bound in result['inputs'].items()
                                        if sha(ROOT/rel) != bound]
    write_text(HERE/filename,json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(filename,flush=True)
    print(json.dumps([c for c in result['checks'] if 'insulation_margin_mm' in c],indent=2),flush=True)


if __name__=='__main__':
    main()

# SPDX-License-Identifier: MIT
"""Private conditional 14 AWG geometry. No selected source is modified.

This uses the selected hypothetical connector pose/exit pitch as a study datum.
Those dimensions have NOT been established for Pimoroni CAB0244.
"""
from pathlib import Path
import math
import re
import sys
import types

HERE = Path(__file__).resolve().parent
CV = HERE.parents[1]
sys.path.insert(0, str(CV))
from cv_io import read_text
import routes as R

RADIUS = 9.25
OD = 3.7
SERVICE_KNOTS = {
    'positive': [[-65.5,8.3,63],[-31.2,8.3,25],[-31.2,-5.8,10],[-51.2,-5.8,-8],[-51.2,-5.8,-125]],
    'negative': [[-65.5,12.7,63],[-31.2,12.7,20],[-31.2,-.8,3],[-51.2,-.8,-8],[-51.2,-.8,-125]],
}
STORAGE_PARAMETERS = {
    'positive': [-29.5,48.,-18.5,-50.,-100.,57.5],
    'negative': [-31.2,40.,-22.9,-50.,-103.,39.],
}


def local_geometry():
    source = read_text(CV / 'power_routes.py')
    marker = '        # The baseline gives one assumed pad point'
    if source.count(marker) != 1:
        raise ValueError('Selected local-construction boundary changed')
    source = source[:source.index(marker)]
    # All standalone 8s in this explicitly bounded local-construction block are
    # bend radii/multipliers. No current, fuse, contact or cutoff inputs occur here.
    source = re.sub(r'\b8\b', '9.25', source).replace('math.radians(110)', 'math.radians(90)')
    source += ('        rows.append(dict(id=name,local_points=local,local_length_mm=local_length,local_end=Q,face=face))\n'
               '    return dict(cores=rows,fuse_start=S,fuse_end=T,wrap=wrap)\n')
    private = types.ModuleType('_isolated_factory250_local')
    exec(compile(source, 'isolated_factory250_local', 'exec'), private.__dict__)
    return private.build(R)


def line(a,b,step=.4):
    count = max(1,math.ceil(math.dist(a,b)/step))
    return [R.vadd(a,R.vmul(R.vsub(b,a),i/count)) for i in range(count+1)]


def arc(start,tangent,normal,angle):
    count = max(2,math.ceil(RADIUS*angle/.4))
    return [R.vadd(start,R.vadd(R.vmul(tangent,RADIUS*math.sin(angle*i/count)),
                               R.vmul(normal,RADIUS*(1-math.cos(angle*i/count))))) for i in range(count+1)]


def hump(x0,x1,lane,z0,z1,high):
    def side(drop):
        angle = math.acos(1-drop/(2*RADIUS)) if drop <= 2*RADIUS else math.pi/2
        leg = max(0,drop-2*RADIUS)
        return angle,leg,2*RADIUS*math.sin(angle),2*RADIUS*angle+leg
    a1,l1,x1s,length1 = side(high-z0)
    a2,l2,x2s,length2 = side(high-z1)
    flat = x0-x1-x1s-x2s
    if flat < 0:
        raise ValueError('Hump cannot fit without reversing its middle leg')
    points = arc([x0,lane,z0],[-1,0,0],[0,0,1],a1)
    tangent = [-math.cos(a1),0,math.sin(a1)]
    end = R.vadd(points[-1],R.vmul(tangent,l1))
    points += line(points[-1],end)[1:]
    points += arc(points[-1],tangent,[-math.sin(a1),0,-math.cos(a1)],a1)[1:]
    points += line(points[-1],R.vadd(points[-1],[-flat,0,0]))[1:]
    points += arc(points[-1],[-1,0,0],[0,0,-1],a2)[1:]
    tangent = [-math.cos(a2),0,-math.sin(a2)]
    points += line(points[-1],R.vadd(points[-1],R.vmul(tangent,l2)))[1:]
    points += arc(points[-1],tangent,[-math.sin(a2),0,math.cos(a2)],a2)[1:]
    return points,length1+length2+flat


def curvature_radius(points):
    radii = []
    for a,b,c in zip(points,points[1:],points[2:]):
        u,v = R.vsub(b,a),R.vsub(c,a)
        cross = [u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
        twice_area = R.norm(cross)
        if twice_area > 1e-10:
            radii.append(math.dist(a,b)*math.dist(b,c)*math.dist(a,c)/(2*twice_area))
    return min(radii)


def build():
    local = local_geometry()
    for core in local['cores']:
        cid = core['id']
        root = SERVICE_KNOTS[cid][0]
        q = core['local_end']
        front,zbase,lane,start,rear,endbase = STORAGE_PARAMETERS[cid]
        prefix = R.rounded_path([root,[front,root[1],zbase],[front,lane,zbase],[start,lane,zbase]],RADIUS,8,0,.4)
        if prefix['errors']:
            raise ValueError(prefix['errors'])
        transition = []
        transition_drop = 12 if cid == 'positive' else 13
        for i in range(121):
            t = i/120
            blend = 10*t**3-15*t**4+6*t**5
            transition.append([rear,lane+(q[1]-lane)*blend,endbase-RADIUS-transition_drop*t])
        if transition[-1][2] < q[2]+RADIUS or rear+RADIUS > q[0]:
            raise ValueError('Tail would reverse to reach its local exit')
        tail = arc([rear+RADIUS,lane,endbase],[-1,0,0],[0,0,-1],math.pi/2)+transition[1:]
        tail += line(transition[-1],[rear,q[1],q[2]+RADIUS])[1:]
        tail += arc(tail[-1],[0,0,-1],[1,0,0],math.pi/2)[1:]
        tail += line(tail[-1],q)[1:]
        root_allowance = math.dist(root,[-65.5,14.6,63])
        fixed = (prefix['rounded_length_mm']+sum(math.dist(a,b) for a,b in zip(tail,tail[1:]))
                 +core['local_length_mm']+root_allowance)
        low,high = max(zbase,endbase),94.
        minimum = fixed+hump(start,rear+RADIUS,lane,zbase,endbase,low)[1]
        for _ in range(60):
            mid = (low+high)/2
            if fixed+hump(start,rear+RADIUS,lane,zbase,endbase,mid)[1] > 250:
                high = mid
            else:
                low = mid
        stored,height = hump(start,rear+RADIUS,lane,zbase,endbase,(low+high)/2),(low+high)/2
        points = prefix['sampled_centerline']+stored[0][1:]+tail[1:]+list(reversed(core['local_points']))[1:]
        service = R.rounded_path(SERVICE_KNOTS[cid],RADIUS,8,24 if cid=='positive' else 4,.4)
        minimum_finished = max(minimum,root_allowance+service['rounded_length_mm'])/.9
        rigid_zone = 20 if cid=='positive' else 0
        core.update(root=root,root_allowance_mm=root_allowance,installed_points=points,
                    path_allocation_mm=fixed+stored[1],minimum_storage_family_mm=minimum,
                    stored_excess_mm=250-minimum,service_curve=service,
                    service_margin_mm=250-root_allowance-service['rounded_length_mm']-25,
                    rigid_inline_zone_mm=rigid_zone,
                    proposed_exposed_wire_nominal_mm=250-rigid_zone,
                    minimum_finished_allocation_for_storage_mm=minimum/.9,
                    minimum_finished_allocation_for_service_mm=(root_allowance+service['rounded_length_mm'])/.9,
                    minimum_finished_allocation_mm=minimum_finished,
                    minimum_exposed_wire_geometric_mm=minimum_finished-rigid_zone,
                    length_convention_note='Excludes connector body; positive subtracts the 20 mm rigid inline zone. Actual strip, solder overlap, factory joint and root datums remain unmeasured. Catalog 250 mm does not prove this usable length.',
                    hump_top_z_mm=height,local_minimum_sampled_curvature_mm=curvature_radius(core['local_points']),
                    installed_minimum_sampled_curvature_mm=curvature_radius(points))
    local.update(od_mm=OD,analysis_radius_mm=RADIUS,
                 wrap_minimum_sampled_curvature_mm=curvature_radius(local['wrap']),
                 fuse_to_wrap_nominal_insulation_gap_mm=5-2.5-OD/2,
                 status='Conditional exploratory geometry; actual CAB0244 dimensions, retention and deployment unqualified')
    return local

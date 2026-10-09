# SPDX-License-Identifier: MIT
"""Full intact300mm compact HDMI material geometry; no CAD dependency.

The full strip is modeled, including its R3 developable miter and deployable
serpentine. This does not certify actual laminate radius, EMI or service life.
"""
import math
from routes import AXES, unit, vsub, vadd, vmul, cross, rounded_path, obstacle_overlap, hull

def ribbon300(length,stack_y=22.2,evf_shift_y=11,obstacles=(),right_inner=-25.5,left_inner=25.2,profile=None,pose="installed",lift=0,drop=0,initial_u=5,tail=2,right_x=-70):
    """Natural U turn + one isometric 45-degree cylindrical miter fold.

    Adafruit3557 Pi head / 3556 EVF head. The miter is meshed in material
    coordinates; it is NOT a perpendicular-section loft. No edgewise stretch or
    arbitrary plane twist is introduced. Radius/material/clocking are still gates.
    """
    width=10.;thick=.4;R=3.;rr=5.;q=math.sqrt(.5)
    pi=[-59.8,stack_y-21.85-15,77.5+lift]
    evf=[-141.6+154-length,-5.5+evf_shift_y,37.3-drop]
    sf=math.sqrt(2)*math.pi*R
    origin=[pi[0],evf[1]-math.pi*R*q,77.5+lift+2*initial_u]
    a=[-q,q,0];b=[q,q,0];up=[0,0,1]
    frames=[];segments=[];centerline=[]
    def mesh(corners0,corners1):
        cs=corners0+corners1
        segments.append(dict(vertices=cs,box={ax:[min(v[j] for v in cs),max(v[j] for v in cs)] for j,ax in enumerate(AXES)}))
    def strip_line(points,w):
        fs=[]
        for i,p in enumerate(points):
            t=unit(vsub(points[min(i+1,len(points)-1)],points[max(0,i-1)]));n=unit(cross(t,w))
            cs=[vadd(p,vadd(vmul(w,x*width/2),vmul(n,y*thick/2))) for x,y in [(-1,-1),(1,-1),(1,1),(-1,1)]]
            f=dict(point=p,tangent=t,width_vector=w,normal=n,corners=cs,section_is_curved=False)
            fs.append(f);frames.append(f)
            if not centerline or math.dist(centerline[-1],p)>1e-7:centerline.append(p)
        for x,y in zip(fs,fs[1:]):mesh(x['corners'],y['corners'])
    pre=[]
    for j in range(9):pre.append([pi[0],pi[1]-tail*j/8,pi[2]])
    uy=pi[1]-tail
    for j in range(1,61):
        t=math.pi*j/60
        pre.append([pi[0],uy-initial_u*math.sin(t),pi[2]+initial_u*(1-math.cos(t))])
    target=[origin[0],origin[1]-5,origin[2]]
    start=pre[-1];num=math.ceil(math.dist(start,target)/.35)
    for j in range(1,num+1):pre.append(vadd(start,vmul(vsub(target,start),j/num)))
    strip_line(pre,[-1,0,0])
    def surface(s,w):
        u=(s+w)*q;v=(s-w)*q
        if v<=0:return vadd(origin,vadd(vmul(a,u),vmul(b,v))),up
        if v>=math.pi*R:return vadd(origin,vadd(vmul(a,u),vadd(vmul(b,-(v-math.pi*R)),vmul(up,2*R)))),[0,0,-1]
        th=v/R
        p=vadd(origin,vadd(vmul(a,u),vadd(vmul(b,R*math.sin(th)),vmul(up,R*(1-math.cos(th))))))
        n=vadd(vmul(up,math.cos(th)),vmul(b,-math.sin(th)))
        return p,n
    ns=math.ceil((sf+10)/.5);nw=20
    ss=[-5+(sf+10)*i/ns for i in range(ns+1)];ws=[-width/2+width*i/nw for i in range(nw+1)]
    grid=[]
    for st in ss:
        row=[]
        for w in ws:
            p,n=surface(st,w);row.append([vadd(p,vmul(n,-thick/2)),vadd(p,vmul(n,thick/2))])
        grid.append(row)
        p,n=surface(st,0);pm,_=surface(st-.001,0);pp,_=surface(st+.001,0);wm,_=surface(st,-.001);wp,_=surface(st,.001)
        frames.append(dict(point=p,tangent=unit(vsub(pp,pm)),width_vector=unit(vsub(wp,wm)),normal=n,section_is_curved=True,material_s_mm=st))
        if math.dist(centerline[-1],p)>1e-7:centerline.append(p)
    for i in range(ns):
        for j in range(nw):
            lo=[grid[i][j][0],grid[i+1][j][0],grid[i+1][j+1][0],grid[i][j+1][0]]
            hi=[grid[i][j][1],grid[i+1][j][1],grid[i+1][j+1][1],grid[i][j+1][1]]
            mesh(lo,hi)
    post_start=surface(sf+5,0)[0]
    stock=300
    top=origin[2]+2*R
    bottom=28.3-drop
    prefix_length=tail+math.pi*initial_u+math.dist(start,target)+(sf+10)
    def tail_path(left_x):
        knots=[post_start,[left_x,evf[1],top],[left_x,evf[1],top-10],
               [right_x,evf[1],top-10],[right_x,evf[1],73.5],
               [-114,evf[1],73.5],[-119,evf[1],75.5],[-134,evf[1],75.5],[-134,evf[1],bottom],
               [evf[0],evf[1],bottom],evf]
        return knots,rounded_path(knots,rr,0,4,.2)
    lo,hi=-128.3,-117
    for _ in range(80):
        left_x=(lo+hi)/2
        knots,post=tail_path(left_x)
        if post['errors']:raise RuntimeError(post['errors'])
        total=prefix_length+post['rounded_length_mm']
        if total>300:lo=left_x
        else:hi=left_x
    left_x=(lo+hi)/2
    knots,post=tail_path(left_x)
    base_total=prefix_length+post['rounded_length_mm']
    depth=0
    loops=[dict(plane='XZ',kind='two180degreeSerpentineTurns',left_x=left_x,right_x=right_x,radius_mm=rr,top_z=top,mid_z=top-10,bottom_z=73.5,knots=knots,initial_u_radius=initial_u,initial_straight_tail=tail)]
    strip_line(post['sampled_centerline'],[0,1,0])
    hits={};walls=[]
    for seg in segments:
        box=seg['box']
        for ax,lo,hi in [('x',-length+2.5,-5.2),('y',right_inner,left_inner),('z',2.5,97.5)]:
            if box[ax][0]<lo-1e-6 or box[ax][1]>hi+1e-6:
                if ax not in walls:walls.append(ax)
        for o in obstacles:
            ib=obstacle_overlap(box,o)
            if ib:
                h=hits.setdefault(o['id'],dict(obstacle=o['id'],overlap_box=ib,segments=0));h['segments']+=1;h['overlap_box']=hull([h['overlap_box'],ib])
    total=prefix_length+post['rounded_length_mm']
    return dict(status='UNQUALIFIED DEVELOPABLE SHAPE: dimensional, material, retention, EMI and exact printed-solid checks remain open' if not walls and not hits else 'BLOCKED: full developable strip intersects a listed obstacle or wall',
                envelope_status='clear of listed source proxies only' if not walls and not hits else 'blocked',
                pose=pose,pi_head_displacement=[0,0,lift],evf_head_displacement=[0,0,-drop],explicit_slack_loops=loops,base_route_without_slack_mm=base_total,head_set='Adafruit3557 right-angle Pi +3556 straight EVF',head_clocking_gate='3557 cable exit toward-Pi-Y inferred from keyed plug orientation; verify against actual Pi and adapter before print release',
                width_mm=width,thickness_allowance_mm=thick,minimum_centerline_radius_allowance_mm=R,
                shape='Variable-radius natural U (R5 installed, R3 both-unplugged), one R3 45-degree cylindrical developable fold, two R5 flatwise serpentine turns and an R5 rear ramp; no imposed spatial twist',
                fold_origin=origin,fold_axis=a,fold_cross_axis=b,fold_normal=up,fold_radius_mm=R,fold_material_centerline_length_mm=sf,
                fold_formula='u=(s+w)/sqrt(2),v=(s-w)/sqrt(2); p=u*a+R*sin(v/R)*b+R*(1-cos(v/R))*n; straight material continuations before/after cylinder',
                material_metric='ds^2+dw^2 analytically preserved on mid-surface: no edgewise stretching',
                width_at_pi=[-1,0,0],width_at_evf=[0,1,0],endpoint_global_width_change_deg=90,transported_frame_roll_deg=0,twist_zone_length_mm=0,
                routed_length_mm=total,stock_length_mm=stock,remaining_length_mm=stock-total,
                service_allowance_mm=None,remaining_after_allowance_mm=None,service_length_policy='The entire stock ribbon is explicitly modeled in both final and pre-mate shapes; no extra fictitious percentage allowance is added. Actual cable length/connector engagement tolerance remains a gate',
                cable_source='https://www.adafruit.com/product/3561' if stock==200 else 'https://www.adafruit.com/product/3562',
                max_edgewise_bend_strain_proxy=0,max_outer_laminate_bend_strain_proxy=thick/(2*R),max_twist_edge_extension_proxy=0,
                material_warning='The mid-surface is isometric; outer-laminate strain proxy is6.67% for unverified0.4mm thickness atR3. Actual copper-layer depth, neutral axis, minimum bend radius and fold lifetime are unpublished. R3 is a physical material gate, not a passed limit. No fold crease is sharpened to zero radius.',
                geometric_check='Full10mm material-coordinate strip; each developable-fold cell is extruded along its own surface normal. Sampled prism AABBs are conservative; parent CAD must check exact printed geometry and retention.',
                wall_overrun_axes=walls,obstacle_overlaps=list(hits.values()),frames=frames,segments=segments)


def compact_300_service(lift=0.0, drop=0.0, obstacles=()):
    """Full compact ribbon; lift and drop are independent [0,6] mm strokes.

    Source-tested service sequence: drop 0->6, then lift 0->6.
    All +Y removal conflicts and actual physical qualification remain open.
    """
    if not (0 <= lift <= 6 and 0 <= drop <= 6):
        raise ValueError("Service strokes must lie within 0..6 mm")
    pose = "installed" if lift == drop == 0 else "both_unplugged" if lift == drop == 6 else "service"
    return ribbon300(158, obstacles=obstacles, lift=lift, drop=drop,
                     initial_u=max(3.0, 5.5-lift/2), tail=2.0, pose=pose)

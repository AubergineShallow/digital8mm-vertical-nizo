# SPDX-License-Identifier: MIT
"""Provisional 270 mm 16 AWG source geometry. No CAD imports.

Separate from the frozen HDMI checkpoint. Every unmeasured pad/pin/root datum is
explicit. This model is not permission to open an energized body or build a pack.
"""
import math


def build(R, obstacles=()):
    # R is the already loaded routes module; use its shared geometry primitives.
    c=math.cos(math.radians(21));s=math.sin(math.radians(21));q=math.sqrt(.5)
    C=[-51.2,-.7,-18]
    u=[c*q,s*q,-q];v=[-s,c,0];w=[c*q,s*q,q]
    d=R.vmul(u,-1);n=R.vmul(w,-1);h=[-c,-s,0];nh=[-s,c,0]
    def p(local):return R.vadd(C,R.vadd(R.vmul(u,local[0]),R.vadd(R.vmul(v,local[1]),R.vmul(w,local[2]))))
    F=p([-13,-5.1,0]);S=R.vadd(F,R.vmul(d,4));T=R.vadd(S,R.vmul(d,20))
    def line(a,b,step=.3):
        N=max(1,math.ceil(math.dist(a,b)/step))
        return [R.vadd(a,R.vmul(R.vsub(b,a),j/N)) for j in range(N+1)]
    def arc(start,tangent,normal,radius,angle,step=.3):
        N=max(2,math.ceil(radius*angle/step))
        return [R.vadd(start,R.vadd(R.vmul(tangent,radius*math.sin(angle*j/N)),R.vmul(normal,radius*(1-math.cos(angle*j/N))))) for j in range(N+1)]
    def helix(t):
        a=math.radians(110)*(10*t**3-15*t**4+6*t**5)
        return R.vadd(S,R.vadd(R.vmul(d,20*t),R.vadd(R.vmul(v,5*math.cos(a)),R.vmul(n,5*math.sin(a)))))
    wrap=[helix(j/500) for j in range(501)]
    wrap_length=sum(math.dist(a,b) for a,b in zip(wrap,wrap[1:]))
    rows=[]
    for name,face,tail_end,rigid_end,rad2 in [('positive',F,S,T,8),('negative',R.vadd(F,R.vmul(v,5)),R.vadd(S,R.vmul(v,5)),wrap[-1],24)]:
        first=line(face,tail_end)
        middle=line(S,T) if name=='positive' else wrap
        if name=='positive':
            # Replace only the exposed, above-floor exit after the frozen fuse.
            outward=[0,-1,0]
            n1=R.unit(R.vsub(outward,R.vmul(d,R.dot(outward,d))))
            aa=math.radians(20)
            a=arc(T,d,n1,8,aa)
            t1=R.vadd(R.vmul(d,math.cos(aa)),R.vmul(n1,math.sin(aa)))
            up=[0,0,1];bb=math.acos(R.dot(t1,up))
            n2=R.unit(R.vsub(up,R.vmul(t1,R.dot(t1,up))))
            b=arc(a[-1],t1,n2,8,bb)
            cc=arc(b[-1],up,[-1,0,0],8,math.pi/2)
            local=first+middle[1:]+a[1:]+b[1:]+cc[1:]
            local_length=24+8*(aa+bb+math.pi/2)
            Q=cc[-1]
        else:
            a=arc(rigid_end,d,n,8,math.pi/4)
            b=arc(a[-1],h,nh,rad2,math.radians(21))
            local=first+middle[1:]+a[1:]+b[1:]
            local_length=4+wrap_length+8*math.pi/4+rad2*math.radians(21)
            Q=b[-1]
        # The baseline gives one assumed pad point, not two measured pin centers.
        # These separated wire exits are a explicit, not-yet-qualified root design.
        root=[-65.5,8.3 if name=='positive' else 12.7,63]
        assumed_pad=[-65.5,14.6,63]
        root_stub=math.dist(root,assumed_pad)
        zbase=79 if name=='positive' else 47
        front_x=-29.5 if name=='positive' else -30
        lane=-16.0 if name=='positive' else -19.7
        hump_start=-44.4 if name=='positive' else -40
        hump_width=40 if name=='positive' else 34
        before=[root,[-65.5,root[1],zbase],[front_x,root[1],zbase],[front_x,lane,zbase],[hump_start,lane,zbase]]
        endbase=79 if name=='positive' else 56
        rear=-100 if name=='positive' else -104
        transition_top=48 if name=='positive' else 30
        after=[[hump_start-hump_width,lane,endbase],[rear,lane,endbase],[rear,lane,transition_top]]
        prefix=R.rounded_path(before,8,8,0,.3);suffix=R.rounded_path(after,8,0,0,.3)
        transition=[]
        for jj in range(201):
            t=jj/200;ff=10*t**3-15*t**4+6*t**5
            transition.append([rear,lane+(Q[1]-lane)*ff,transition_top-12*t])
        trans_length=sum(math.dist(a,b) for a,b in zip(transition,transition[1:]))
        down=line(transition[-1],[rear,Q[1],Q[2]+8])
        round_bottom=arc(down[-1],[0,0,-1],[1,0,0],8,math.pi/2)
        to_Q=line(round_bottom[-1],Q)
        tail_points=transition+down[1:]+round_bottom[1:]+to_Q[1:]
        tail_length=trans_length+math.dist(down[0],down[-1])+8*math.pi/2+math.dist(to_Q[0],to_Q[-1])
        if prefix['errors'] or suffix['errors']:
            rows.append(dict(id=name,status='blocked',errors=prefix['errors']+suffix['errors']));continue
        # An asymmetric, explicitly drawn XZ hump consumes all remaining stock.
        # Its left and right vertical excursions need not have equal heights.
        fixed=prefix['rounded_length_mm']+suffix['rounded_length_mm']+tail_length+local_length+root_stub
        target=270-fixed
        def side(drop):
            if drop<=16:
                angle=math.acos(1-max(0,drop)/16);leg=0
            else:angle=math.pi/2;leg=drop-16
            return angle,leg,16*math.sin(angle),16*angle+leg
        def hump(high,sample=False):
            a1,l1,x1,len1=side(high-zbase);a2,l2,x2,len2=side(high-endbase)
            flat=hump_width-x1-x2
            length=len1+len2+flat
            if not sample:return length
            at=[hump_start,lane,zbase];pts=[];t0=[-1,0,0]
            seg=arc(at,t0,[0,0,1],8,a1);pts+=seg;at=seg[-1]
            t1=[-math.cos(a1),0,math.sin(a1)]
            to=R.vadd(at,R.vmul(t1,l1));pts+=line(at,to)[1:];at=to
            seg=arc(at,t1,[-math.sin(a1),0,-math.cos(a1)],8,a1);pts+=seg[1:];at=seg[-1]
            to=R.vadd(at,[-flat,0,0]);pts+=line(at,to)[1:];at=to
            seg=arc(at,t0,[0,0,-1],8,a2);pts+=seg[1:];at=seg[-1]
            t2=[-math.cos(a2),0,-math.sin(a2)]
            to=R.vadd(at,R.vmul(t2,l2));pts+=line(at,to)[1:];at=to
            seg=arc(at,t2,[-math.sin(a2),0,math.cos(a2)],8,a2);pts+=seg[1:]
            return pts,length,dict(rise_angle_deg=math.degrees(a1),fall_angle_deg=math.degrees(a2),rise_straight_mm=l1,fall_straight_mm=l2,middle_straight_mm=flat,top_z=high)
        low=max(zbase,endbase);high=110
        if hump(low)>target:
            rows.append(dict(id=name,status='blocked',errors=['270mm too short by %.4fmm'%(hump(low)-target)]));continue
        for _ in range(64):
            mid=(low+high)/2
            if hump(mid)<target:low=mid
            else:high=mid
        high=(low+high)/2;bump,bump_length,hump_data=hump(high,True)
        upper_points=prefix['sampled_centerline']+bump[1:]+suffix['sampled_centerline'][1:]+tail_points[1:]
        upper=dict(sampled_centerline=upper_points,rounded_length_mm=prefix['rounded_length_mm']+bump_length+suffix['rounded_length_mm']+tail_length,errors=[],status='geometric-only',minimum_radius_mm=8,slack_hump=hump_data)
        length=upper['rounded_length_mm']+local_length+root_stub
        points=upper_points+list(reversed(local))[1:]
        if name=='positive':
            ti=min(range(len(points)),key=lambda j:math.dist(points[j],T))
            si=min(range(len(points)),key=lambda j:math.dist(points[j],S))
            flexible_parts=[dict(id='positive_board_to_fuse',points=points[:ti+1]),dict(id='positive_fuse_to_housing',points=points[si:])]
        else:flexible_parts=[dict(id='negative_complete',points=points)]
        hits={};wall=[]
        for point in points:
            pb={ax:[point[i]-1.6,point[i]+1.6] for i,ax in enumerate('xyz')}
            if point[2]>2.5 and (pb['y'][0]<-25.5 or pb['y'][1]>25.2 or pb['z'][1]>97.5):wall.append(point)
            for ob in obstacles:
                ib=R.obstacle_overlap(pb,ob)
                if ib:
                    rec=hits.setdefault(ob['id'],dict(obstacle=ob['id'],overlap_box=ib,points=0));rec['points']+=1;rec['overlap_box']=R.hull([rec['overlap_box'],ib])
        rows.append(dict(id=name,stock_length_mm=270,modeled_length_mm=length,root=root,source_assumed_pad=assumed_pad,unmodeled_root_joint_allowance_mm=root_stub,
                         root_warning='Actual pads and wire exit/strain-relief construction are unknown. This allowance is NOT a passedR8 transition and must not be counted as a completed physical pad connection.',
                         finished_path_allocation_mm=270,rigid_inline_zone_mm=20 if name=='positive' else 0,
                         length_convention_gate='Positive270mm allocation includes20mm rigid fuse/solder sleeve. Actual copper overlap and cut convention must be measured. Do not claim270mm of flexible wire plus the sleeve fits. Electrical calculation conservatively charges270mm copper in both cores.',
                         flexible_wire_parts=flexible_parts,local_length_mm=local_length,local_points=local,local_end=Q,upper_curve=upper,full_centerline_excluding_unmeasured_root_joint=points,
                         xz_loop_top_z=high,body_lane_y=lane,od_mm=3.2,minimum_round_bend_radius_mm=8,
                         source_proxy_hits=list(hits.values()),wall_overrun_points=wall,
                         status='blocked' if hits or wall or upper['errors'] else 'nominal source-body route only; pad transition, printed pockets, retention and dynamic service remain open'))
    # Positive fuse is the sole axial cylinder, not the old side-mounted sleeve.
    def cylbox(r):return {ax:[min(S[i],T[i])-r*math.sqrt(1-d[i]**2),max(S[i],T[i])+r*math.sqrt(1-d[i]**2)] for i,ax in enumerate('xyz')}
    # Exact source pose; caller can build/loft or sweep it in the CAD environment.
    original=[-47.25,-.1,-33.2]
    def transform(point):return p(R.vsub(point,original))
    service=[]
    for i in range(101):
        t=i/100;yaw=math.radians(21*(1-t));pitch=math.radians(45+45*t)
        cy,sy=math.cos(yaw),math.sin(yaw);cp,sp=math.cos(pitch),math.sin(pitch)
        mat=[[cy*cp,-sy,cy*sp],[sy*cp,cy,sy*sp],[-sp,0,cp]]
        ccen=[C[0],C[1],C[2]-20*t]
        def pp(vec):return [ccen[a]+sum(mat[a][b]*vec[b] for b in range(3)) for a in range(3)]
        service.append(dict(phase='unwind_and_lower',fraction=t,center=ccen,matrix=mat,fuse_start=pp([-17,-5.1,0]),fuse_end=pp([-37,-5.1,0]),fuse_pocket_radius_mm=2.8,pack_translation=[0,0,-20*t],
                            note='Coordinated yaw unwind and pitch-to-vertical; pack must move with connector. Flexible-wire deformation not certified by this rigid pose.'))
    mat=[[0,0,1],[0,1,0],[-1,0,0]]
    for i in range(1,101):
        down=i;ccen=[C[0],C[1],C[2]-20-down]
        service.append(dict(phase='withdraw_vertical',fraction=i/100,center=ccen,matrix=mat,fuse_start=[C[0],C[1]-5.1,ccen[2]+17],fuse_end=[C[0],C[1]-5.1,ccen[2]+37],fuse_pocket_radius_mm=2.8,pack_translation=[0,0,-20-down],note='Final female wire face isZ=-125,15mm below grip mouth. Flexible270mm cores still need motion validation.'))
    return dict(status='PROVISIONAL POWER GEOMETRY; DO NOT BUILD/ENERGIZE; noG-W5 pass',
                selected_wire='Provisional270mm finished route allocation per polarity, OD3.2 16AWG reservation; positive includes its20mm fuse/joint zone. Original60mm18AWG pack lead unchanged',
                rejected_wire='250mm cannot meet the conservative front-bypass service model with its25mm allowance',
                junction_center=C,junction_yaw_deg=21,junction_pitch_deg=45,junction_transform_matrix=[[u[i],v[i],w[i]] for i in range(3)],
                full_old_assembly_proxy_box=R.tbox(R.L.COTS['xt30_pair']['box'],transform),
                core_exit_spacing_assumption_mm=5,cores=rows,source_oldframe_reference=[-47.25,-.1,-33.2],junction_housing_original_box=R.B(-60.25,-34.25,-7.8,2.4,-36.4,-30),
                pocket_paths=[dict(id=c['id']+'_local_wire_pocket',points=c['local_points'],radius_mm=1.9,note='Sweep this tube only where it intersects printed material; preserve1.6mm loaded ligaments and keyhole voids') for c in rows],
                fuse=dict(start=S,end=T,axis=d,rigid_length_mm=20,radius_mm=2.5,box=cylbox(2.5),pocket_radius_mm=2.8,pocket_box=cylbox(2.8),near_lead_station_mm=4,far_lead_station_mm=24,proximity_limit_mm=25),
                negative_wrap=dict(radius_about_fuse_mm=5,axial_length_mm=20,angle_deg=110,angle_law='theta=110deg*(10t^3-15t^4+6t^5)',length_mm=wrap_length,min_curvature_radius_mm=8.325221,wire_to_fuse_mm=.9,points=wrap),
                rigid_service_poses=service,service_warning='Mandatory battery isolation before body opening. These are rigid connector/fuse poses only; all270mm wire deformation, guide release and pinch clearance need validation. Do not present them as a passed extraction.',
                mechanical_snapshot=dict(path='routing-snapshots/power-yaw21-270-provisional/power-270-yaw21.json',sha256='4b2eaa913d685b561a33d4f706e78e631912d793ce80b0f46b8d5c31e39f34f3',unchanged='Connector/fuse pose, negative local exit, all below-floor wire/pocket geometry, and 201 rigid service poses. Parent exact CAD source power_geometry.py passed those rigid poses after 3 mm tongue-corner relief; this is not a flexible-loom service pass.',replaced='Positive wire after the frozen fuse endpoint: all changed wire material remains above Z6.562951; both upper 270 mm storage paths are recomputed.'),
                protected_ligament=dict(status='Parent integrated 3 mm triangular tongue-corner relief and swept pocket; exact valid single-solid check reported. Structural strength remains unqualified.',required_mm=1.6,reported_sampled_remaining_mm=1.88,nominal_neck_area_mm2=203.5,original_neck_area_mm2=208),
                electrical=dict(copper_length_accounting='Conservative270mm copper per polarity; no resistance credit for positive rigid fuse-zone displacement or solder overlap',i_a=8.6,limit_v=.15,estimated_60c_copper_drop_v=.142810903056,remaining_voltage_budget_v=.15-.142810903056,gate='G-W5 hard hot-load measurement: measured hot fuse/contact resistance not covered by the remaining7.19mV'),
                retention='Use releasable/open guides only. Tight ties are NOT counted as deployable slack; battery-isolation extraction must be proved before any body-opening sequence.')

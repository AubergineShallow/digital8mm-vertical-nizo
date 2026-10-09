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
        a=arc(rigid_end,d,n,8,math.pi/4)
        b=arc(a[-1],h,nh,rad2,math.radians(21))
        first=line(face,tail_end)
        middle=line(S,T) if name=='positive' else wrap
        local=first+middle[1:]+a[1:]+b[1:]
        local_length=4+(20 if name=='positive' else wrap_length)+8*math.pi/4+rad2*math.radians(21)
        Q=b[-1]
        # The baseline gives one assumed pad point, not two measured pin centers.
        # These separated wire exits are a explicit, not-yet-qualified root design.
        root=[-65.5,8.3 if name=='positive' else 12.7,63]
        assumed_pad=[-65.5,14.6,63]
        root_stub=math.dist(root,assumed_pad)
        zbase=79 if name=='positive' else 47
        front_x=-29.5 if name=='positive' else -30
        lane=-16.0 if name=='positive' else -19.7
        before=[root,[-65.5,root[1],zbase],[front_x,root[1],zbase],[front_x,lane,zbase],[-45,lane,zbase]]
        after=[[-85,lane,zbase],[-100,lane,zbase],[-100,lane,36]]
        prefix=R.rounded_path(before,8,8,0,.3);suffix=R.rounded_path(after,8,0,0,.3)
        transition=[]
        for jj in range(201):
            t=jj/200;ff=10*t**3-15*t**4+6*t**5
            transition.append([-100,lane+(Q[1]-lane)*ff,36-12*t])
        trans_length=sum(math.dist(a,b) for a,b in zip(transition,transition[1:]))
        down=line(transition[-1],[-100,Q[1],Q[2]+8])
        round_bottom=arc(down[-1],[0,0,-1],[1,0,0],8,math.pi/2)
        to_Q=line(round_bottom[-1],Q)
        tail_points=transition+down[1:]+round_bottom[1:]+to_Q[1:]
        tail_length=trans_length+math.dist(down[0],down[-1])+8*math.pi/2+math.dist(to_Q[0],to_Q[-1])
        if prefix['errors'] or suffix['errors']:
            rows.append(dict(id=name,status='blocked',errors=prefix['errors']+suffix['errors']));continue
        base=prefix['rounded_length_mm']+40+suffix['rounded_length_mm']+tail_length+local_length+root_stub
        extra=270-base;turn=math.pi/2;leg=0
        if extra<0:
            rows.append(dict(id=name,status='blocked',errors=['270mm too short by%.4fmm'%(-extra)]));continue
        max_arc_extra=32*(math.pi/2-1)
        if extra<=max_arc_extra:
            lo,hi=0,math.pi/2
            for _ in range(60):
                mid=(lo+hi)/2
                if 32*(mid-math.sin(mid))<extra:lo=mid
                else:hi=mid
            turn=(lo+hi)/2
        else:leg=(extra-max_arc_extra)/2
        flat=40-32*math.sin(turn)-2*leg*math.cos(turn)
        bump=[];at=[-45,lane,zbase]
        t0=[-1,0,0];up=[0,0,1]
        seg=arc(at,t0,up,8,turn);bump+=seg;at=seg[-1]
        t1=[-math.cos(turn),0,math.sin(turn)]
        to=R.vadd(at,R.vmul(t1,leg));bump+=line(at,to)[1:];at=to
        seg=arc(at,t1,[-math.sin(turn),0,-math.cos(turn)],8,turn);bump+=seg[1:];at=seg[-1]
        to=R.vadd(at,[-flat,0,0]);bump+=line(at,to)[1:];at=to
        seg=arc(at,t0,[0,0,-1],8,turn);bump+=seg[1:];at=seg[-1]
        t3=[-math.cos(turn),0,-math.sin(turn)]
        to=R.vadd(at,R.vmul(t3,leg));bump+=line(at,to)[1:];at=to
        seg=arc(at,t3,[-math.sin(turn),0,math.cos(turn)],8,turn);bump+=seg[1:]
        bump_length=32*turn+2*leg+flat
        upper_points=prefix['sampled_centerline']+bump[1:]+suffix['sampled_centerline'][1:]+tail_points[1:]
        high=zbase+16*(1-math.cos(turn))+leg*math.sin(turn)
        upper=dict(sampled_centerline=upper_points,rounded_length_mm=prefix['rounded_length_mm']+bump_length+suffix['rounded_length_mm']+tail_length,errors=[],status='geometric-only',minimum_radius_mm=8,slack_hump=dict(angle_deg=math.degrees(turn),straight_leg_mm=leg,middle_straight_mm=flat,added_length_mm=extra,top_z=high))
        length=upper['rounded_length_mm']+local_length+root_stub
        points=upper_points+list(reversed(local))[1:]
        hits={};wall=[]
        for point in points:
            pb={ax:[point[i]-1.6,point[i]+1.6] for i,ax in enumerate('xyz')}
            if point[2]>2.5 and (pb['y'][0]<-25.5 or pb['y'][1]>25.2 or pb['z'][1]>97.5):wall.append(point)
            for ob in obstacles:
                ib=R.overlap(pb,ob['box'])
                if ib:
                    rec=hits.setdefault(ob['id'],dict(obstacle=ob['id'],overlap_box=ib,points=0));rec['points']+=1;rec['overlap_box']=R.hull([rec['overlap_box'],ib])
        rows.append(dict(id=name,stock_length_mm=270,modeled_length_mm=length,root=root,source_assumed_pad=assumed_pad,unmodeled_root_joint_allowance_mm=root_stub,
                         root_warning='Actual pads and wire exit/strain-relief construction are unknown. This allowance is NOT a passedR8 transition and must not be counted as a completed physical pad connection.',
                         local_length_mm=local_length,local_points=local,local_end=Q,upper_curve=upper,full_centerline_excluding_unmeasured_root_joint=points,
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
                selected_wire='270mm16AWG copper per core, OD3.2 reservation; original60mm18AWG pack lead unchanged',
                rejected_wire='250mm cannot meet the conservative front-bypass service model with its25mm allowance',
                junction_center=C,junction_yaw_deg=21,junction_pitch_deg=45,junction_transform_matrix=[[u[i],v[i],w[i]] for i in range(3)],
                full_old_assembly_proxy_box=R.tbox(R.L.COTS['xt30_pair']['box'],transform),
                core_exit_spacing_assumption_mm=5,cores=rows,source_oldframe_reference=[-47.25,-.1,-33.2],junction_housing_original_box=R.B(-60.25,-34.25,-7.8,2.4,-36.4,-30),
                pocket_paths=[dict(id=c['id']+'_local_wire_pocket',points=c['local_points'],radius_mm=1.9,note='Sweep this tube only where it intersects printed material; preserve1.6mm loaded ligaments and keyhole voids') for c in rows],
                fuse=dict(start=S,end=T,axis=d,rigid_length_mm=20,radius_mm=2.5,box=cylbox(2.5),pocket_radius_mm=2.8,pocket_box=cylbox(2.8),near_lead_station_mm=4,far_lead_station_mm=24,proximity_limit_mm=25),
                negative_wrap=dict(radius_about_fuse_mm=5,axial_length_mm=20,angle_deg=110,angle_law='theta=110deg*(10t^3-15t^4+6t^5)',length_mm=wrap_length,min_curvature_radius_mm=8.325221,wire_to_fuse_mm=.9,points=wrap),
                rigid_service_poses=service,service_warning='Mandatory battery isolation before body opening. These are rigid connector/fuse poses only; all270mm wire deformation, guide release and pinch clearance need validation. Do not present them as a passed extraction.',
                protected_ligament=dict(status='blocked pending exact printed redesign',minimum_existing_mm=.594595,required_mm=1.6,neck_point=[-75,-13,-.163742],pocket_nearest_point=[-74.460427,-13.249809,-.163742],reason='Filling the gap would occupy the required keyhole sliding slot; reinforce above or beside it without closing that void.'),
                electrical=dict(i_a=8.6,limit_v=.15,estimated_60c_copper_drop_v=.142810903056,remaining_voltage_budget_v=.15-.142810903056,gate='G-W5 hard hot-load measurement: measured hot fuse/contact resistance not covered by the remaining7.19mV'),
                retention='Use releasable/open guides only. Tight ties are NOT counted as deployable slack; battery-isolation extraction must be proved before any body-opening sequence.')

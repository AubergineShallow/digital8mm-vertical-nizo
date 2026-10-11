# SPDX-License-Identifier: MIT
"""Source-only harness study for the vertical-board D2 candidate (millimetres).

No CadQuery import; baseline layout.py is read in a separate module namespace.
This is a candidate, NOT a passed routing design. Rigid connector proxy envelopes
are retained, including their uncertainty. Soft paths are newly authored in the
vertical frame. A blocked tail is drawn where it WOULD have to go, not clipped to
make the body appear to fit. build() is JSON serializable and has no file writes.

X lensward; Y operator-left; Z up. The parent model owns printed geometry.
"""
from cv_io import read_text, write_text
from pathlib import Path
import copy
import importlib.util
import itertools
import json
import math
import types
import hashlib

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location('_vertical_routes_baseline', ROOT / 'layout.py')
L = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(L)
AXES = 'xyz'
REVISION = 'vertical-harness-source-study-2026-10-11-h1-feed-routes'


def B(x0,x1,y0,y1,z0,z1):
    return dict(x=[x0,x1],y=[y0,y1],z=[z0,z1])


def rp(p, stack_y=22.2):
    return [p[0]-28.0,stack_y-p[2],p[1]+39.3]


def trp(p,t):
    return [p[i]+t[i] for i in range(3)]


def corners(b):
    return itertools.product(*(b[a] for a in AXES))


def tbox(b, fn):
    p = [fn(p) for p in corners(b)]
    return {a:[min(q[i] for q in p),max(q[i] for q in p)] for i,a in enumerate(AXES)}


def center(b):
    return [(b[a][0]+b[a][1])/2 for a in AXES]


def hull(boxes):
    return {a:[min(b[a][0] for b in boxes),max(b[a][1] for b in boxes)] for a in AXES}


def overlap(a,b):
    r = {k:[max(a[k][0],b[k][0]),min(a[k][1],b[k][1])] for k in AXES}
    return r if all(r[k][1]-r[k][0]>1e-7 for k in AXES) else None


def obstacle_overlap(a,o):
    """Conservative box intersection with optional exact 2D primitive rejection."""
    hit=overlap(a,o['box'])
    if not hit:return None
    p=o.get('primitive') or {}
    if p.get('type')=='cylinder_y':
        d2=sum(max(a[ax][0]-v,0,v-a[ax][1])**2 for ax,v in zip(('x','z'),p['center_xz']))
        if d2>p['radius']**2+1e-9:return None
    if p.get('type')=='xz_rectangle':
        aa,bb=p['ends_xz'];dx,dz=bb[0]-aa[0],bb[1]-aa[1];ll=math.hypot(dx,dz)
        u=[dx/ll,dz/ll];v=[-u[1],u[0]];bc=[(aa[i]+bb[i])/2 for i in range(2)]
        ac=[sum(a[k])/2 for k in ('x','z')];ah=[(a[k][1]-a[k][0])/2 for k in ('x','z')]
        delta=[ac[i]-bc[i] for i in range(2)]
        for axis in ([1,0],[0,1],u,v):
            da=abs(sum(delta[i]*axis[i] for i in range(2)))
            ra=sum(ah[i]*abs(axis[i]) for i in range(2))
            rb=ll/2*abs(sum(u[i]*axis[i] for i in range(2)))+p['half_width']*abs(sum(v[i]*axis[i] for i in range(2)))
            if da>ra+rb+1e-9:return None
    if p.get('type')=='oriented_box':
        ac=center(a);ah=[(a[k][1]-a[k][0])/2 for k in AXES]
        axes=p['axes'];delta=vsub(ac,p['center'])
        world=[[1,0,0],[0,1,0],[0,0,1]]
        tests=world+list(axes)+[[x[1]*y[2]-x[2]*y[1],x[2]*y[0]-x[0]*y[2],x[0]*y[1]-x[1]*y[0]] for x in world for y in axes]
        for axis in tests:
            if norm(axis)<1e-9:continue
            if abs(dot(delta,axis))>sum(ah[i]*abs(axis[i]) for i in range(3))+sum(p['half_sizes'][j]*abs(dot(axes[j],axis)) for j in range(3))+1e-9:return None
    return hit


def volume(b):
    return math.prod(b[a][1]-b[a][0] for a in AXES)


def vsub(a,b): return [a[i]-b[i] for i in range(3)]
def vadd(a,b): return [a[i]+b[i] for i in range(3)]
def vmul(a,s): return [s*x for x in a]
def norm(a): return math.sqrt(sum(x*x for x in a))
def unit(a): return vmul(a,1/norm(a))
def dot(a,b): return sum(x*y for x,y in zip(a,b))


def rounded_path(points, radius, first_tail=0, last_tail=0, step=1.0):
    """Exact circular corner fillets with tangent and endpoint-tail checks.

    Minimum radius is never reduced to fit a short segment. Invalid paths retain
    their requested knots but are not emitted as a falsely valid smooth curve.
    Length is exact (line + circular arc), sampling is only for collision review.
    """
    p = [list(map(float,x)) for x in points]
    leg = [math.dist(a,b) for a,b in zip(p,p[1:])]
    trims = [0.0]*len(p)
    turn = [0.0]*len(p)
    errors=[]
    for i in range(1,len(p)-1):
        u=unit(vsub(p[i],p[i-1])); v=unit(vsub(p[i+1],p[i]))
        angle=math.acos(max(-1,min(1,dot(u,v))))
        if angle > math.pi-1e-7:
            errors.append('180 degree reversal at knot %s needs an explicit loop' % i)
            continue
        turn[i]=angle; trims[i]=radius*math.tan(angle/2)
    for i, length in enumerate(leg):
        need=trims[i]+trims[i+1]+(first_tail if i==0 else 0)+(last_tail if i==len(leg)-1 else 0)
        if length+1e-8<need:
            errors.append('leg %s: %.3f mm available, %.3f mm required by bends and straight tails' % (i,length,need))
    exact=sum(leg)-2*sum(trims)+radius*sum(turn)
    out=[]
    def line(a,b):
        n=max(1,math.ceil(math.dist(a,b)/step))
        for j in range(n):out.append(vadd(a,vmul(vsub(b,a),j/n)))
    if not errors:
        last=p[0]
        for i in range(1,len(p)-1):
            if turn[i]<1e-8:continue
            u=unit(vsub(p[i],p[i-1]));v=unit(vsub(p[i+1],p[i]))
            enter=vsub(p[i],vmul(u,trims[i]));leave=vadd(p[i],vmul(v,trims[i]))
            bis=unit(vsub(v,u))
            c=vadd(p[i],vmul(bis,radius/math.cos(turn[i]/2)))
            e0=unit(vsub(enter,c)); e1=u
            line(last,enter)
            n=max(2,math.ceil(radius*turn[i]/step))
            for j in range(n):
                t=turn[i]*j/n
                out.append(vadd(c,vmul(vadd(vmul(e0,math.cos(t)),vmul(e1,math.sin(t))),radius)))
            last=leave
        line(last,p[-1]);out.append(p[-1])
    return dict(knots=p,centerline_radius_mm=radius,first_straight_min_mm=first_tail,
                last_straight_min_mm=last_tail,raw_length_mm=sum(leg),
                rounded_length_mm=exact if not errors else None,
                corner_trim_mm=trims,turn_degrees=[math.degrees(t) for t in turn],
                sampled_centerline=out,errors=errors,status='blocked' if errors else 'geometric-path-only')


def header_housings(stack_y=22.2):
    """Actual seven source proxy housings, not the oversized shared routing box."""
    h=L.HDR_HOUSING; g=L.COTS['pi5']['features']['gpio']; out=[]
    for cable,kind,pins in L.HEADER_HOUSINGS:
        xy=[(g['x'][1]-1.27-h['pitch']*((n-1)//2),L.PI['header_rows_y'][n%2]) for n in pins]
        sec=max(h['sec']);s=sec/2
        old=B(min(q[0] for q in xy)-s,max(q[0] for q in xy)+s,
              min(q[1] for q in xy)-s,max(q[1] for q in xy)+s,
              h['seat_z'],h['seat_z']+max(h['length']))
        box=tbox(old,lambda p:rp(p,stack_y)); tail=center(box);tail[1]=box['y'][0]
        out.append(dict(id='hdr_'+cable+'_'+'_'.join(map(str,pins)),cable=cable,pins=list(pins),
                        box=box,wire_exit=tail,mating_direction=[0,1,0],
                        source='layout.HEADER_HOUSINGS + HDR_HOUSING + actual GPIO pin centers',
                        status='unmeasured proxy; MP-QT / G-HDR-1 remain open'))
    return out


def connectors(length, stack_y=22.2, evf_shift_y=11, panel_shift_y=3, hdmi_assembly="adafruit3557_3556"):
    roll=lambda p:rp(p,stack_y)
    evf=(154-length,-16+evf_shift_y,0);moves={'encoder':(8,-10+panel_shift_y,21),'switch_1824':(12,-10+panel_shift_y,21)}
    hs=header_housings(stack_y);out=[]
    for old in L.PLUGS:
        row=copy.deepcopy(old); row['source_keepout']=old['box']; row['box']=None
        end=old['end']
        fn=roll if end in ('pi5','x1203','cooler') else (lambda p:trp(p,evf)) if end in ('hmx039','evf_board') else (lambda p,t=moves[end]:trp(p,t)) if end in moves else (lambda p:list(p))
        if old['box']:
            row['box']=tbox(L.KEEPOUTS[old['box']],fn)
        if old.get('head'):row['head']=tbox(old['head'],fn)
        if old['id'] in ('p_qt_hdr','p_run_hdr','p_fps_hdr'):
            row['baseline_conservative_box']=row['box']
            row['housing_boxes']=[h['box'] for h in hs if h['cable']==old['cable']]
            row['box']=hull(row['housing_boxes'])
        if old['id']=='p_usb_pi':
            # Source-registered actual GPIO-side USB2 upper receptacle.
            # The31x15.5x9.8 allowance is NOT a measured Adafruit4448 overmold.
            cx,cy,cz=-121.779999264573,stack_y-32.42600076744,16.000319443808
            row['box']=B(cx-31,cx,cy-4.9,cy+4.9,cz-7.75,cz+7.75)
            row['port_center']=[cx,cy,cz];row['wire_exit']=None
            row['note']='Official Pi5 four-hole registration: GPIO-side USB2 upper socket. Full exterior allowance only; actual Adafruit4448 body/exit and installed cuttable lead require measurement. Old Ethernet-row placement is rejected.'
        if hdmi_assembly.startswith('adafruit') and old['id'] in ('p_hdmi_pi','p_hdmi_evf'):
            row['baseline_box']=row['box']
            if row.get('head'):row['baseline_mating_head']=copy.deepcopy(row['head'])
            row['source']='Adafruit3556 catalog26.5x17.3x4.0mm, full length conservatively outside receptacle; https://www.adafruit.com/product/3556'
            if old['id']=='p_hdmi_pi':
                cy=stack_y-21.85
                if hdmi_assembly=='adafruit3557_3556':
                    row['box']=B(-68.55,-51.05,cy-15,cy+2,63,77.5)
                    row['catalog_body_box']=B(-68.55,-51.05,cy-15,cy,63,77.5)
                    row['wire_exit']=[-59.8,cy-15,77.5];row['wire_exit_direction']=[0,-1,0]
                    row['source']='Adafruit3557 catalog17.5x15x14.5mm plus conservative2mm mating-side datum allowance; https://www.adafruit.com/product/3557'
                else:
                    row['box']=B(-68.45,-51.15,cy-2,cy+2,63,89.5)
                    row['wire_exit']=[-59.8,cy,89.5];row['wire_exit_direction']=[0,0,1]
            else:
                xx=-141.6+154-length;yy=-5.5+evf_shift_y
                row['box']=B(xx-2,xx+2,yy-8.65,yy+8.65,37.3,63.8)
                row['wire_exit']=[xx,yy,37.3];row['wire_exit_direction']=[0,0,-1]
            row['head']=copy.deepcopy(row['box'])
            row['head_datum_warning']='Keyed orientation preserved; port centering and mating-depth offset are inferred, not vendor datum dimensions. Do not rotate90deg to reduce width.'
        row['qualification']='unmeasured source proxy; no hardware fit approval'
        out.append(row)
    return out,hs


def source_obstacles(length, stack_y=22.2, evf_shift_y=11, power_button=True, panel_shift_y=3, upper_storage=True):
    """Fine source COTS feature boxes, plus explicit parent-model critical regions.

    These boxes are for conservative broad-phase checks; parent CAD must run exact
    solid intersections. No cable/end-part pair is globally exempted.
    """
    roll=lambda p:rp(p,stack_y)
    out=[]
    def add(id,b,fn=lambda p:list(p)):
        out.append(dict(id=id,box=tbox(b,fn)))
    f=L.COTS['pi5']['features'];x0,x1=L.PI['x'];y0,y1=L.PI['y']
    add('pi_pcb',f['pcb'],roll);add('pi_underside',B(x0+6.5,x1-6.5,y0+6.5,y1-6.5,16,18.5),roll)
    source=Path(__file__).resolve().parent/'routing-snapshots/hdmi-ck1044-clear-20261009-0524/official-fpc-sources'
    portdata=json.loads(read_text(source/'port-landmarks.json'))['objects']
    transform=lambda p:[-34-p[0],stack_y-18.5-p[2],63-p[1]]
    for name,row in portdata.items():
        q=row['bbox_native_mm'];add('pi_'+name,B(*q),transform)
    csi=json.loads(read_text(source/'connector-extraction.json'))['components']
    for name,row in csi.items():add('pi_'+name,B(*row['native_bbox_mm']),transform)
    add('ups_pcb',L.COTS['x1203']['features']['pcb'],roll)
    add('ups_pogo',B(x1-58,x1-7,y0+.5,y0+5,7.6,16),roll)
    add('ups_components',B(x0+12,x0+40,y0+12,y1-12,7.6,11),roll)
    add('ups_xh',B(x0+2,x0+10,y0+10,y0+16,7.6,13.5),roll)
    add('cooler_bounding_proxy',L.COTS['cooler']['box'],roll)
    for id in ('gs_camera','run_button','pack'):add(id,L.COTS[id]['box'])
    # The selected mechanical pose is bound to the frozen power JSON. The old
    # full assembly envelope included a side-mounted fuse that is now replaced
    # by one separately modeled axial fuse, so retain the actual housing box.
    phi=math.radians(21);q=math.sqrt(.5);c=math.cos(phi);ss=math.sin(phi)
    columns=([c*q,ss*q,-q],[-ss,c,0],[c*q,ss*q,q])
    def selected_xt30(p):
        local=vsub(p,[-47.25,-.1,-33.2])
        return [-51.2+sum(columns[j][0]*local[j] for j in range(3)),
                -.7+sum(columns[j][1]*local[j] for j in range(3)),
                -18+sum(columns[j][2]*local[j] for j in range(3))]
    housing=B(-60.25,-34.25,-7.8,2.4,-36.4,-30)
    out.append(dict(id='xt30_selected_housing',box=tbox(housing,selected_xt30),
                    primitive=dict(type='oriented_box',center=selected_xt30(center(housing)),axes=columns,half_sizes=[13,5.1,3.2]),
                    source='Frozen power mechanical pose; inline fuse is separate. Locally seated core-end contact still needs endpoint review.'))
    for id,t in [('encoder',(8,-10+panel_shift_y,21)),('switch_1824',(12,-10+panel_shift_y,21))]:add(id,L.COTS[id]['box'],lambda p,t=t:trp(p,t))
    for id in ('hmx039','evf_board','foam_pad'):add(id,L.COTS[id]['box'],lambda p:trp(p,(154-length,-16+evf_shift_y,0)))
    if power_button:add('power_switch_proxy',B(-29.03,-10.97,-4.4+panel_shift_y,30+panel_shift_y,16.47,34.53))
    if power_button:add('power_switch_nut_reserve',B(-31,-9,19.2+panel_shift_y,22.2+panel_shift_y,14.5,36.5))
    else:add('plunger_dogleg',B(-33.3,-30.8,-5,1,20,45.8))
    add('rear_top_panel_boss_box',B(-137.5,-128.5,-25.55,23.5,87.2,96.2))
    out.append(dict(id='carrier_rear_post',box=B(-131.8,-122.2,-25.55,17.2,64.2,73.8),primitive=dict(type='cylinder_y',center_xz=[-127,69],radius=4.8)))
    out.append(dict(id='carrier_diagonal_arm',box=B(-129,-91,17.2,20.2,51,71),primitive=dict(type='xz_rectangle',ends_xz=[[-127,69],[-93,53]],half_width=2)))
    add('carrier_front_rail',B(-39,-29,14+stack_y-19,17+stack_y-19,4,64))
    # Storage below EVF: compact choice preserves its full published housing size.
    sz=32.1 if upper_storage else 24.4
    compact=B(-156,-110,stack_y-sz-3.5-.366,stack_y-sz+3.5-.366,26.5-.000105,41.5-.000105)
    original=tbox(L.COTS['usb_stick']['box'],lambda p:trp(roll(trp(p,(0,0,sz-24.4))),(0,-.366,-.000105)))
    add('usb_storage',compact if length<180 else original)
    for i,(x,y) in enumerate(L.PI['holes']):
        xx,_,zz=roll([x,y,7.6]);add('kit_standoff_'+str(i),B(xx-3,xx+3,stack_y-18.5,stack_y-7.6,zz-3,zz+3))
    return out


def pigtail_study(stack_y=22.2):
    P=L.PIGTAIL;pad=rp([*P['pad']['xy'],L.PI['x1203_z'][1]],stack_y)
    # Pair lies side-by-side in Y, 2.4 mm OD per core: narrow X span clears the
    # pogo field's front edge at X=-41. The source pad is NEVER moved to the lane.
    points=[pad,[-39,8.5,63],[-39,8.5,5],[-39,-8.5,5],[-39,-8.5,-125]]
    radius=P['bend']['flex_r_od']*max(P['od_range'])+max(P['od_range'])/2
    p=rounded_path(points,radius,8,0)
    path=p['rounded_length_mm']
    def drop(cut):
        d=P['drop'];r=d['mohm_per_m']*2*(cut+60)/1000+L.PIGTAIL_FUSE['cold_mohm']+d['xt30_mohm']
        return d['i_peak_a']*r/1000
    required=next((n for n in range(5,1001,5) if n-max(10,n*.1)>=(path or 1e8)),None) if path else None
    return dict(assumed_pad=pad,pad_status=P['pad']['status'],lane_x=-39,lane_y=8.5,
                floor_lane_y=-8.5,service_wire_end=[-39,-8.5,-125],grip_mouth_z=-110,
                face_out_min_mm=15,housing_credit_mm=0,service_path=p,
                service_route_mm=path,allowance_rule='max(10 mm, 10% of finished cut length)',
                required_cut_mm=required,maximum_18awg_cut_mm=225,
                voltage_drop_at_225_v=drop(225),voltage_drop_at_required_v=drop(required) if required else None,
                peak_current_a=8.6,limit_v=.15,wire='18 AWG; 21 mOhm/m per conductor; 60 mm pack lead; 4.46 mOhm fuse; 1 mOhm XT30',
                shortfall_at_225_mm=path-(225-22.5) if path else None,
                pair_section_mm=[2.4,4.8],inner_bend_min_mm=4.8,
                status='blocked' if required is None or required>225 else 'unqualified-geometric-pass',
                decision='Do not cut or energize. Measure actual pads; revise route or power architecture and repeat electrical/thermal tests. No 16 AWG substitution or voltage-drop waiver is applied.')




def xt30_transform(p):
    c=math.sqrt(.5);d=vsub(p,[-47.25,-.1,-33.2])
    return [-48.8+c*d[0]+c*d[2],-.1+d[1],-18-c*d[0]+c*d[2]]

def xt30_exit_study():
    c=math.sqrt(.5);out=[]
    for name,x,r,od,d,n in [('female',-60.25,8,3.2,[-c,0,c],[c,0,c]),('male',-34.25,6,2.4,[c,0,-c],[-c,0,-c])]:
        for y in (-5.2,-.2):
            face=xt30_transform([x,y,-33.2]);start=vadd(face,vmul(d,4));ps=[]
            for j in range(9):ps.append(vadd(face,vmul(d,4*j/8)))
            for j in range(1,33):
                t=math.pi/4*j/32;ps.append(vadd(start,vadd(vmul(d,r*math.sin(t)),vmul(n,r*(1-math.cos(t))))))
            box={ax:[min(p[i] for p in ps)-od/2,max(p[i] for p in ps)+od/2] for i,ax in enumerate(AXES)}
            out.append(dict(end=name,core_y=y,face=face,points=ps,box=box,straight_mm=4,radius_mm=r,od_mm=od,length_mm=4+r*math.pi/4,
                            terminal_tangent=[0,0,1] if name=='female' else [0,0,-1]))
    return dict(center=[-48.8,-.1,-18],rotation_y_deg=45,full_envelope=tbox(L.COTS['xt30_pair']['box'],xt30_transform),
                core_spacing_assumption_mm=5,core_spacing_gate='Actual pin centers and positive/negative orientation unknown; no polarity is inferred from this drawing',
                curves=out,web_window=B(-65.8,-35,-9,9,-10,2.5),floor_passage=B(-65.8,-55,-8,2,0,2.5),
                status='Local connector exits only; inline fuse, complete stow and service motion still open',
                source='Source proxy and independent local curve study; exact printed cradle caused0.8mm rearward shift')


def inline_fuse_study():
    c=math.sqrt(.5);d=[-c,0,c];n=[-c,0,-c];parts=[]
    for y in (-5.2,-.2):
        face=xt30_transform([-60.25,y,-33.2]);ss=vadd(face,vmul(d,4));end=vadd(ss,vmul(d,20))
        curve=[]
        for j in range(33):
            a=math.pi/4*j/32;curve.append(vadd(end,vadd(vmul(d,8*math.sin(a)),vmul(n,8*(1-math.cos(a))))))
        parts.append(dict(core_y=y,positive_assumption=y==-5.2,housing_face=face,rigid_start=ss,rigid_end=end,outgoing_curve=curve,
                          outgoing_radius_mm=8,outgoing_tangent=[-1,0,0],od_mm=3.2))
    pos=parts[0];start=pos['rigid_start'];end=pos['rigid_end']
    def cb(radius):return {ax:[min(start[i],end[i])-radius*math.sqrt(1-d[i]*d[i]),max(start[i],end[i])+radius*math.sqrt(1-d[i]*d[i])] for i,ax in enumerate(AXES)}
    return dict(status='Local inline fuse and two outgoing cores only; downstream routing and250mm stow/service remain blocked',
                sleeve_axis_start=start,sleeve_axis_end=end,sleeve_radius_mm=2.5,sleeve_box=cb(2.5),pocket_radius_mm=2.8,pocket_box=cb(2.8),
                path_to_near_end_mm=4,path_to_far_end_mm=24,proximity_limit_mm=25,cores=parts,
                pocket_description='Cut the oblique radius2.8 cylinder, not its enclosing rectangular box. It merges the rear base sliding void locally; exact loaded-ligament review required.',
                floor_pocket_rear_x_at_z2_5=-73.2598,base_pocket_rear_x_at_z0=-70.7598,pocket_lowest_z_at_grip_rear_x_minus71=.2402,
                source_clearances_mm=dict(fuse_to_cooler=3.819282,fuse_to_pi=4.8,outgoing_wire_to_cooler=1.643903,negative_core_to_pi=.7,wire_to_fuse=.9,core_to_core=1.8),
                gates=['Actual positive pin must be the modeledY=-5.2 exit; other polarity makes sleeve overlap Pi','20mm includes ALL rigid solder joints and heat-shrink; extra4mm after it would hit cooler','Actual pin center spacing5mm is unmeasured','Remove old side-mounted fuse from XT30 proxy; do not model or purchase two fuses','Confirm full250mm stored length and below-mouth service motion'])

def pigtail_16_study(stack_y=22.2):
    pad=rp([*L.PIGTAIL['pad']['xy'],L.PI['x1203_z'][1]],stack_y)
    # Source pad is on the PCB face; insulation center must stand1.9mm off it.
    # This is an unmeasured solder-root construction, explicitly gated.
    root=[pad[0],12.7,pad[2]]
    points=[root,[-31,12.7,35],[-31,-3.3,35],[-31,-3.3,4.5],[-63.163961,-3.3,4.5],[-63.163961,-3.3,-125]]
    p=rounded_path(points,8,8,0);stub=math.dist(pad,root);length=p['rounded_length_mm']+stub
    nominal_wire_r=2*(.270*13.17+.060*21)
    contacts=4.46+1
    cold=8.6*(nominal_wire_r+contacts)/1000
    hot=8.6*(nominal_wire_r*(1+.00393*(60-20))+contacts)/1000
    hole=B(-65.8,-55,-8,2,0,2.5)
    floor_box=B(-63.163961-1.6,-63.163961+1.6,-6.8,1.4,0,2.5)
    return dict(assumed_pad=pad,pad_status=L.PIGTAIL['pad']['status'],wire='Proposed 16 AWG copper, vendor and actual OD pending; existing 60 mm pack lead stays 18 AWG',
                service_path=p,service_route_mm=length,solder_exit_stub_mm=stub,solder_exit_stub_gate='Actual joint exit and insulation center offset must be measured; do not route insulation through the PCB',required_cut_mm=math.ceil(length/.9/5)*5,selected_cut_mm=270,
                allowance_rule='max(10 mm, 10% finished cut): 27 mm reserved',remaining_after_allowance_mm=270-27-length,
                peak_current_a=8.6,limit_v=.15,wire16_mohm_per_m_at20c=13.17,pack18_mohm_per_m_at20c=21,
                fuse_cold_mohm=4.46,xt30_mohm=1,voltage_drop_nominal_v=cold,voltage_drop_both_wires60c_v=hot,
                thermal_model='Copper alpha 0.00393/K from 20 to 60 C; fuse/contact resistance remains baseline estimate, not a hot-fuse qualification',
                additional_hot_contact_budget_mohm=(.15-hot)/8.6*1000,
                alternative_270mm=dict(selected=True,length_mm=270,remaining_after_allowance_mm=270-27-length,voltage_drop_both_wires60c_v=8.6*(2*(.270*13.17+.060*21)*(1+.00393*40)+5.46)/1000,note='Separate candidate, not silently substituted; positive fuse segment, actual solder roots and full service motion still require validation'),
                per_core_od_reserved_mm=3.2,pair_section_mm=[6.4,3.2],pair_width_axis='X in the provisional inter-board approach; individual Y-spaced cores at rotated XT30',inner_bend_min_mm=6.4,centerline_bend_mm=8,
                floor_pair_box=floor_box,floor_hole=hole,floor_clearance_mm=dict(x=min(floor_box['x'][0]-hole['x'][0],hole['x'][1]-floor_box['x'][1]),y=min(floor_box['y'][0]-hole['y'][0],hole['y'][1]-floor_box['y'][1])),
                strain_relief='Neutral-cure RTV at actual pads; keep pair just below UPS PCB with measured component and standoff clearances. No unsupported solder joints.',
                rejected_250mm=dict(usable_length_mm=225,shortfall_mm=length-225,reason='Conservative source bypass exceeds usable250mm lead'),status='PROVISIONAL270mm service-centerline estimate; pad transition and full flexible deployment remain STOPs',
                decision='Do not freeze or energize. Confirm vendor OD/resistance, actual pads and solder-cup sizes, reroute or re-pose the grip junction, then repeat exact sweeps and the G-W5 hot test.')



def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]

def rotate(v,axis,angle):
    return vadd(vadd(vmul(v,math.cos(angle)),vmul(cross(axis,v),math.sin(angle))),vmul(axis,dot(axis,v)*(1-math.cos(angle))))

def bezier(p0,p1,p2,p3,t):
    return [((1-t)**3*p0[i]+3*(1-t)**2*t*p1[i]+3*(1-t)*t*t*p2[i]+t**3*p3[i]) for i in range(3)]

def rejected_twisted_ribbon_study(length,stack_y=22.2,evf_shift_y=11,obstacles=(),right_inner=-25.5,left_inner=25.2, profile=None):
    """Full 10 x 0.4 mm ribbon frames, parallel transported then slowly twisted.

    0.4 mm is an unverified conservative thickness allowance, NOT a vendor spec.
    The signed roll needed after parallel transport is calculated, not assumed.
    Copper layer depth and allowable strain are unknown: geometric clearance is
    never relabelled as material/electrical qualification.
    """
    width=10.;thick=.4;rad=5.0;pi=[-59.8,stack_y-21.85,89.5]
    evf=[-141.6+154-length,-5.5+evf_shift_y,37.3]
    pts=[]
    def add(q):
        if not pts or math.dist(pts[-1],q)>1e-7:pts.append(list(q))
    for j in range(9):add([pi[0],pi[1],pi[2]+2*j/8])
    # Natural first bend: width remains X, bending in YZ rather than edgewise.
    for j in range(1,81):
        a=math.pi*j/80
        add([pi[0],pi[1]-rad*(1-math.cos(a)),pi[2]+2+rad*math.sin(a)])
    twist_start=len(pts)-1
    profile=profile or [78,-20,76,-85,77]
    p0=pts[-1];p1=[pi[0],p0[1],profile[0]];p2=[pi[0],profile[1],profile[2]];p3=[profile[3],evf[1],profile[4]];p4=[-105,evf[1],72];p5=[-115,evf[1],72]
    controls=[p0,p1,p2,p3,p4,p5]
    for j in range(1,401):
        t=j/400
        add([sum(math.comb(5,k)*(1-t)**(5-k)*t**k*controls[k][ax] for k in range(6)) for ax in range(3)])
    p3=p5
    twist_end=len(pts)-1
    tail=rounded_path([p3,[-134.5,evf[1],72],[-134.5,evf[1],27.3],[evf[0],evf[1],27.3],evf],rad,0,2,.35)
    if tail['errors']:return dict(status='blocked',errors=tail['errors'])
    for q in tail['sampled_centerline']:add(q)
    tangents=[]
    for i,p in enumerate(pts):
        t=vsub(pts[min(i+1,len(pts)-1)],pts[max(0,i-1)])
        tangents.append(unit(t))
    widths=[[1.,0.,0.]]
    for a,b in zip(tangents,tangents[1:]):
        axis=cross(a,b);mag=norm(axis)
        w=widths[-1]
        if mag>1e-12:w=rotate(w,vmul(axis,1/mag),math.atan2(mag,dot(a,b)))
        widths.append(unit(vsub(w,vmul(b,dot(w,b)))))
    desired=[0.,1.,0.];tt=tangents[twist_end];ww=widths[twist_end]
    roll=math.atan2(dot(tt,cross(ww,desired)),dot(ww,desired))
    arc=[0.]
    for a,b in zip(pts,pts[1:]):arc.append(arc[-1]+math.dist(a,b))
    twist_len=arc[twist_end]-arc[twist_start]
    natural_roll=[];curv=[]
    for i in range(len(pts)):
        dk=vmul(vsub(tangents[min(i+1,len(pts)-1)],tangents[max(0,i-1)]),1/max(1e-9,arc[min(i+1,len(pts)-1)]-arc[max(0,i-1)]))
        curv.append(dk)
        base=widths[i];nn=unit(cross(tangents[i],base));aa=dot(dk,base);bb=dot(dk,nn)
        prior=natural_roll[-1] if natural_roll else 0.
        theta=math.atan2(-aa,bb) if abs(aa)+abs(bb)>1e-5 else prior
        theta=min([theta+k*math.pi for k in range(-6,7)],key=lambda x:abs(x-prior))
        natural_roll.append(theta)
    # Use a gradual material-frame roll, not abrupt Frenet-frame flips.
    natural_roll=[roll*(max(0,min(1,(ss-arc[twist_start])/twist_len))**2)*(3-2*max(0,min(1,(ss-arc[twist_start])/twist_len))) for ss in arc]
    frames=[];max_edge=0.;max_thick=0.;max_twist=0.
    for i,p in enumerate(pts):
        u=max(0,min(1,(arc[i]-arc[twist_start])/twist_len))
        smooth=u*u*(3-2*u)
        w=rotate(widths[i],tangents[i],natural_roll[i]);n=unit(cross(tangents[i],w))
        cs=[vadd(p,vadd(vmul(w,a*width/2),vmul(n,b*thick/2))) for a,b in [(-1,-1),(1,-1),(1,1),(-1,1)]]
        dk=[0.,0.,0.]
        if 0<i<len(pts)-1:
            ds=(arc[i+1]-arc[i-1]);dk=vmul(vsub(tangents[i+1],tangents[i-1]),1/ds)
        edge=width/2*abs(dot(dk,w));bend=thick/2*abs(dot(dk,n))
        rate=abs(natural_roll[min(i+1,len(pts)-1)]-natural_roll[max(0,i-1)])/max(1e-9,arc[min(i+1,len(pts)-1)]-arc[max(0,i-1)])
        twstrain=math.sqrt(1+(width/2*rate)**2)-1
        max_edge=max(max_edge,edge);max_thick=max(max_thick,bend);max_twist=max(max_twist,twstrain)
        frames.append(dict(point=p,tangent=tangents[i],width_vector=w,normal=n,corners=cs,
                           edgewise_bend_strain_proxy=edge,outer_laminate_bend_strain_proxy=bend,twist_edge_extension_proxy=twstrain))
    segments=[];hits={};walls=[]
    for i,(a,b) in enumerate(zip(frames,frames[1:])):
        cs=a['corners']+b['corners']
        box={ax:[min(q[j] for q in cs),max(q[j] for q in cs)] for j,ax in enumerate(AXES)}
        segments.append(dict(vertices=cs,box=box))
        for ax,lo,hi in [('x',-length+2.5,-5.2),('y',right_inner,left_inner),('z',2.5,97.5)]:
            if box[ax][0]<lo-1e-6 or box[ax][1]>hi+1e-6:
                if ax not in walls:walls.append(ax)
        for o in obstacles:
            ib=obstacle_overlap(box,o)
            if ib:
                h=hits.setdefault(o['id'],dict(obstacle=o['id'],overlap_box=ib,segments=0))
                h['segments']+=1;h['overlap_box']=hull([h['overlap_box'],ib])
    return dict(status='BLOCKED: excessive edgewise distortion in the proposed ribbon shape; not a physically cleared route',
                envelope_status='clear of listed source proxies only' if not walls and not hits else 'blocked by a listed source proxy or wall',
                width_mm=width,thickness_allowance_mm=thick,minimum_centerline_radius_allowance_mm=rad,
                width_at_pi=[1,0,0],width_at_evf=[0,1,0],endpoint_global_width_change_deg=90,
                transported_frame_roll_deg=math.degrees(natural_roll[-1]),frame_method='Parallel transport plus a cubic-smooth material roll distributed over the complete transition; all bending and twist strain proxies remain explicit',twist_zone_length_mm=twist_len,
                routed_length_mm=arc[-1],stock_length_mm=200,remaining_length_mm=200-arc[-1],
                alternate_ribbon=dict(pn='Adafruit3562',length_mm=300,url='https://www.adafruit.com/product/3562',note='Stock ribbon intact; do not cut/splice. Availability not confirmed.'),
                max_edgewise_bend_strain_proxy=max_edge,max_outer_laminate_bend_strain_proxy=max_thick,max_twist_edge_extension_proxy=max_twist,
                material_warning='The large edgewise proxy is a SHAPE BLOCKER, not merely an unknown material property. These are kinematic outer-edge/outer-laminate proxies, not copper strain predictions. Copper layer depth, neutral axis, laminate shear/slip, allowed bend, allowed twist and flex life are unpublished. Any nonzero proxy needs a measured sample and electrical qualification; no guessed material limit is used.',
                geometric_check='Full rectangle at every sample with transported and smoothly twisted width vectors; adjacent-frame prism AABBs are conservative. Exact solid loft/intersections with printed geometry still required.',
                wall_overrun_axes=walls,obstacle_overlaps=list(hits.values()),frames=frames,segments=segments)


def ribbon_study(length,stack_y=22.2,evf_shift_y=11,obstacles=(),right_inner=-25.5,left_inner=25.2,profile=None,pose="installed"):
    """Natural U turn + one isometric 45-degree cylindrical miter fold.

    Adafruit3557 Pi head / 3556 EVF head. The miter is meshed in material
    coordinates; it is NOT a perpendicular-section loft. No edgewise stretch or
    arbitrary plane twist is introduced. Radius/material/clocking are still gates.
    """
    if pose not in ('installed','premate'):raise ValueError(pose)
    drop=6 if pose=='premate' else 0
    width=10.;thick=.4;R=3.;rr=5.;q=math.sqrt(.5)
    pi=[-59.8,stack_y-21.85-15,77.5]
    evf=[-141.6+154-length,-5.5+evf_shift_y,37.3-drop]
    sf=math.sqrt(2)*math.pi*R
    origin=[pi[0],evf[1]-math.pi*R*q,83.5]
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
    for j in range(9):pre.append([pi[0],pi[1]-2*j/8,pi[2]])
    uy=pi[1]-2
    for j in range(1,61):
        t=math.pi*j/60
        pre.append([pi[0],uy-R*math.sin(t),pi[2]+R*(1-math.cos(t))])
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
    stock=200 if length<180 else 300
    bottom=(28.3 if stock==200 else 24.3)-drop
    base_knots=[post_start,[-115,evf[1],89.5],[-115,evf[1],74.5],[-134,evf[1],74.5],[-134,evf[1],bottom],[evf[0],evf[1],bottom],evf]
    base_post=rounded_path(base_knots,rr,0,4,.35)
    prefix_length=2+math.pi*R+math.dist(start,target)+(sf+10)
    base_total=prefix_length+base_post['rounded_length_mm']
    arc_excess=2*math.pi*rr-4*rr
    if stock==200:
        depth=(stock-base_total-arc_excess)/2
        # Complete stock cable: four flatwise R5 quarters and two sliding legs.
        knots=[post_start,[-81,evf[1],89.5],[-81,evf[1],79.5-depth],[-91,evf[1],79.5-depth],[-91,evf[1],89.5]]+base_knots[1:]
        loops=[dict(plane='XZ',start_x=-76,end_x=-96,leg_mm=depth,radius_mm=rr,highest_z=89.5,lowest_z=79.5-depth)]
    else:
        depth=(stock-base_total-2*arc_excess)/4
        # Two lateral loops in the clear rear bay; stay forward of EVF hardware.
        knots=base_knots[:4]
        for top in (69.5,49.5):
            knots += [[-134,evf[1],top-5],[-144-depth,evf[1],top-5],[-144-depth,evf[1],top-15],[-134,evf[1],top-15]]
        knots += base_knots[4:]
        loops=[dict(plane='XZ',start_z=t,end_z=t-20,leg_mm=depth,radius_mm=rr,rear_x=-144-depth) for t in (69.5,49.5)]
    post=rounded_path(knots,rr,0,4,.35)
    if depth<0 or post['errors']:return dict(status='blocked',errors=post['errors'] or ['negative slack-loop depth'])
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
                pose=pose,evf_head_displacement=[0,0,-drop],explicit_slack_loops=loops,base_route_without_slack_mm=base_total,head_set='Adafruit3557 right-angle Pi +3556 straight EVF',head_clocking_gate='3557 cable exit toward-Pi-Y inferred from keyed plug orientation; verify against actual Pi and adapter before print release',
                width_mm=width,thickness_allowance_mm=thick,minimum_centerline_radius_allowance_mm=R,
                shape='R3 natural U-turn plus one 45-degree cylindrical developable fold, then R5 flatwise turns; no imposed spatial twist',
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

# ---------------------------------------------------------------------------------------------------------------
# Review 2026-10-10 (H1: VN-26 routes, VN-60 / FP-11f): installed EVF feed and pack-lead routes.
# The EVF feed is a cut-to-length assembly (BOM D2-22 Adafruit 4448 donor; D2-16 1N5817 in the + conductor with the
# ground spliced beside it; D2-23 Pololu 2180 / 2181 RCY pair, 100 mm tails). The route starts on the GPIO-side USB2
# port face (connectors() p_usb_pi) and runs straight through the 31 x 15.5 x 9.8 mm head/bend allowance: the
# received rigid head (metal, overmold and strain relief) must end within feed['head_max_mm'] (24.7) of the port face
# (MEASUREMENTS-TO-CLOSE Adafruit 4448 row; re-route if longer). It then drops into the -Y channel behind the USB
# heads, runs forward under the panel-screw boss carrying the splice zone, turns up short of the stored power loops
# (negative return at X-104), comes back along Z38.5 carrying the mated RCY pair (the storage stick, fitted later at
# storage_in, is still out at evf_mate; finger access is the mate_reach HOLD), climbs the rear corner, crosses over
# the board rail and lands on the
# EVF 5 V pad point of record from above (r7 MATE_POSES usb_5v_evf far point, moved with the EVF shift; the pad
# position itself is MP-EVF). The rigid parts are oriented boxes on straight legs, checked by verify_harness_checks.py
# (feed_volumes rows: exact Boolean against the closed camera and the HDMI ribbon cells, cable separation, tails).
USB5V_KNOTS = [None,                                   # port face centre, from connectors() p_usb_pi
               (-152.5, None, 16.0),                   # head axis end: the bend starts head_max_mm from the face
               (-152.5, -21.5, 20.5),                  # -Y exit below the storage stick, clear of the rear wall
               (-108.0, -21.5, 20.5),                  # splice leg (Z20.5, above the J4 lock boss top Z12.6)
               (-108.0, -19.5, 38.5),                  # turn up 4 mm short of the negative power loop at X-104
               (-152.5, -19.5, 38.5),                  # RCY leg (Z35..42: under the panel boss, over the stick lane)
               (-152.5, -19.5, 52.0),                  # rear-corner climb (eyepiece and EVF plate are further -X / +Y)
               (-146.5, -19.5, 64.0),                  # step forward past the EVF rear plate and the OLED seat bars
               (-146.5, -19.5, 76.0),                  # up beside the board rail (X-143.95), clear of the seat (X-149)
               (-140.8, -4.0, 77.7),                   # over the rail to the pad column
               None]                                   # EVF 5 V pad point of record (approached from above)
USB5V_RADIUS, USB5V_TAILS, USB5V_OD = 6.0, (6.0, 4.0), 3.6
FEED_VOLUMES = [   # id, leg, station after the leg's entry fillet, length along the route, (width, height), width axis
    dict(id='diode_sleeve', leg=2, station=1.0, length=30.0, section=(4.8, 4.8), width_hint=(0, 0, 1),
         source='BOM D2-16 MCC 1N5817-TP (DO-41 body <= 5.2 mm x dia 2.7 mm) spliced into the + core by the r7 splice '
                'method (1.5 mm stub + 5 mm lap per lead, ASSEMBLY r4 fuse splice) under the BOM D2-46 adhesive 3:1 '
                'sleeve (about 4.8 mm recovered; 30 mm class as the r4 fuse splice); square section circumscribing it. '
                'The ground lap splice is staggered along the same leg inside the lead envelope.',
         gate='G-W6 and MEASUREMENTS-TO-CLOSE Adafruit 4448 row (cut plan, splice and sleeve lengths)', default=None),
    dict(id='option_c_reserve', leg=2, station=8.0, length=16.0, section=(7.5, 4.5), width_hint=(0, 0, 1),
         source='BOM D2-16P option-C regulator carrier, est. 16 x 7.5 x 4.5 mm sleeved envelope (carrier not measured). '
                'Option C replaces the diode at the same splice (r7 WIRING s4.8), so its reserve is centred in the '
                'splice zone, as r7 placed the carrier inside the feed keep-out.',
         gate='G-W13 on receipt of the carrier (only if option C is adopted)',
         default='default pending user decision 10 (VN-80): the reserve is kept free on the route so option C can '
                 'replace the diode without a re-route; its BOM quantity stays 0'),
    dict(id='rcy_pair', leg=4, station=0.25, length=32.0, section=(7.0, 7.0), width_hint=(0, 0, 1),
         source='BOM D2-23 Pololu 2180 + 2181 mated pair, provisional 32 x 7 x 7 mm junction reserve (ASSEMBLY-VERTICAL)',
         gate='MEASUREMENTS-TO-CLOSE EVF power RCY pair row (housings, mated length, exits); finger access at evf_mate '
              'is the mate_reach evf_5v:evf HOLD', default=None),
]


def place_on_leg(curve, leg, station, length, section, width_hint):
    """Oriented box of length x section on the straight part of leg `leg` (knot leg -> leg+1), starting `station` mm
    after the leg's entry fillet. Raises if it does not fit on the straight part."""
    k, tr = curve['knots'], curve['corner_trim_mm']
    a, b = k[leg], k[leg + 1]
    u = unit(vsub(b, a))
    straight = math.dist(a, b) - tr[leg] - tr[leg + 1]
    if station < -1e-9 or station + length > straight + 1e-9:
        raise ValueError('feed volume does not fit on leg %d: %.2f + %.2f > %.2f mm' % (leg, station, length, straight))
    start = vadd(a, vmul(u, tr[leg] + station))
    c = vadd(start, vmul(u, length / 2))
    w = unit(vsub(list(width_hint), vmul(u, dot(list(width_hint), u))))
    h = cross(u, w)
    cs = [vadd(c, vadd(vmul(u, su * length / 2), vadd(vmul(w, sw * section[0] / 2), vmul(h, sh * section[1] / 2))))
          for su in (-1, 1) for sw in (-1, 1) for sh in (-1, 1)]
    return dict(leg=leg, station_mm=station, straight_mm=straight, center=c, axis=u, width_vector=w, height_vector=h,
                dims_mm=[length, section[0], section[1]], aabb=[f(q[i] for q in cs) for i in range(3) for f in (min, max)],
                ends=[vadd(c, vmul(u, -length / 2)), vadd(c, vmul(u, length / 2))])


def _station(points, q):
    """Arc position along a sampled centreline of its point nearest q."""
    best, s, acc = (float('inf'), 0.0), 0.0, 0.0
    for a, b in zip(points, points[1:]):
        ab = vsub(b, a); n2 = dot(ab, ab)
        t = 0.0 if n2 == 0 else max(0.0, min(1.0, dot(vsub(q, a), ab) / n2))
        d = math.dist(vadd(a, vmul(ab, t)), q)
        if d < best[0]:
            best = (d, acc + t * math.sqrt(n2))
        acc += math.sqrt(n2)
    return best[1]


def usb_5v_feed(port_centre, pad):
    knots = []
    for k in USB5V_KNOTS:
        knots.append(list(port_centre) if k is None and not knots else list(pad) if k is None
                     else [k[0], port_centre[1] if k[1] is None else k[1], k[2]])
    curve = rounded_path(knots, USB5V_RADIUS, USB5V_TAILS[0], USB5V_TAILS[1], .2)
    if curve['errors']:
        return curve, None
    vols = []
    for v in FEED_VOLUMES:
        pv = place_on_leg(curve, v['leg'], v['station'], v['length'], v['section'], v['width_hint'])
        pv.update(id=v['id'], source=v['source'], gate=v['gate'], default=v['default'])
        vols.append(pv)
    pts = curve['sampled_centerline']
    head = math.dist(knots[0], knots[1]) - curve['corner_trim_mm'][1]
    by = {v['id']: v for v in vols}
    st = dict(head_exit=head, splice_start=_station(pts, by['diode_sleeve']['ends'][0]),
              splice_end=_station(pts, by['diode_sleeve']['ends'][1]), rcy_start=_station(pts, by['rcy_pair']['ends'][0]),
              rcy_end=_station(pts, by['rcy_pair']['ends'][1]), board=curve['rounded_length_mm'])
    feed = dict(volumes=vols, stations_mm=st, head_max_mm=head, pad_point=list(pad),
                head_gate='The received rigid head (metal, overmold, strain relief) must end within %.1f mm of the port '
                          'face for this route (MEASUREMENTS-TO-CLOSE Adafruit 4448 row); a longer head needs a '
                          're-route.' % head,
                pad_gate='EVF 5 V pad point is the r7 usb_5v_evf far point moved with the EVF shift (MP-EVF measures '
                         'the traced EXT+/GND pads)',
                carried='The donor half (head to the 2180 housing) is plugged on the bench and carried with the module '
                        'at carrier_in; the 2181 half travels with the EVF board at evf_in and is mated in situ at '
                        'evf_mate (mate_reach evf_5v:evf HOLD).')
    return curve, feed


def pack_lead_route(power):
    """Pack lead from the pack top (+X end; hypothesis of record, MP-PACK measures the BMS lead exit) to the posed XT30
    male face. The two 18 AWG cores leave the male contacts at the 5 mm pitch (power_routes core_exit_spacing) and
    join the bundle PACK_MERGE_MM out along the housing axis: the bundle is swept at the two-core envelope up to the
    merge point (sweep_points) and each core on its own stub from its contact (harness_rules installed clearance)."""
    C, M = power['junction_center'], power['junction_transform_matrix']
    u, v = [M[i][0] for i in range(3)], [M[i][1] for i in range(3)]
    p = lambda a, b: [C[i] + u[i] * a + v[i] * b for i in range(3)]
    face = p(13.0, -2.6)                                # male wire face centre between the contacts (v -5.1 / -0.1)
    knee = vadd(face, vmul(u, 10.0))                    # straight out of the housing along its axis
    root = [-29.0, 0.5, -36.8]                          # pack top face near its +X end (old knots' +X-end hypothesis)
    curve = rounded_path([root, knee, face], 6.0, 4.0, 4.0, .2)
    merge = vadd(face, vmul(u, PACK_MERGE_MM))
    stubs = []
    for b in (-5.1, -0.1):
        a0 = p(13.0, b)
        stubs.append(dict(id='core_v%+.1f' % b, d=2.4, points=rounded_path(
            [a0, vadd(a0, vmul(u, 1.5)), merge], 1.0, 0, 0, .2)['sampled_centerline']))
    sweep = None
    if not curve['errors']:
        # the axial distance from the face falls monotonically along root -> knee -> face
        sweep = [q for q in curve['sampled_centerline'] if dot(vsub(q, face), u) > PACK_MERGE_MM + 1e-9] + [merge]
    return curve, stubs, sweep


PACK_MERGE_MM = 8.0   # cores fan from the 5 mm contact pitch into the bundle within this distance of the male face


def build(length=158, stack_y=22.2, evf_shift_y=11, right_inner=-25.5, left_inner=25.2, panel_shift_y=3, power_button=True, hdmi_assembly="adafruit3557_3556", pigtail_awg=16, upper_storage=True, hdmi_stock_mm=300):
    if length<145:raise ValueError('length too short for the specified stack')
    roll=lambda p:rp(p,stack_y)
    plugs,hs=connectors(length,stack_y,evf_shift_y,panel_shift_y,hdmi_assembly); byid={p['id']:p for p in plugs}
    obs=source_obstacles(length,stack_y,evf_shift_y,power_button,panel_shift_y,upper_storage);e=154-length
    center_hdr=lambda cid:[sum(h['wire_exit'][i] for h in hs if h['cable']==cid)/sum(h['cable']==cid for h in hs) for i in range(3)]
    qt=center_hdr('qt');run=center_hdr('run_lead');fps=center_hdr('fps_lead')
    # Tail points on the FULL retained source envelopes. HDMI/USB plug+strain-
    # relief boxes have no validated split: those root assumptions stay gated.
    hd0=[-59.8,stack_y-41,67.3]; hd1=[-140.8+e,-5.5+evf_shift_y,52]
    usb0=[-147,stack_y-32.1,60.25];usb1=[-136.8+e,-15+evf_shift_y,67]
    fpc1=[L.cam_cover_rear()-3,0,43.75]
    definitions=[
        ('fpc',200,.30,1,5,4,[[-83,stack_y-23,61],[-83,stack_y-23,82],[-33.5,stack_y-23,82],[-33.5,0,43.75],fpc1],
         '22-to-15 ribbon, width16mm. Provisional4mm final straight replaces a rejected5mm allowance: geometry offers4.41mm. Actual tail/bend requirement and full-width developable folds MUST be measured; this is not a passed FPC route.'),
        ('hdmi',200,3.0,6,6,6,[hd0,[-59.8,hd0[1]-12,67.3],[-59.8,hd0[1]-12,82],[-115,hd0[1]-12,82],[-115,-16,82],[-115,-16,40],[hd1[0],-16,40],[hd1[0],hd1[1],40],hd1],
         'Pi rigid envelope retained. Its outward tail cannot be hidden in the remaining side gap. EVF plug mates upward after the board is installed.'),
        ('usb_5v',200,USB5V_OD,USB5V_RADIUS,USB5V_TAILS[0],USB5V_TAILS[1],([usb0,[-147,usb0[1],81],[-118.8,-19,81],[-118.8,-19,20.5],[-130.8,-19,20.5],[-130.8,-3.5,20.5],[-130.8,-3.5,67],usb1] if length<180 else [usb0,[-147,usb0[1],81],[-134,usb0[1],81],[-134,usb1[1],67],usb1]),
         'Superseded upper-port study knots (kept only as the definition placeholder); the installed EVF feed is '
         'usb_5v_feed() for the selected compact scope, with the diode sleeve, option-C reserve and RCY pair placed as '
         'feed volumes (review VN-60 / FP-11f).'),
        ('oled_flex',50,.20,1,2,2,[[-146.07+e,evf_shift_y,84.8],[-146.07+e,evf_shift_y,88],[-146.07+e,9+evf_shift_y,88],[-140.4+e,9+evf_shift_y,88],[-140.4+e,-2.5+evf_shift_y,88]],
         'Native OLED/driver assembly only translated as a rigid optical module; 12.4 mm ribbon cannot be treated as round wire.'),
        ('qt',250,3.2,6.4,3,4,[[qt[0],-23.4,25],[qt[0],-23.4,78],[-84,-23.4,78],[-84,11.8+panel_shift_y,77],[-72,11.8+panel_shift_y,77]],
         'Each GPIO socket has its own source-derived housing and branch; upper main lane must be separated from HDMI, not stacked without a check.'),
        ('run_lead',250,1.6,3.2,3,3,[[run[0],-23.4,25],[run[0],-23.4,69],[run[0],5.5,69],[-30.5,5.5,69],[-30.5,10,55],[-35.2,10,50],[-35.2,10,32],[-35.2,5.25,28],[-31,5.25,5],[-31,5.25,-14.2]],
         'Two independent wires; floor hole is the existing run passage. Camera and power-linkage crossings remain checked.'),
        ('fps_lead',250,2.6,5.2,3,3,[[fps[0],-23.4,25],[fps[0],-23.4,66],[fps[0],-9,66],[-111,-9,79],[-111,9.2+panel_shift_y,78]],
         '200 mm GPIO-to-PH lead plus 50 mm switch pigtail retained; actual junction pose is separately reserved.'),
        ('pigtail',225,2.4,6,8,4,[[*roll([*L.PIGTAIL['pad']['xy'],L.PI['x1203_z'][1]])],[-39,8.5,63],[-39,8.5,5],[-39,-8.5,5],[-39,-8.5,-18],[-66.25,-8.5,-18],[-66.25,0,-30],[-60.25,0,-30]],
         'Two 18 AWG cores. 225 mm is the unchanged maximum, not an approved cut; service reach is evaluated separately.'),
        ('fan',60,2.0,4,3,3,[roll([-54,-10,27]),roll([-54,-2,27]),roll([-35,-2,27]),roll([-35,12,24])],
         'Native fan lead remains inside its moving stack; fan-header and motor-root coordinates are estimates, not measured ports.'),
        ('pack_lead',60,2.4,6,4,4,[[-26.5,0,-38],[-26.5,0,-24],[-34.25,0,-24],[-34.25,0,-33.2]],
         'Pack BMS lead and XT30 male remain in the grip; measured rigid solder-tail length is required.')]
    if hdmi_assembly.startswith('adafruit'):
        hp=byid['p_hdmi_pi']['wire_exit'];he=byid['p_hdmi_evf']['wire_exit']
        definitions[1]=('hdmi',200,.4,2.5,2,2,[hp,[hp[0],hp[1],94],[hp[0],-10,94],[-137,-10,94],[-137,he[1],94],[-137,he[1],31.3],[he[0],he[1],31.3],he],
            'Adafruit3557 right-angle Pi head,3556 straight EVF head and intact3562 ribbon300x10mm. Full material-coordinate geometry follows below.0.4mm thickness andR3 miter remain unverified physical allowances. Less durable/shielded than premade cable; positive retention and signal qualification required.')
    if pigtail_awg==16:
        definitions[7]=('pigtail',270,3.2,8,8,4,[roll([*L.PIGTAIL['pad']['xy'],L.PI['x1203_z'][1]]),[-35,12,35],[-39,-8.5,10],[-39,-8.5,-18],[-66.25,-8.5,-18],[-66.25,0,-30],[-60.25,0,-30]],
            'Selected provisional270mm16AWG, twoOD3.2 cores. Full per-core stored geometry is in power_routes.py. Actual pads, printed pocket/ligament and flexible withdrawal remain gates; existing60mm18AWG pack lead is unchanged.')
    if power_button:
        definitions.append(('power_button',150,1.6,3.2,3,3,
            [[-37,4.5,48],[-37,4.5,55],[-30.5,4.5,55],[-30.5,-12,55],[-33.8,-12,51],[-33.8,-12,33],[-20,-12,33],[-20,-12,25.5],[-20,-4.4+panel_shift_y,25.5]],
            'Adafruit1505 NO button to Pi5 J2, via removable 2-pin junction. J2 point is a routing hypothesis inside an unmeasured region, NOT the known header location. Verify NO contacts and Pi power-button behavior; not a hard battery isolator.'))
        plugs.extend([dict(id='p_power_j2',cable='power_button',end='pi5',box=None,rigid=False,estimated_pad_region=B(-45,-33,-1,6,38,51),qualification='Actual J2 solder-pad location, strain relief and solder access unmeasured'),
                      dict(id='p_power_switch',cable='power_button',end='power_switch',box=None,rigid=False,qualification='Terminal-root location and rear protection unmeasured; removable 2-pin inline junction required')])
    branches=[]
    for h in hs:
        root=h['wire_exit']
        c=rounded_path([root,[root[0],-23.4,root[2]],[root[0],-23.4,25]],3.2,3,0)
        branches.append(dict(id=h['id'],cable=h['cable'],pins=h['pins'],curve=c,od_mm=1.6,
                             status='blocked' if c['errors'] else 'geometric-only; actual wire OD and tail unmeasured'))
    routes=[]
    for cid,length_mm,od,r,tail0,tail1,pts,note in definitions:
        curve=rounded_path(pts,r,tail0,tail1)
        feed=None
        if cid=='usb_5v':
            # H1 (VN-26 routes, VN-60 / FP-11f): installed full-core route for the selected compact scope only.
            if (length,stack_y,evf_shift_y,panel_shift_y)==(158,22.2,11,3):
                try:
                    curve,feed=usb_5v_feed(byid['p_usb_pi']['port_center'],usb1)
                except ValueError as exc:
                    curve=dict(curve,sampled_centerline=[],rounded_length_mm=None,errors=['feed volume placement: %s' % exc],status='blocked')
                note=('Adafruit4448 cuttable donor (catalog300mm / supplier325+/-10) plus Pololu2180/2181 100mm tails and '
                      'the 1N5817 splice, cut to the installed route: GPIO-side USB2 port face -> -Y channel (splice zone) -> '
                      'RCY leg -> rear climb -> EVF 5 V pad point of record from above. Feed volumes, head length and pad '
                      'gates are in feed; the old 200mm value is an allocation, not a required intact stock length.')
            else:
                curve=dict(knots=None,sampled_centerline=[],rounded_length_mm=None,raw_length_mm=None,centerline_radius_mm=r,first_straight_min_mm=tail0,last_straight_min_mm=tail1,
                    errors=['Installed EVF feed route solved for the selected compact scope (length158, stackY22.2, EVFshift11, panelshift3) only; other scopes need their own route solve'],status='blocked')
        if cid=='fpc':
            note=('Official intact200mm camera cable, full16mm conservative width. Old centerline/root and remainder are superseded; both real inserted/free-flex frames and full material placement remain open.')
            curve=dict(knots=None,sampled_centerline=[],rounded_length_mm=None,raw_length_mm=None,centerline_radius_mm=r,first_straight_min_mm=tail0,last_straight_min_mm=tail1,
                errors=['Superseded root/path: source-registered CSI departs -Y and needs the camera inserted/free-flex datum. No current full installed route (the camera FPC of record is the signal_routes fpc centreline).'],status='blocked')
        if cid in ('pigtail','pack_lead'):
            curve=dict(knots=None,sampled_centerline=[],rounded_length_mm=None,raw_length_mm=None,centerline_radius_mm=r,first_straight_min_mm=tail0,last_straight_min_mm=tail1,errors=['Installed full-core route incomplete; use source-bounded local arcs in xt30_local_exits and pigtail_inline_fuse, not the retired horizontal-junction knots'],status='blocked')
        if cid=='hdmi' and hdmi_assembly.startswith('adafruit'):
            curve['ribbon_orientation_status']='BLOCKED pending full10mm width + keyed end-plane sweep, permitted twist and actual bend specification; a centerline is not an FFC-fit result'
        route_len=curve['rounded_length_mm']
        branch_lengths=[b['curve']['rounded_length_mm'] for b in branches if b['cable']==cid]
        if route_len is not None and branch_lengths:
            route_len=route_len+max(branch_lengths) if all(x is not None for x in branch_lengths) else None
        # Retain specified harness, reserving its WHOLE unconsumed length; no
        # virtual trimming of purchased FPC/HDMI/USB/QT/native leads.
        slack=length_mm-route_len if route_len is not None else None
        routes.append(dict(id=cid,name=next((c['name'] for c in L.CABLES if c['id']==cid),'Pi5 J2 normally-open power-button harness'),
                           ends=list(L.CABLE_ENDS.get(cid,('pi5','power_switch'))),length_mm=length_mm,od_mm=od,
                           curve=curve,branched_installed_length_mm=route_len,slack_mm=slack,note=note,status='blocked' if curve['errors'] or (slack is not None and slack<0) else 'unqualified-path',
                           endpoint_gate='Verify wire-root position, connector strain relief, minimum static and repeated-service bend radii on actual purchased harness.'))
        if feed:
            routes[-1].update(feed=feed,selected_source='routes.py:usb_5v_feed')
    for pp in plugs:
        if pp.get('rigid') and pp.get('box'):obs.append(dict(id='connector_'+pp['id'],box=pp['box']))
    ribbon=None;ribbon_premate=None;ribbon_unplugged=None
    if hdmi_assembly.startswith('adafruit'):
        if length<180 and hdmi_stock_mm==300:
            import hdmi_routes
            ribbon=hdmi_routes.compact_300_service(0,0,obs)
            ribbon_premate=hdmi_routes.compact_300_service(0,6,obs)
            ribbon_unplugged=hdmi_routes.compact_300_service(6,6,obs)
        else:
            ribbon=ribbon_study(length,stack_y,evf_shift_y,obs,right_inner,left_inner)
            ribbon_premate=ribbon_study(length,stack_y,evf_shift_y,obs,right_inner,left_inner,pose='premate')
    if ribbon and ribbon.get('routed_length_mm'):
        rr=next(c for c in routes if c['id']=='hdmi')
        rr['curve']['sampled_centerline']=[f['point'] for f in ribbon['frames']]
        rr['curve']['rounded_length_mm']=ribbon['routed_length_mm']
        rr['curve']['knots']='See hdmi_ribbon: natural U, material-coordinate developable45degree fold, then flatwise XZ bends'
        rr['branched_installed_length_mm']=ribbon['routed_length_mm']
        rr['length_mm']=ribbon['stock_length_mm']
        rr['slack_mm']=ribbon['stock_length_mm']-ribbon['routed_length_mm']
        rr['slack_mode']='All stock length appears in explicit deployable loops; no empty volume allowance'
        rr['curve']['ribbon_orientation_status']=ribbon['status']
        rr['curve']['centerline_radius_mm']=3
        rr['curve']['first_straight_min_mm']=2
        rr['curve']['last_straight_min_mm']=4
        rr['curve']['corner_trim_mm']=None
        rr['curve']['turn_degrees']=None
        rr['curve']['raw_length_mm']=None
        rr['curve']['errors']=[]
        rr['curve']['status']='full-developable-material-shape; physical gates open'
        rr['full_width_reservation_status']=ribbon['status']
    # Authoritative per-core source proposals, separate from retired exploratory
    # knots. Root/fan-in gaps are carried as explicit gates, never hidden links.
    import power_routes, signal_routes
    api=types.SimpleNamespace(**globals())
    selected_power=power_routes.build(api,obs) if pigtail_awg==16 else None
    signals=signal_routes.build(api)
    requested_scope=(stack_y,evf_shift_y,right_inner,left_inner,panel_shift_y)
    selected_scope=(22.2,11,-25.5,25.2,3)
    signals['parameter_scope_gate']='Selected signal and power source shapes use stack_y22.2, EVFshift11, innerY[-25.5,25.2], panelshift3. Other requested transforms require a new route solve.' if requested_scope!=selected_scope else 'Selected parameter scope matched; hardware qualification remains open.'
    route_by_id={r['id']:r for r in routes}
    for key,cid in [('qt','qt'),('fps','fps_lead'),('fpc','fpc'),('power_button','power_button')]:
        if cid not in route_by_id:continue
        item=signals[key];rr=route_by_id[cid]
        rr['curve']=copy.deepcopy(item['curve']);rr['selected_source']='signal_routes.py:'+key
        rr['selected_geometry']=item;rr['status']='blocked-physical-interface-gates'
        total=item.get('modeled_flexible_wire_total_mm',item.get('nominal_total_mm',item.get('nominal_longest_breakout_plus_main_mm',rr['curve']['rounded_length_mm'])))
        rr['branched_installed_length_mm']=total;rr['slack_mm']=rr['length_mm']-total
        if key=='fps' and 'wire_parts' in item:
            rr['assembly_reference_curve']=rr['curve']
            rr['wire_parts']=item['wire_parts'];rr['rigid_junction']=item['junction']
            rr['curve']=copy.deepcopy(item['lead_200']['curve'])
            rr['curve']['representation_note']='Display 200 mm main lead only. Full physical geometry is wire_parts plus rigid_junction; assembly_reference_curve is not flexible cable.'
            obs.append(dict(id='fps_inline_ph_junction',box=item['junction']['box']))
    rr=route_by_id['run_lead'];rr['cores']=signals['run_cores'];rr['curve']=copy.deepcopy(signals['run_cores'][0]['curve'])
    rr['curve']['representation_note']='Display first core only. Both independent 250 mm paths are authoritative in cores; no shared centerline.'
    rr['branched_installed_length_mm']=250;rr['slack_mm']=0;rr['status']='blocked-terminal-and-service-gates';rr['selected_source']='signal_routes.py:run_cores'
    branches=signals['branches']+[dict(id=c['id'],cable='run_lead',pins=c['pins'],od_mm=c['od_mm'],curve=c['curve'],status=c['status']) for c in signals['run_cores']]
    if selected_power:
        rr=route_by_id['pigtail'];rr['cores']=selected_power['cores'];cc=selected_power['cores'][0]
        rr['curve']=dict(sampled_centerline=cc['full_centerline_excluding_unmeasured_root_joint'],knots='Explicit local arcs plus full upper stored curve; see power_geometry',
                         rounded_length_mm=cc['modeled_length_mm']-cc['unmodeled_root_joint_allowance_mm'],raw_length_mm=None,centerline_radius_mm=8,first_straight_min_mm=8,last_straight_min_mm=4,
                         errors=['Actual solder-root transition is length-only; no geometric pad-joint or flexible-service qualification'],status='blocked-root-and-service-gates')
        rr['branched_installed_length_mm']=270;rr['slack_mm']=0;rr['status']='blocked-root-thermal-and-flexible-service-gates';rr['selected_source']='power_routes.py:cores'
        rr['stock_accounting_warning']='270 mm finished path per polarity is fully allocated, including the positive20mm fuse/joint zone. This does not prove270mm flexible copper plus a fuse fits. The unmeasured root allowance is not a geometric transition, deployable slack, or a free tolerance allowance.'
        # H1 (VN-26 routes): installed pack lead to the posed XT30 male face, selected compact scope only.
        if (length,stack_y,evf_shift_y,panel_shift_y)==(158,22.2,11,3):
            rr=route_by_id['pack_lead'];pc,stubs,sweep=pack_lead_route(selected_power)
            rr.update(curve=pc,stubs=stubs,sweep_points=sweep,branched_installed_length_mm=pc['rounded_length_mm'],
                      slack_mm=None if pc['rounded_length_mm'] is None else rr['length_mm']-pc['rounded_length_mm'],
                      status='blocked' if pc['errors'] else 'unqualified-path',selected_source='routes.py:pack_lead_route',
                      note='Existing 60 mm 18 AWG pack lead (D2-13): pack top +X end (MP-PACK) to the posed XT30 male face; the '
                           'two cores fan to the 5 mm contact pitch within PACK_MERGE_MM of the face (stubs). Rigid solder-tail '
                           'length and the BMS exit are MP-PACK.')
    # Separate stow reservations; spaces are proposed, not a fill-fraction waiver.
    # Signal lanes are above the Pi in negative Y, Z=72..76. Stow is above them.
    reservations=[
        dict(id='fpc_fold',cables=['fpc'],box=B(-118.5,-101.9,-23.2,-6.7,78.2,88.5),fill_max=.20,method='flat accordion, 1 mm inner-radius minimum only if cable maker permits'),
        dict(id='hdmi_stow',cables=['hdmi'],box=B(-128,-90,3,14,90.8,97),fill_max=.20,method='single-layer elongated loop; 6 mm centerline bend radius'),
        dict(id='usb_stow',cables=['usb_5v'],box=B(-128,-86,-24,0,88.5,96.5),fill_max=.20,method='proposed spare stow only: the cut-to-length EVF feed has its diode sleeve, option-C reserve and RCY pair placed on the installed usb_5v route (feed volumes); rear panel boss atX-133 excludes the earlier rear portion'),
        dict(id='controls_stow',cables=['qt','fps_lead'],box=B(-97.5,-73,11,24.7,64.7,94.3),fill_max=.20,method='separate tied loops; do not span the panel closure or encoder snap land'),
        dict(id='run_stow',cables=['run_lead'],box=B(-42,-30,-20,5,90,96),fill_max=.20,method='two-wire loop; outside camera/camera-catch'),
        dict(id='grip_stow',cables=['pigtail','pack_lead'],box=copy.deepcopy(L.KEEPOUTS['ko_xt30']),fill_max=.20,method='fold above XT30 pair and pack; fuse sleeve remains straight'),
    ]
    reservations.append(dict(id='oled_flex_stow',cables=['oled_flex'],box=B(-147+e,-137+e,evf_shift_y-7.5,evf_shift_y+7.5,94.3,96.5),fill_max=.20,method='single S fold above driver; must verify printed top-rail and roof clearance with full12.4mm ribbon width'))
    if power_button:reservations.append(dict(id='power_stow',cables=['power_button'],box=B(-28,-16,-20,-8,6,33),fill_max=.20,method='two-wire loop behind switch; charge removable PH pair separately; check against printed panel and terminal guard'))
    reservations=[q for q in reservations if q['id'] not in ('hdmi_stow','controls_stow','run_stow','grip_stow')]
    # QT/FPS/RUN/power material is explicit in selected modules. A legacy box
    # is not credited as an extra quantity of deployable cable.
    for res in reservations:
        hits=[]
        for o in obs:
            ib=obstacle_overlap(res['box'],o)
            if ib:hits.append(dict(obstacle=o['id'],overlap_box=ib,overlap_mm3=volume(ib)))
        res['obstacle_overlaps']=hits
        res['status']='blocked' if hits else 'unqualified-reservation'
        res['volume_mm3']=volume(res['box'])
        known=[r for r in routes if r['id'] in res['cables'] and r['slack_mm'] is not None]
        res['slack_demand_mm3']=sum(max(0,r['slack_mm'])*(16*.3 if r['id']=='fpc' else 12.4*.2 if r['id']=='oled_flex' else 10*.4 if r['id']=='hdmi' and hdmi_assembly.startswith('adafruit') else math.pi*(r['od_mm']/2)**2) for r in known)
        res['rigid_splice_demand_mm3']=600 if res['id']=='usb_stow' else (576 if res['id'] in ('controls_stow','power_stow') else 0)
        res['slack_demand_mm3']+=res['rigid_splice_demand_mm3']
        res['capacity_mm3']=res['volume_mm3']*res['fill_max']
        res['capacity_complete']=len(known)==len(res['cables'])
        if res['slack_demand_mm3']>res['capacity_mm3']:res['status']='blocked'
    for a,b in itertools.combinations(reservations,2):
        ib=overlap(a['box'],b['box'])
        if ib:
            for x,y in ((a,b),(b,a)):
                x.setdefault('other_reservation_overlaps',[]).append(y['id']);x['status']='blocked'
    path_reviews=[]
    for r in routes:
        samples=r['curve']['sampled_centerline']
        radius=r['od_mm']/2
        over=[];hits={}
        for i,(a,b) in enumerate(zip(samples,samples[1:])):
            sb={ax:[min(a[j],b[j])-radius,max(a[j],b[j])+radius] for j,ax in enumerate(AXES)}
            # Grip-crossing routes leave the body through existing holes; below
            # the floor they are checked against source grip contents instead.
            if sb['z'][1]>2.5:
                for ax,lo,hi in [('x',-length+2.5,-5.2),('y',right_inner,left_inner),('z',2.5,97.5)]:
                    if ax=='z' and sb['z'][0]<2.5:continue
                    if sb[ax][0]<lo-1e-7 or sb[ax][1]>hi+1e-7:
                        if ax not in over:over.append(ax)
            for o in obs:
                ib=obstacle_overlap(sb,o)
                if ib:
                    ent=hits.setdefault(o['id'],dict(obstacle=o['id'],sample_intervals=0,overlap_box=ib))
                    ent['sample_intervals']+=1;ent['overlap_box']=hull([ent['overlap_box'],ib])
        if over:r['status']='blocked'
        elif r['id']=='hdmi' and ribbon:r['status']='unqualified-developable-shape' if not ribbon['obstacle_overlaps'] and abs(ribbon['remaining_length_mm'])<1e-6 else 'blocked'
        path_reviews.append(dict(cable=r['id'],wall_overrun_axes=over,source_proxy_intersections=list(hits.values()),
                                sampling_step_mm=1,method='Conservative AABB of each sampled centerline segment plus cable radius; source COTS AABBs. No endpoint pair exclusions.',
                                ribbon_warning='Only thickness envelope checked; ribbon-width/orientation sweep remains open' if r['id'] in ('fpc','oled_flex') or (r['id']=='hdmi' and hdmi_assembly.startswith('adafruit')) else None,
                                status='blocked' if over or r['curve']['errors'] else 'exact CAD and local contact review required'))
    clashes=[]
    for a,b in itertools.combinations([p for p in plugs if p['rigid'] and p['box']],2):
        # Adjacent individual GPIO housing section tolerance is reported below;
        # two multi-housing hulls are not used to waive any overlap.
        aa=a.get('housing_boxes',[a['box']]);bb=b.get('housing_boxes',[b['box']])
        for x,y in itertools.product(aa,bb):
            ib=overlap(x,y)
            if ib:clashes.append(dict(a=a['id'],b=b['id'],overlap_box=ib,overlap_mm3=volume(ib)))
    internal_housing_hits=[]
    for a,b in itertools.combinations(hs,2):
        ib=overlap(a['box'],b['box'])
        if ib:internal_housing_hits.append(dict(a=a['id'],b=b['id'],overlap_box=ib,reason='Worst-case2.6mm housing width exceeds2.54mm header pitch. Source permits2.5mm minimum; actual section must be measured, never shrunk silently.'))
    walls=[]
    for p in plugs:
        if not p['box']:continue
        for axis,lo,hi in [('x',-length+2.5,-5.2),('y',right_inner,left_inner),('z',2.5,97.5)]:
            b=p['box'][axis]
            if b[0]<lo-1e-6 or b[1]>hi+1e-6:walls.append(dict(plug=p['id'],axis=axis,box=b,cavity=[lo,hi]))
    pig18=pigtail_study(stack_y)
    pig=pigtail_16_study(stack_y) if pigtail_awg==16 else pig18
    local_fpc=B(fpc1[0]-5,fpc1[0],-8.5,8.5,43.6,43.9)
    dog=next((o['box'] for o in obs if o['id']=='plunger_dogleg'),None)
    fpc_hit=overlap(local_fpc,dog) if dog else None
    header_tails=[dict(id=h['id'],wire_exit=h['wire_exit'],clear_to_inner_wall_mm=h['wire_exit'][1]-right_inner,
                      minimum_need_mm=3+3.2+.8,status='blocked' if h['wire_exit'][1]-right_inner<7 else 'unqualified') for h in hs]
    service=[
        dict(id='carrier_out',direction=[0,1,0],travel_mm=70,
             mandatory_first_precondition='STOP until the battery can be disconnected through the grip mouth with the final retained lead. Isolate battery before any body opening.',
             prerequisites=['disconnect XT30 through grip mouth BEFORE opening body','remove +Y panel','unplug rear USB storage along -X','disconnect HDMI, USB-5V, camera FPC and GPIO leads','disconnect XT30 below grip mouth','disconnect the power-button 2-pin junction','release pigtail strain relief only if it prevents the carrier lift'],
             sequence='Install camera first, then carrier. Pi/UPS/cooler/fan move together. No attached rigid cable may be swept through fixed hardware.',
             status='exact CAD sweep required'),
        dict(id='evf_hdmi_mate',plug='p_hdmi_evf',path_displacements=[[0,30,-12],[0,0,-12],[0,0,0]],
             plug_box=byid['p_hdmi_evf']['box'],head_box=byid['p_hdmi_evf']['head'],stroke_mm=6,
             sequence='Install OLED and driver board from +Y first; bring HDMI in below the bottom rail and push upward +Z.',
             status='blocked by plug/plug overlap in compact length where reported; verify entire swept head and finger corridor'),
        dict(id='panel_mate',panel_displacement=[0,60,0],hand_boxes_mm=dict(jst_sh=[30,20,24],ph_pair=[35,22,26]),
             cables=['qt','fps_lead'],status='STOP: the FPS PH junction is on the cooler/right side atY[-25,-19]. Stack blocks direct access from the open+Y side; the50mm pigtail cannot justify60mm panel travel. A full-material cable-supported housing lift/pullout and actual release tool corridor are not yet modeled',
             fps_access_prerequisite='After proven battery isolation, establish a supported PH junction access/service shape before translating the panel. No implicit panel-side disconnect or tugging on crimp wires is allowed.'),
        dict(id='usb_5v_mate',plug='p_usb_pi',direction=[1,0,0],unplug_stroke_mm=12,
             swept_box=hull([byid['p_usb_pi']['box'],tbox(byid['p_usb_pi']['box'],lambda p:trp(p,(-12,0,0)))]),
             status='rear approach and access opening must be cut or mating completed before carrier installation; no wall tunneling allowed'),
        dict(id='xt30_service',wire_end=[-51.2,-5.8,-125],hand_box=B(-66.2,-36.2,-20.8,9.2,-165,-125),
             status='STOP: rigid connector/fuse poses do not prove retained full-core deployment or safe isolation access',selected_cut_mm=270 if pigtail_awg==16 else 225,maximum_cut_mm=None,
             maximum_length_gate='G-W5 hot-load uncertainty controls the permitted wire length;270mm is provisional, not an electrical release'),
        dict(id='power_panel_disconnect',cable='power_button',junction='removable 2-pin inline connector, terminal sleeves and positive strain relief',
             estimated_junction_box=B(-35,-29,-15,-7,30,42),panel_service_displacement=[0,60,0],
             status='unmeasured J2 datum; connector choice, terminal guard and panel reach need verification'),
    ]
    return dict(revision=REVISION,length=length,width=left_inner-right_inner+5.3,height=100,stack_y=stack_y,evf_shift_y=evf_shift_y,power_button=power_button,hdmi_assembly=hdmi_assembly,pigtail_awg=pigtail_awg,upper_storage=upper_storage,units='mm',frame='X lensward, Y operator-left, Z up',
                status='BLOCKED / UNQUALIFIED source routing study; no inherited release gate is passed',
                hdmi_original_elbow_fallback=dict(head_outboard_y=stack_y-41,straight_tail_mm=6,centerline_bend_radius_mm=6,cable_radius_mm=1.5,required_inner_right_y=stack_y-41-13.5,extra_wall_mm=max(0,right_inner-(stack_y-41-13.5)),note='Conditional minimum using the explicitly outward elbow and the chosen bend/tail allowances. Add manufacturing clearance; vendor dimensions remain unmeasured.'),
                route_count=len(routes),plug_end_count=len(plugs),plugs=plugs,header_housings=hs,header_wire_branches=branches,routes=routes,
                obstacles=obs,slack_reservations=reservations,service_envelopes=service,hdmi_ribbon=ribbon,hdmi_ribbon_premate=ribbon_premate,hdmi_ribbon_unplugged=ribbon_unplugged,hdmi_200_rejected=dict(status='Rejected/fragile service study, retained in frozen0241 snapshot',reason='Both heads unplugged leaves only0.011286mm upper-loop legs, effectively zero length tolerance; do not claim serviceability',selected=False),power_geometry=selected_power,signal_geometry=signals,
                retired_xt30_local_exits=dict(selected=False,reason='Superseded by source-bound21degree-yaw power_geometry',study=xt30_exit_study()),
                retired_pigtail_inline_fuse=dict(selected=False,reason='Superseded by power_geometry fuse and local cores',study=inline_fuse_study()),pigtail=dict(selected_finished_path_allocation_mm=270,status='PROVISIONAL; positive includes20mm fuse/joint zone. Actual cut convention, root, retention, flexible service and G-W5 remain hard STOPs',electrical=selected_power['electrical'],geometry_key='power_geometry') if selected_power else pig,
                retired_pigtail_service_estimate=dict(selected=False,study=pig),baseline_18awg_pigtail=pig18,
                source_sha256={f:hashlib.sha256((Path(__file__).parent/f).read_bytes()).hexdigest() for f in ('routes.py','power_routes.py','signal_routes.py','hdmi_routes.py')},
                checks=dict(route_source_reviews=path_reviews,rigid_connector_collisions=clashes,rigid_connector_wall_overruns=walls,
                            gpio_straight_tail_checks=header_tails,header_housing_tolerance_overlaps=internal_housing_hits,camera_fpc_straight_tail=dict(box=local_fpc,plunger_overlap=fpc_hit,status='blocked' if fpc_hit else 'unqualified'),
                            collision_policy='No whole cable/part or whole part/part pair is exempted. COTS source AABBs are broad-phase evidence, not exact solid clearance. Endpoint contact must be reviewed locally in parent CAD.'),
                gates=['Actual connector metrology and wire exit directions','Cable-maker bend and straight-tail requirements','Exact CAD cable-sweep / printed-solid intersections',
                       'USB2 port and HDMI simultaneous fit','G-W2 actual X1203 pad position','G-W5 unchanged 8.6 A / 0.15 V drop limit','FPC and new power-button harness intersection check','GPIO individual-tail and bundle-merger qualification','Power-button drawing/listing dimensional discrepancy and actual Pi5 J2 pad datum','Slack packing and service reach',
                       'All inherited physical gates remain open; Samsung FIT Plus storage performance is not qualified'])


if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--length',type=float,default=158);ap.add_argument('--output',type=Path)
    a=ap.parse_args();result=build(a.length);data=json.dumps(result,indent=2)
    if a.output:write_text(a.output,data+'\n')
    else:print(data)

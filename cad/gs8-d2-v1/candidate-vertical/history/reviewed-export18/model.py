# SPDX-License-Identifier: MIT
"""D2 vertical-board review candidate. Millimetres; X lensward, Y operator-left, Z up.

A separate, non-release design. Baseline modules/data remain untouched on disk.
The Pi, UPS, cooler and supplied standoffs rotate as a rigid assembly. Purchased
parts are dimensioned proxies, not measurements. No physical gate is inherited.
"""
from pathlib import Path
import copy, json, math, sys
import cadquery as cq
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import layout as L
import cots, d2_common as dc, printed_grip, printed_small, printed_collar, printed_panel
import power_geometry as PG
import fps_geometry as FG
import structure_geometry as SG
import strap_route_proposal as SR
import fps_fixed_support as FS
import fps_pair_guide as FPG
import official_pi5_geometry as OP
sys.path.insert(0,str(Path(__file__).resolve().parent / "structural-review"))
import j4_trial_geometry as JG
# Relocate the independent base lock 2 mm toward the right wall, clear of rolled USB jacks.
L.J4_LOCK=copy.deepcopy(L.J4_LOCK);L.J4_LOCK["c"]=(L.J4_LOCK["c"][0],-22.0)
L.SCREWS=copy.deepcopy(L.SCREWS)
for _s in L.SCREWS:
    if _s["id"]=="s_j":
        for _k in ("head_point","tip"):_s[_k]=(_s[_k][0],_s[_k][1]-2,_s[_k][2])
L.FLOOR_HOLES=copy.deepcopy(L.FLOOR_HOLES)
L.FLOOR_HOLES["pigtail"]=L.B(-65.8,-55,-8,2,0,2.5)
L.BASE_OPENING=copy.deepcopy(L.BASE_OPENING);L.BASE_OPENING["x"]=(-65.8,-25.5)
V=cq.Vector
REV='D2-V1 vertical-board review, 2026-10-09'
STACK_DX=-28.0
PCB_Z_OFFSET=39.3
WIDTH=56.0
STACK_Y=22.2
EY=11.0
HEIGHT=100.0
PANEL_IN=25.2
OPTICAL_AXIS=(0.0,60.0)
CONTROL_Z=78.0
CONTROL_MOVES={'encoder':(8,-7,21),'switch_1824':(12,-7,23),
               'knob_exp':(8,-7,21),'knob_fps':(12,-5,23)}
# Upper rear + lower front carrier ears deliberately outside the PCB outline.
CARRIER_SCREWS=[(-127.0,69.0),(-25.0,9.0)]
PANEL_SCREWS=[(-120.5,48.0),(-125.0,91.7),(-10.8,8.3),(-10.8,91.7)]


def panel_screws(length):
    # Original59mm storage body is taller than compactSSD; separately checked boss height.
    return [(x-(length-150) if x < -100 else x, z+(3.0 if i==0 and length>170 else 0.0))
            for i,(x,z) in enumerate(PANEL_SCREWS)]


def box(x0,x1,y0,y1,z0,z1):
    return cq.Solid.makeBox(x1-x0,y1-y0,z1-z0,V(x0,y0,z0))

def cyl(axis,r,a,b,u,v):
    p={'x':(a,u,v),'y':(u,a,v),'z':(u,v,a)}[axis]
    d={'x':(1,0,0),'y':(0,1,0),'z':(0,0,1)}[axis]
    return cq.Solid.makeCylinder(r,b-a,V(*p),V(*d))

def fuse(parts):
    return parts[0].fuse(*parts[1:]).clean() if len(parts)>1 else parts[0]

def tr(s,t):return s.translate(V(*t))

def roll(s):return s.rotate((0,0,0),(1,0,0),90).translate(V(STACK_DX,STACK_Y,PCB_Z_OFFSET))

def rp(p):return (p[0]+STACK_DX,STACK_Y-p[2],p[1]+PCB_Z_OFFSET)

def bounds(s):
    b=s.BoundingBox();return [b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax]

def import_part(p):return cq.importers.importStep(str(ROOT/'out/step/parts'/f'{p}.step')).val()


def evf_support(length):
    """Positive OLED seat, two board edge grooves and in-situ HDMI opening.
    Display/spigot spacing is unchanged. Board slides from +Y; HDMI mates from -Z.
    """
    f=-length; xi=f+2.5; by=-25.55-EY
    adds=[];cuts=[]
    # Rear spigot seat, clearance radius 14.65. Panel supplies +Y clamp.
    adds.append(box(xi-.05,f+4.4,-16.5,0,61,95).cut(cyl('x',14.65,xi-.2,f+4.5,0,78)))
    adds.append(box(xi-.05,f+4.4,by,-16.4,63,93))
    # OLED emitter at F+6; recess with one mm foam behind; open to +Y.
    adds.extend([box(f+4.6,f+6,by,8,69.45,86.55),
                 box(f+4.6,f+9,by,8,69.45,71.05),
                 box(f+4.6,f+9,by,8,84.95,86.55),
                 box(f+4.6,f+9,-9.55,-7.95,69.45,86.55)])
    cuts.append(box(f+4.5,f+6.1,-5,5,74,82))
    # PCB plane F+15.6..17.2, 2.1 wide groove. 1.3 mm groove walls.
    xc=f+16.4; g=1.05; rx0=xc-g-1.3;rx1=xc+g+1.3
    adds.extend([box(rx0,rx1,by,12.5,61.5,65.25),box(rx0,rx1,by,12.5,91.25,94)])
    cuts.extend([box(xc-g,xc+g,-15.3,12.6,63.75,65.35),
                 box(xc-g,xc+g,-15.3,12.6,91.15,92.75),
                 box(rx0-.1,f+15.5,-14.65,3.65,61.4,65.35),
                 box(rx0-.1,xc-g+.01,-14.65,12.6,63.75,65.35),
                 box(f+17.19,f+17.8,-13,2,61.4,63.85),
                 box(rx0-.1,xc-g+.01,-10,5,91.15,91.65)])
    adds.append(box(rx1-.01,rx1+.65,-14.65,3.65,61.5,65.25))
    # Continuous PCB-only shelf stays behind the4mm straight adapter; no0.35mm orphan rail.
    adds.append(box(f+15.5,rx1+.65,by,12.5,61.5,63.75))
    return tr(fuse(adds).cut(*cuts).clean(),(0,EY,0))


def collar_print_stock(finished):
    """Fuse sacrificial membranes without same-domain cleanup.
    The pinned kernel's cleanup can corrupt the Fujinon stock boolean. Keep the
    valid uncleaned union, and verify no finished material is removed. Baseline
    disk geometry and all physical post-processing gates remain unchanged.
    """
    C=L.COLLAR;t=C['bridge_membrane_t'];seat=C['flange_x'][1]
    if not 0<t<=.3:raise ValueError('Invalid membrane thickness')
    sh=finished.copy()
    disks=[cyl('x',C['hole_d']/2+.1,seat-t,seat,*C['feet'][k]) for k in C['bolted']]
    stock=sh.fuse(*disks)
    added=stock.Volume()-finished.Volume();expected=len(disks)*math.pi*(C['hole_d']/2)**2*t
    if not stock.isValid() or len(stock.Solids())!=1 or abs(added-expected)>.02:raise ValueError('Invalid collar print union')
    lost=finished.copy().cut(stock.copy()).Volume()
    if lost>.001:raise ValueError('Membrane union removed finished material')
    return dict(shape=stock,added_volume_mm3=added,membrane_count=len(disks),membrane_thickness_mm=t,
                cleared_hole_d_mm=C['hole_d'],postprocess='Clear three3.4mm anchor holes by hand; remove all debris without altering washer seats, cone or foot datums. G-COL-1 remains open.',
                assembled_geometry='Finished cleared geometry only in STEP/assembly checks',kernel_check=dict(finished_loss_mm3=lost,cleanup_used=False))


def candidate_strap_layout():
    st=copy.deepcopy(L.STRAP)
    for b in st['upper_slots']+[st['upper_recess']]:
        b['x']=tuple(v-18.5 for v in b['x']);b['y']=tuple(v+12 for v in b['y'])
    rear=min(st['upper_slots'],key=lambda b:sum(b['x']))
    rear['x']=tuple(v-2 for v in rear['x'])
    st['upper_recess']['x']=(st['upper_recess']['x'][0]-2,st['upper_recess']['x'][1])
    return st


def load_corrected_pi():
    import hashlib,json
    folder=Path(__file__).resolve().parent/'out/source-components'
    meta=json.loads((folder/'pi5-corrected.json').read_text())
    for relative,expected in meta['sources'].items():
        if hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()!=expected:
            raise ValueError('Corrected Pi source changed; rerun make_corrected_pi.py: '+relative)
    step=folder/meta['file']
    if hashlib.sha256(step.read_bytes()).hexdigest()!=meta['sha256']:raise ValueError('Corrected Pi STEP changed')
    shape=cq.importers.importStep(str(step)).val()
    if not shape.isValid() or abs(shape.Volume()-meta['raw_solid_volume_sum_mm3'])>.02:raise ValueError('Corrected Pi cache invalid')
    return shape

def make_cooler_proxy():
    # The source drawing omits perimeter/fan-to-pin offsets. Retain the illustrative
    # heatsink/blower only; remove the four fictitious feet. Two plain markers show
    # true board-hole axes, not measured push-pin/head/spring geometry.
    c=L.COTS['cooler'];b=c['box'];x0,x1=b['x'];y0,y1=b['y'];fb=c['features']['blower']
    plate=box(x0,x1,y0,y1,21.6,23.4)
    fins=[box(fb['x'][1],x1,y,y+1,23.4,30.5) for y in [y0+1+2.5*i for i in range(int((y1-y0-2)/2.5))]]
    blower=box(fb['x'][0],fb['x'][1],fb['y'][0],fb['y'][1],23.4,b['z'][1])
    blower=blower.cut(cyl('z',9,b['z'][1]-.6,b['z'][1],sum(fb['x'])/2,sum(fb['y'])/2))
    body=roll(fuse([plate,blower]+fins))
    pins=[cyl('y',1.45,-.5,4.5,*r['candidate_xz']) for r in OP.cooler_mount_axes()]
    return body.fuse(*pins)


def make_carrier():
    """Open perimeter carrier; four lower kit screws replaced with M2.5x8.
    Four 4.0 mm bosses sit against the UPS underside. A1mm head recess leaves
    3.0mm under the screw seat:8-3-1.6=3.4mm nominal engagement, gated by real standoff depth.
    No cooler removal, PCB-edge clip, spring keeper or pogo interface alteration.
    """
    holes=[rp((x,y,6)) for x,y in L.PI['holes']]
    # Central opening does not trap the UPS components or underside cable exits.
    s=box(-96.5,-29,14,17,4,64.0).cut(box(-86,-39,13,18,16,54))
    # Extend the frame to the two mounting ears and connect to existing top/bottom rails.
    # Diagonal rear arm clears the carried upper USB2 power head and FPS body.
    ax,az,bx,bz=-127.,69.,-93.,53.
    norm=math.hypot(bx-ax,bz-az);nx=-(bz-az)/norm*2;nz=(bx-ax)/norm*2
    pts=[(ax+nx,az+nz),(bx+nx,bz+nz),(bx-nx,bz-nz),(ax-nx,az-nz)]
    wire=cq.Wire.makePolygon([V(x,14,z) for x,z in pts]+[V(pts[0][0],14,pts[0][1])])
    arm=cq.Solid.extrudeLinear(wire,[],V(0,3,0))
    s=s.fuse(arm,box(-34,-25,14,17,5,13))
    for x,_,z in holes:
        s=s.fuse(cyl('y',4.5,13,17,x,z))
    for x,z in CARRIER_SCREWS:
        s=s.fuse(cyl('y',4.8,14,17,x,z))
    for x,_,z in holes:
        s=s.cut(cyl('y',1.4,12.9,17.1,x,z),cyl('y',2.65,16,17.1,x,z))
    for x,z in CARRIER_SCREWS:s=s.cut(cyl('y',1.7,13.9,17.1,x,z),cyl('y',3.2,16.6,17.1,x,z))
    for x,z in [(-92,25),(-92,45),(-34,25),(-34,45)]:
        s=s.cut(box(x-1.5,x+1.5,13.9,17.1,z-.5,z+.5))
    return SG.reinforce_carrier(tr(s.clean(),(0,3.2,0)))


def collar_setup():
    """Keep optical seating/cone datums, reduce non-optical exterior and ear span.
    Changed clamp stiffness invalidates earlier spring/thermal estimates (M1 open).
    """
    L.COLLAR=copy.deepcopy(L.COLLAR)
    L.COLLAR['body_r']=25.0
    L.COLLAR['feet']['LL']=(18.0,30.0)
    L.COLLAR['lug'].update(y_out=-30.0,screw_y=-26.3,bit_relief_y=-22.8)
    L.SCREWS=copy.deepcopy(L.SCREWS)
    for s in L.SCREWS:
        if s['id']=='s_c3':
            s['head_point']=(s['head_point'][0],18,30);s['tip']=(s['tip'][0],18,30)
        if s['id']=='s_c4':
            s['head_point']=(s['head_point'][0],-26.3,s['head_point'][2]);s['tip']=(s['tip'][0],-26.3,s['tip'][2])


def make_tub(length):
    # Small vertical edge radii: broad flat sides and deliberate single 0.3 mm seam.
    outer=(cq.Workplane('XY').box(length,56,100,centered=False).translate((-length,-28,0))
           .edges('|Z').fillet(2).val())
    cavity=box(-length+2.5,-5.2,-25.5,29,2.5,97.5)
    s=outer.cut(cavity)
    adds=[];cuts=[]
    # Panel pocket: 2.8 mm face plate sits within the silhouette, 0.3 seam at perimeter.
    cuts.append(box(-length+2.8,-2.8,25.2,28.1,2.8,97.2))
    # Preserve existing grip keyhole interface and independently locking PT fastener.
    for t in L.TONGUES:adds.append(dc.keyhole_tongue(t,chamfer_minus_y=False))
    j=L.J4_LOCK;x,z=j['c'][0],0
    adds.append(cyl('z',j['od']/2,2.4,j['top'],x,j['c'][1]))
    cuts.append(cyl('z',1.25,-.1,13,x,j['c'][1]))
    for b in L.FLOOR_HOLES.values():cuts.append(dc.box_solid(dict(b,z=(-.1,2.6))))
    # Camera floating rear catch remains on removable panel; front datum and counterbore unchanged.
    cuts.extend([cyl('x',16.2,-3.9,-2.69,0,60),cyl('x',18.75,-5.3,-3.9,0,60),
                 cyl('x',18.25,-2.7,.1,0,60)])
    for k,(y,z) in L.COLLAR['feet'].items():
        # A recess leaves a genuine bearing seat at X=-2.7; no floating decorative foot.
        cuts.append(cyl('x',4.3,-2.7,.1,y,z))
        if k in L.COLLAR['bolted']:
            adds.append(cyl('x',4,-7.6,-5.1,y,z))
            cuts.extend([cyl('x',2,-7,-2.7,y,z),cyl('x',1.7,-7.7,-6.9,y,z)])
    # Original two-tine metal lock-tab torque catch, now grown from integral roof.
    for b in L.tab_catch_boxes():
        b=dict(b);b['z']=(b['z'][0],98.0);adds.append(dc.box_solid(b))
    # Real vertical-PCB carrier mounting bosses, facing the open left side.
    for x,z in CARRIER_SCREWS:
        adds.append(cyl('y',4.8,-25.55,17.2,x,z))
        cuts.append(cyl('y',1.25,7.2,17.3,x,z))
    # Four panel fasteners, all same PH1 drive and accessible from one side.
    ps=panel_screws(length)
    for x,z in ps:
        adds.append(cyl('y',4.5,-25.55,23.5,x,z))
        cuts.append(cyl('y',1.25,13.1,23.6,x,z))
    # Same rear panel screw relocated above the corrected USB2 head. Integral
    # tapered root and a compression-only landing retain corner support; peel is gated.
    px,pz=panel_screws(length)[0]
    adds.append(cq.Solid.makeCone(6.5,4.5,2.05,V(px,-25.55,pz),V(0,1,0)))
    adds.append(box(-length+6,-length+11,21.5,24.9,2.4,5.5))
    # EVF support and genuine bore, wholly separate from Pi/cooler region.
    adds.append(evf_support(length))
    cuts.append(cyl('x',14.65,-length-.1,-length+4.6,EY,78))
    # Rear storage finger recess; preserves straight removal along -X.
    cuts.append(box(-length-.1,-length+14,-23,3,20,48))
    # Side intake directly opposite blower; five 3 mm slots and solid edge webs.
    for z in (18,24,30,36):cuts.append(box(-103,-68,-28.1,-25.4,z,z+3))
    # Functional CSI latch/service slot. No loose cover or extra control.
    # Direct cooler-side tool access avoids the blocked over-PCB path; real latch/jaws gated.
    cuts.append(cq.Workplane(obj=box(-89,-77,-28.1,-25.4,41,68)).edges('|Y').fillet(1).val())
    adds.extend([FS.shelf(),FPG.build()])
    # Isolated forward exhaust, below optical bay; vertical ribs prevent broadside weakening.
    for z in (15,21,27,33):cuts.append(box(-40,-32,-28.1,-25.4,z,z+3))
    # Front exhaust below the optical bay; solid microSD guide strip and collar-seat lands retained.
    for z in (8,14,20,26,32):
        for ya,yb in ((-23,1),(8,11.5)):
            cuts.append(box(-5.3,.1,ya,yb,z,z+3))
    # Baffle ending clear of cooler fins, dividing exhaust from inlet recirculation path.
    adds.append(box(-65,-62,-25.55,-15.3,10,52))
    # Compact UPS heat relief in the panel is separate; no battery ventilation through live terminals.
    # microSD extracts +X through a real straight vertical front slit below the camera.
    cuts.append(box(-5.3,.1,3.8,5.8,27.8,39.8))
    # Wired J2 signal switch replaces the long mechanical linkage and its FPC conflict.
    # Ø16 panel mounting hole; body behind the lower-front bay, no battery current.

    s=s.fuse(*adds).cut(*cuts).clean()
    return PG.cut_passages(s, PG.tub_cuts())


def make_panel(length):
    ey=EY-3.0
    s=box(-length+3.1,-3.1,22.2,25,3.1,96.9)
    adds=[];cuts=[]
    ps=panel_screws(length)
    for x,z in ps:
        adds.append(cyl('y',5.2,20.5,25,x,z))
        cuts.append(cyl('y',1.7,20.4,25.1,x,z))
        cuts.append(cyl('y',3.5,22.6,25.1,x,z))
    # Original verified encoder cradle, repositioned without changing its coupon geometry.
    adds.extend(tr(a,(CONTROL_MOVES['encoder'][0],CONTROL_MOVES['encoder'][1]-3,CONTROL_MOVES['encoder'][2])) for a in printed_panel._cradle(L))
    # Camera cover catch: 0.5 behind maximum cover, while carrier is behind -34.
    adds.append(box(-30.67,-27.34,1,22.6,66,76))
    # EVF clamp/flex pad and positive PCB edge stop, mechanically rooted to the panel.
    f=-length
    clamp=box(f+2.6,f+5.8,8+ey,22.6,63,93).cut(cyl('x',14.4,f+2.5,f+6,ey,78))
    adds.extend([clamp,box(f+6,f+9.2,8.3+ey,22.6,69.5,86.5),
                 box(f+15.1,f+17.7,12.3+ey,22.6,70,86)])
    # The pad stops the OLED gently; foam remains an explicit purchased consumable.
    adds.append(box(f+8.93,f+10.53,-7.8+ey,22.6,71.2,84.8))
    cuts.append(cyl('x',14.4,f-.1,f+4.6,ey,78))
    # Upper/lower register lands make the seam locate without extra loose parts.
    adds.extend([box(-length+12,-20,20.5,22.6,3.1,5.1),box(-length+25,-20,20.5,22.6,94.9,96.9)])
    for cid,r in [('encoder',3.75),('switch_1824',5)]:
        old=L.ENCODER if cid=='encoder' else L.SWITCH_1824
        dx,dy,dz=CONTROL_MOVES[cid];x,z=old['c'][0]+dx,old['c'][1]+dz
        cuts.append(cyl('y',r,22.1,25.1,x,z))
    # Replacement power control, same user function through Pi5 J2 (signal only).
    # Side-panel mounting clears the optical/FPC bay; rear dimensions remain conservative.
    cuts.append(cyl('y',8.1,22.1,25.1,-20,25.5))
    # Switch anti-rotation keyed slot, real user-facing two-position control.
    cuts.append(cyl('y',1.7,22.1,25.1,FG.X,FG.Z-9.5))
    for x in (-88,-80,-72,-64):cuts.append(box(x,x+3,22.4,25.1,20,45))
    items=[]
    for old in L.ENGRAVE['items']:
        if old['id']=='badge' or old['id'].startswith('fps'):continue
        it=copy.deepcopy(old)
        for key in ('c','at'):
            if key in it:it[key]=(it[key][0]+8,it[key][1]+21)
        items.append(it)
    items.append(dict(id='fps_ticks',kind='ticks',c=(FG.X,FG.Z),r=(12.4,13.2),deg=[-15.,15.],stroke=.8))
    for value,angle in [('18',-15.),('24',15.)]:
        items.append(dict(id='fps_'+value,kind='text',at=L.pol((FG.X,FG.Z),15.5,angle),text=value,h=2.6))
    items.append(dict(id='power_label',kind='text',at=(-20,40),text='power',h=2.8))
    cuts+=dc.engrave(items,face_y=25)
    return tr(s.fuse(*adds).cut(*cuts).clean(),(0,3,0))


def make_kit():
    # Build the original four standoffs and upper screws, remove lower screw heads/shanks
    # and install four long screws through carrier. Their quantities replace, not add to kit.
    raw=cots.x1203_kit(L,L.COTS['x1203_kit'])
    raw=raw.intersect(box(-100,0,-40,30,7.6,30))
    out=roll(raw)
    for x,y in L.PI['holes']:
        xx,_,zz=rp((x,y,6))
        out=out.fuse(cyl('y',2.5,19.2,21.6,xx,zz),cyl('y',1.2,11.2,19.2,xx,zz))
    return out


def pt_screw(x,z,seat):
    """ISO-style PH1 recess is a simplified physical proxy, not a machining drawing."""
    s=cyl('y',3,seat,seat+2.4,x,z).fuse(cyl('y',1.5,seat-12,seat,x,z))
    return s.cut(box(x-1.8,x+1.8,seat+1.8,seat+2.5,z-.45,z+.45),
                 box(x-.45,x+.45,seat+1.8,seat+2.5,z-1.8,z+1.8))


def _build(storage='compact',lens='kowa_lm6hc'):
    if storage not in ('compact','original'):raise ValueError(storage)
    length=158.0 if storage=='compact' else 185.0
    L.LENS=lens
    original=cots.build_all(L)
    rows={}
    for k,r in original.items():
        if r.get('shape') is None or k.startswith('s_'):continue
        s=r['shape'].val(); mass=r['mass']
        if k=='pi5':
            s=load_corrected_pi()
            r=dict(r,src='Four-hole-registered official Pi5 named component assembly; overlaps retained explicitly to preserve every USB/GPIO/CSI contact, six-hole1.6mm kit-datum PCB and underside/SoC/button proxies. HDMI shell envelopes; source/received thickness and adapter mating remain gates. '+OP.C.SOURCE_URL)
        elif k=='usb_stick':
            body_native=dc.safe_chamfer(cq.Workplane().add(dc.box_solid(L.STICK['body'])),'|X',1.0).val()
            s=tr(roll(tr(body_native,(0,0,7.7))),(0,OP.STORAGE_DY,OP.STORAGE_DZ))
        elif k=='cooler':
            s=make_cooler_proxy();r=dict(r,src='ILLUSTRATIVE inherited cooler perimeter/fan; two approximate alignment pins on source-verified board axes replace four fictitious feet. Exact CSI/proxy overlaps remain unresolved. Real fan/perimeter/pin profile and thermal qualification required.')
        elif k in ('x1203','microsd'):s=roll(s)
        elif k=='x1203_kit':s=make_kit();mass=6.8
        elif k in ('eyepiece','hmx039','evf_board','foam_pad'):s=tr(s,(154-length,EY-16,0))
        elif k in CONTROL_MOVES:s=tr(s,CONTROL_MOVES[k])
        elif k=='xt30_pair':
            # Keep the actual connector proxy, remove its old side-mounted fuse once.
            pair=max(s.Solids(),key=lambda q:q.Volume())
            pair=PG.pose(pair,PG.DATA['rigid_service_poses'][0])
            fs=PG.DATA['fuse'];s=pair.fuse(PG.cylinder(fs['start'],fs['end'],2.5))
            r=dict(r,src='XT30 pair and ONE inline15A fuse; frozen21deg yaw/45deg pitch pose,270mm16AWG provisional pigtail. Legacy12g lump includes estimated pigtail mass; its distributed mass is not resolved. Actual pins/pads, flexible service, hot drop and strength gates remain open.')
        elif k=='strap':
            st=copy.deepcopy(L.STRAP)
            try:
                L.STRAP=candidate_strap_layout()
                s=SR.build(tr(cots.strap(L,r),(0,12,0)))
            finally:L.STRAP=st
        if k=='usb_stick' and storage=='compact':
            # Full official overall dimension outside the receptacle plane (conservative).
            # No assumed plug-length subtraction. Actual housing profile/port reach is G-V-STORAGE.
            s=tr(box(-156,-122,-13.4,-6.4,26.5,41.5),(0,OP.STORAGE_DY,OP.STORAGE_DZ))
            mass=5.0;r=dict(r,src='Princeton PHD-USSD-500G; official34×15×7mm including cap, conservatively all34mm outside port plus separate estimated plug; remove/bag cap. Up-to500MB/s write is not warm sustained proof. Linux/identity/fit/power/G-W10 open. https://www.princeton.co.jp/product/storage/phdussd.html')
        rows[k]=dict(shape=s,kind='cots',mass=mass,source=r['src'])
    reserve=tr(roll(tr(dc.box_solid(L.STICK['plug']),(0,0,7.7))),(0,OP.STORAGE_DY,OP.STORAGE_DZ))
    rows['usb_storage_plug_reserve']=dict(shape=reserve,kind='keepout',mass=0,source='NON-MATERIAL estimated USB-A plug envelope. Not an installed part or occupied material. Actual plug shell/contact geometry, engagement and insertion remain OPEN; export16 full-solid conflict preserved. No source contacts removed.')
    # Corrected real SKU. Original12g total estimate is retained, not double counted.
    fps_parts=FG.switch_parts()
    for key,mass in [('switch_1824',9.7),('fps_nut',2.0),('fps_mounting_washer',.3)]:
        rows[key]=dict(shape=fps_parts[key],kind='cots' if key=='switch_1824' else 'hardware',mass=mass,
                       source='Lorlin CK1044 source envelope;13 hole-derived pin reserves; nut/washer dimensions and12g assembly mass remain estimates. '+FG.SOURCE)
    # Source-driven existing grip/cap/cup; corrected source-based FPS knob.

    oldstrap=copy.deepcopy(L.STRAP); oldbase=copy.deepcopy(L.BASE); oldscrews=copy.deepcopy(L.SCREWS)
    try:
        L.STRAP=candidate_strap_layout()
        L.BASE=copy.deepcopy(L.BASE);L.BASE['y']=(-25.2,25.2)
        L.SCREWS=[s for s in L.SCREWS if s['id'] not in ('s_b1','s_b2')]
        grip=SG.reinforce_grip(PG.cut_passages(printed_grip.build_part(L,'base_grip').val(), PG.grip_cuts()))
        grip=PG.cut_passages(grip.fuse(JG.entry_floor_stock()).clean(),PG.grip_cuts())
    finally:L.STRAP,L.BASE,L.SCREWS=oldstrap,oldbase,oldscrews
    printed={'base_grip':grip,'cap':printed_grip.build_part(L,'cap').val(),
             'eyecup':tr(printed_small.build_part(L,'eyecup').val(),(154-length,EY-16,0)),
             'knob_exp':tr(printed_small.build_part(L,'knob_exp').val(),CONTROL_MOVES['knob_exp']),
             'knob_fps':FG.knob(),
             'carrier':make_carrier()}
    if storage=='original':printed['stick_sleeve']=tr(roll(tr(printed_small.build_part(L,'stick_sleeve').val(),(0,0,7.7))),(0,OP.STORAGE_DY,OP.STORAGE_DZ))
    oldc,olds=copy.deepcopy(L.COLLAR),copy.deepcopy(L.SCREWS)
    try:
        collar_setup()
        printed.update(tub=make_tub(length),panel=make_panel(length),lens_collar=printed_collar.build_part(L).val())
        for s in L.SCREWS:
            if s['id'].startswith('s_c'):
                rows[s['id']]=dict(shape=cots.screw(L,s),kind='hardware',mass=L.screw_mass(s),source=s['spec'])
        stock=collar_print_stock(printed['lens_collar'])
        gauge=printed_collar.centring_gauge(L).val()
    finally:L.COLLAR,L.SCREWS=oldc,olds
    for k,s in printed.items():
        factor=.6 if k=='base_grip' else (.85 if k in ('tub','panel') else 1)
        rows[k]=dict(shape=s,kind='printed',mass=s.Volume()*(.00121 if k=='eyecup' else .00107)*factor,source='candidate-vertical/model.py + baseline sources')
    rows['power_button']=dict(shape=cyl('y',8,-1.4,28,-20,25.5).fuse(cyl('y',9.03,28,33,-20,25.5)),kind='cots',mass=4.6,source='Adafruit1505 normally-open momentary black signal switch; vendor max18.06×18×29.4mm conflicts with drawing24.8mm; reserve full29.4mm behind flange plus5mm button; panel thread and profile measured gate open')
    rows['power_nut_reserve']=dict(shape=cyl('y',11,22.2,25.2,-20,25.5).cut(cyl('y',8.1,22.1,25.3,-20,25.5)),kind='hardware',mass=.8,source='UNVERIFIED nut reserve: OD22×3; vendor drawing omits nut dimensions; fit gate required')
    # Seven PH1 PT screws: four sidepanel, two carrier, one existing independent base lock.
    for i,(x,z) in enumerate(panel_screws(length)):
        rows[f'p_panel{i+1}']=dict(shape=pt_screw(x,z,25.6),kind='hardware',mass=.8,source='PT 3x12 PH1')
    for i,(x,z) in enumerate(CARRIER_SCREWS):
        rows[f'p_carrier{i+1}']=dict(shape=pt_screw(x,z,19.8),kind='hardware',mass=.8,source='PT 3x12 PH1')
    sj=next(s for s in L.SCREWS if s['id']=='s_j')
    rows['p_grip']=dict(shape=cots.screw(L,sj),kind='hardware',mass=.8,source='PT 3x12 PH1')
    return dict(revision=REV,storage=storage,lens=lens,length=length,width=WIDTH,height=HEIGHT,rows=rows,
                collar_print_stock=stock,gauge=gauge,fps_geometry=FG.provenance(),pi_source_geometry=OP.provenance(),
                physical_state='UNQUALIFIED REVIEW CANDIDATE; all 56 inherited physical gates and M1 remain open')


def build(storage='compact',lens='kowa_lm6hc'):
    # Coordinated2.4mm lips and heads;0.25mm mating gaps and independent lock retained.
    with JG.trial_layout(L,lip=2.4,head=2.4):
        return _build(storage,lens)

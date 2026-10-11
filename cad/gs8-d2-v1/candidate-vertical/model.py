# SPDX-License-Identifier: MIT
"""D2 vertical-board review candidate. Millimetres; X lensward, Y operator-left, Z up.

A separate, non-release design. Baseline modules/data remain untouched on disk.
The Pi, UPS, cooler and supplied standoffs rotate as a rigid assembly. Purchased
parts are dimensioned proxies, not measurements. No physical gate is inherited.
"""
from cv_io import read_text
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
import vent_geometry as VG
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
REV='D2-V1 vertical-board shadow-plenum candidate, 2026-10-09'
STACK_DX=-28.0
PCB_Z_OFFSET=39.3
WIDTH=28.0-VG.OUTER_Y
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
# FP-11c (VN-54, VN-56): the carrier prints +Y face down on one continuous bed face at y 22.2 (the old arm face);
# PT counterbores 7.0 mm in 5.2 mm ear bosses (structure_geometry: r7 panel values, r7 bit 6.5).
CARRIER_BED_Y=STACK_Y
CARRIER_CBORE_R=SG.CARRIER_CBORE_R
CARRIER_EAR_R=SG.CARRIER_EAR_R
# FP-11c (VN-38): third printed locating feature, no new screw. The carrier bottom-rail tongue (x -86..-74) lands
# on a tub floor seat rib (its -Y bearing, top z 6.5 under the X1203 at z 7.0) and sits 0.15 mm under a panel stop
# pad (its +Y stop; r7 HOOD_STACK_STOP gap 0.15, window 0.1-0.3). verify_check_scope credits it from the STEPs only.
LOCATOR_X=-80.0
LOCATOR_SEAT_TOP=6.5
LOCATOR_STOP_GAP=0.15
POWER_NUT_AXIS_XZ=(-20.0,25.5)
POWER_NUT_RESERVE_R=11.0   # _build power_nut_reserve row (OD 22 x 3)
CARRIER_LOCATORS=[dict(id='bottom_rail_tongue',at=(LOCATOR_X,(4.0+LOCATOR_SEAT_TOP)/2),
                       tongue_box=(LOCATOR_X-6,LOCATOR_X+6,17.2,CARRIER_BED_Y,4.0,9.0),
                       seat_box=(LOCATOR_X-6.5,LOCATOR_X+6.5,10.0,17.2,2.0,LOCATOR_SEAT_TOP+.5),seat_part='tub',
                       stop_box=(LOCATOR_X-6.5,LOCATOR_X+6.5,CARRIER_BED_Y,25.4,3.0,9.5),stop_part='panel')]
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


# T2 (review 2026-10-10: VN-34, VN-53 -Y tine, VN-25 tub print minors). Every addition below is self-supporting in
# the tub print pose (-Y face down): its underside rises at TUB_PRINT_SLOPE_DEG from the bed plane, steeper than r7's
# 45 deg allowance (layout.PRINT_OVERHANG overhang_deg), so no paint-on support is needed.
TUB_PRINT_SLOPE_DEG=50.0
EVF_HDMI_RECEPTACLE_Y=(4.0,17.0)   # r7 checks._evf_board_zones 'hdmi receptacle' y in the r7 board frame (cots hdmi 'y 4..17')


def _hull_top_y(poly,x):
    """Largest y where the vertical line at x meets the closed polygon poly [(x, y)], or None."""
    ys=[]
    for (x0,y0),(x1,y1) in zip(poly,poly[1:]+poly[:1]):
        if x0!=x1 and (x0-x)*(x1-x)<=0:ys.append(y0+(x-x0)*(y1-y0)/(x1-x0))
    return max(ys) if ys else None


def tub_print_fixes(length):
    """T2 tub geometry, assembly frame. -> (adds, cuts) for make_tub.
    (1) -Y tab-catch tine (VN-53, outer faces only): its catch face (y = -y_in, facing +Y) faces UP in print and is
        not touched. The flange grows from the -Y wall instead of hanging at y -20.28, and the web's outer face
        (y -11.28) gets a fill whose underside rises from the flange at TUB_PRINT_SLOPE_DEG; both run to the catch top,
        merging with the panel-screw boss column and the roof. Nothing on the camera side of the tine changes.
    (2) LL collar insert boss (r7 declared a paint-on 'll_insert_boss_chin' for the same boss): a coaxial cone under
        the boss axis (lower half only) whose underside rises from the front wall at the print slope; the boss, its
        insert bore and screw-tip relief are unchanged (cut afterwards in make_tub).
    (3) rear panel-screw compression landing: a wedge under its -Y face from the floor (the landing face is unchanged).
    (4) floor: the tooth where the pigtail hole meets the power floor hull is cut back so the hole roof rises from the
        hull's highest point at the print slope to the pigtail hole edge (the hole only grows; no feature moves).
    (5) FPS pair guide: a lofted corbel under its -Y face that narrows at the print slope onto the connector-rest arm
        (x -136..-133, z 76.3..78.05; fps_fixed_support.connector_rest); the wire slit stays open.
    (6) VN-34: a local relief in the EVF PCB shelf under the HDMI receptacle zone, from the board's -X face to the PCB
        face + the PCB's groove clearance (g - 0.8 = 0.25), so the PCB edge, not the receptacle, takes the -Z stop
        even with the board pushed +X in its groove (check_evf_restraint connector rule, unchanged)."""
    run=1/math.tan(math.radians(TUB_PRINT_SLOPE_DEG))     # horizontal run per mm of rise
    rise=math.tan(math.radians(TUB_PRINT_SLOPE_DEG))
    f=-length;adds=[];cuts=[]
    # (1) -Y tine
    tc={b['kind']:b for b in L.tab_catch_boxes() if b['side']==-1}
    web,fl=tc['web'],tc['flange'];z0,zt=web['z'][0],98.0
    adds.append(box(fl['x'][0],fl['x'][1],-25.55,fl['y'][0]+.01,z0,zt))
    wy=fl['y'][0]+(web['x'][1]-fl['x'][1])*rise
    pts=[(fl['x'][1]-.01,fl['y'][0]),(web['x'][1],wy),(web['x'][1],web['y'][0]+.01),(fl['x'][1]-.01,web['y'][0]+.01)]
    w=cq.Wire.makePolygon([V(x,y,z0) for x,y in pts]+[V(pts[0][0],pts[0][1],z0)])
    adds.append(cq.Solid.extrudeLinear(w,[],V(0,0,zt-z0)))
    # (2) LL collar insert boss cone (lower half)
    if 'LL' in L.COLLAR['bolted']:
        y,z=L.COLLAR['feet']['LL'];r0=4.0;r1=r0+2.5*rise
        cone=cq.Solid.makeCone(r1,r0,2.5,V(-5.1,y,z),V(-1,0,0))
        adds.append(cone.intersect(box(-7.6,-5.1,y-r1-.1,y,z-r1-.1,z+r1+.1)))
    # (3) rear panel-screw landing wedge (landing box: x f+6..f+11, y 21.5..24.9, z 2.4..5.5)
    lz0,lz1,ly=2.5,5.5,21.5
    pts=[(ly-(lz1-lz0)*rise,lz0),(ly-(lz1-lz0)*rise,lz0-.1),(ly+.01,lz0-.1),(ly+.01,lz1),(ly,lz1)]
    w=cq.Wire.makePolygon([V(f+6,y,z) for y,z in pts]+[V(f+6,pts[0][0],pts[0][1])])
    adds.append(cq.Solid.extrudeLinear(w,[],V(5,0,0)))
    # (4) floor tooth between the pigtail hole and the power floor hull
    pig=L.FLOOR_HOLES['pigtail'];hull=list(PG.floor_hull())
    xs=[pig['x'][1]+.05*i for i in range(1,161)]
    top=[(x,_hull_top_y(hull,x)) for x in xs]
    top=[(x,y) for x,y in top if y is not None and y<pig['y'][1]]
    if top:
        xp,yp=max(top,key=lambda t:t[1])
        yl=yp+(xp-pig['x'][1])*rise
        if yl<pig['y'][1] and xp>pig['x'][1]:
            pts=[(xp,yp-.02),(pig['x'][1],yl),(pig['x'][1]-.1,yl),(pig['x'][1]-.1,yp-.6),(xp,yp-.6)]
            w=cq.Wire.makePolygon([V(x,y,-.1) for x,y in pts]+[V(pts[0][0],pts[0][1],-.1)])
            cuts.append(cq.Solid.extrudeLinear(w,[],V(0,0,2.7)))
    # (5) FPS pair guide corbel (guide footprint x -137.625..-129.375, z 76.3..83.35 at y 6; fps_pair_guide.build)
    gx0,gx1,gz0,gz1,gy=-137.625,-129.375,76.3,83.35,6.0
    ax0,ax1,az1=-136.0,-133.0,78.05
    depth=max(gz1-az1,gx1-ax1,ax0-gx0)*rise
    bot=[V(ax0,gy-depth,gz0),V(ax1,gy-depth,gz0),V(ax1,gy-depth,az1),V(ax0,gy-depth,az1)]
    tp=[V(gx0,gy+.01,gz0),V(gx1,gy+.01,gz0),V(gx1,gy+.01,gz1),V(gx0,gy+.01,gz1)]
    corbel=cq.Solid.makeLoft([cq.Wire.makePolygon(bot+[bot[0]]),cq.Wire.makePolygon(tp+[tp[0]])],True)
    slit=[(-134.9,81.85),(-132.1,81.85),(-131.2,83.36),(-135.8,83.36)]
    w=cq.Wire.makePolygon([V(x,gy-depth-.1,z) for x,z in slit]+[V(slit[0][0],gy-depth-.1,slit[0][1])])
    adds.append(corbel.cut(cq.Solid.extrudeLinear(w,[],V(0,depth+.3,0))))
    # (6) VN-34 EVF receptacle relief (evf_support frame + EY; PCB plane f+15.6..17.2, groove half-width g 1.05)
    ry0,ry1=EVF_HDMI_RECEPTACLE_Y[0]-16+EY-.5,EVF_HDMI_RECEPTACLE_Y[1]-16+EY+.5
    cuts.append(box(f+15.45,f+15.6+(1.05-.8),ry0,ry1,62.9,63.8))
    return adds,cuts


# T2 (VN-53, FP-11b): the +Y tab-catch tine. Its catch face (y = +y_in, facing -Y) faces DOWN in the -Y-down tub
# print, and both free edges of that face border camera sweeps: behind it the lock tab and heads pass x -22.97 ->
# -11.87 at |y| <= 7.08, z <= 82.1 in camera_in, below it they roll in the slot. No tub geometry can anchor it (every
# anchor would stand in a sweep) and paint-on support would land on the catch face (VN-53). So the tine is split at
# TAB_CATCH_SPLIT_Z: above it the web merges into a ceiling over the slot (above every tab position) and stays
# integral; below it a separate stub is printed upright (bed face down, catch face vertical) and bonded into the tub
# before assembly (steps print_inserts), located on the ceiling datum by a tenon (default pending user decision 16:
# bonded stub, see FIX-LOG T2). make_tub returns the bonded tub (adhesive fills the pocket clearance), so every
# assembly check sees the same catch faces; tub_print_parts gives the two print files.
TAB_CATCH_SPLIT_Z=83.5                     # joint plane: tab top 82.1 (CAM top_r 22.1 above the axis z 60) + 1.4
TAB_CATCH_CEILING_TOP=90.0                 # into the panel-screw boss column (its underside z 87.5..89.2 over the tine x)
TAB_CATCH_TENON=dict(x=(-13.5,-9.2),t=1.6,h=3.5)    # on the stub top; its -Y face lies on the catch-face plane
TAB_CATCH_POCKET_CLEAR=dict(x=.1,y=.2,z=.1)          # adhesive clearance; the -Y face is the datum (no clearance)
TAB_CATCH_BED_CHAMFER=.6                   # r7 layout.FDM BED_CHAMFER on the stub's bed edges (print_rules.check_bed_chamfer)


def tab_catch_split():
    """+Y tine split from the r7 tab_catch_boxes (unchanged). -> dict(adds: [ceiling, pad] fused into the tub,
    envelope: the integral stub region, pocket: tenon pocket in the tub, stub: the bonded insert incl. its tenon)."""
    tc={(b['side'],b['kind']):b for b in L.tab_catch_boxes()}
    wp,fp,wm=tc[(1,'web')],tc[(1,'flange')],tc[(-1,'web')]
    zs=TAB_CATCH_SPLIT_Z;x0,x1=wp['x'];yin,yout=wp['y'];z0=wp['z'][0]
    ceiling=box(x0,x1,wm['y'][1]-.01,yin+.01,zs,TAB_CATCH_CEILING_TOP)
    pad=box(fp['x'][1]-.01,x1,yout-.01,yout+1.2,zs,98.0)     # +Y web 1.2 thicker above the joint: pocket wall
    env=box(x0,x1,yin,yout,z0-.1,zs).fuse(box(fp['x'][0],fp['x'][1],yin,fp['y'][1],z0-.1,zs)).clean()
    T,C=TAB_CATCH_TENON,TAB_CATCH_POCKET_CLEAR
    pocket=box(T['x'][0]-C['x'],T['x'][1]+C['x'],yin,yin+T['t']+C['y'],zs-.1,zs+T['h']+C['z'])
    stub=box(x0,x1,yin,yout,z0,zs).fuse(box(fp['x'][0],fp['x'][1],yin,fp['y'][1],z0,zs)).clean()
    stub=cq.Workplane(obj=stub).edges('<Z').chamfer(TAB_CATCH_BED_CHAMFER).val()
    stub=stub.fuse(box(T['x'][0],T['x'][1],yin,yin+T['t'],zs-.01,zs+T['h'])).clean()
    return dict(adds=[ceiling,pad],envelope=env,pocket=pocket,stub=stub)


def tub_print_parts(tub):
    """T2 print files for a bonded tub from make_tub. -> (tub print stock: without the stub, with the tenon pocket;
    the stub insert). Both in the assembly frame; export_candidate gives each its own print pose."""
    sp=tab_catch_split()
    stock=tub.cut(sp['envelope']).cut(sp['pocket']).clean()
    if not stock.isValid() or len(stock.Solids())!=1:raise ValueError('tub print stock is not one valid solid')
    return stock,sp['stub']


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
    meta=json.loads(read_text(folder/'pi5-corrected.json'))
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
    Four kit bosses sit against the UPS underside. The kit-screw seat stays at y 19.2:3.0mm under the screw seat:
    8-3-1.6=3.4mm nominal engagement, gated by real standoff depth.
    No cooler removal, PCB-edge clip, spring keeper or pogo interface alteration.
    FP-11c (VN-54, VN-56): frame, ears, kit/ear bosses and arm all reach the continuous +Y bed face at y 22.2 (the
    frame printed 2 mm above the bed); kit heads (y 19.2..21.6) sit in r2.65 pockets with the arm's r3.35 lead-in;
    PT counterbores 7.0 mm in 5.2 mm ear bosses; r7 FDM 0.6 mm 45 deg chamfer on the exterior bed edges; a 50 deg
    relief keeps 0.6 mm (normal to its slope) to the power-nut reserve.
    """
    top=CARRIER_BED_Y-3.2   # the body is built 3.2 mm lower in Y, then moved
    holes=[rp((x,y,6)) for x,y in L.PI['holes']]
    # Central opening does not trap the UPS components or underside cable exits.
    s=box(-96.5,-29,14,top,4,64.0).cut(box(-86,-39,13,top+1,16,54))
    # Extend the frame to the two mounting ears and connect to existing top/bottom rails.
    # Diagonal rear arm clears the carried upper USB2 power head and FPS body.
    ax,az,bx,bz=-127.,69.,-93.,53.
    norm=math.hypot(bx-ax,bz-az);nx=-(bz-az)/norm*2;nz=(bx-ax)/norm*2
    pts=[(ax+nx,az+nz),(bx+nx,bz+nz),(bx-nx,bz-nz),(ax-nx,az-nz)]
    wire=cq.Wire.makePolygon([V(x,14,z) for x,z in pts]+[V(pts[0][0],14,pts[0][1])])
    arm=cq.Solid.extrudeLinear(wire,[],V(0,top-14,0))
    s=s.fuse(arm,box(-34,-25,14,top,5,13))
    for x,_,z in holes:
        s=s.fuse(cyl('y',4.5,13,top,x,z))
    for x,z in CARRIER_SCREWS:
        s=s.fuse(cyl('y',CARRIER_EAR_R,14,top,x,z))
    for x,_,z in holes:
        s=s.cut(cyl('y',1.4,12.9,top+.1,x,z),cyl('y',2.65,16,top+.1,x,z),cyl('y',3.35,top-.7,top+.1,x,z))
    for x,z in CARRIER_SCREWS:s=s.cut(cyl('y',1.7,13.9,top+.1,x,z),cyl('y',CARRIER_CBORE_R,16.6,top+.1,x,z))
    for x,z in [(-92,25),(-92,45),(-34,25),(-34,45)]:
        s=s.cut(box(x-1.5,x+1.5,13.9,top+.1,z-.5,z+.5))
    s=_carrier_bed_chamfer(SG.reinforce_carrier(tr(s.clean(),(0,3.2,0)))).cut(_power_nut_relief())
    if not s.isValid() or len(s.Solids())!=1:raise ValueError('Invalid carrier after the power-nut relief')
    return s


def _carrier_bed_chamfer(s):
    """r7 FDM BED_CHAMFER (0.6 mm, 45 deg) on the exterior edges of the +Y bed face only; holes keep their sections."""
    s=s.clean()   # merge the coplanar frame and arm faces into one bed face
    faces=[f for f in s.Faces() if abs(f.Center().y-CARRIER_BED_Y)<1e-6 and f.normalAt().y>1-1e-9]
    if len(faces)!=1:raise ValueError('carrier bed face is not one planar face: %d'%len(faces))
    c=s.chamfer(dc.FDM['BED_CHAMFER'],None,faces[0].outerWire().Edges())
    if not c.isValid() or len(c.Solids())!=1:raise ValueError('carrier bed chamfer failed')
    return c


def _power_nut_relief(gap=0.8,rise=1.2):
    """FP-11c: with the bed face at y 22.2 the right rail's outer 2 mm met the power-nut reserve face (_build row
    power_nut_reserve: OD 22, y 22.2..25.2, axis (-20, 25.5)) at 0 mm. A cone coaxial with the nut leaves `gap` at the
    bed face (0.8 there, 0.61 normal to the slope) and rises `rise` mm per mm (50 deg), so the relief still grows from
    the bed in print."""
    r=POWER_NUT_RESERVE_R+gap+.1/rise
    return cq.Solid.makeCone(r,0,r*rise,V(POWER_NUT_AXIS_XZ[0],CARRIER_BED_Y+.1,POWER_NUT_AXIS_XZ[1]),V(0,-1,0))


def carrier_locator_seat():
    """FP-11c (VN-38) tub floor seat rib under the carrier bottom-rail tongue: +Y face on the carrier datum y 17.2, top
    z LOCATOR_SEAT_TOP; its -Y face falls 4 in 5 to the floor so it grows from the tub's -Y bed wall in print."""
    x,t=LOCATOR_X,LOCATOR_SEAT_TOP
    pts=[(17.2,2.0),(17.2,t),(15.2,t),(15.2-1.25*(t-2.5),2.5),(15.2-1.25*(t-2.5),2.0)]
    w=cq.Wire.makePolygon([V(x-6,y,z) for y,z in pts]+[V(x-6,*pts[0])])
    return cq.Solid.extrudeLinear(w,[],V(12,0,0))


def carrier_locator_stop():
    """FP-11c (VN-38) panel stop pad over the carrier tongue, assembly frame (make_panel builds 3 mm lower in Y)."""
    return box(LOCATOR_X-6,LOCATOR_X+6,CARRIER_BED_Y+LOCATOR_STOP_GAP,25.4,3.1,9.0)


# C2 (FP-11d, VN-55): the s_c4 lug back to r7's proportions. r7 (layout COLLAR lug): bit relief -27.0, screw -31.0,
# lug face -35.0, i.e. relief to screw 4.0 and screw to face 4.0. The 9ced753 candidate had 3.5 / 3.7 (relief -22.8,
# screw -26.3, face -30.0): the 7.0 washer ended exactly on the relief face (0.2 into it at the 0.2 float) and the r 3.9
# flat-support footprint (7.0 / 2 + float 0.2 + edge 0.2) ran 0.2 past the lug face. The relief stays at -22.8, so the
# body wall between the relief and the bore is unchanged (verify_candidate collar_relief_nominal_after_bed_chamfer,
# hypot(22.8, 6) - 21.15 - 0.6 = 1.83 >= 1.6; moving the relief instead would drop it below 1.6). Screw, insert and
# driver line move 0.5 mm to -26.8 and the lug face 0.8 mm to -30.8: washer 0.5 mm from the relief (0.3 at the float,
# r7 0.5 / 0.3), footprint 0.1 mm inside the face (r7 0.1), dia 6.5 bit 0.75 mm from the relief (r7 0.75), lug wall
# outside the dia 4.0 insert bore 2.0 mm (was 1.7; r7 2.0).
COLLAR_LUG_Y_OUT=-30.8
COLLAR_SCREW_Y=-26.8
COLLAR_BIT_RELIEF_Y=-22.8
# C2 (FP-11d, VN-58): the LR compression foot (dia 7.6) reaches 28.64 mm from the lens axis, 3.64 mm outside the body
# r 25, and r7 gives ears only to the bolted feet. A cone on the foot axis under it (front face +X on the bed, so the
# foot grows -X off the body rear face) shrinks 1 mm in radius per LR_SUPPORT_RUN mm toward the bed: about 50 deg from
# the bed plane, steeper than the r7 45 deg rule. Only the part outside r (body_r - 0.5) is added.
LR_SUPPORT_RUN=1.2


def collar_setup():
    """Keep optical seating/cone datums, reduce non-optical exterior and ear span.
    Changed clamp stiffness invalidates earlier spring/thermal estimates (M1 open).
    C2 (FP-11d): lug face, s_c4 screw and bit relief at r7's spacing (COLLAR_LUG_Y_OUT, COLLAR_SCREW_Y,
    COLLAR_BIT_RELIEF_Y).
    """
    L.COLLAR=copy.deepcopy(L.COLLAR)
    L.COLLAR['body_r']=25.0
    L.COLLAR['feet']['LL']=(18.0,30.0)
    L.COLLAR['lug'].update(y_out=COLLAR_LUG_Y_OUT,screw_y=COLLAR_SCREW_Y,bit_relief_y=COLLAR_BIT_RELIEF_Y)
    L.SCREWS=copy.deepcopy(L.SCREWS)
    for s in L.SCREWS:
        if s['id']=='s_c3':
            s['head_point']=(s['head_point'][0],18,30);s['tip']=(s['tip'][0],18,30)
        if s['id']=='s_c4':
            s['head_point']=(s['head_point'][0],COLLAR_SCREW_Y,s['head_point'][2]);s['tip']=(s['tip'][0],COLLAR_SCREW_Y,s['tip'][2])


def lr_foot_support():
    """C2 (FP-11d, VN-58) support cone under the LR compression foot, assembly frame. Call in the collar_setup state.
    Cone on the foot axis from the foot radius at the body rear face (collar_spec rear_x) toward +X (the bed side),
    radius -1 mm per LR_SUPPORT_RUN mm; kept only outside r (body_r - 0.5) about the lens axis, so it cannot reach
    the bore, the cone seat or the rear land, and it ends inside the body before the collar front."""
    C=L.COLLAR;ly,lz=L.LENS_AXIS;y,z=C['feet']['LR'];r=C['foot_d']/2
    x0=L.collar_spec(L.LENS)['rear_x']
    cone=cq.Solid.makeCone(r,0.0,r*LR_SUPPORT_RUN,V(x0,y,z),V(1,0,0))
    keep_out=cq.Solid.makeCylinder(C['body_r']-0.5,r*LR_SUPPORT_RUN+2.0,V(x0-1.0,ly,lz),V(1,0,0))
    return cone.cut(keep_out)


def make_collar(lens=None):
    """The candidate lens collar: r7 printed_collar.build_part (candidate layout from collar_setup) + the LR foot
    support (VN-58). Call in the collar_setup state; lens defaults to L.LENS. j7_collar_checks rebuilds the collars
    with this same function (its context rows compare the rebuild with the manifest-bound STEP)."""
    old=L.LENS
    try:
        if lens is not None:L.LENS=lens
        base=printed_collar.build_part(L,'lens_collar',L.LENS).val()
        # No same-domain cleanup (as collar_print_stock): on these collars clean() moves the volume by ~0.001 mm3.
        sol=base.copy().fuse(lr_foot_support())
    finally:L.LENS=old
    if not sol.isValid() or len(sol.Solids())!=1:raise ValueError('collar LR support union is not one valid solid')
    if base.copy().cut(sol.copy()).Volume()>1e-6:raise ValueError('collar LR support removed collar material')
    return sol


# C2 (feather edge, FP-09 note): the narrowed base (y +-25.2) puts the -Y face 3.2 mm from the s_j lock axis (y -22,
# moved 2 mm for the USB jacks), inside the dia 7.0 counterbore (r 3.5, z -8..-2): the bore broke through the face over
# x -111 +- 1.4 and left 0.1-0.4 mm feather walls beside it (thin spot 0.373 at -112.87, -24.96, -6.38). A local
# wall closes it: r SJ_SIDE_WALL_R about the screw axis (1.4 mm round the bore, 1.7 mm proud of the face, still 1.1
# inside the tub's -Y face at -28), z -8..-2.9, then a cone to r 3.2 at z -0.7 (52 deg from the bed plane, base prints
# +Z down; it ends below the 0.6 mm bed chamfer). Counterbore, clearance hole and head seat are unchanged.
SJ_SIDE_WALL_R=4.9
GRIP_BASE_Y=25.2


def sj_side_wall():
    """C2 local wall outside the base -Y face round the s_j counterbore (assembly frame); only the part at
    y < -(GRIP_BASE_Y - 0.3), less the counterbore. Uses L.J4_LOCK and the s_j cbore row."""
    sj=next(s for s in L.SCREWS if s['id']=='s_j');x,y=L.J4_LOCK['c'];cb=sj['cbore'];rb=cb['d']/2
    z0,z1=cb['z'];zc,zt,rt=-2.9,-0.7,GRIP_BASE_Y+y   # rt: radius that reaches the face line at z -0.7
    if not (y<0 and 0<rt<rb<SJ_SIDE_WALL_R):raise ValueError('s_j side wall: lock not inside the -Y counterbore case')
    body=cq.Solid.makeCylinder(SJ_SIDE_WALL_R,zc-z0,V(x,y,z0),V(0,0,1)).fuse(
        cq.Solid.makeCone(SJ_SIDE_WALL_R,rt,zt-zc,V(x,y,zc),V(0,0,1)))
    outside=box(x-SJ_SIDE_WALL_R-1,x+SJ_SIDE_WALL_R+1,y-SJ_SIDE_WALL_R-1,-(GRIP_BASE_Y-0.3),z0-0.1,0.0)
    return body.intersect(outside).cut(cq.Solid.makeCylinder(rb,z1-z0+0.1,V(x,y,z0-0.1),V(0,0,1)))


# C2 (FP-11e, VN-57): the rear J4 head pocket of the base ends at x -64.75 (tongue_r base_pocket x -83.25..-64.75).
# The power passage box (power_geometry.grip_cuts, GRIP_PASSAGE_BOX) and the base pigtail opening (layout FLOOR_HOLES
# pigtail x -65.8..-55, y -8..2, cut through the base by printed_grip) removed the pocket's +X end wall, so the pocket
# floor (a roof in the +Z-down print) had no anchor at that end over y -12.4..9 (102.9 mm2 unsupported). For y >= -4.0
# the base gets an end wall back to x -63.25 (1.5 mm past the pocket end; below the pocket floor it fills x -66..-63.25).
# The installed XT30 pair/fuse and all 201 rigid service poses of the junction and pack stay 1.145 mm from that block
# (probe on the ec60b42d STEPs; verify_power_service re-checks). Below y -4.0 the installed fuse, the negative core and
# the service sweep need the passage to x -66 (installed pair overlap 50.0 mm3 with a wall there): that band of the
# pocket floor keeps the declared support zone (grip_support_zones).
GRIP_PASSAGE_BOX=(-66.0,-35.0,-12.4,9.0,-10.0,0.1)   # = power_geometry.grip_cuts box (tests compare)
GRIP_PASSAGE_WALL=dict(x=(-66.0,-63.25),y=(-4.0,9.0),z=(-10.0,0.0))
# C2 (found while fixing VN-57): the passage box ends at x -35.0 and the base run-lead drop (layout KEEPOUTS
# ko_run_drop, x -34..-28, y 1.5..9, cut through the base by printed_grip) starts at x -34.0. Below y 6.25 the
# run-button drop opening (RUN_BTN body y +-6 + SLIDE, from x -35.25) already joins them; over y 6.25..9 a 1.0 mm wall
# stood between them, z -10..0 (thin spots 0.999 at x -34.0, y 6.8 / 8.0 once the base faces are re-unified). The box
# end goes back to x -35.6 over that band only (wall 1.6 mm, the r7 loaded minimum); the junction sweep and the
# installed pair stay >= 12.9 mm away (probe), and the run and switch passages are not touched.
GRIP_RUN_WALL=dict(x=(-35.6,-35.0),y=(L.RUN_BTN['body']['y'][1]+L.FDM['SLIDE'],9.0),z=(-10.0,0.0))


def grip_passage_wall(w=None):
    """C2 material given back to the base beside the power passage (assembly frame, build layout state): block `w`
    (default GRIP_PASSAGE_WALL) less the rear keyhole (window, neck slot, head pocket) and less every power capsule /
    fuse pocket (power_geometry.local_cutters), so no passage the frozen route cuts is filled."""
    w=w or GRIP_PASSAGE_WALL;blk=box(*w['x'],*w['y'],*w['z'])
    t=next(t for t in L.TONGUES if t['id']=='tongue_r')
    blk=blk.cut(dc.keyhole_slot(t))
    bb=blk.BoundingBox()
    for c in PG.local_cutters():
        cb=c.BoundingBox()
        if cb.xmin<bb.xmax and cb.xmax>bb.xmin and cb.ymin<bb.ymax and cb.ymax>bb.ymin and cb.zmin<bb.zmax and cb.zmax>bb.zmin:
            blk=blk.cut(c.copy())
    return blk


def make_base_grip():
    """Base grip as model._build makes it (candidate strap, base y +-GRIP_BASE_Y, no s_b1/s_b2, power passages,
    heel doubler, J4 entry floor stock) + the C2 s_j side wall and the C2 rear-pocket end wall (VN-57). The
    declared pocket-floor support zone is grip_support_zones(). Call in model.build's layout (JG.trial_layout)."""
    oldstrap=copy.deepcopy(L.STRAP); oldbase=copy.deepcopy(L.BASE); oldscrews=copy.deepcopy(L.SCREWS)
    try:
        L.STRAP=candidate_strap_layout()
        L.BASE=copy.deepcopy(L.BASE);L.BASE['y']=(-GRIP_BASE_Y,GRIP_BASE_Y)
        L.SCREWS=[s for s in L.SCREWS if s['id'] not in ('s_b1','s_b2')]
        grip=SG.reinforce_grip(PG.cut_passages(printed_grip.build_part(L,'base_grip').val(), PG.grip_cuts()))
        grip=PG.cut_passages(grip.fuse(JG.entry_floor_stock()).clean(),PG.grip_cuts())
        adds=[sj_side_wall(),grip_passage_wall(),grip_passage_wall(GRIP_RUN_WALL)]
    finally:L.STRAP,L.BASE,L.SCREWS=oldstrap,oldbase,oldscrews
    out=grip
    for a in adds:
        out=out.fuse(a).clean()
        if not out.isValid() or len(out.Solids())!=1:raise ValueError('base grip C2 addition union is not one valid solid')
    # C2 (bed_chamfer row, FP-11a check): JG.entry_floor_stock re-squared the base front top edge (x -0.5, z 0) over
    # y -19.5..19.5 (39.0 mm without the 0.6 mm 45 deg bed chamfer). Cut r7's own slab chamfer back there.
    bc=L.FDM['BED_CHAMFER'];x1=L.BASE['x'][1]
    w=cq.Wire.makePolygon([V(x1+.1,-19.6,.1),V(x1+.1,-19.6,-bc-.1),V(x1-bc-.1,-19.6,.1),V(x1+.1,-19.6,.1)])
    out=out.cut(cq.Solid.extrudeLinear(w,[],V(0,39.2,0))).clean()
    if not out.isValid() or len(out.Solids())!=1:raise ValueError('base grip front bed chamfer cut is not one valid solid')
    return out


def grip_support_zones(tongues):
    """C2 (FP-11e, VN-57) declared paint-on support zone of the base grip (assembly frame), for print_rules.
    `tongues` = the J4 trial tongue rows (JG.trial_layout). The rear head pocket floor (print +Z down: a roof at the
    pocket bottom) keeps its +X end wall only for y >= GRIP_PASSAGE_WALL y0; below that the installed fuse, the
    negative core and the rigid junction service sweep need the passage up to x -66, so that band of the floor has
    no anchor at its +X end. The zone covers that band only, x from the pocket -X wall + 0.5 to the passage face
    + 0.2. It lies inside the neck slot / window footprint (|y| < neck slot half width), so supports stand on the
    bed and never on the keyhole lips; they touch only the pocket floor, which clears the tongue head by the slide
    gap and carries no J4 load. Gate: clear it through the window, check the floor is flat and the head slides."""
    t=next(t for t in tongues if t['id']=='tongue_r');p=t['base_pocket'];nk=t['base_neck_slot']
    bx0,_,by0,_,_,_=GRIP_PASSAGE_BOX;wy0=GRIP_PASSAGE_WALL['y'][0]
    zf=p['z'][0]
    y0,y1=by0-0.2,wy0+0.2
    if not (nk['y'][0]<y0 and y1<nk['y'][1]):raise ValueError('grip support zone leaves the neck slot footprint')
    return [dict(id='grip_rear_pocket_passage_band',kind='support',
                 box=(p['x'][0]+0.5,bx0+0.2,y0,y1,zf-0.4,zf+0.2),
                 why='rear J4 head pocket floor beside the power passage (VN-57): paint-on support from the bed '
                     'through the neck slot and window; touches the pocket floor only (slide clearance face, no J4 '
                     'load), never the keyhole lips; remove through the window, then check the head slide')]


def make_tub(length):
    # Small vertical edge radii: broad flat sides and deliberate single 0.3 mm seam.
    outer=(cq.Workplane('XY').box(length,56,100,centered=False).translate((-length,-28,0))
           .edges('|Z').fillet(2).val())
    cavity=box(-length+2.5,-5.2,-25.5,29,2.5,97.5)
    s=outer.cut(cavity)
    adds=VG.additions(length);cuts=VG.mouth_cuts(length)
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
    adds.append(carrier_locator_seat())   # FP-11c (VN-38) third locating feature: -Y seat of the carrier tongue
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
    # Original intake ports feed a separate external shadow plenum.
    cuts.extend(VG.inlet_cuts())
    # Functional CSI latch/service slot. No loose cover or extra control.
    # Direct cooler-side tool access avoids the blocked over-PCB path; real latch/jaws gated.
    cuts.append(cq.Workplane(obj=box(-89,-77,VG.OUTER_Y-.1,-25.4,41,68)).edges('|Y').fillet(1).val())
    adds.extend([FS.shelf(),FPG.build()])
    # Isolated forward exhaust, below optical bay; vertical ribs prevent broadside weakening.
    cuts.extend(VG.side_exhaust_cuts())
    # Front broad face is closed; exhaust leaves the concealed plenum edge mouths.
    cuts.extend(VG.front_exhaust_cuts())
    # Baffle ending clear of cooler fins, dividing exhaust from inlet recirculation path.
    adds.append(box(-65,-62,-25.55,-15.3,10,52))
    # Panel is plain: inherited apparent UPS grooves were blind0.2mm skins, not vents.
    # microSD extracts +X through a real straight vertical front slit below the camera.
    cuts.append(box(-5.3,.1,3.8,5.8,27.8,39.8))
    # Wired J2 signal switch replaces the long mechanical linkage and its FPC conflict.
    # Ø16 panel mounting hole; body behind the lower-front bay, no battery current.
    t2a,t2c=tub_print_fixes(length);adds+=t2a;cuts+=t2c   # T2: print-pose fixes and the VN-34 relief
    t2s=tab_catch_split();adds+=t2s['adds']                 # T2 (VN-53): ceiling + pad over the +Y tine joint

    s=s.fuse(*adds).cut(*cuts).clean()
    s=PG.cut_passages(s, PG.tub_cuts())
    s=s.cut(t2s['envelope']).fuse(t2s['stub']).clean()      # T2: bonded +Y stub (bed-chamfered) in place
    if not s.isValid() or len(s.Solids())!=1:raise ValueError('bonded tub is not one valid solid')
    return s


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
    # CF (VN-25 thin-spot gate): the clamp starts 0.5 behind the plate's rear edge (f+2.6; plate from -length+3.1),
    # where its crown over the r 14.4 bore was a 0.2 mm skin (thin spot 0.312 at (-155.05, 25.6, 79.51)). That strip
    # is cut where its skin would be under MIN_WALL; the plate-backed crown and both prongs keep their full length.
    dz=math.sqrt(14.4**2-(22.6-L.FDM['MIN_WALL']-ey)**2)
    clamp=clamp.cut(box(f+2.5,-length+3.1,ey,22.7,78-dz,78+dz))
    adds.extend([clamp,box(f+6,f+9.2,8.3+ey,22.6,69.5,86.5),
                 box(f+15.1,f+17.7,12.3+ey,22.6,70,86)])
    # The pad stops the OLED gently; foam remains an explicit purchased consumable.
    adds.append(box(f+8.93,f+10.53,-7.8+ey,22.6,71.2,84.8))
    cuts.append(cyl('x',14.4,f-.1,f+4.6,ey,78))
    adds.append(tr(carrier_locator_stop(),(0,-3,0)))   # FP-11c (VN-38): +Y stop over the carrier tongue
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
    # Remove the four inherited blind grooves; preserve full panel skin.
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

    grip=make_base_grip()
    printed={'base_grip':grip,'cap':printed_grip.build_part(L,'cap').val(),
             'eyecup':tr(printed_small.build_part(L,'eyecup').val(),(154-length,EY-16,0)),
             'knob_exp':tr(printed_small.build_part(L,'knob_exp').val(),CONTROL_MOVES['knob_exp']),
             'knob_fps':FG.knob(),
             'carrier':make_carrier()}
    if storage=='original':printed['stick_sleeve']=tr(roll(tr(printed_small.build_part(L,'stick_sleeve').val(),(0,0,7.7))),(0,OP.STORAGE_DY,OP.STORAGE_DZ))
    oldc,olds=copy.deepcopy(L.COLLAR),copy.deepcopy(L.SCREWS)
    try:
        collar_setup()
        printed.update(tub=make_tub(length),panel=make_panel(length),lens_collar=make_collar())
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
                core_origin=(-length,VG.OUTER_Y,0),ventilation=VG.metadata(length),collar_print_stock=stock,gauge=gauge,fps_geometry=FG.provenance(),pi_source_geometry=OP.provenance(),
                physical_state='UNQUALIFIED REVIEW CANDIDATE; every inherited r7 physical gate (r7 out/build-receipt.json hardware_gates) and M1 remain open')


def build(storage='compact',lens='kowa_lm6hc'):
    # Coordinated2.4mm lips and heads;0.25mm mating gaps and independent lock retained.
    with JG.trial_layout(L,lip=2.4,head=2.4):
        return _build(storage,lens)

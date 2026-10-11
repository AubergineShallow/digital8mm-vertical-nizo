"""Integral outer shadow plenum. Nominal geometry only; no thermal qualification.

Revision trial2 (review 2026-10-10, FP-11a: VN-51, VN-52, VN-59, VN-37). The tub prints outer face down (-Y), so the
plenum roof (the old side-wall face, y -28, print z 7.6) is a bridge over the 6 mm gap. Trial1 held it up with a grid
of 1.6 mm round posts, which no single slicer bridge direction can serve (VN-51), and left 35-71 mm open spans over
the four edge mouths (VN-52). Trial2 replaces the posts with continuous 1.2 mm ribs (r7 FDM MIN_WALL) laid along the
flow, with staggered 3 mm breaks so each bay stays one air volume:

- cold bay: x-direction rows (constant z) at 4-9 mm pitch; every roof line in z meets a row (or a port slot, or the
  bottom-mouth lintel) within 21 mm. No rib enters the cold underside branch band (z 2.5-17.8), so that branch keeps
  its full section. Both cold mouths get a 45 deg lintel (LINTEL high, with a LINTEL_LAND flat land at the outer face
  so it leaves no acute edge); the rows run through the
  rear mouth as mullions and the underside mouth has mullions at most 25 mm apart for the lintel's first strand.
- hot bay: two roof regions split by a diagonal rib from the front-bottom frame corner to the lowest exhaust port.
  Below it the underside mouth zone bridges in x between z-direction ribs (one of them the single mouth mullion); the
  rest bridges in z between x-direction rows, row z 21 being the single front-mouth mullion. The hot mouths take no
  lintel: area parity (VN-37) leaves 24 mm2 of the measured hot mouth rectangles (534 vs 510 mm2 of ports) and one
  mullion per mouth already uses 14.4 mm2; a lintel of any printable height (2 layers) would cost about 36 mm2 more.
- skin: the r7 BED_CHAMFER (0.6 mm, 45 deg) on the exterior edges of the bed face (VN-59). The CSI slot through the
  skin keeps its sharp bed edge: its straight section is a checked dimension.

Every number below is nominal CAD geometry. Bridge quality, cleanout, airflow and cooling remain physical gates.
"""
import math
import cadquery as cq
V=cq.Vector
OUTER_Y=-35.6
INNER_Y=-25.5
SKIN_INNER=-34.0
WALL_OUTER=-28.0
GAP=6.0
SIDE_Z=(18.,24.,30.,36.)
HOT_Z=(16.,23.,30.,37.)
RIB_T=1.2                    # r7 layout.FDM MIN_WALL; roof-bridge ribs only, no structural load path
RIB_Y=(SKIN_INNER-.05,WALL_OUTER+.1)   # ribs fuse into the skin and the old side wall, as the trial1 posts did
LINTEL=1.0                   # 45 deg lintel height at the cold mouths' outer face
LINTEL_LAND=1.2              # flat land (r7 MIN_WALL deep) between the outer face and the 45 deg slope: no knife edge
BREAK_W=3.0                  # hot upper rows: staggered breaks join the dead-space channels into the bay's air
COLD_BREAK_W=6.0             # cold rows: wider staggered breaks feed the upper rear-mouth channels down to the ports
BED_CHAMFER=0.6              # r7 layout.FDM BED_CHAMFER (45 deg) on the skin's exterior bed edges
COLD_BREAKS={'even':(-116.5,-138.5),'odd':(-128.5,-147.5)}   # break centres, all left of the cold ports (x < -104);
                             # even and odd breaks never overlap, so a roof line in z crosses at most one break
HOT_BREAKS={'even':-40.0,'odd':-25.0}
HOT_PORT_ROW_X=(-59.8,-17.3) # rows 21/28/35 stop 0.8 mm short of the port ends (within r7's 1.0 mm cantilever):
                             # a 2.2 mm lane at the divider and a collector column behind the front mouth join the
                             # port channels; row 28 continues to x -9.5 and row 21 runs -10.5..0 (front-mouth
                             # mullion). Rib ends avoid the integer x planes the check-scope series sampling uses.
HOT_BOTTOM_MULLION_X=-31.0   # off the verifier's mouth ray at x -32; bridges -59..-31.6 and -30.4..-4.6
HOT_FRONT_MULLION_Z=21.0     # = inter-port row 21; off the verifier's front ray at z 22.5
HOT_ZRIB_X=(-48.0,-31.0,-19.0)
HOT_ZRIB_TOP=16.3            # into the lowest hot port slot (z 16-19): closes the underside-mouth roof region
HOT_DIAGONAL=((-3.2,2.0),(-17.5,17.0))    # frame corner (x -5..-2.5, z 0..2.5 solid) -> inside hot port 0's corner
HOT_LEFT_SEPARATOR=(-62.1,-58.5,15.85,17.05)  # divider -> hot port 0's left end, above the z 2.6-15.8 branch band


def box(a,b,c,d,e,f):return cq.Solid.makeBox(b-a,d-c,f-e,V(a,c,e))


def prism(points,vec):
    """Planar polygon (3D points) extruded along vec."""
    w=cq.Wire.makePolygon([V(*p) for p in points],close=True)
    return cq.Solid.extrudeLinear(cq.Face.makeFromWires(w),V(*vec))


def inlet_cuts():return [box(-103,-68,-28.1,-25.4,z,z+3) for z in SIDE_Z]
def side_exhaust_cuts():return [box(-59,-16.5,-28.1,-25.4,z,z+3) for z in HOT_Z]
def front_exhaust_cuts():return []


def _segments(x0,x1,breaks=(),w=BREAK_W):
    """Interval [x0, x1] minus the w wide breaks centred at `breaks`."""
    segs=[(x0,x1)]
    for c in breaks:
        a,b=c-w/2,c+w/2
        segs=[q for s in segs for q in ((s[0],min(s[1],a)),(max(s[0],b),s[1])) if q[1]-q[0]>1e-6]
    return segs


def cold_rows(length):
    """Cold-bay x-direction rows: [(z_centre, [(x0, x1), ...])]. Rows inside the rear mouth's z range (5-75) start at
    the outer face, so they are its mullions; the others start in the rear frame. Row 18.45 lies just above the cold
    underside branch band (sections z 2.6-17.8) and stops before the lowest port; rows 22.5/28.5/34.5 sit between the
    port slots; 43-67 stop at the CSI block (one short row at 55 serves the column right of it)."""
    xs,xf=-length,-length+2.4
    w=COLD_BREAK_W
    rows=[(18.45,[(xs,-104.)])]
    for i,z in enumerate((22.5,28.5,34.5)):
        rows.append((z,_segments(xs,-64.9,COLD_BREAKS['odd' if i%2==0 else 'even'],w)))
    for i,z in enumerate((43.,51.,59.,67.)):
        rows.append((z,_segments(xs,-90.9,COLD_BREAKS['even' if i%2==0 else 'odd'],w)))
    rows.append((55.,[(-75.1,-64.9)]))
    for i,z in enumerate((76.,84.,92.)):
        rows.append((z,_segments(xf,-64.9,COLD_BREAKS['even' if i%2==0 else 'odd'],w)))
    return rows


def hot_rows(length):
    """Hot-bay x-direction rows (upper/front roof region): [(z_centre, [(x0, x1), ...])]. Rows 21/28/35 lie between
    the port slots (HOT_PORT_ROW_X); row 28 also anchors the collector column x -17.3..-9.5 and row 21's second
    segment (-10.5..0) anchors x -10.5..-2.5 and runs out through the front mouth as its mullion. Rows 43-91 reach the
    front frame."""
    a,b=HOT_PORT_ROW_X
    rows=[(21.,[(a,b),(-10.5,0.)]),(28.,[(a,-9.5)]),(35.,[(a,b)])]
    for i,z in enumerate((43.,51.,59.,67.,75.,83.,91.)):
        rows.append((z,_segments(-62.1,-2.4,[HOT_BREAKS['odd' if i%2==0 else 'even']])))
    return rows


def hot_zribs():
    """Hot underside-mouth zone z-direction ribs: [(x_centre, z0, z1)]. The rib at HOT_BOTTOM_MULLION_X is the uncut
    frame in the mouth (z 0-2.5) and continues up the zone; the others start above the mouth's last sampled neck
    plane (z 2.62)."""
    return [(x,2.4 if x==HOT_BOTTOM_MULLION_X else 2.75,HOT_ZRIB_TOP) for x in HOT_ZRIB_X]


def cold_bottom_mullions(length):
    """x centres of the cold underside-mouth mullions: the fewest (even count, so none sits on the verifier's
    mouth-centre ray) leaving openings of at most 25 mm for the lintel's first strand."""
    a,b=-length+4.,-83.
    n=2
    while (b-a-n*RIB_T)/(n+1)>25.:n+=2
    return [a+(k+1)*(b-a)/(n+1) for k in range(n)]


def _openings(lo,hi,bars):
    """[lo, hi] minus RIB_T wide bars centred at `bars` (kept inside)."""
    out,cur=[],lo
    for c in sorted(bars):
        if lo<c<hi:
            out.append((cur,c-RIB_T/2));cur=c+RIB_T/2
    out.append((cur,hi))
    return [q for q in out if q[1]-q[0]>1e-6]


def _lintel_x(x_face,z0,z1):
    """Material kept at the top of a mouth through an x-facing frame, outer face x_face (rear): a LINTEL high lintel
    with a LINTEL_LAND deep flat underside at the outer face, then a 45 deg slope up to the roof (no acute edge)."""
    s,w,y=LINTEL,LINTEL_LAND,WALL_OUTER
    return prism([(x_face-.2,y-s,z0),(x_face+w,y-s,z0),(x_face+w+s+.1,y+.1,z0),(x_face-.2,y+.1,z0)],(0,0,z1-z0))


def _lintel_z(x0,x1):
    """Same for the underside (outer face z 0)."""
    s,w,y=LINTEL,LINTEL_LAND,WALL_OUTER
    return prism([(x0,y-s,-.2),(x0,y-s,w),(x0,y+.1,w+s+.1),(x0,y+.1,-.2)],(x1-x0,0,0))


def mouth_cuts(length):
    """The four edge mouths as openings between their mullions; the cold ones keep a 45 deg lintel."""
    cuts=[]
    rear=[z for z,segs in cold_rows(length) if 5<z<75 and segs[0][0]<=-length]
    for z0,z1 in _openings(5.,75.,rear):
        c=box(-length-.1,-length+2.6,SKIN_INNER,WALL_OUTER,z0,z1).cut(_lintel_x(-length,z0-.1,z1+.1))
        cuts.extend(c.Solids())
    for x0,x1 in _openings(-length+4.,-83.,cold_bottom_mullions(length)):
        c=box(x0,x1,SKIN_INNER,WALL_OUTER,-.1,2.6).cut(_lintel_z(x0-.1,x1+.1))
        cuts.extend(c.Solids())
    for x0,x1 in _openings(-59.,-5.,[HOT_BOTTOM_MULLION_X]):
        cuts.append(box(x0,x1,SKIN_INNER,WALL_OUTER,-.1,2.6))
    for z0,z1 in _openings(5.,40.,[HOT_FRONT_MULLION_Z]):
        cuts.append(box(-2.6,.1,SKIN_INNER,WALL_OUTER,z0,z1))
    return cuts


def post_centres(length):
    """Trial1 round-post centres. Trial2 has no round posts (continuous ribs instead): empty. verify_check_scope adds
    a sample plane at every post centre; trial2 places no rib parallel to a series-section plane family inside that
    family's range (tests/test_plenum_trial2.py proves the sampled minimum against rib-centre and 0.1 mm planes)."""
    return []


def _diagonal():
    (x0,z0),(x1,z1)=HOT_DIAGONAL
    dx,dz=x1-x0,z1-z0;n=math.hypot(dx,dz);px,pz=-dz/n*RIB_T/2,dx/n*RIB_T/2
    y0,y1=RIB_Y
    pts=[(x0+px,y0,z0+pz),(x1+px,y0,z1+pz),(x1-px,y0,z1-pz),(x0-px,y0,z0-pz)]
    return prism(pts,(0,y1-y0,0))


def ribs(length):
    """All plenum rib solids (cold rows, hot rows, hot z-ribs, the diagonal and the left separator)."""
    y0,y1=RIB_Y;h=RIB_T/2;out=[]
    for z,segs in cold_rows(length)+hot_rows(length):
        out+=[box(a,b,y0,y1,z-h,z+h) for a,b in segs]
    out+=[box(x-h,x+h,y0,y1,za,zb) for x,za,zb in hot_zribs()]
    a,b,c,d=HOT_LEFT_SEPARATOR
    out+=[box(a,b,y0,y1,c,d),_diagonal()]
    return out


def skin(length):
    """1.6 mm outer skin with the r7 45 deg bed chamfer on its exterior bed-face edges (VN-59)."""
    wp=cq.Workplane('XY').add(box(-length,0,OUTER_Y,SKIN_INNER,0,100)).faces('<Y').edges().chamfer(BED_CHAMFER)
    return wp.val()


def additions(length):
 # Face is uninterrupted except the required CSI service aperture. Frame and
 # separated cold/hot bays are integral; no new fastener or loose cover.
 a=[skin(length),
 box(-length,-length+2.5,SKIN_INNER-.05,-25.4,0,100),
 box(-2.5,0,SKIN_INNER-.05,-25.4,0,100),
 box(-length,0,SKIN_INNER-.05,-25.4,0,2.5),
 box(-length,0,SKIN_INNER-.05,-25.4,97.5,100),
 box(-65,-62,SKIN_INNER-.05,-27.9,2.4,97.6),
 box(-91,-75,SKIN_INNER-.05,-27.9,39,70)]
 return a+ribs(length)


def mouth_nominal(length):
    """Nominal mouth areas (mm2) in the verifiers' rectangles: gross, minus mullions, minus the lintel at the outer
    neck plane (0.05 mm in, inside the lintel land), as the verifiers sample it."""
    g=GAP;s=LINTEL
    rear=[z for z,segs in cold_rows(length) if 5<z<75 and segs[0][0]<=-length]
    nb=len(cold_bottom_mullions(length))
    return dict(cold_rear=dict(gross=70*g,net=70*(g-s)-len(rear)*RIB_T*(g-s),mullions=len(rear),lintel_mm=LINTEL),
                cold_bottom=dict(gross=(length-87)*g,net=(length-87)*(g-s)-nb*RIB_T*(g-s),mullions=nb,lintel_mm=LINTEL),
                hot_bottom=dict(gross=54*g,net=54*g-RIB_T*g,mullions=1,lintel_mm=0.),
                hot_front=dict(gross=35*g,net=35*g-RIB_T*g,mullions=1,lintel_mm=0.))


def support_summary(length):
    """Plain-data description of the roof support for reports and docs."""
    return dict(revision='trial2 ribs + lintels',rib_thickness_mm=RIB_T,rib_y_mm=list(RIB_Y),break_width_mm=BREAK_W,
                cold_rows=[(z,segs) for z,segs in cold_rows(length)],hot_rows=[(z,segs) for z,segs in hot_rows(length)],
                hot_z_ribs=hot_zribs(),hot_diagonal=HOT_DIAGONAL,hot_left_separator=HOT_LEFT_SEPARATOR,
                cold_bottom_mullions_x=cold_bottom_mullions(length),hot_bottom_mullion_x=HOT_BOTTOM_MULLION_X,
                hot_front_mullion_z=HOT_FRONT_MULLION_Z,lintel_mm=LINTEL,lintel_land_mm=LINTEL_LAND,lintel_mouths=['cold_rear','cold_bottom'],
                skin_bed_chamfer_mm=BED_CHAMFER,mouths=mouth_nominal(length))


def metadata(length=158):
 mn=mouth_nominal(length)
 return dict(revision='shadow-gap plenum trial2 (flow ribs, 45 deg cold-mouth lintels, mullions, skin bed chamfer)',outer_side_y_mm=OUTER_Y,inner_side_y_mm=INNER_Y,
  outer_skin_mm=1.6,plenum_gap_mm=GAP,original_side_wall_mm=2.5,
  intake_wall_throat_mm2=420.,exhaust_wall_throat_mm2=510.,
  cold_rear_mouth_mm2=mn['cold_rear']['net'],cold_bottom_mouth_mm2=mn['cold_bottom']['net'],hot_bottom_mouth_mm2=mn['hot_bottom']['net'],hot_front_mouth_mm2=mn['hot_front']['net'],
  mouth_gross_mm2={k:v['gross'] for k,v in mn.items()},
  csi_access_open_area_mm2=12*27-(4-math.pi),csi_unchanged_straight_access=True,
  panel_previous_relief='Four blind grooves with0.2mm retained floors, not through-vents; removed for plain2.8mm panel',
  airflow='Separate integral cold/hot outer bays; rear/underside intake and front/underside exhaust. 1.2 mm flow ribs with staggered breaks; internal baffle and CSI bypass remain unsealed. Area is not flow or cooling.',
  print='Outer face on bed with 0.6 mm bed chamfer. Roof bridges run between continuous 1.2 mm ribs (one slicer direction per roof region; spans computed by verify_print_checks print_bridge_direction); cold mouths have 45 deg lintels, every mouth has mullions. Slicer inspection and the all-four-mouth plenum coupon remain gates. No automatic trapped supports.',
  support=support_summary(length),
  physical_qualified=False,remaining=['Actual cooler profile/registration','Fan operating point and plenum pressure loss','Hand and strap occlusion','Plenum bridge/cleanout coupon (all four mouths)','Real CSI latch/jaw access','All56 inherited gates andM1'])

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

Revision trial3 (review 2026-10-10 fix-up FX, VN-37 reopened). The trial2 rows choked the paths from the ports to the
mouths: the path-aware min cut (plenum_flow.py, max flow over the free gap volume) of the trial2 geometry is hot 255 of
510 mm2 and cold 206 of 420 mm2, although every sampled plane passed. Trial3 keeps roof support lines but lets the air
through them and lays them along the flow:

- every rib is a hanging beam (BEAM_Y0 to the wall: 5 layers under the roof) carried by full-depth pillars (PILLAR_L)
  at its ends and at most WINDOW_MAX apart (staggered between neighbouring ribs); the roof lands on a continuous line,
  the 5 mm windows under the beam carry the flow, and each beam underside is a straight bridge between two pillars;
- no rib, beam or pillar stands in front of a wall port (z-rib pieces stop at the slot edges, rows lie under the
  strips between the slots);
- hot bay: the underside zone, the port band left of x -31 and everything above it are one roof region bridged in x
  between z-ribs (x -60.4 lane rib, -48, -31; pieces between the slots) that run from the underside mouth to the top
  frame, so the underside branch flows along them; right of x -31 the front zone is bridged in z between rows (21/28/35
  under the strips, 40.6 on the top slot, 49, 77; row 21 runs out as the front-mouth mullion), so the front branch
  flows along them; the column right of the slots has its floor at the band row (z 10), its left side on the column
  rib (x -17.1, up to the lowest slot's corner) and the lip rib (x -3.2) separates the front-mouth lip from the
  underside zone. The trial2 diagonal, left separator and port-band rows are gone.
  The hot min cut is 444.5 mm2 of 510: the bay with no rib at all reaches only 493.2 mm2 (plenum_flow empty-bay bound),
  so no internal layout can give 510 with these ports and mouths; that needs a port or mouth change (user decision 17).
- cold bay: the trial2 rows without breaks and without row 18.45, windowed, no pillar in COLD_WINDOW_X (where the rear
  air turns into the port channels); 0.6 mm cold-mouth lintels (3 layers, 45 deg, with the 1.2 mm land). Cold min cut
  420 = the wall ports.

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
LINTEL=0.6                   # 45 deg lintel height at the cold mouths' outer face (trial3: 3 layers; trial2 1.0)
LINTEL_LAND=1.2              # flat land (r7 MIN_WALL deep) between the outer face and the 45 deg slope: no knife edge
BREAK_W=3.0                  # trial2 only (kept for the record): row breaks; trial3 rows have no breaks
COLD_BREAK_W=6.0             # trial2 only
BED_CHAMFER=0.6              # r7 layout.FDM BED_CHAMFER (45 deg) on the skin's exterior bed edges
COLD_BREAKS={'even':(),'odd':()}   # trial3: no breaks (the beam windows join the bay's air)
COLD_WINDOW_X=(-106.0,-92.0)       # trial3: cold rows keep this span free of pillars (one 14 mm window)
BEAM_Y0=-29.0                # trial3: hanging beam from y -29 to the wall (5 x 0.2 mm layers under the roof)
PILLAR_L=1.2                 # full-depth pillar length along its rib (r7 MIN_WALL)
WINDOW_MAX=14.0              # longest beam bridge between two pillars
HOT_BOTTOM_MULLION_X=-31.0   # off the verifier's mouth ray at x -32; bridges -59..-31.6 and -30.4..-4.6
HOT_FRONT_MULLION_Z=21.0     # = front-zone row 21; off the verifier's front ray at z 22.5
HOT_UZ_X=(-48.0,)            # full-height z-rib of the x-bridged region (pieces between the hot slots)
HOT_BOUNDARY_X=-31.0         # = HOT_BOTTOM_MULLION_X: the underside-mouth mullion runs up the bay; between the slots
                             # (solid pieces) and above the top slot (windowed) it separates the x-bridged region
                             # (left) from the z-bridged front zone (right)
HOT_LANE_X=-60.4             # z-rib x -61.0..-59.8 left of the slots (their left ends x -59) from below the lowest to
                             # above the top slot: the strip of roof between the divider and the slot ends is within
                             # r7's 1.0 mm cantilever of a support on both sides
HOT_ZRIB_X=HOT_UZ_X+(HOT_BOUNDARY_X,HOT_LANE_X)
HOT_ZRIB_TOP=16.0
HOT_SLOTS=tuple((z,z+3.) for z in HOT_Z)
HOT_F_ROWS=(21.0,28.0,35.0,40.6,49.0,77.0)  # front-zone rows: 21/28/35 under the strips between the slots (28/35 stop
                             # 0.8 mm short of the slot ends), 40.6 on the top slot's upper edge (z 40.0..41.2, so
                             # no z-run in the front zone ends at a slot whose hole leaves the region), 49/77 above; row 21 is
                             # the front-mouth mullion
HOT_F_X=(HOT_BOUNDARY_X+RIB_T/2,-2.4)
HOT_STRIP_ROW_END=-17.3      # rows 21/28/35/40.6: 0.8 mm short of the slot ends (x -16.5), within r7's 1.0 mm cantilever
HOT_BAND_ROW=(10.0,-16.5,-2.6)   # z centre, x0, x1: floor of the z-bridged column right of the slots (the underside
                             # zone below it stays x-bridged)
HOT_COLUMN_X=-17.1           # z-rib x -17.7..-16.5 from the band row up to the lowest slot's lower edge: left side of
                             # the column below the slots (its top meets the slot's lower-right corner)
HOT_LIP_X=-3.2               # z-rib x -3.8..-2.6 from the bottom frame to the band row: the front-mouth lip below row 21
                             # is z-bridged, the underside zone left of it x-bridged
HOT_DIAGONAL=None            # trial3: no diagonal
HOT_LEFT_SEPARATOR=None      # trial3: removed (the underside zone and the port band are one x-bridged region)


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
    """Cold-bay x-direction rows: [(z_centre, [(x0, x1)])]. Rows inside the rear mouth's z range (5-75) start at the
    outer face, so they are its mullions; the others start in the rear frame. Row 18.45 lies just above the cold
    underside branch band (sections z 2.6-17.8) and stops before the lowest port; rows 22.5/28.5/34.5 sit under the
    strips between the port slots; 43-67 stop at the CSI block (one short row at 55 serves the column right of it).
    Trial3: no breaks; every row is a windowed beam (rib_boxes)."""
    xs,xf=-length,-length+2.4
    rows=[(z,[(xs,-64.9)]) for z in (22.5,28.5,34.5)]   # trial3: row 18.45 gone (the bay below row 22.5 spans 19.4)
    rows+=[(z,[(xs,-90.9)]) for z in (43.,51.,59.,67.)]
    rows.append((55.,[(-75.1,-64.9)]))
    rows+=[(z,[(xf,-64.9)]) for z in (76.,84.,92.)]
    return rows


def hot_rows(length):
    """Hot front-zone rows (z-bridged): [(z_centre, [(x0, x1)])]. Row 21 runs out through the front mouth as its
    mullion; rows 28/35 lie under the strips between the slots; the band row caps the underside zone under the
    column right of the slots."""
    a,b=HOT_F_X
    out=[]
    for z in HOT_F_ROWS:
        end=0. if z==HOT_FRONT_MULLION_Z else (HOT_STRIP_ROW_END if HOT_SLOTS[0][0]<z<HOT_SLOTS[-1][1]+RIB_T else b)
        out.append((z,[(a,end)]))
    z,x0,x1=HOT_BAND_ROW
    return out+[(z,[(x0,x1)])]


def _pieces(z0,z1):
    """[z0, z1] minus the hot slot bands (no rib in front of a port)."""
    out,cur=[],z0
    for a,b in HOT_SLOTS:
        if cur<a<z1:out.append((cur,a))
        cur=max(cur,b)
    if cur<z1:out.append((cur,z1))
    return [q for q in out if q[1]-q[0]>1e-6]


def hot_zribs():
    """Hot z-direction rib pieces: [(x_centre, z0, z1)]. The rib at HOT_BOTTOM_MULLION_X is the uncut frame in the
    underside mouth (z 0-2.5) and continues up the bay; the others start above the mouth's last sampled neck plane
    (z 2.62). Pieces stop at the slot edges, so no rib stands in front of a wall port."""
    out=[]
    for x in HOT_UZ_X+(HOT_BOUNDARY_X,):
        out+=[(x,a,b) for a,b in _pieces(2.4 if x==HOT_BOTTOM_MULLION_X else 2.75,97.6)]
    out.append((HOT_LIP_X,2.4,HOT_BAND_ROW[0]+RIB_T/2))
    out.append((HOT_LANE_X,HOT_SLOTS[0][0]-0.6,HOT_SLOTS[-1][1]+0.6))
    out.append((HOT_COLUMN_X,HOT_BAND_ROW[0]-RIB_T/2,HOT_SLOTS[0][0]))
    return out


def _windowed(lo,hi,must=(),solid=(),stagger=False):
    """Pillar intervals along a rib from lo to hi: both ends, every `must` position (centred) and every `solid`
    interval, then extra pillars so that no window is longer than WINDOW_MAX. stagger: the extra pillars of a gap
    sit half a pitch along (one more pillar), so neighbouring parallel ribs do not line their pillars up across the
    flow. -> sorted [(a, b)]."""
    P=PILLAR_L
    if hi-lo<=2*P+1e-9:return [(lo,hi)]
    fixed=sorted([(lo,lo+P),(hi-P,hi)]+[(max(lo,m-P/2),min(hi,m+P/2)) for m in must]+list(solid))
    merged=[list(fixed[0])]
    for a,b in fixed[1:]:
        if a<=merged[-1][1]+1e-9:merged[-1][1]=max(merged[-1][1],b)
        else:merged.append([a,b])
    out=[]
    for (a,b),(c,d) in zip(merged,merged[1:]):
        out.append((a,b))
        g=c-b
        k=0
        while (g-k*P)/(k+1)>WINDOW_MAX+1e-9:k+=1
        w=(g-k*P)/(k+1)
        ts=[b+(i+1)*w+i*P for i in range(k)]
        if stagger and k and w>P:
            ts=[t-(w+P)/2 for t in ts]+[ts[-1]+(w+P)/2]
        out+=[(t,t+P) for t in ts]
    out.append(tuple(merged[-1]))
    return [(round(a,6),round(b,6)) for a,b in out]


def rib_boxes(length):
    """Plain-data plenum rib material: [(x0, x1, y0, y1, z0, z1)]. Each rib = full-depth pillars (RIB_Y) plus one
    hanging beam over its whole length (BEAM_Y0 .. RIB_Y[1]); mouth mullion parts inside a frame are full depth."""
    y0,y1=RIB_Y;h=RIB_T/2;out=[]
    xf=-length+2.6
    rows=cold_rows(length)+hot_rows(length)
    alt={z:i%2==1 for i,z in enumerate(sorted({z for z,_ in cold_rows(length)}))}
    alt.update({z:i%2==1 for i,z in enumerate(sorted({z for z,_ in hot_rows(length)}))})
    for z,segs in rows:
        for a,b in segs:
            solid=[]
            if a<=-length:solid.append((a,xf))           # rear-mouth mullion through the frame
            if b>=0.:solid.append((-2.6,b))               # front-mouth mullion through the frame
            # cold rows: no pillar in front of the port band's left end (COLD_WINDOW_X), where the rear-mouth air turns
            # into the port channels (the path-aware min cut runs there); the keep-out is one window <= WINDOW_MAX
            must=[c for c in (COLD_WINDOW_X[0]-PILLAR_L/2,COLD_WINDOW_X[1]+PILLAR_L/2) if a+PILLAR_L<c<b] if b<=-65 else []
            for c,d in _windowed(a,b,must,solid,alt[z]):out.append((c,d,y0,y1,z-h,z+h))
            out.append((a,b,BEAM_Y0,y1,z-h,z+h))
    for x,za,zb in hot_zribs():
        must=[z for z in HOT_F_ROWS if x==HOT_BOUNDARY_X and za+PILLAR_L<z<zb-PILLAR_L]
        solid=[(za,2.6)] if za<2.5 else []                # mullion / frame landing through the bottom frame
        if x==HOT_BOUNDARY_X and zb-za<=4.0+1e-9:
            solid.append((za,zb))                         # pieces between the slots: front-zone row junctions
        for c,d in _windowed(za,zb,must,solid,x==HOT_BOUNDARY_X):out.append((x-h,x+h,y0,y1,c,d))
        out.append((x-h,x+h,BEAM_Y0,y1,za,zb))
    return out


def rib_polys(length):
    """Plain-data slanted rib material: [(pts_xz, y0, y1)]. Trial3 has none (no diagonal)."""
    return []


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


def ribs(length):
    """All plenum rib solids: rib_boxes (pillars and hanging beams) and the solid diagonal."""
    out=[box(a,b,c,d,e,f) for a,b,c,d,e,f in rib_boxes(length)]
    for pts,y0,y1 in rib_polys(length):
        out.append(prism([(x,y0,z) for x,z in pts],(0,y1-y0,0)))
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
    return dict(revision='trial3 windowed ribs (hanging beams on pillars) + lintels',rib_thickness_mm=RIB_T,rib_y_mm=list(RIB_Y),
                beam_y_mm=[BEAM_Y0,RIB_Y[1]],pillar_length_mm=PILLAR_L,window_max_mm=WINDOW_MAX,hot_boundary_x=HOT_BOUNDARY_X,hot_band_row=HOT_BAND_ROW,hot_column_x=HOT_COLUMN_X,hot_lip_x=HOT_LIP_X,
                cold_rows=[(z,segs) for z,segs in cold_rows(length)],hot_rows=[(z,segs) for z,segs in hot_rows(length)],
                hot_z_ribs=hot_zribs(),hot_diagonal=HOT_DIAGONAL,hot_left_separator=HOT_LEFT_SEPARATOR,
                cold_bottom_mullions_x=cold_bottom_mullions(length),hot_bottom_mullion_x=HOT_BOTTOM_MULLION_X,
                hot_front_mullion_z=HOT_FRONT_MULLION_Z,lintel_mm=LINTEL,lintel_land_mm=LINTEL_LAND,lintel_mouths=['cold_rear','cold_bottom'],
                skin_bed_chamfer_mm=BED_CHAMFER,mouths=mouth_nominal(length))


def metadata(length=158):
 mn=mouth_nominal(length)
 return dict(revision='shadow-gap plenum trial3 (windowed flow ribs, 45 deg cold-mouth lintels, mullions, skin bed chamfer)',outer_side_y_mm=OUTER_Y,inner_side_y_mm=INNER_Y,
  outer_skin_mm=1.6,plenum_gap_mm=GAP,original_side_wall_mm=2.5,
  intake_wall_throat_mm2=420.,exhaust_wall_throat_mm2=510.,
  cold_rear_mouth_mm2=mn['cold_rear']['net'],cold_bottom_mouth_mm2=mn['cold_bottom']['net'],hot_bottom_mouth_mm2=mn['hot_bottom']['net'],hot_front_mouth_mm2=mn['hot_front']['net'],
  mouth_gross_mm2={k:v['gross'] for k,v in mn.items()},
  csi_access_open_area_mm2=12*27-(4-math.pi),csi_unchanged_straight_access=True,
  panel_previous_relief='Four blind grooves with0.2mm retained floors, not through-vents; removed for plain2.8mm panel',
  airflow='Separate integral cold/hot outer bays; rear/underside intake and front/underside exhaust. 1.2 mm ribs built as hanging beams on full-depth pillars (5 mm flow windows under each beam, no rib in front of a port; path-aware min cut in check_scope); internal baffle and CSI bypass remain unsealed. Area is not flow or cooling.',
  print='Outer face on bed with 0.6 mm bed chamfer. Roof bridges run between continuous 1.2 mm beam lines (one slicer direction per roof region; each beam is a straight bridge of at most 10 mm between pillars; spans computed by verify_print_checks print_bridge_direction); cold mouths have 45 deg lintels, every mouth has mullions. Slicer inspection and the all-four-mouth plenum coupon remain gates. No automatic trapped supports.',
  support=support_summary(length),
  physical_qualified=False,remaining=['Actual cooler profile/registration','Fan operating point and plenum pressure loss','Hand and strap occlusion','Plenum bridge/cleanout coupon (all four mouths)','Real CSI latch/jaw access','All56 inherited gates andM1'])

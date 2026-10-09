"""Lorlin CK1044 source-based envelope; actual receipt, pins and fit remain gates.

The baseline CK1049/D-shaft combination was inconsistent with Lorlin's table.
No baseline module is modified. Nut/washer and terminal sections are declared
reservations, not dimensions certified by the manufacturer.
"""
import copy, math
import cadquery as cq
import cots, printed_small, layout as L
V=cq.Vector
SOURCE='https://lorlinelectronics.co.uk/wp-content/uploads/2020/11/CK-ROTARY-Nov-2020-1.pdf'
X=-111.0; Z=80.0; MOUNT_Y=25.2; BODY_REAR_Y=11.1
BUSH_END_Y=33.2; SHAFT_END_Y=37.0
KNOB_Y=(30.2,37.2); KNOB_DIAMETER=24.0
FLAT_POSITION1_DEG=90.0; POINTER_POSITION1_DEG=-15.0
# PCB-front drawing mapped to the +Y exterior view: screen-right is negative X.
# Confirm actual molded numbering/clocking and selected A/2 continuity on receipt.
PCB_SCREEN_X_SIGN=-1.0

def cy(r,y0,y1,x=X,z=Z):
 return cq.Solid.makeCylinder(r,y1-y0,V(x,y0,z),V(0,1,0))

def pin_centres():
 rows=[]
 for i in range(1,13):
  a=math.radians(255-30*(i-1))
  rows.append(dict(id=str(i),x=X+PCB_SCREEN_X_SIGN*11.1*math.cos(a),z=Z+11.1*math.sin(a)))
 a=math.radians(225)
 rows.append(dict(id='A',x=X+PCB_SCREEN_X_SIGN*3.85*math.cos(a),z=Z+3.85*math.sin(a)))
 return rows

def switch_parts():
 body=cy(13.75,BODY_REAR_Y,MOUNT_Y)
 bush=cy(4.76,MOUNT_Y-.01,BUSH_END_Y)
 shaft=cots._d_shaft_y(X,Z,3.175,5.5,BUSH_END_Y-.01,SHAFT_END_Y)
 shaft=shaft.rotate((X,0,Z),(X,1,Z),-FLAT_POSITION1_DEG)
 # Max specified peg diameter3.15;2mm axial projection has no stated tolerance.
 peg=cy(1.575,MOUNT_Y-.01,MOUNT_Y+2,X,Z-9.5)
 # Actual pin cross-section is not published. PCBholeØ1.5 plus0.1radial
 # clearance is a provisional conservative reservation, not pin metrology.
 pins=[cy(.85,7.1,BODY_REAR_Y+.05,p['x'],p['z']) for p in pin_centres()]
 switch=body.fuse(bush,shaft,peg,*pins)
 # Existing hardware estimates retained explicitly until received hardware is measured.
 washer=cy(7.5,28,28.6).cut(cy(4.9,27.9,28.7))
 nut=cots._hex_y(12.7,X,Z,28.6,31).cut(cy(4.82,28.5,31.1))
 parts={'switch_1824':switch,'fps_nut':nut,'fps_mounting_washer':washer}
 for n,s in parts.items():
  if not s.isValid() or len(s.Solids())!=1:raise ValueError('Invalid corrected FPS part:'+n)
 return parts

def knob():
 oldk,olds,oldo=L.KNOBS,L.SWITCH_1824,printed_small.KNOB
 try:
  L.KNOBS=copy.deepcopy(oldk);L.SWITCH_1824=copy.deepcopy(olds)
  L.KNOBS['knob_fps'].update(c=(X,Z),d=KNOB_DIAMETER,y=KNOB_Y,bore='D 6.35/5.5',index_deg=FLAT_POSITION1_DEG)
  L.SWITCH_1824['bushing']['a']=(MOUNT_Y,BUSH_END_Y)
  printed_small.KNOB=copy.deepcopy(oldo);printed_small.KNOB['knob_fps'].pop('index')
  s=printed_small.build_part(L,'knob_fps').val()
 finally:L.KNOBS,L.SWITCH_1824,printed_small.KNOB=oldk,olds,oldo
 # Pointer is independently indexed from the D-flat:30degree real detents,
 # not the inherited90degree label/flat assumption.
 a=math.radians(POINTER_POSITION1_DEG);n=(-math.sin(a),math.cos(a));t=(-n[1],n[0])
 pts=[(X+n[0]*r+t[0]*q*.6,Z+n[1]*r+t[1]*q*.6) for r,q in ((5,-1),(10,-1),(10,1),(5,1))]
 s=s.cut(printed_small._xz_prism(pts,KNOB_Y[1]-.6,KNOB_Y[1]+.1))
 if not s.isValid() or len(s.Solids())!=1:raise ValueError('Invalid CK1044 knob')
 return s

def provenance():
 return dict(part='Lorlin CK1044',source=SOURCE,body_diameter_mm=27.5,body_axial_mm=14.1,
  mounting_face_y=MOUNT_Y,bushing=dict(diameter_mm=9.52,thread='3/8-32 imperial',projection_mm=8),
  shaft=dict(stock_length_from_mounting_face_mm=38,diameter_mm=6.35,flat_across_mm=5.5,flat_length_mm=30,
             trim_end_y=SHAFT_END_Y,trim_length_from_mounting_face_mm=SHAFT_END_Y-MOUNT_Y,
             nominal_flat_engagement_after_recess_mm=SHAFT_END_Y-(BUSH_END_Y+L.FDM['SLIDE'])),
  detents=dict(travel_deg=30,stop_positions=2,pointer_deg=[-15,15],flat_position1_deg=90,
               wiring='A and throw2:position1 open/high=18fps;position2 closed/low=24fps. Verify molded labels and continuity.'),
  pin_count=13,pin_centres=pin_centres(),pin_projection_mm=4,pin_radius_reserve_mm=.85,
  mass_note='Original12g assembly estimate retained across body/nut/washer; actual supplied mass and stop-ring geometry remain unmeasured.',
  open_gates=['Actual pin section, PCB view/clocking and solder fanout','Supplied nut, mounting washer and stop/tang washer inventory and dimensions',
              'Shaft trim/deburr, bore coupon, press/pull force and flat engagement','Two-position stop and actual18/24 continuity',
              'Peg offset/projection tolerance, panel mounting torque and creep'])

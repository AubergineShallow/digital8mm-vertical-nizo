"""Integral outer shadow plenum. Nominal geometry only; no thermal qualification."""
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
def box(a,b,c,d,e,f):return cq.Solid.makeBox(b-a,d-c,f-e,V(a,c,e))
def inlet_cuts():return [box(-103,-68,-28.1,-25.4,z,z+3) for z in SIDE_Z]
def side_exhaust_cuts():return [box(-59,-16.5,-28.1,-25.4,z,z+3) for z in HOT_Z]
def front_exhaust_cuts():return []
def mouth_cuts(length):return [
 box(-length-.1,-length+2.6,SKIN_INNER,WALL_OUTER,5,75),
 box(-length+4,-83,SKIN_INNER,WALL_OUTER,-.1,2.6),
 box(-59,-5,SKIN_INNER,WALL_OUTER,-.1,2.6),
 box(-2.6,.1,SKIN_INNER,WALL_OUTER,5,40)]
def post_centres(length):
 pts=set()
 for x in range(int(-length+8),-6,8):
  for z in range(8,94,8):pts.add((float(x),float(z)))
 for z in (22.5,28.5,34.5):
  for x in (-100.,-92.,-84.,-76.,-69.):pts.add((x,z))
 for z in (21.,28.,35.,43.):
  for x in (-56.,-48.,-40.,-32.,-24.,-18.):pts.add((x,z))
 def blocked(x,z):
  if -92<x<-74 and 38<z<71:return True
  if -104<x<-67 and any(a-1<z<a+4 for a in SIDE_Z):return True
  if -60<x<-15.5 and any(a-1<z<a+4 for a in HOT_Z):return True
  if -66<x<-61:return True
  return False
 return sorted((x,z) for x,z in pts if not blocked(x,z))
def additions(length):
 # Face is uninterrupted except the required CSI service aperture. Frame and
 # separated cold/hot bays are integral; no new fastener or loose cover.
 a=[box(-length,0,OUTER_Y,SKIN_INNER,0,100),
 box(-length,-length+2.5,SKIN_INNER-.05,-25.4,0,100),
 box(-2.5,0,SKIN_INNER-.05,-25.4,0,100),
 box(-length,0,SKIN_INNER-.05,-25.4,0,2.5),
 box(-length,0,SKIN_INNER-.05,-25.4,97.5,100),
 box(-65,-62,SKIN_INNER-.05,-27.9,2.4,97.6),
 box(-91,-75,SKIN_INNER-.05,-27.9,39,70)]
 for x,z in post_centres(length):a.append(cq.Solid.makeCylinder(.8,6.15,V(x,SKIN_INNER-.05,z),V(0,1,0)))
 return a

def metadata(length=158):
 return dict(revision='shadow-gap plenum trial1',outer_side_y_mm=OUTER_Y,inner_side_y_mm=INNER_Y,
  outer_skin_mm=1.6,plenum_gap_mm=GAP,original_side_wall_mm=2.5,
  intake_wall_throat_mm2=420.,exhaust_wall_throat_mm2=510.,
  cold_rear_mouth_mm2=420.,cold_bottom_mouth_mm2=(length-87)*GAP,hot_bottom_mouth_mm2=324.,hot_front_mouth_mm2=210.,
  csi_access_open_area_mm2=12*27-(4-math.pi),csi_unchanged_straight_access=True,
  panel_previous_relief='Four blind grooves with0.2mm retained floors, not through-vents; removed for plain2.8mm panel',
  airflow='Separate integral cold/hot outer bays; rear/underside intake and front/underside exhaust. Internal baffle and CSI bypass remain unsealed. Area is not flow or cooling.',
  print='Outer face on bed;1.6mm integral posts nominal8mm grid. Internal roof bridges and inaccessible support removal require a representative plenum coupon and slicer inspection. No automatic trapped supports.',
  physical_qualified=False,remaining=['Actual cooler profile/registration','Fan operating point and plenum pressure loss','Hand and strap occlusion','Plenum bridge/cleanout coupon','Real CSI latch/jaw access','All56 inherited gates andM1'])
